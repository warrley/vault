import sys; sys.path.insert(0, 'paper1_heat_burgers')
import os, numpy as np, torch, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
from generate_perfect_paper1_figures import load_burgers, predict_burgers

plt.rcParams.update({
    'font.family':        'serif',
    'font.serif':         ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size':          9.0,
    'axes.labelsize':     9.0,
    'axes.titlesize':     9.5,
    'xtick.labelsize':    8.0,
    'ytick.labelsize':    8.0,
    'legend.fontsize':    8.0,
    'mathtext.fontset':   'stix',
})

model, nu, _ = load_burgers()
N = 250
NQ = 22

# Opção 1: 2D Vector Field (4 instantes) com zoom no domínio central [-0.8, 0.8] para destacar os vórtices
xi_zoom = np.linspace(-0.8, 0.8, N); yi_zoom = np.linspace(-0.8, 0.8, N)
Xz, Yz = np.meshgrid(xi_zoom, yi_zoom)
xz_f, yz_f = Xz.ravel(), Yz.ravel()

xq_z = np.linspace(-0.75, 0.75, NQ); yq_z = np.linspace(-0.75, 0.75, NQ)
Xqz, Yqz = np.meshgrid(xq_z, yq_z)
xqz_f, yqz_f = Xqz.ravel(), Yqz.ravel()

times = [0.0, 0.3, 0.5, 1.0]
titles_2d = [r'(a) $t = 0{,}0\ \mathrm{s}$', r'(b) $t = 0{,}3\ \mathrm{s}$', r'(c) $t = 0{,}5\ \mathrm{s}$', r'(d) $t = 1{,}0\ \mathrm{s}$']

fig, axes = plt.subplots(1, 4, figsize=(7.6, 2.3), dpi=350, sharey=True)
im_ref = None

for i, (t, title, ax) in enumerate(zip(times, titles_2d, axes)):
    u, v, spd = predict_burgers(model, xz_f, yz_f, t)
    uq, vq, _ = predict_burgers(model, xqz_f, yqz_f, t)
    SPD = spd.reshape(N, N)
    Uq, Vq = uq.reshape(NQ, NQ), vq.reshape(NQ, NQ)

    im = ax.imshow(SPD, extent=[-0.8, 0.8, -0.8, 0.8], origin='lower',
                   cmap='jet', vmin=0.0, vmax=1.0, aspect='equal')
    if i == 0:
        im_ref = im

    spq = np.sqrt(Uq**2 + Vq**2)
    nf  = np.where(spq > 1e-5, spq, 1e-5)
    Un, Vn = Uq / nf, Vq / nf
    scale = spq / 1.0
    mask = scale > 0.04
    if mask.any():
        ax.quiver(Xqz[mask], Yqz[mask],
                  Un[mask] * scale[mask],
                  Vn[mask] * scale[mask],
                  color='white', alpha=0.92,
                  scale=13, width=0.009,
                  headwidth=3.6, headlength=4.2,
                  pivot='mid')

    ax.set_title(title, fontsize=8.8, pad=3)
    ax.set_xlabel(r'$x$', fontsize=8.2, labelpad=2)
    if i == 0:
        ax.set_ylabel(r'$y$', fontsize=8.2, labelpad=2)
    ax.set_xticks([-0.5, 0, 0.5])
    ax.set_yticks([-0.5, 0, 0.5])
    ax.tick_params(labelsize=7.5)

plt.subplots_adjust(left=0.07, right=0.88, bottom=0.18, top=0.88, wspace=0.16)
cbar_ax = fig.add_axes([0.90, 0.20, 0.016, 0.66])
cb = fig.colorbar(im_ref, cax=cbar_ax)
cb.set_label(r'$\|\mathbf{u}\| = \sqrt{u^2 + v^2}\ [\mathrm{m/s}]$', fontsize=8.0)
cb.ax.tick_params(labelsize=7.0)
fig.savefig('paper1_heat_burgers/preview_burgers_2d_zoomed.png', dpi=350, bbox_inches='tight')
plt.close(fig)

# Opção 2: 3D Surface de Burgers (Magnitude ||u||) com zoom nos subplots individuais
xi_full = np.linspace(-1, 1, 180); yi_full = np.linspace(-1, 1, 180)
Xf, Yf = np.meshgrid(xi_full, yi_full)
xf_full, yf_full = Xf.ravel(), Yf.ravel()

fig = plt.figure(figsize=(7.6, 2.7), dpi=350)
surf_last = None
times_3d = [0.0, 0.3, 0.5]
labels_3d = [r'(a) $\|\mathbf{u}(x,y,0{,}0\ \mathrm{s})\|$', r'(b) $\|\mathbf{u}(x,y,0{,}3\ \mathrm{s})\|$', r'(c) $\|\mathbf{u}(x,y,0{,}5\ \mathrm{s})\|$']

for i, (lbl, t) in enumerate(zip(labels_3d, times_3d)):
    u, v, spd = predict_burgers(model, xf_full, yf_full, t)
    SPD = spd.reshape(180, 180)
    ax = fig.add_subplot(1, 3, i+1, projection='3d')
    surf = ax.plot_surface(Xf, Yf, SPD, cmap='jet', vmin=0.0, vmax=1.0,
                           linewidth=0, antialiased=False, alpha=1.0, shade=True,
                           rstride=1, cstride=1)
    surf_last = surf
    ax.contourf(Xf, Yf, SPD, zdir='z', offset=0.0, cmap='jet',
                vmin=0.0, vmax=1.0, alpha=0.80, levels=25)
    ax.set_zlim(0.0, 1.05)
    ax.set_xlim(-1.0, 1.0); ax.set_ylim(-1.0, 1.0)
    ax.set_xticks([-1.0, 0.0, 1.0]); ax.set_yticks([-1.0, 0.0, 1.0]); ax.set_zticks([0.0, 0.5, 1.0])
    ax.set_xlabel(r'$x$', fontsize=8.2, labelpad=-4)
    ax.set_ylabel(r'$y$', fontsize=8.2, labelpad=-4)
    ax.set_zlabel(r'$\|\mathbf{u}\|$', fontsize=8.2, labelpad=-5)
    ax.set_title(lbl, fontsize=8.8, pad=0)
    ax.view_init(elev=28, azim=-55)
    ax.tick_params(labelsize=6.8, pad=0.5)
    try:
        ax.set_box_aspect(None, zoom=1.18)
    except Exception:
        pass

plt.subplots_adjust(left=0.02, right=0.88, bottom=0.10, top=0.90, wspace=0.18)
cbar_ax = fig.add_axes([0.90, 0.20, 0.016, 0.60])
cb = fig.colorbar(surf_last, cax=cbar_ax)
cb.set_label(r'$\|\mathbf{u}\|\ [\mathrm{m/s}]$', fontsize=8.0)
cb.ax.tick_params(labelsize=7.0)
fig.savefig('paper1_heat_burgers/preview_burgers_3d_zoom.png', dpi=350, bbox_inches='tight')
plt.close(fig)

# Opção 3: Composição Completa (Linha 1: 3D de ||u|| com zoom; Linha 2: 2D com quiver e zoom)
fig = plt.figure(figsize=(7.6, 4.6), dpi=350)
gs = gridspec.GridSpec(2, 3, height_ratios=[1.35, 1.0], hspace=0.32, wspace=0.25,
                       left=0.05, right=0.92, top=0.95, bottom=0.07)

times_comp = [0.0, 0.3, 0.5]
labels_comp_3d = [r'(a) $\|\mathbf{u}_\theta\|$ em $t = 0{,}0\ \mathrm{s}$', r'(b) $\|\mathbf{u}_\theta\|$ em $t = 0{,}3\ \mathrm{s}$', r'(c) $\|\mathbf{u}_\theta\|$ em $t = 0{,}5\ \mathrm{s}$']
labels_comp_2d = [r'(d) Vetores em $t = 0{,}0\ \mathrm{s}$', r'(e) Vetores em $t = 0{,}3\ \mathrm{s}$', r'(f) Vetores em $t = 0{,}5\ \mathrm{s}$']

# Linha 1: 3D
for i, (lbl, t) in enumerate(zip(labels_comp_3d, times_comp)):
    u, v, spd = predict_burgers(model, xf_full, yf_full, t)
    SPD = spd.reshape(180, 180)
    ax = fig.add_subplot(gs[0, i], projection='3d')
    surf = ax.plot_surface(Xf, Yf, SPD, cmap='jet', vmin=0.0, vmax=1.0,
                           linewidth=0, antialiased=False, alpha=1.0, shade=True,
                           rstride=1, cstride=1)
    ax.contourf(Xf, Yf, SPD, zdir='z', offset=0.0, cmap='jet',
                vmin=0.0, vmax=1.0, alpha=0.85, levels=25)
    ax.set_zlim(0.0, 1.05)
    ax.set_xlim(-1.0, 1.0); ax.set_ylim(-1.0, 1.0)
    ax.set_xticks([-1.0, 0.0, 1.0]); ax.set_yticks([-1.0, 0.0, 1.0]); ax.set_zticks([0.0, 0.5, 1.0])
    ax.set_xlabel(r'$x$', fontsize=8.0, labelpad=-4)
    ax.set_ylabel(r'$y$', fontsize=8.0, labelpad=-4)
    ax.set_zlabel(r'$\|\mathbf{u}\|$', fontsize=8.0, labelpad=-5)
    ax.set_title(lbl, fontsize=8.6, pad=-1)
    ax.view_init(elev=28, azim=-55)
    ax.tick_params(labelsize=6.8, pad=0.5)
    try:
        ax.set_box_aspect(None, zoom=1.18)
    except Exception:
        pass

# Linha 2: 2D com Quiver
for i, (lbl, t) in enumerate(zip(labels_comp_2d, times_comp)):
    u, v, spd = predict_burgers(model, xz_f, yz_f, t)
    uq, vq, _ = predict_burgers(model, xqz_f, yqz_f, t)
    SPD = spd.reshape(N, N)
    Uq, Vq = uq.reshape(NQ, NQ), vq.reshape(NQ, NQ)

    ax = fig.add_subplot(gs[1, i])
    im = ax.imshow(SPD, extent=[-0.8, 0.8, -0.8, 0.8], origin='lower',
                   cmap='jet', vmin=0.0, vmax=1.0, aspect='equal')
    spq = np.sqrt(Uq**2 + Vq**2)
    nf  = np.where(spq > 1e-5, spq, 1e-5)
    Un, Vn = Uq / nf, Vq / nf
    scale = spq / 1.0
    mask = scale > 0.04
    if mask.any():
        ax.quiver(Xqz[mask], Yqz[mask],
                  Un[mask] * scale[mask],
                  Vn[mask] * scale[mask],
                  color='white', alpha=0.92,
                  scale=13, width=0.009,
                  headwidth=3.6, headlength=4.2,
                  pivot='mid')
    ax.set_title(lbl, fontsize=8.5)
    ax.set_xlabel(r'$x$', fontsize=8.0); ax.set_ylabel(r'$y$', fontsize=8.0)
    ax.set_xticks([-0.5, 0, 0.5]); ax.set_yticks([-0.5, 0, 0.5])
    ax.tick_params(labelsize=7.2)
    cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.tick_params(labelsize=6.8)

fig.savefig('paper1_heat_burgers/preview_burgers_composite.png', dpi=350, bbox_inches='tight')
plt.close(fig)

print("Generated Burgers previews successfully!")
