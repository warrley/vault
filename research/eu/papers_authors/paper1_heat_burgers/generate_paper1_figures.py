"""
Gera figuras de publicacao para o Paper 1 (Burgers 2D + Calor 2D)
no mesmo estilo visual do Paper 2 (paper2_heat_irregular_domain).

Estilo:
  - font.family = serif (Times New Roman / DejaVu Serif)
  - mathtext.fontset = stix
  - font.size  = 8.5 / axes.title = 9.0
  - DPI = 300, bbox_tight
  - cmap principal: inferno  (calor); cmap Burgers: quiver branco + inferno
  - Titulos: (a1), (a2) ... em portugues
  - Figuras compactas, estilo artigo de 2 colunas (~7 pol de largura)
"""

import os, warnings
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
warnings.filterwarnings('ignore')

# ─── Estilo idêntico ao paper2 ───────────────────────────────────────────────
plt.rcParams.update({
    'font.family':      'serif',
    'font.serif':       ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size':        8.5,
    'axes.labelsize':   8.5,
    'axes.titlesize':   9.0,
    'xtick.labelsize':  7.5,
    'ytick.labelsize':  7.5,
    'figure.dpi':       300,
    'savefig.dpi':      300,
    'savefig.bbox':     'tight',
    'mathtext.fontset': 'stix',
    'axes.spines.top':  False,
    'axes.spines.right':False,
})

ROOT    = "/home/warley/vault/research/eu/paper1_heat_burgers"
OUT     = os.path.join(ROOT, "new_figures")
MDIR    = os.path.join(ROOT, "models")
os.makedirs(OUT, exist_ok=True)

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
    ckpt  = torch.load(os.path.join(MDIR, 'pinn_burgers_2d_20k.pth'),
                       map_location='cpu', weights_only=False)
    model = PINN(3, 2)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model, ckpt.get('nu', 0.01), ckpt.get('loss_history', None)

def load_heat():
    ckpt  = torch.load(os.path.join(MDIR, 'pinn_heat_2d_20k.pth'),
                       map_location='cpu', weights_only=False)
    model = PINN(3, 1)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()
    return model, ckpt.get('alpha', 0.1), ckpt.get('loss_history', None)

def predict_burgers(model, x, y, t):
    with torch.no_grad():
        inp = torch.tensor(
            np.stack([x, y, np.full_like(x, t)], axis=1), dtype=torch.float32)
        out = model(inp).numpy()
    u, v = out[:, 0], out[:, 1]
    return u, v, np.sqrt(u**2 + v**2)

def predict_heat(model, x, y, t):
    with torch.no_grad():
        inp = torch.tensor(
            np.stack([x, y, np.full_like(x, t)], axis=1), dtype=torch.float32)
        return model(inp).numpy().squeeze()

def _save(fig, name):
    for target_dir in [OUT, os.path.join(ROOT, "figures")]:
        os.makedirs(target_dir, exist_ok=True)
        base = os.path.join(target_dir, name)
        fig.savefig(base + '.pdf', dpi=300, bbox_inches='tight')
        fig.savefig(base + '.png', dpi=300, bbox_inches='tight')
    print(f'  saved → {name}.pdf / .png (in new_figures/ and figures/)')
    plt.close(fig)

# =============================================================================
# FIGURA B1: Burgers — campo de velocidade (6 snapshots, quiver + inferno)
# Estilo: 1×6 horizontal compacto, como fig3 do paper2
# =============================================================================
def fig_b1_burgers_speed_snapshots():
    print('[B1] Burgers — 6 snapshots velocidade + quiver …')
    model, nu, _ = load_burgers()

    times = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    N, NQ = 200, 22

    xi = np.linspace(-1, 1, N); yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    xq = np.linspace(-1, 1, NQ); yq = np.linspace(-1, 1, NQ)
    Xq, Yq = np.meshgrid(xq, yq)
    xqf, yqf = Xq.ravel(), Yq.ravel()

    data, vmax = [], 0
    for t in times:
        u, v, spd = predict_burgers(model, xf, yf, t)
        uq, vq, _ = predict_burgers(model, xqf, yqf, t)
        data.append((spd.reshape(N,N), uq.reshape(NQ,NQ), vq.reshape(NQ,NQ)))
        vmax = max(vmax, spd.max())

    fig, axes = plt.subplots(1, 6, figsize=(7.2, 1.95), sharey=True)

    for i, (t, ax) in enumerate(zip(times, axes)):
        SPD, Uq, Vq = data[i]
        im = ax.imshow(SPD, extent=[-1,1,-1,1], origin='lower',
                       cmap='inferno', vmin=0, vmax=vmax, aspect='equal')
        # Quiver normalizado (tamanho prop. a magnitude)
        spq = np.sqrt(Uq**2 + Vq**2)
        nf  = np.where(spq > 1e-6, spq, 1e-6)
        Un, Vn = Uq/nf, Vq/nf
        scale  = spq / (vmax + 1e-8)
        skip_mask = scale > 0.05
        if skip_mask.any():
            ax.quiver(Xq[skip_mask], Yq[skip_mask],
                      Un[skip_mask]*scale[skip_mask],
                      Vn[skip_mask]*scale[skip_mask],
                      color='white', alpha=0.75,
                      scale=18, width=0.007,
                      headwidth=3.5, headlength=4,
                      pivot='mid')
        ax.set_title(f'(a{i+1}) $t = {t:.1f}$', fontsize=8.0)
        ax.set_xlabel('$x$')
        if i == 0:
            ax.set_ylabel('$y$')
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])

    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85,
                        label=r'Velocidade $\|\mathbf{u}\|$')
    cbar.ax.tick_params(labelsize=7)
    plt.suptitle(r'Burgers 2D — evolução do campo de velocidade ($\nu = 0{,}01$)',
                 fontsize=9.0, y=1.03)
    plt.tight_layout()
    _save(fig, 'fig_b1_burgers_speed_snapshots')

# =============================================================================
# FIGURA B2: Burgers — colisão dos blobs (4 painéis, foco no fenômeno)
# =============================================================================
def fig_b2_burgers_collision():
    print('[B2] Burgers — colisão dos blobs (4 painéis) …')
    model, nu, _ = load_burgers()

    times  = [0.0, 0.3, 0.5, 1.0]
    N, NQ  = 220, 24

    xi = np.linspace(-1, 1, N); yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()
    xq = np.linspace(-1, 1, NQ); yq = np.linspace(-1, 1, NQ)
    Xq, Yq = np.meshgrid(xq, yq)
    xqf, yqf = Xq.ravel(), Yq.ravel()

    labels = [
        r'(a1) $t=0{,}0$ — blobs separados',
        r'(a2) $t=0{,}3$ — aproximando',
        r'(a3) $t=0{,}5$ — colisão / fusão',
        r'(a4) $t=1{,}0$ — fundidos, difundindo',
    ]
    data, vmax = [], 0
    for t in times:
        u, v, spd = predict_burgers(model, xf, yf, t)
        uq, vq, _ = predict_burgers(model, xqf, yqf, t)
        data.append((spd.reshape(N,N), uq.reshape(NQ,NQ), vq.reshape(NQ,NQ)))
        vmax = max(vmax, spd.max())

    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.2), sharey=True)
    im_ref = None

    for i, (lbl, ax) in enumerate(zip(labels, axes)):
        SPD, Uq, Vq = data[i]
        im = ax.imshow(SPD, extent=[-1,1,-1,1], origin='lower',
                       cmap='inferno', vmin=0, vmax=vmax, aspect='equal')
        if i == 0:
            im_ref = im
        spq = np.sqrt(Uq**2 + Vq**2)
        nf  = np.where(spq > 1e-6, spq, 1e-6)
        Un, Vn = Uq/nf, Vq/nf
        scale  = spq / (vmax + 1e-8)
        sk = scale > 0.04
        if sk.any():
            ax.quiver(Xq[sk], Yq[sk], Un[sk]*scale[sk], Vn[sk]*scale[sk],
                      color='white', alpha=0.8,
                      scale=16, width=0.008,
                      headwidth=3.5, headlength=4, pivot='mid')
        ax.set_title(lbl, fontsize=7.8)
        ax.set_xlabel('$x$')
        if i == 0:
            ax.set_ylabel('$y$')
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])

    cbar = fig.colorbar(im_ref, ax=axes.ravel().tolist(), shrink=0.85,
                        label=r'Velocidade $\|\mathbf{u}\|$')
    cbar.ax.tick_params(labelsize=7)
    plt.suptitle(r'Burgers 2D — sequência de colisão dos blobs gaussianos ($\nu = 0{,}01$)',
                 fontsize=9.0, y=1.03)
    plt.tight_layout()
    _save(fig, 'fig_b2_burgers_collision')

# =============================================================================
# FIGURA B3: Burgers — streamlines (3 tempos, 1×3)
# =============================================================================
def fig_b3_burgers_streamlines():
    print('[B3] Burgers — streamlines …')
    model, nu, _ = load_burgers()

    times = [0.0, 0.5, 1.0]
    N = 180

    xi = np.linspace(-1, 1, N); yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)

    for i, (t, ax) in enumerate(zip(times, axes)):
        u, v, spd = predict_burgers(model, xf, yf, t)
        U, V, SPD = u.reshape(N,N), v.reshape(N,N), spd.reshape(N,N)
        im = ax.imshow(SPD, extent=[-1,1,-1,1], origin='lower',
                       cmap='inferno', vmin=0, vmax=SPD.max(), aspect='equal')
        ax.streamplot(xi, yi, U, V, color=SPD, cmap='inferno',
                      linewidth=0.9, density=1.3, arrowsize=0.9,
                      arrowstyle='->', minlength=0.04)
        ax.set_title(f'(a{i+1}) $t = {t:.1f}$', fontsize=8.0)
        ax.set_xlabel('$x$')
        if i == 0:
            ax.set_ylabel('$y$')
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.85)
        cb.set_label(r'$\|\mathbf{u}\|$', fontsize=7.5)
        cb.ax.tick_params(labelsize=7)

    plt.suptitle(r'Burgers 2D — linhas de corrente ($\nu = 0{,}01$)',
                 fontsize=9.0, y=1.03)
    plt.tight_layout()
    _save(fig, 'fig_b3_burgers_streamlines')

# =============================================================================
# FIGURA B4: Burgers — componentes u e v (2×3)
# =============================================================================
def fig_b4_burgers_components():
    print('[B4] Burgers — componentes u e v …')
    model, nu, _ = load_burgers()

    times = [0.0, 0.5, 1.0]
    N = 200

    xi = np.linspace(-1, 1, N); yi = np.linspace(-1, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    data, au, av = [], 0, 0
    for t in times:
        u, v, _ = predict_burgers(model, xf, yf, t)
        U, V = u.reshape(N,N), v.reshape(N,N)
        data.append((U, V))
        au = max(au, np.abs(U).max())
        av = max(av, np.abs(V).max())

    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.4), sharey='row')

    for col, t in enumerate(times):
        U, V = data[col]
        for row, (arr, amax, comp, letter) in enumerate([
            (U, au, r'$u$', 'a'), (V, av, r'$v$', 'b')
        ]):
            ax = axes[row, col]
            im = ax.imshow(arr, extent=[-1,1,-1,1], origin='lower',
                           cmap='RdBu_r', vmin=-amax, vmax=amax, aspect='equal')
            # linha de zero
            cs = ax.contour(X, Y, arr, levels=[0], colors='k',
                            linewidths=0.8, linestyles='--')
            ax.set_title(f'({letter}{col+1}) $t = {t:.1f}$', fontsize=8.0)
            ax.set_xlabel('$x$')
            if col == 0:
                ax.set_ylabel('$y$')
            ax.set_xticks([-1, 0, 1])
            ax.set_yticks([-1, 0, 1])
            cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.85)
            cb.set_label(comp, fontsize=8)
            cb.ax.tick_params(labelsize=7)

    plt.suptitle(r'Burgers 2D — componentes $u$ e $v$ da velocidade ($\nu = 0{,}01$)',
                 fontsize=9.0, y=1.02)
    plt.tight_layout()
    _save(fig, 'fig_b4_burgers_components')

# =============================================================================
# FIGURA H1: Calor — evolução 2D heatmap (1×6, estilo fig3 do paper2)
# =============================================================================
def fig_h1_heat_heatmap():
    print('[H1] Calor — heatmap 2D (6 snapshots) …')
    model, alpha, _ = load_heat()

    times = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    N = 200

    xi = np.linspace(0, 1, N); yi = np.linspace(0, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    data, zmax = [], 0
    for t in times:
        u = predict_heat(model, xf, yf, t).reshape(N, N)
        data.append(u); zmax = max(zmax, u.max())

    fig, axes = plt.subplots(1, 6, figsize=(7.2, 1.95), sharey=True)

    for i, (t, ax) in enumerate(zip(times, axes)):
        im = ax.imshow(data[i], extent=[0,1,0,1], origin='lower',
                       cmap='inferno', vmin=0, vmax=zmax, aspect='equal')
        ax.set_title(f'(a{i+1}) $t = {t:.1f}$', fontsize=8.0)
        ax.set_xlabel('$x$')
        if i == 0:
            ax.set_ylabel('$y$')
        ax.set_xticks([0, 0.5, 1])
        ax.set_yticks([0, 0.5, 1])

    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85,
                        label='Temperatura $u(x,y,t)$')
    cbar.ax.tick_params(labelsize=7)
    plt.suptitle(r'Equação do Calor 2D — evolução da temperatura ($\alpha = 0{,}1$)',
                 fontsize=9.0, y=1.03)
    plt.tight_layout()
    _save(fig, 'fig_h1_heat_heatmap')

# =============================================================================
# FIGURA H2: Calor — superfície 3D (6 snapshots 2×3)
# =============================================================================
def fig_h2_heat_3d():
    print('[H2] Calor — superfície 3D (6 snapshots) …')
    model, alpha, _ = load_heat()

    times = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    N = 70

    xi = np.linspace(0, 1, N); yi = np.linspace(0, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    data, zmax = [], 0
    for t in times:
        u = predict_heat(model, xf, yf, t).reshape(N, N)
        data.append(u); zmax = max(zmax, u.max())

    fig = plt.figure(figsize=(7.2, 5.0))
    fig.patch.set_facecolor('white')

    for i, (t, Z) in enumerate(zip(times, data)):
        ax = fig.add_subplot(2, 3, i+1, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='inferno', vmin=0, vmax=zmax,
                               linewidth=0, antialiased=True, alpha=0.95,
                               rstride=1, cstride=1)
        # projeção no chão
        ax.contourf(X, Y, Z, zdir='z', offset=0, cmap='inferno',
                    vmin=0, vmax=zmax, alpha=0.25, levels=15)
        ax.set_zlim(0, zmax*1.05)
        ax.set_xlim(0,1); ax.set_ylim(0,1)
        ax.set_xlabel('$x$', fontsize=7.5, labelpad=2)
        ax.set_ylabel('$y$', fontsize=7.5, labelpad=2)
        ax.set_zlabel('$u$', fontsize=7.5, labelpad=2)
        ax.set_title(f'(a{i+1}) $t = {t:.1f}$', fontsize=8.5, pad=6)
        ax.view_init(elev=28, azim=-55)
        ax.tick_params(labelsize=6.5)
        cb = fig.colorbar(surf, ax=ax, fraction=0.028, pad=0.07, shrink=0.65)
        cb.set_label('$u$', fontsize=7); cb.ax.tick_params(labelsize=6)

    plt.suptitle(r'Equação do Calor 2D — superfície 3D da temperatura ($\alpha = 0{,}1$)',
                 fontsize=9.0, y=1.01)
    plt.tight_layout()
    _save(fig, 'fig_h2_heat_3d')

# =============================================================================
# FIGURA H3: Calor — 4 snapshots 3D grandes (1×4, estilo paper publicacao)
# =============================================================================
def fig_h3_heat_3d_large():
    print('[H3] Calor — 3D grande 4 painéis …')
    model, alpha, _ = load_heat()

    times  = [0.0, 0.3, 0.7, 1.0]
    labels = [r'(a) $t=0{,}0$', r'(b) $t=0{,}3$',
              r'(c) $t=0{,}7$', r'(d) $t=1{,}0$']
    N = 90

    xi = np.linspace(0, 1, N); yi = np.linspace(0, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    data, zmax = [], 0
    for t in times:
        u = predict_heat(model, xf, yf, t).reshape(N, N)
        data.append(u); zmax = max(zmax, u.max())

    fig = plt.figure(figsize=(7.2, 2.5))
    for i, (lbl, Z) in enumerate(zip(labels, data)):
        ax = fig.add_subplot(1, 4, i+1, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='inferno', vmin=0, vmax=zmax,
                               linewidth=0, antialiased=True, alpha=0.96,
                               rstride=1, cstride=1)
        ax.contourf(X, Y, Z, zdir='z', offset=0, cmap='inferno',
                    vmin=0, vmax=zmax, alpha=0.3, levels=12)
        ax.set_zlim(0, zmax*1.05)
        ax.set_xlim(0,1); ax.set_ylim(0,1)
        ax.set_xlabel('$x$', fontsize=7, labelpad=1)
        ax.set_ylabel('$y$', fontsize=7, labelpad=1)
        ax.set_zlabel('$u$', fontsize=7, labelpad=1)
        ax.set_title(lbl, fontsize=8.5, pad=5)
        ax.view_init(elev=30, azim=-60)
        ax.tick_params(labelsize=6)
        if i == len(times)-1:
            cb = fig.colorbar(surf, ax=ax, fraction=0.06, pad=0.14, shrink=0.85)
            cb.set_label('$u$', fontsize=8); cb.ax.tick_params(labelsize=7)

    plt.suptitle(r'Equação do Calor 2D — superfície 3D ($\alpha = 0{,}1$)',
                 fontsize=9.0, y=1.03)
    plt.tight_layout()
    _save(fig, 'fig_h3_heat_3d_large')

# =============================================================================
# FIGURA H4: Calor — superfícies 3D sobrepostas (fundo escuro, estilo premium)
# =============================================================================
def fig_h4_heat_3d_stacked():
    print('[H4] Calor — superfícies 3D sobrepostas …')
    model, alpha, _ = load_heat()

    times  = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    N = 55

    xi = np.linspace(0, 1, N); yi = np.linspace(0, 1, N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    surfs, zmax = [], 0
    for t in times:
        u = predict_heat(model, xf, yf, t).reshape(N, N)
        surfs.append(u); zmax = max(zmax, u.max())

    inferno = plt.get_cmap('inferno')

    fig = plt.figure(figsize=(5.5, 4.2))
    ax  = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#111111'); fig.patch.set_facecolor('#111111')

    for idx, (t, Z) in enumerate(zip(times, surfs)):
        frac  = idx / (len(times) - 1)
        color = inferno(0.15 + frac * 0.85)
        ax.plot_surface(X, Y, Z, color=color,
                        alpha=0.62 - 0.07*idx, linewidth=0, antialiased=True)

    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_zlim(0, zmax*1.1)
    for lbl, setter in [('$x$', ax.set_xlabel), ('$y$', ax.set_ylabel), ('$u$', ax.set_zlabel)]:
        setter(lbl, color='white', fontsize=9, labelpad=6)
    ax.tick_params(colors='white', labelsize=7)
    ax.xaxis.pane.fill = False; ax.yaxis.pane.fill = False; ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('#333333')
    ax.yaxis.pane.set_edgecolor('#333333')
    ax.zaxis.pane.set_edgecolor('#333333')
    ax.grid(True, color='#2a2a2a', alpha=0.6)
    ax.view_init(elev=22, azim=-50)

    from matplotlib.lines import Line2D
    handles = [Line2D([0],[0], color=inferno(0.15+i/(len(times)-1)*0.85),
               lw=3.5, label=f'$t={t:.1f}$') for i, t in enumerate(times)]
    leg = ax.legend(handles=handles, loc='upper right', framealpha=0.2,
                    fontsize=7.5)
    for text in leg.get_texts():
        text.set_color('white')

    ax.set_title(r'Calor 2D — superfícies 3D sobrepostas ($\alpha = 0{,}1$)',
                 color='white', fontsize=9.0, pad=12)
    plt.tight_layout()
    _save(fig, 'fig_h4_heat_3d_stacked')

# =============================================================================
# FIGURA EXTRA: Curvas de perda (se disponíveis no checkpoint)
# =============================================================================
def fig_loss_curves():
    print('[LOSS] Curvas de perda dos dois modelos …')
    _, nu, lh_b = load_burgers()
    _, alpha, lh_h = load_heat()

    if lh_b is None and lh_h is None:
        print('  loss_history nao encontrado nos checkpoints, pulando.')
        return

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.4))

    # (a) Calor 2D
    if lh_h is not None:
        ax = axes[0]
        ep = lh_h['epoch']
        ax.semilogy(ep, lh_h['total'], label=r'$\mathcal{L}_\mathrm{total}$', color='#1f77b4', lw=1.4)
        ax.semilogy(ep, lh_h['pde'],   label=r'$\mathcal{L}_\mathrm{pde}$',   color='#d62728', lw=1.1, ls='--')
        ax.semilogy(ep, lh_h['ic'],    label=r'$\mathcal{L}_\mathrm{ic}$',    color='#2ca02c', lw=1.1, ls='-.')
        ax.semilogy(ep, lh_h['bc'],    label=r'$\mathcal{L}_\mathrm{bc}$',    color='#ff7f0e', lw=1.1, ls=':')
        ax.set_xlabel('Época')
        ax.set_ylabel('Erro Médio Quadrático (MSE)')
        ax.grid(True, which='both', ls=':', alpha=0.45)
        ax.legend(fontsize=7.0, framealpha=0.9, loc='upper right', ncol=2)
        ax.set_title(r'(a) Equação do Calor 2D ($\alpha = 0{,}1$)', fontsize=8.5)
        ax.set_xlim(0, max(ep))

    # (b) Burgers 2D
    if lh_b is not None:
        ax = axes[1]
        ep = lh_b['epoch']
        ax.semilogy(ep, lh_b['total'], label=r'$\mathcal{L}_\mathrm{total}$', color='#1f77b4', lw=1.4)
        ax.semilogy(ep, lh_b['pde'],   label=r'$\mathcal{L}_\mathrm{pde}$',   color='#d62728', lw=1.1, ls='--')
        ax.semilogy(ep, lh_b['ic'],    label=r'$\mathcal{L}_\mathrm{ic}$',    color='#2ca02c', lw=1.1, ls='-.')
        ax.semilogy(ep, lh_b['bc'],    label=r'$\mathcal{L}_\mathrm{bc}$',    color='#ff7f0e', lw=1.1, ls=':')
        ax.set_xlabel('Época')
        ax.set_ylabel('Erro Médio Quadrático (MSE)')
        ax.grid(True, which='both', ls=':', alpha=0.45)
        ax.legend(fontsize=7.0, framealpha=0.9, loc='upper right', ncol=2)
        ax.set_title(r'(b) Equação de Burgers 2D ($\nu = 0{,}01$)', fontsize=8.5)
        ax.set_xlim(0, max(ep))

    plt.tight_layout()
    _save(fig, 'fig_loss_curves')

# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print('=' * 55)
    print('Gerando figuras — Paper 1 (Burgers + Calor 2D)')
    print(f'Saída: {OUT}')
    print('=' * 55)

    # Burgers
    fig_b1_burgers_speed_snapshots()
    fig_b2_burgers_collision()
    fig_b3_burgers_streamlines()
    fig_b4_burgers_components()

    # Calor
    fig_h1_heat_heatmap()
    fig_h2_heat_3d()
    fig_h3_heat_3d_large()
    fig_h4_heat_3d_stacked()

    # Perdas
    fig_loss_curves()

    print('=' * 55)
    print('Concluído! Todas as figuras salvas em new_figures/')

# Patch: regenera apenas a curva de perda com a estrutura correta do dict
if __name__ == '__rerun__':
    pass
