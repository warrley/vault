#!/usr/bin/env python3
"""
Gera os gráficos de alta qualidade para o Artigo 2 (Heat 2D Irregular Domain):
1. fig_loss_other_style.pdf / .png: Estilo inspirado em other_loss.py com linhas finas, fontes Stix/CM e legendas matemáticas (\mathcal{L}).
2. fig_chapa_evolution.pdf / .png: Sequência temporal 2D da chapa (t=0.1, 0.5, 1.0, 2.0s) com furos demarcados e escala adequada.
3. fig_chapa_nomask_extrapol.pdf / .png: Comparativo t=2.0s (sem máscara, evidenciando o relevo contínuo) e t=5.0s (extrapolação temporal).
"""

import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Tipografia padrão científico
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 9.5,
    'axes.labelsize': 10.5,
    'axes.titlesize': 11.0,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'legend.fontsize': 8.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'cm'
})

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ckpt_path = "./paper2_heat_irregular_domain/models/pinn_heat_holes_checkpoint.pth"
fig_dir = "./paper2_heat_irregular_domain/figures"
os.makedirs(fig_dir, exist_ok=True)

print(f"[*] Carregando checkpoint: {ckpt_path}")
checkpoint = torch.load(ckpt_path, map_location='cpu', weights_only=False)

# ------------------------------------------------------------------------------
# 1. FIGURA DA FUNÇÃO DE PERDA (Estilo other_loss.py)
# ------------------------------------------------------------------------------
history = checkpoint['loss_history']
ep_raw = np.array(history['epoch'])
step = 50
freq = ep_raw[1] - ep_raw[0] if len(ep_raw) > 1 else 1
jump = max(1, int(step / freq))
ep_plot = ep_raw[::jump]

plot_config = {
    'total': (r'$\mathcal{L}_{\mathrm{total}}$', '#1f77b4', 1.2, '-'),
    'pde': (r'$\mathcal{L}_{\mathrm{pde}}$', '#d62728', 0.85, '-'),
    'bc_holes': (r'$\mathcal{L}_{\mathrm{furos}}$ ($u|_{\partial\mathcal{H}_k}=0$)', '#2ca02c', 0.85, '-'),
    'bc_ext': (r'$\mathcal{L}_{\mathrm{ext}}$ ($u|_{\partial\Omega_{\mathrm{ext}}}=1$)', '#9467bd', 0.85, '-'),
    'ic': (r'$\mathcal{L}_{\mathrm{ic}}$ ($u|_{t=0}=0$)', '#ff7f0e', 0.85, '-')
}

plt.figure(figsize=(7.0, 3.4))
for k, (label, color, lw, ls) in plot_config.items():
    if k in history:
        vals = np.array(history[k])[::jump]
        plt.semilogy(ep_plot, vals, label=label, color=color, lw=lw, ls=ls)

# Destaque da rigidez em 26k épocas
plt.axvline(26000, color='gray', linestyle='--', lw=0.8, alpha=0.7)
plt.text(26300, 3e-3, r'Rigidez numérica ($\sim 26\mathrm{k}$)', fontsize=8, color='#333333', rotation=90)

plt.grid(True, which='major', ls='-', alpha=0.35)
plt.grid(True, which='minor', ls=':', alpha=0.15)
plt.legend(loc='upper right', framealpha=0.92, edgecolor='lightgray', ncol=2)
plt.xlabel('Épocas de Treinamento')
plt.ylabel('Erro Quadrático Médio (MSE)')
plt.xlim(0, 50000)
loss_fig_path = os.path.join(fig_dir, "fig_loss_detailed.pdf")
plt.savefig(loss_fig_path)
plt.savefig(os.path.join(fig_dir, "fig_loss_detailed.png"))
plt.close()
print(f"[OK] Gráfico de perda gerado em: {loss_fig_path}")

# ------------------------------------------------------------------------------
# 2. PLOTS DA CHAPA (EVOLUÇÃO TÉRMICA 2D)
# ------------------------------------------------------------------------------
class IrregularHeatPINN(nn.Module):
    def __init__(self, hidden_dim=128, num_layers=5):
        super().__init__()
        layers = [nn.Linear(3, hidden_dim), nn.Tanh()]
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x, y, t):
        return self.net(torch.cat([x, y, t], dim=1))

model = IrregularHeatPINN(hidden_dim=128, num_layers=5).to(device)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

L = 1.0
holes = [(0.30, 0.30, 0.12), (0.70, 0.30, 0.12), (0.50, 0.70, 0.12)]
nx, ny = 180, 180
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_flat, YP_flat = XP.flatten(), YP.flatten()

XP_val = torch.tensor(XP_flat, dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP_flat, dtype=torch.float32, device=device).unsqueeze(1)

# Máscara binária dos furos
mask_holes = np.zeros_like(XP, dtype=bool)
for (hx, hy, hr) in holes:
    mask_holes |= ((XP - hx)**2 + (YP - hy)**2 <= hr**2)

eval_times = [0.1, 0.5, 1.0, 2.0]
fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.05), sharey=True, dpi=300)

for idx, t_val in enumerate(eval_times):
    TP_val = torch.full_like(XP_val, t_val, device=device)
    with torch.no_grad():
        U_pred = model(XP_val, YP_val, TP_val).cpu().numpy().reshape(nx, ny)
    
    # Mascarar os furos para visão física no domínio
    U_vis = np.ma.masked_array(U_pred, mask=mask_holes)
    
    im = axes[idx].imshow(U_vis, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
    axes[idx].contour(XP, YP, U_pred, levels=[0.2, 0.4, 0.6, 0.8], colors='cyan', linewidths=0.5, alpha=0.7)
    
    for (hx, hy, hr) in holes:
        axes[idx].add_patch(plt.Circle((hx, hy), hr, color='lime', fill=True, facecolor='white', lw=1.2, ls='--', zorder=4))
        
    axes[idx].set_title(f"$t = {t_val}\\,\\mathrm{{s}}$", fontsize=9.0, pad=4)
    axes[idx].set_xlabel("$x$ [m]", fontsize=8.5)
    axes[idx].tick_params(labelsize=7.5)
    if idx == 0:
        axes[idx].set_ylabel("$y$ [m]", fontsize=8.5)

cbar_ax = fig.add_axes([0.92, 0.22, 0.015, 0.62])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label('Temperatura $u(x, y, t)$', fontsize=8.5)
cbar.ax.tick_params(labelsize=7.5)

plt.subplots_adjust(left=0.07, right=0.90, bottom=0.20, top=0.88, wspace=0.12)
chapa_fig_path = os.path.join(fig_dir, "fig3_thermal_evolution.pdf")
plt.savefig(chapa_fig_path)
plt.savefig(os.path.join(fig_dir, "fig3_thermal_evolution.png"))
plt.close()
print(f"[OK] Evolução térmica gerada em: {chapa_fig_path}")

# ------------------------------------------------------------------------------
# 3. PLOTS: SEM MÁSCARA (t=2.0s) E EXTRAPOLAÇÃO (t=5.0s)
# ------------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.2, 2.6), dpi=300)

# Painel 1: t=2.0s sem máscara
TP_val_2 = torch.full_like(XP_val, 2.0, device=device)
with torch.no_grad():
    U_nomask_2 = model(XP_val, YP_val, TP_val_2).cpu().numpy().reshape(nx, ny)

im1 = ax1.imshow(U_nomask_2, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=-0.8, vmax=1.0)
ax1.contour(XP, YP, U_nomask_2, levels=6, colors='cyan', linewidths=0.5, alpha=0.7)
for (hx, hy, hr) in holes:
    ax1.add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=1.3, ls='--'))
ax1.set_title('(a) $t=2{,}0\\,\\mathrm{s}$ (Sem Máscara Visual)', fontsize=9.0)
ax1.set_xlabel('$x$ [m]', fontsize=8.5); ax1.set_ylabel('$y$ [m]', fontsize=8.5)
ax1.tick_params(labelsize=7.5)
cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
cbar1.ax.tick_params(labelsize=7.0)

# Painel 2: t=5.0s extrapolação
TP_val_5 = torch.full_like(XP_val, 5.0, device=device)
with torch.no_grad():
    U_extrapol_5 = model(XP_val, YP_val, TP_val_5).cpu().numpy().reshape(nx, ny)

im2 = ax2.imshow(U_extrapol_5, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
ax2.contour(XP, YP, U_extrapol_5, levels=6, colors='cyan', linewidths=0.5, alpha=0.7)
for (hx, hy, hr) in holes:
    ax2.add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=1.3, ls='--'))
ax2.set_title('(b) $t=5{,}0\\,\\mathrm{s}$ (Extrapolação Cega)', fontsize=9.0)
ax2.set_xlabel('$x$ [m]', fontsize=8.5)
ax2.tick_params(labelsize=7.5)
cbar2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
cbar2.ax.tick_params(labelsize=7.0)

plt.tight_layout()
diag_fig_path = os.path.join(fig_dir, "fig4_nomask_extrapol.pdf")
plt.savefig(diag_fig_path)
plt.savefig(os.path.join(fig_dir, "fig4_nomask_extrapol.png"))
plt.close()
print(f"[OK] Diagnóstico sem máscara gerado em: {diag_fig_path}")
