#!/usr/bin/env python3
"""
Utilitário Avançado de Plotagem de Perdas para PINNs
Gera gráficos de convergência de alta qualidade (padrão IEEE/Elsevier).
Estilo: Linhas finas, contínuas, escala logarítmica e grid suave.
"""

import os
import argparse
import torch
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_loss_convergence(
    checkpoint_path,
    output_path,
    step=100,
    title="Convergência da Função de Perda (PINN)",
):
    # Configurações tipográficas para artigos científicos
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "mathtext.fontset": "cm",  # Fonte padrão LaTeX / Computer Modern para os símbolos matemáticos
        }
    )

    print(f"[*] Carregando checkpoint: {checkpoint_path}")
    if not os.path.exists(checkpoint_path):
        print("[!] Arquivo não encontrado.")
        return

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    if "loss_history" not in checkpoint:
        print("[!] O checkpoint não contém 'loss_history'.")
        return

    history = checkpoint["loss_history"]

    # Determinar a amostragem baseada nos arrays
    epochs_raw = np.array(history["epoch"])
    freq_salvamento = epochs_raw[1] - epochs_raw[0] if len(epochs_raw) > 1 else 1
    jump = max(1, int(step / freq_salvamento))

    ep_plot = epochs_raw[::jump]

    # Mapeamento com o L caligráfico (\mathcal{L}) e subscritos em fonte romana
    plot_config = {
        "total": (r"$\mathcal{L}_{\mathrm{total}}$", "#1f77b4", 1.2),  # Azul mais forte
        "pde": (r"$\mathcal{L}_{\mathrm{pde}}$", "#d62728", 0.8),  # Vermelho fino
        "bc": (r"$\mathcal{L}_{\mathrm{bc}}$", "#2ca02c", 0.8),  # Verde fino
        "bc_holes": (
            r"$\mathcal{L}_{\mathrm{bc\_holes}}$",
            "#2ca02c",
            0.8,
        ),  # Verde fino
        "bc_ext": (r"$\mathcal{L}_{\mathrm{bc\_ext}}$", "#9467bd", 0.8),  # Roxo fino
        "ic": (r"$\mathcal{L}_{\mathrm{ic}}$", "#ff7f0e", 0.8),  # Laranja fino
    }

    plt.figure(figsize=(7.0, 4.2))

    for key in ["total", "pde", "bc", "bc_holes", "bc_ext", "ic"]:
        if key in history and len(history[key]) > 0:
            val_plot = np.array(history[key])[::jump]
            label, color, lw = plot_config[key]
            plt.semilogy(ep_plot, val_plot, label=label, lw=lw, color=color, ls="-")

    plt.grid(True, which="major", ls="-", alpha=0.3)
    plt.grid(True, which="minor", ls=":", alpha=0.2)
    plt.legend(loc="upper right", framealpha=0.95, edgecolor="gray")
    plt.xlabel("Épocas")
    plt.ylabel("MSE")
    plt.title(title, pad=12)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    print(f"[OK] Gráfico gerado com sucesso em: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plota o gráfico de convergência de uma PINN."
    )
    parser.add_argument(
        "-c", "--checkpoint", required=True, help="Caminho para o arquivo .pth"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Caminho para salvar o .png/.pdf"
    )
    parser.add_argument(
        "-s", "--step", type=int, default=100, help="Salto de épocas (ex: 100)"
    )
    parser.add_argument(
        "-t",
        "--title",
        type=str,
        default="Convergência das Perdas",
        help="Título do Gráfico",
    )

    args = parser.parse_args()
    plot_loss_convergence(args.checkpoint, args.output, args.step, args.title)
