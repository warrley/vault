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
N = 220
xi = np.linspace(0, 1, N); yi = np.linspace(0, 1, N)
X, Y = np.meshgrid(xi, yi)
xf, yf = X.ravel(), Y.ravel()

fig = plt.figure(figsize=(7.6, 4.4), dpi=350)
gs = gridspec.GridSpec(2, 3, height_ratios=[1.15, 1.0], hspace=0.36, wspace=0.28,
                       left=0.05, right=0.92, top=0.94, bottom=0.08)

times_3d = [0.0, 0.2, 0.5]
labels_3d = [r'(a) $t = 0{,}0\ \mathrm{s}$', r'(b) $t = 0{,}2\ \mathrm{s}$', r'(c) $t = 0{,}5\ \mathrm{s}$']

for i, (lbl, t) in enumerate(zip(labels_3d, times_3d)):
    Z = predict_heat(model, xf, yf, t).reshape(N, N)
    ax = fig.add_subplot(gs[0, i], projection='3d')
    surf = ax.plot_surface(X, Y, Z, cmap='turbo', vmin=0.0, vmax=1.0,
                           linewidth=0, antialiased=True, alpha=0.96,
                           rstride=1, cstride=1)
    ax.contourf(X, Y, Z, zdir='z', offset=0.0, cmap='turbo',
                vmin=0.0, vmax=1.0, alpha=0.45, levels=25)
    ax.set_zlim(0.0, 1.05)
    ax.set_xlim(0.0, 1.0); ax.set_ylim(0.0, 1.0)
    ax.set_xticks([0.0, 0.5, 1.0]); ax.set_yticks([0.0, 0.5, 1.0]); ax.set_zticks([0.0, 0.5, 1.0])
    ax.set_xlabel(r'$x$', fontsize=8.0, labelpad=-3)
    ax.set_ylabel(r'$y$', fontsize=8.0, labelpad=-3)
    ax.set_zlabel(r'$u$', fontsize=8.0, labelpad=-4)
    ax.set_title(lbl, fontsize=8.8, pad=2)
    ax.view_init(elev=28, azim=-55)
    ax.tick_params(labelsize=6.8, pad=1.0)

t_cmp = 0.2
u_p = predict_heat(model, xf, yf, t_cmp).reshape(N, N)
u_e = np.sin(np.pi * X) * np.sin(np.pi * Y) * np.exp(-2 * np.pi**2 * alpha * t_cmp)
err = np.abs(u_p - u_e)

ax_d = fig.add_subplot(gs[1, 0])
im_d = ax_d.imshow(u_p, extent=[0, 1, 0, 1], origin='lower', cmap='turbo', vmin=0.0, vmax=0.7)
ax_d.set_title(r'(d) Predição PINN ($t=0{,}2\ \mathrm{s}$)', fontsize=8.5)
ax_d.set_xlabel(r'$x$', fontsize=8.0); ax_d.set_ylabel(r'$y$', fontsize=8.0)
ax_d.tick_params(labelsize=7.2)
cb_d = plt.colorbar(im_d, ax=ax_d, fraction=0.046, pad=0.04)
cb_d.ax.tick_params(labelsize=7.0)

ax_e = fig.add_subplot(gs[1, 1])
im_e = ax_e.imshow(u_e, extent=[0, 1, 0, 1], origin='lower', cmap='turbo', vmin=0.0, vmax=0.7)
ax_e.set_title(r'(e) Solução Exata ($t=0{,}2\ \mathrm{s}$)', fontsize=8.5)
ax_e.set_xlabel(r'$x$', fontsize=8.0); ax_e.set_ylabel(r'$y$', fontsize=8.0)
ax_e.tick_params(labelsize=7.2)
cb_e = plt.colorbar(im_e, ax=ax_e, fraction=0.046, pad=0.04)
cb_e.ax.tick_params(labelsize=7.0)

ax_f = fig.add_subplot(gs[1, 2])
im_f = ax_f.imshow(err, extent=[0, 1, 0, 1], origin='lower', cmap='plasma', vmin=0.0)
ax_f.set_title(r'(f) Erro $|u_\theta - u^\star|$ ($t=0{,}2\ \mathrm{s}$)', fontsize=8.5)
ax_f.set_xlabel(r'$x$', fontsize=8.0); ax_f.set_ylabel(r'$y$', fontsize=8.0)
ax_f.tick_params(labelsize=7.2)
cb_f = plt.colorbar(im_f, ax=ax_f, fraction=0.046, pad=0.04)
cb_f.formatter.set_powerlimits((0, 0))
cb_f.ax.yaxis.get_offset_text().set_fontsize(7.0)
cb_f.ax.tick_params(labelsize=7.0)

fig.savefig('paper1_heat_burgers/preview_combined_turbo.png', dpi=350, bbox_inches='tight')
plt.close(fig)
print('Generated preview_combined_turbo.png')
