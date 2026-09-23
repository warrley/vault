#!/usr/bin/env python3
"""
Gera figuras de alta qualidade 3D da norma ||u|| da Equação de Burgers 2D
para o Paper 1 (paper1_heat_burgers) em:
  - t = 0.0 s  →  figures/burgers_3d_t0.png  + .pdf
  - t = 0.5 s  →  figures/burgers_3d_t05.png + .pdf
  - Pair combinada →  figures/fig_b2_burgers_3d_pair.png + .pdf

Parâmetros de qualidade:
  - Grid: 300x300 pontos
  - Quiver: 18x18 vetores
  - DPI: 300
  - Colormap: inferno
  - Antialiasing ativado
  - Projeção de isotermas na base z=0
  - Tipografia STIX/Serif
"""

import os, warnings
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
warnings.filterwarnings('ignore')

# ─── Estilo de publicação ────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        'serif',
    'font.serif':         ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size':          9.0,
    'axes.labelsize':     9.0,
    'axes.titlesize':     9.5,
    'xtick.labelsize':    8.0,
    'ytick.labelsize':    8.0,
    'figure.dpi':         300,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'mathtext.fontset':   'stix',
})

ROOT    = "/home/warley/vault/research/eu/paper1_heat_burgers"
MDIR    = os.path.join(ROOT, "models")
FIG_DIR = os.path.join(ROOT, "figures")
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
    return model

def predict_burgers(model, x, y, t):
    with torch.no_grad():
        inp = torch.tensor(
            np.stack([x, y, np.full_like(x, t)], axis=1), dtype=torch.float32)
        out = model(inp).numpy()
    u, v = out[:, 0], out[:, 1]
    return u, v, np.sqrt(u**2 + v**2)

def _save(fig, name):
    out_pdf = os.path.join(FIG_DIR, f"{name}.pdf")
    out_png = os.path.join(FIG_DIR, f"{name}.png")
    fig.savefig(out_pdf, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  [OK] Salvo: {out_pdf}")
    print(f"  [OK] Salvo: {out_png}")

# =============================================================================
# FIGURA INDIVIDUAL: superfície 3D de ||u|| para um instante t
# =============================================================================
def _make_3d_surface(model, t, N=300, NQ=18):
    xi = np.linspace(-1, 1, N)
    yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    u, v, spd = predict_burgers(model, xf, yf, t)
    Z = spd.reshape(N, N)

    # Grid coarso para quiver
    xq = np.linspace(-1, 1, NQ)
    yq = np.linspace(-1, 1, NQ)
    Xq, Yq = np.meshgrid(xq, yq)
    xqf, yqf = Xq.ravel(), Yq.ravel()
    uq, vq, spq = predict_burgers(model, xqf, yqf, t)
    Uq = uq.reshape(NQ, NQ)
    Vq = vq.reshape(NQ, NQ)
    Sq = spq.reshape(NQ, NQ)

    return X, Y, Z, Xq, Yq, Uq, Vq, Sq

def _draw_3d_axes(ax, X, Y, Z, Xq, Yq, Uq, Vq, Sq, vmax, t, label):
    surf = ax.plot_surface(X, Y, Z,
                           cmap='inferno', vmin=0.0, vmax=vmax,
                           linewidth=0, antialiased=True,
                           alpha=0.92, rstride=1, cstride=1)
    # Isotermas projetadas na base
    ax.contourf(X, Y, Z, zdir='z', offset=0.0,
                cmap='inferno', vmin=0.0, vmax=vmax,
                alpha=0.30, levels=20)

    ax.set_zlim(0.0, vmax * 1.05)
    ax.set_xlim(-1.0, 1.0)
    ax.set_ylim(-1.0, 1.0)
    ax.set_xticks([-1.0, 0.0, 1.0])
    ax.set_yticks([-1.0, 0.0, 1.0])
    ax.set_zticks([0.0, round(vmax/2, 1), round(vmax, 1)])
    ax.set_xlabel('$x$',        fontsize=8.5, labelpad=-2)
    ax.set_ylabel('$y$',        fontsize=8.5, labelpad=-2)
    ax.set_zlabel(r'$\|\mathbf{u}\|$', fontsize=8.5, labelpad=-4)
    t_str = f"{t:.1f}".replace('.', '{,}')
    ax.set_title(fr'{label} $t = {t_str}\,\mathrm{{s}}$', fontsize=9.2, pad=3)
    ax.view_init(elev=30, azim=-55)
    ax.tick_params(labelsize=7.0, pad=0.5)
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_edgecolor('0.7')
    ax.grid(True, linestyle=':', alpha=0.3)
    return surf

# =============================================================================
# IMAGENS INDIVIDUAIS  (burgers_3d_t0  e  burgers_3d_t05)
# =============================================================================
def generate_individual_figures():
    print('[1] Gerando figuras 3D individuais de Burgers ...')
    model = load_burgers()

    configs = [
        (0.0, 'burgers_3d_t0',  '(a)'),
        (0.5, 'burgers_3d_t05', '(b)'),
    ]

    # Calcula vmax global (t=0.0 tem os picos mais altos)
    X0, Y0, Z0, Xq0, Yq0, Uq0, Vq0, Sq0 = _make_3d_surface(model, 0.0)
    X5, Y5, Z5, Xq5, Yq5, Uq5, Vq5, Sq5 = _make_3d_surface(model, 0.5)
    vmax = max(Z0.max(), Z5.max())
    data = {
        0.0: (X0, Y0, Z0, Xq0, Yq0, Uq0, Vq0, Sq0),
        0.5: (X5, Y5, Z5, Xq5, Yq5, Uq5, Vq5, Sq5),
    }

    for (t, name, lbl) in configs:
        Xd, Yd, Zd, Xqd, Yqd, Uqd, Vqd, Sqd = data[t]
        fig = plt.figure(figsize=(4.2, 3.5), facecolor='white')
        ax = fig.add_subplot(111, projection='3d')
        surf = _draw_3d_axes(ax, Xd, Yd, Zd, Xqd, Yqd, Uqd, Vqd, Sqd, vmax, t, lbl)

        # Colorbar
        cbar = fig.colorbar(surf, ax=ax, shrink=0.65, pad=0.08,
                            label=r'Velocidade $\|\mathbf{u}\|$ [m/s]')
        cbar.ax.tick_params(labelsize=7.0)

        # Anotação da norma L2
        _save(fig, name)

    return data, vmax

# =============================================================================
# FIGURA COMPOSTA PARA O ARTIGO  (fig_b2_burgers_3d_pair)
# =============================================================================
def generate_pair_figure(data, vmax):
    print('[2] Gerando figura composta fig_b2_burgers_3d_pair ...')

    configs = [
        (0.0, '(a)'),
        (0.5, '(b)'),
    ]

    fig = plt.figure(figsize=(7.4, 3.2), facecolor='white')

    axes = [
        fig.add_subplot(1, 2, 1, projection='3d'),
        fig.add_subplot(1, 2, 2, projection='3d'),
    ]

    surf_last = None
    for ax, (t, lbl) in zip(axes, configs):
        Xd, Yd, Zd, Xqd, Yqd, Uqd, Vqd, Sqd = data[t]
        surf = _draw_3d_axes(ax, Xd, Yd, Zd, Xqd, Yqd, Uqd, Vqd, Sqd, vmax, t, lbl)
        surf_last = surf

    fig.subplots_adjust(left=0.02, right=0.88, bottom=0.05, top=0.96, wspace=0.06)
    cbar_ax = fig.add_axes([0.90, 0.18, 0.015, 0.64])
    cbar = fig.colorbar(surf_last, cax=cbar_ax)
    cbar.set_label(r'Magnitude $\|\mathbf{u}\| = \sqrt{u^2+v^2}$ [m/s]', fontsize=7.8)
    cbar.ax.tick_params(labelsize=7.0)

    _save(fig, 'fig_b2_burgers_3d_pair')

# =============================================================================
if __name__ == '__main__':
    print('=' * 60)
    print('Gerando Figuras 3D de Burgers 2D — Paper 1')
    print('=' * 60)
    data, vmax = generate_individual_figures()
    generate_pair_figure(data, vmax)
    print('=' * 60)
    print('Concluído com sucesso!')
