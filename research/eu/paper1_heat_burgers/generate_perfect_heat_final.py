import sys; sys.path.insert(0, 'paper1_heat_burgers')
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from generate_perfect_paper1_figures import load_heat, predict_heat

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

model, alpha, _ = load_heat()
N = 250
xi = np.linspace(0, 1, N); yi = np.linspace(0, 1, N)
X, Y = np.meshgrid(xi, yi)
xf, yf = X.ravel(), Y.ravel()

times_3d = [0.0, 0.2, 0.5]
labels_3d = [r'(a) $u_\theta(x,y,0{,}0\ \mathrm{s})$', r'(b) $u_\theta(x,y,0{,}2\ \mathrm{s})$', r'(c) $u_\theta(x,y,0{,}5\ \mathrm{s})$']

t_cmp = 1.0
u_p = predict_heat(model, xf, yf, t_cmp).reshape(N, N)
u_e = np.sin(np.pi * X) * np.sin(np.pi * Y) * np.exp(-2 * np.pi**2 * alpha * t_cmp)
err = np.abs(u_p - u_e)

# Colormap vermelho bem mais homogêneo: começa em 0.42 (vermelho vivo/médio) e vai até 0.98 (vermelho escuro/bordô)
reds_deep = matplotlib.colors.LinearSegmentedColormap.from_list(
    'reds_deep', plt.cm.Reds(np.linspace(0.42, 0.98, 256))
)
# Para o erro, também um vermelho bem contínuo e homogêneo
reds_err = matplotlib.colors.LinearSegmentedColormap.from_list(
    'reds_err', plt.cm.Reds(np.linspace(0.35, 0.98, 256))
)

fig = plt.figure(figsize=(7.6, 4.7), dpi=350)
# Aumentamos o ratio da linha 3D para 1.45 vs 1.0 da linha 2D
gs = gridspec.GridSpec(2, 3, height_ratios=[1.45, 1.0], hspace=0.28, wspace=0.24,
                       left=0.04, right=0.93, top=0.95, bottom=0.07)

# Linha 1: 3D com superfície 100% sólida e plots maiores (zoom aumentado)
for i, (lbl, t) in enumerate(zip(labels_3d, times_3d)):
    Z = predict_heat(model, xf, yf, t).reshape(N, N)
    ax = fig.add_subplot(gs[0, i], projection='3d')
    
    # Superfície 3D sólida e opaca com sombreamento
    surf = ax.plot_surface(X, Y, Z, cmap='inferno', vmin=0.0, vmax=1.0,
                           linewidth=0, antialiased=False, alpha=1.0, shade=True,
                           rstride=1, cstride=1)
    # Contorno de base projetado
    ax.contourf(X, Y, Z, zdir='z', offset=0.0, cmap='inferno',
                vmin=0.0, vmax=1.0, alpha=0.90, levels=30)
    
    ax.set_zlim(0.0, 1.05)
    ax.set_xlim(0.0, 1.0); ax.set_ylim(0.0, 1.0)
    ax.set_xticks([0.0, 0.5, 1.0]); ax.set_yticks([0.0, 0.5, 1.0]); ax.set_zticks([0.0, 0.5, 1.0])
    ax.set_xlabel(r'$x$', fontsize=8.2, labelpad=-4)
    ax.set_ylabel(r'$y$', fontsize=8.2, labelpad=-4)
    ax.set_zlabel(r'$u$', fontsize=8.2, labelpad=-5)
    ax.set_title(lbl, fontsize=9.0, pad=-1)
    ax.view_init(elev=26, azim=-55)
    ax.tick_params(labelsize=7.0, pad=0.5)
    # Zoom no 3D para deixar os plots individuais bem maiores
    try:
        ax.set_box_aspect(None, zoom=1.18)
    except Exception:
        pass

# Linha 2: 2D bem homogêneo e avermelhado
vmin_val = min(u_p.min(), u_e.min())
vmax_val = max(u_p.max(), u_e.max())

# (d) PINN
ax_d = fig.add_subplot(gs[1, 0])
im_d = ax_d.imshow(u_p, extent=[0, 1, 0, 1], origin='lower', cmap=reds_deep,
                   vmin=vmin_val, vmax=vmax_val)
ax_d.set_title(r'(d) Predição PINN ($t=1{,}0\ \mathrm{s}$)', fontsize=8.5)
ax_d.set_xlabel(r'$x$', fontsize=8.0); ax_d.set_ylabel(r'$y$', fontsize=8.0)
ax_d.tick_params(labelsize=7.2)
cb_d = plt.colorbar(im_d, ax=ax_d, fraction=0.046, pad=0.04)
cb_d.ax.tick_params(labelsize=7.0)

# (e) Solução Analítica
ax_e = fig.add_subplot(gs[1, 1])
im_e = ax_e.imshow(u_e, extent=[0, 1, 0, 1], origin='lower', cmap=reds_deep,
                   vmin=vmin_val, vmax=vmax_val)
ax_e.set_title(r'(e) Solução Analítica ($t=1{,}0\ \mathrm{s}$)', fontsize=8.5)
ax_e.set_xlabel(r'$x$', fontsize=8.0); ax_e.set_ylabel(r'$y$', fontsize=8.0)
ax_e.tick_params(labelsize=7.2)
cb_e = plt.colorbar(im_e, ax=ax_e, fraction=0.046, pad=0.04)
cb_e.ax.tick_params(labelsize=7.0)

# (f) Erro Absoluto
ax_f = fig.add_subplot(gs[1, 2])
im_f = ax_f.imshow(err * 1e3, extent=[0, 1, 0, 1], origin='lower', cmap=reds_err,
                   vmin=0.0, vmax=float(err.max() * 1e3))
ax_f.set_title(r'(f) Erro Absoluto $|u_\theta - u^\star|$', fontsize=8.5)
ax_f.set_xlabel(r'$x$', fontsize=8.0); ax_f.set_ylabel(r'$y$', fontsize=8.0)
ax_f.tick_params(labelsize=7.2)
cb_f = plt.colorbar(im_f, ax=ax_f, fraction=0.046, pad=0.04)
cb_f.set_label(r'$\times 10^{-3}$', fontsize=7.5, labelpad=2)
cb_f.ax.tick_params(labelsize=7.0)

fig.savefig('paper1_heat_burgers/preview_zoom_opaque.png', dpi=350, bbox_inches='tight')
plt.close(fig)
print("Saved preview_zoom_opaque.png")
