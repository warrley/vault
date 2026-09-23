#!/usr/bin/env python3
import os, warnings
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
warnings.filterwarnings('ignore')

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
    ckpt = torch.load(os.path.join(MDIR, 'pinn_burgers_2d_20k.pth'), map_location='cpu', weights_only=False)
    model = PINN(3, 2)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model

def predict_uv(model, X, Y, t, N):
    with torch.no_grad():
        xf = X.ravel().astype(np.float32)
        yf = Y.ravel().astype(np.float32)
        tf = np.full_like(xf, t)
        inp = torch.tensor(np.stack([xf, yf, tf], axis=1))
        out = model(inp).numpy()
    u   = out[:, 0].reshape(N, N)
    v   = out[:, 1].reshape(N, N)
    spd = np.sqrt(u**2 + v**2)
    return u, v, spd

def gen_fig_2d(model):
    print("Gerando fig_b_burgers_2d_norm ...")
    N = 200
    NQ = 32
    LEVELS = 500
    times = [0.0, 0.5]
    labels = [r'(a) $\|\mathbf{u}\|$ em $t = 0{,}0\,\mathrm{s}$', r'(b) $\|\mathbf{u}\|$ em $t = 0{,}5\,\mathrm{s}$']

    xi = np.linspace(-1, 1, N)
    yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi, indexing='ij')

    xq = np.linspace(-1, 1, NQ)
    yq = np.linspace(-1, 1, NQ)
    Xq, Yq = np.meshgrid(xq, yq, indexing='ij')

    vmax = 1.0
    fig = plt.figure(figsize=(7.4, 3.2), facecolor='white')
    axes = [fig.add_subplot(1, 2, 1), fig.add_subplot(1, 2, 2)]
    cf_last = None

    for i, (ax, lbl, t) in enumerate(zip(axes, labels, times)):
        u, v, spd = predict_uv(model, X, Y, t, N)
        uq, vq, _ = predict_uv(model, Xq, Yq, t, NQ)
        
        cf = ax.contourf(X, Y, spd, levels=np.linspace(0.0, vmax, LEVELS),
                         cmap='jet', vmin=0.0, vmax=vmax, rasterized=True)
        cf_last = cf

        spq = np.sqrt(uq**2 + vq**2)
        nf  = np.where(spq > 1e-6, spq, 1e-6)
        Un, Vn = uq / nf, vq / nf
        scale  = spq / (vmax + 1e-8)
        mask   = scale > 0.03
        ax.quiver(Xq[mask], Yq[mask], Un[mask] * scale[mask], Vn[mask] * scale[mask],
                  color='white', alpha=0.80, scale=16, width=0.004,
                  headwidth=3.0, headlength=3.5, pivot='mid')

        ax.set_title(lbl, fontsize=9.2)
        ax.set_xlabel('$x$', fontsize=9.0)
        if i == 0:
            ax.set_ylabel('$y$', fontsize=9.0)
        else:
            ax.set_yticklabels([])
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.set_yticks([-1, -0.5, 0, 0.5, 1])
        ax.tick_params(labelsize=7.5)
        ax.set_aspect('equal')

    cbar_ax = fig.add_axes([0.91, 0.15, 0.015, 0.70])
    cb = fig.colorbar(cf_last, cax=cbar_ax)
    cb.set_label(r'$\|\mathbf{u}\| = \sqrt{u^2+v^2}$', fontsize=8.5)
    cb.ax.tick_params(labelsize=7.5)
    
    fig.subplots_adjust(left=0.06, right=0.88, bottom=0.15, top=0.88, wspace=0.1)
    pdf = os.path.join(FIG_DIR, 'fig_b_burgers_2d_norm.pdf')
    png = os.path.join(FIG_DIR, 'fig_b_burgers_2d_norm.png')
    fig.savefig(pdf, dpi=300, facecolor='white')
    fig.savefig(png, dpi=300, facecolor='white')
    plt.close(fig)

def gen_fig_3d(model):
    print("Gerando fig_b_burgers_3d_u ...")
    N = 100
    times = [0.0, 0.5]
    labels = [r'(c) $u$ em $t = 0{,}0\,\mathrm{s}$', r'(d) $u$ em $t = 0{,}5\,\mathrm{s}$']

    xi = np.linspace(-1, 1, N)
    yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi, indexing='ij')

    data = []
    zmax = 0
    for t in times:
        u, v, spd = predict_uv(model, X, Y, t, N)
        data.append(u)
        zmax = max(zmax, np.abs(u).max())

    fig = plt.figure(figsize=(7.4, 3.2), facecolor='white')
    surf_last = None
    
    for i, (lbl, t, u) in enumerate(zip(labels, times, data)):
        ax = fig.add_subplot(1, 2, i + 1, projection='3d')
        surf = ax.plot_surface(X, Y, u, cmap='jet', vmin=-zmax, vmax=zmax,
                               edgecolor='none', linewidth=0, antialiased=True,
                               alpha=0.95, rstride=1, cstride=1)
        surf_last = surf

        ax.set_zlim(-zmax * 1.05, zmax * 1.05)
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        zt = round(zmax, 1)
        ax.set_zticks([-zt, 0.0, zt])
        ax.set_xlabel('$x$', fontsize=8.0, labelpad=-3)
        ax.set_ylabel('$y$', fontsize=8.0, labelpad=-3)
        ax.set_zlabel('$u$', fontsize=8.0, labelpad=-4)
        ax.set_title(lbl, fontsize=9.0, pad=2)
        ax.view_init(elev=28, azim=-55)
        ax.tick_params(labelsize=6.5, pad=0.5)
        ax.xaxis.pane.set_visible(False)
        ax.yaxis.pane.set_visible(False)

    cbar_ax = fig.add_axes([0.91, 0.15, 0.015, 0.70])
    cb = fig.colorbar(surf_last, cax=cbar_ax)
    cb.set_label('$u$ [m/s]', fontsize=8.5)
    cb.ax.tick_params(labelsize=7.0)
    
    fig.subplots_adjust(left=0.06, right=0.88, bottom=0.05, top=0.95, wspace=0.1)
    pdf = os.path.join(FIG_DIR, 'fig_b_burgers_3d_u.pdf')
    png = os.path.join(FIG_DIR, 'fig_b_burgers_3d_u.png')
    fig.savefig(pdf, dpi=300, facecolor='white')
    fig.savefig(png, dpi=300, facecolor='white')
    plt.close(fig)

if __name__ == '__main__':
    model = load_burgers()
    gen_fig_2d(model)
    gen_fig_3d(model)
