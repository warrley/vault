#!/usr/bin/env python3
"""
Geração de Figuras de Alto Padrão Científico para o Paper 1 (Calor 2D + Burgers 2D)
Estilo:
  - Fontes: Times New Roman / STIX Serif
  - Burgers: Estilo idêntico ao repositório pinns/burger (contourf/imshow 'jet' + quiver branco de velocidade)
  - Calor: Superfície 3D de alta qualidade com colormap 'coolwarm' / 'jet' e contorno na base
  - Perdas: Gráficos de convergência semilogarítmica ampliados, claros e nítidos
"""

import os, warnings
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
warnings.filterwarnings('ignore')

plt.rcParams.update({
    'font.family':        'serif',
    'font.serif':         ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size':          8.5,
    'axes.labelsize':     8.5,
    'axes.titlesize':     9.0,
    'xtick.labelsize':    7.5,
    'ytick.labelsize':    7.5,
    'legend.fontsize':    7.2,
    'figure.dpi':         300,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'mathtext.fontset':   'stix',
})

ROOT = "/home/warley/vault/research/eu/paper1_heat_burgers"
FIG_DIR = os.path.join(ROOT, "figures")
MDIR = os.path.join(ROOT, "models")
os.makedirs(FIG_DIR, exist_ok=True)

# ─── Modelo PINN ─────────────────────────────────────────────────────────────
class PINN(nn.Module):
    def __init__(self, in_dim, out_dim, hidden=64, layers=4):
        super().__init__()
        seq = [nn.Linear(in_dim, hidden), nn.Tanh()]
        for _ in range(layers - 1):
            seq += [nn.Linear(hidden, hidden), nn.Tanh()]
        seq += [nn.Linear(hidden, out_dim)]
        self.net = nn.Sequential(*seq)
    def forward(self, x):
        return self.net(x)

def load_burgers():
    ckpt = torch.load(os.path.join(MDIR, 'pinn_burgers_2d_20k.pth'),
                      map_location='cpu', weights_only=False)
    model = PINN(3, 2)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model, ckpt.get('nu', 0.01), ckpt.get('loss_history', None)

def load_heat():
    ckpt = torch.load(os.path.join(MDIR, 'pinn_heat_2d_20k.pth'),
                      map_location='cpu', weights_only=False)
    model = PINN(3, 1)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model, ckpt.get('alpha', 0.1), ckpt.get('loss_history', None)

def predict_burgers(model, x, y, t):
    with torch.no_grad():
        inp = torch.tensor(np.stack([x, y, np.full_like(x, t)], axis=1), dtype=torch.float32)
        out = model(inp).numpy()
    u, v = out[:, 0], out[:, 1]
    return u, v, np.sqrt(u**2 + v**2)

def predict_heat(model, x, y, t):
    with torch.no_grad():
        inp = torch.tensor(np.stack([x, y, np.full_like(x, t)], axis=1), dtype=torch.float32)
        return model(inp).numpy().squeeze()

def _save(fig, name):
    for target in [FIG_DIR, os.path.join(ROOT, "new_figures")]:
        os.makedirs(target, exist_ok=True)
        fig.savefig(os.path.join(target, name + '.pdf'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(target, name + '.png'), dpi=300, bbox_inches='tight')
    print(f"  [OK] Salvo: {name}.pdf / .png")
    plt.close(fig)

# =============================================================================
# 1. FIGURA DE CONVERGÊNCIA AMPLIADA (Fig. 2)
# =============================================================================
def generate_loss_curves():
    print("[1] Gerando Curvas de Perda Ampliadas...")
    _, nu, lh_b = load_burgers()
    _, alpha, lh_h = load_heat()

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))

    # (a) Calor 2D
    if lh_h is not None:
        ax = axes[0]
        ep = lh_h['epoch']
        ax.semilogy(ep, lh_h['total'], label=r'$\mathcal{L}_{\mathrm{total}}$ (Perda Total)', color='#1f77b4', lw=1.6)
        ax.semilogy(ep, lh_h['pde'],   label=r'$\mathcal{L}_{\mathrm{pde}}$ (Resíduo EDP)',   color='#d62728', lw=1.2, ls='--')
        ax.semilogy(ep, lh_h['ic'],    label=r'$\mathcal{L}_{\mathrm{ic}}$ (Condição Inicial)', color='#2ca02c', lw=1.2, ls='-.')
        ax.semilogy(ep, lh_h['bc'],    label=r'$\mathcal{L}_{\mathrm{bc}}$ (Condição Contorno)', color='#ff7f0e', lw=1.2, ls=':')
        ax.set_xlabel('Épocas de Treinamento', fontsize=8.5)
        ax.set_ylabel('Erro Médio Quadrático (MSE)', fontsize=8.5)
        ax.grid(True, which='major', ls='-', alpha=0.35)
        ax.grid(True, which='minor', ls=':', alpha=0.15)
        ax.legend(fontsize=7.2, framealpha=0.92, loc='upper right')
        ax.set_title(r'(a) Equação do Calor 2D ($\alpha = 0{,}1\,\mathrm{m^2/s}$)', fontsize=8.8, pad=4)
        ax.set_xlim(0, max(ep))

    # (b) Burgers 2D
    if lh_b is not None:
        ax = axes[1]
        ep = lh_b['epoch']
        ax.semilogy(ep, lh_b['total'], label=r'$\mathcal{L}_{\mathrm{total}}$ (Perda Total)', color='#1f77b4', lw=1.6)
        ax.semilogy(ep, lh_b['pde'],   label=r'$\mathcal{L}_{\mathrm{pde}}$ (Resíduo EDP)',   color='#d62728', lw=1.2, ls='--')
        ax.semilogy(ep, lh_b['ic'],    label=r'$\mathcal{L}_{\mathrm{ic}}$ (Condição Inicial)', color='#2ca02c', lw=1.2, ls='-.')
        ax.semilogy(ep, lh_b['bc'],    label=r'$\mathcal{L}_{\mathrm{bc}}$ (Condição Contorno)', color='#ff7f0e', lw=1.2, ls=':')
        ax.set_xlabel('Épocas de Treinamento', fontsize=8.5)
        ax.set_ylabel('Erro Médio Quadrático (MSE)', fontsize=8.5)
        ax.grid(True, which='major', ls='-', alpha=0.35)
        ax.grid(True, which='minor', ls=':', alpha=0.15)
        ax.legend(fontsize=7.2, framealpha=0.92, loc='upper right')
        ax.set_title(r'(b) Equação de Burgers 2D ($\nu = 0{,}01\,\mathrm{m^2/s}$)', fontsize=8.8, pad=4)
        ax.set_xlim(0, max(ep))

    plt.tight_layout()
    _save(fig, 'fig_loss_curves')

# =============================================================================
# 2. FIGURA DO CALOR 2D — SUPERFÍCIES 3D DE ALTA QUALIDADE (Fig. 3)
# =============================================================================
def generate_heat_figure():
    print("[2] Gerando Superfícies 3D da Equação do Calor...")
    model, alpha, _ = load_heat()

    times = [0.0, 0.3, 0.7, 1.0]
    labels = [r'(a) $t = 0{,}0\,\mathrm{s}$', r'(b) $t = 0{,}3\,\mathrm{s}$',
              r'(c) $t = 0{,}7\,\mathrm{s}$', r'(d) $t = 1{,}0\,\mathrm{s}$']
    N = 100

    xi = np.linspace(0, 1, N)
    yi = np.linspace(0, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    data = [predict_heat(model, xf, yf, t).reshape(N, N) for t in times]

    fig = plt.figure(figsize=(7.2, 2.35))
    surf_last = None
    for i, (lbl, Z) in enumerate(zip(labels, data)):
        ax = fig.add_subplot(1, 4, i+1, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='coolwarm', vmin=0.0, vmax=1.0,
                               linewidth=0, antialiased=True, alpha=0.95,
                               rstride=1, cstride=1)
        surf_last = surf
        # Projeção de isotermas na base z=0
        ax.contourf(X, Y, Z, zdir='z', offset=0.0, cmap='coolwarm',
                    vmin=0.0, vmax=1.0, alpha=0.35, levels=15)
        ax.set_zlim(0.0, 1.05)
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        ax.set_xlabel('$x$', fontsize=7.2, labelpad=-4)
        ax.set_ylabel('$y$', fontsize=7.2, labelpad=-4)
        ax.set_zlabel('$u$', fontsize=7.2, labelpad=-5)
        ax.set_title(lbl, fontsize=8.2, pad=1)
        ax.view_init(elev=28, azim=-55)
        ax.tick_params(labelsize=6.0, pad=0.5)

    plt.subplots_adjust(left=0.01, right=0.89, bottom=0.10, top=0.90, wspace=0.12)
    cbar_ax = fig.add_axes([0.91, 0.20, 0.015, 0.60])
    cb = fig.colorbar(surf_last, cax=cbar_ax)
    cb.set_label('Temperatura $u$', fontsize=7.8)
    cb.ax.tick_params(labelsize=6.5)

    _save(fig, 'fig_h3_heat_3d_large')

# =============================================================================
# 3. FIGURA DE BURGERS 2D — ESTILO PINNS/BURGER (JET + QUIVER) (Fig. 4)
# =============================================================================
def generate_burgers_figure():
    print("[3] Gerando Campos Vetoriais de Burgers 2D (Estilo pinns/burger)...")
    model, nu, _ = load_burgers()

    times = [0.0, 0.3, 0.5, 1.0]
    titles = [
        r'(a) $t = 0{,}0\,\mathrm{s}$',
        r'(b) $t = 0{,}3\,\mathrm{s}$',
        r'(c) $t = 0{,}5\,\mathrm{s}$',
        r'(d) $t = 1{,}0\,\mathrm{s}$'
    ]
    N, NQ = 200, 20

    xi = np.linspace(-1, 1, N); yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    xq = np.linspace(-1, 1, NQ); yq = np.linspace(-1, 1, NQ)
    Xq, Yq = np.meshgrid(xq, yq)
    xqf, yqf = Xq.ravel(), Yq.ravel()

    data = []
    for t in times:
        u, v, spd = predict_burgers(model, xf, yf, t)
        uq, vq, _ = predict_burgers(model, xqf, yqf, t)
        data.append((spd.reshape(N, N), uq.reshape(NQ, NQ), vq.reshape(NQ, NQ)))

    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.15), sharey=True)
    im_ref = None

    for i, (title, ax) in enumerate(zip(titles, axes)):
        SPD, Uq, Vq = data[i]
        im = ax.imshow(SPD, extent=[-1, 1, -1, 1], origin='lower',
                       cmap='jet', vmin=0.0, vmax=1.0, aspect='equal')
        if i == 0:
            im_ref = im

        # Quiver branco representando o campo vetorial de velocidade
        spq = np.sqrt(Uq**2 + Vq**2)
        nf  = np.where(spq > 1e-5, spq, 1e-5)
        Un, Vn = Uq / nf, Vq / nf
        scale = spq / 1.0
        mask = scale > 0.03
        if mask.any():
            ax.quiver(Xq[mask], Yq[mask],
                      Un[mask] * scale[mask],
                      Vn[mask] * scale[mask],
                      color='white', alpha=0.90,
                      scale=15, width=0.0075,
                      headwidth=3.5, headlength=4.0,
                      pivot='mid')

        ax.set_title(title, fontsize=8.2, pad=3)
        ax.set_xlabel('$x$', fontsize=8.0, labelpad=2)
        if i == 0:
            ax.set_ylabel('$y$', fontsize=8.0, labelpad=2)
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        ax.tick_params(labelsize=7.0)

    # Ajuste manual e elegante para não sobrepor plots nem colorbar
    plt.subplots_adjust(left=0.07, right=0.88, bottom=0.18, top=0.88, wspace=0.18)
    cbar_ax = fig.add_axes([0.90, 0.20, 0.016, 0.66])
    cbar = fig.colorbar(im_ref, cax=cbar_ax)
    cbar.set_label(r'Magnitude $\|\mathbf{u}\| = \sqrt{u^2 + v^2}$ [m/s]', fontsize=7.5)
    cbar.ax.tick_params(labelsize=6.8)
    _save(fig, 'fig_b2_burgers_collision')

if __name__ == '__main__':
    print("=" * 60)
    print("Regenerando Figuras — Paper 1 (Calor e Burgers 2D)")
    print("=" * 60)
    generate_loss_curves()
    generate_heat_figure()
    generate_burgers_figure()
    print("=" * 60)
    print("Sucesso!")
