import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D

# Tipografia científica consistente
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 8.0,
    'axes.labelsize': 8.0,
    'axes.titlesize': 8.5,
    'xtick.labelsize': 6.5,
    'ytick.labelsize': 6.5,
    'legend.fontsize': 6.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'cm'
})

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ckpt_path = "./paper2_heat_irregular_domain/models/pinn_heat_holes_checkpoint.pth"
fig_dir = "./paper2_heat_irregular_domain/figures"
checkpoint = torch.load(ckpt_path, map_location='cpu', weights_only=False)

# ==============================================================================
# 1. FIGURA 1: Geometria & Escadeamento (MDF vs PINN)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.0, 1.7), dpi=300)
nx_grid = 18
gx = np.linspace(0.14, 0.46, nx_grid)
gy = np.linspace(0.14, 0.46, nx_grid)
for x_val in gx:
    ax1.axvline(x_val, color='lightgray', lw=0.4, alpha=0.8)
for y_val in gy:
    ax1.axhline(y_val, color='lightgray', lw=0.4, alpha=0.8)
dx = gx[1] - gx[0]; dy = gy[1] - gy[0]
for i in range(nx_grid - 1):
    for j in range(nx_grid - 1):
        cx = (gx[i] + gx[i+1]) / 2.0; cy = (gy[j] + gy[j+1]) / 2.0
        if (cx - 0.30)**2 + (cy - 0.30)**2 <= 0.12**2:
            ax1.add_patch(patches.Rectangle((gx[i], gy[j]), dx, dy, color='#ffaaaa', alpha=0.85))
ax1.add_patch(plt.Circle((0.30, 0.30), 0.12, color='darkred', fill=False, lw=1.2, ls='--', label=r'Contorno $\partial\mathcal{H}_k$'))
ax1.set_title(r'(a) MDF: Degraus $\mathcal{O}(\Delta x)$', fontsize=7.2, pad=2)
ax1.set_xlabel('$x$ [m]', fontsize=6.8); ax1.set_ylabel('$y$ [m]', fontsize=6.8)
ax1.set_xlim(0.14, 0.46); ax1.set_ylim(0.14, 0.46); ax1.set_aspect('equal')
ax1.tick_params(labelsize=5.8); ax1.legend(loc='upper right', framealpha=0.9, fontsize=6.0)

theta_pts = np.linspace(0, 2*np.pi, 32, endpoint=False)
x_rim = 0.30 + 0.12 * np.cos(theta_pts); y_rim = 0.30 + 0.12 * np.sin(theta_pts)
np.random.seed(42)
r_int = np.random.uniform(0.12, 0.12 + 0.14, 90); th_int = np.random.uniform(0, 2*np.pi, 90)
xi = 0.30 + r_int * np.cos(th_int); yi = 0.30 + r_int * np.sin(th_int)
ax2.scatter(xi, yi, s=6, color='#1f77b4', alpha=0.7, label=r'Interior $N_f$')
ax2.scatter(x_rim, y_rim, s=14, color='#d62728', zorder=5, label=r'Polar $N_{\mathrm{furos}}$')
ax2.add_patch(plt.Circle((0.30, 0.30), 0.12, color='black', fill=False, lw=1.1, ls='-'))
ax2.set_title(r'(b) PINN: Amostragem Contínua', fontsize=7.2, pad=2)
ax2.set_xlabel('$x$ [m]', fontsize=6.8)
ax2.set_xlim(0.14, 0.46); ax2.set_ylim(0.14, 0.46); ax2.set_aspect('equal')
ax2.tick_params(labelsize=5.8); ax2.legend(loc='upper right', framealpha=0.9, fontsize=6.0)
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig1_geometry_staircasing.pdf"))
plt.savefig(os.path.join(fig_dir, "fig1_geometry_staircasing.png"))
plt.close()

# ==============================================================================
# Rede neural
# ==============================================================================
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
nx, ny = 160, 160
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_val = torch.tensor(XP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
TP_val_2 = torch.full_like(XP_val, 2.0, device=device)

with torch.no_grad():
    U_pred_2 = model(XP_val, YP_val, TP_val_2).cpu().numpy().reshape(nx, ny)

# ==============================================================================
# 2. FIGURA DUPLA: Dinâmica das Perdas (maior largura) + Chapa 3D sem máscara (t=2s)
# ==============================================================================
history = checkpoint['loss_history']
ep_raw = np.array(history['epoch'])
step = 50
jump = max(1, int(step / (ep_raw[1] - ep_raw[0])))
ep_plot = ep_raw[::jump]

fig = plt.figure(figsize=(7.2, 2.35), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[1.30, 1.0], wspace=0.22)

# (a) Loss plot (maior largura, sem ficar excessivamente esticada, legibilidade total)
ax1 = fig.add_subplot(gs[0, 0])
plot_config = {
    'total': (r'$\mathcal{L}_{\mathrm{total}}$', '#1f77b4', 1.15, '-'),
    'pde': (r'$\mathcal{L}_{\mathrm{pde}}$', '#d62728', 0.85, '-'),
    'bc_holes': (r'$\mathcal{L}_{\mathrm{furos}}$ ($u|_{\partial\mathcal{H}_k}=0$)', '#2ca02c', 0.85, '-'),
    'bc_ext': (r'$\mathcal{L}_{\mathrm{ext}}$ ($u|_{\partial\Omega_{\mathrm{ext}}}=1$)', '#9467bd', 0.85, '-'),
    'ic': (r'$\mathcal{L}_{\mathrm{ic}}$ ($u|_{t=0}=0$)', '#ff7f0e', 0.85, '-')
}
for k, (label, color, lw, ls) in plot_config.items():
    if k in history:
        vals = np.array(history[k])[::jump]
        ax1.semilogy(ep_plot, vals, label=label, color=color, lw=lw, ls=ls)

ax1.axvline(26000, color='crimson', linestyle='--', lw=1.1, alpha=0.9)

# Anotação de rigidez numérica nítida, com caixa de destaque
ax1.annotate('Rigidez Numérica\n' + r'($\sim 26\mathrm{k}$ épocas)', 
             xy=(26000, 2.2e-3), xytext=(27500, 5e-2),
             arrowprops=dict(arrowstyle="->", color="crimson", lw=1.0),
             fontsize=7.0, fontweight='bold', color='darkred',
             bbox=dict(boxstyle="round,pad=0.3", fc="#fff5f5", ec="crimson", lw=0.7))

ax1.grid(True, which='major', ls='-', alpha=0.35)
ax1.grid(True, which='minor', ls=':', alpha=0.15)
ax1.legend(loc='upper right', framealpha=0.92, fontsize=6.0, ncol=2)
ax1.set_xlabel('Épocas de Treinamento', fontsize=7.5)
ax1.set_ylabel('MSE', fontsize=7.5)
ax1.set_title(r'(a) Dinâmica de Convergência das Perdas', fontsize=8.0, pad=3)
ax1.tick_params(labelsize=6.5)
ax1.set_xlim(0, 50000)

# (b) Chapa em 3D em t=2.0s sem máscara, com a depressão nas cavidades
ax2 = fig.add_subplot(gs[0, 1], projection='3d')
step3d = 2
XP3 = XP[::step3d, ::step3d]; YP3 = YP[::step3d, ::step3d]; U3 = U_pred_2[::step3d, ::step3d]
surf = ax2.plot_surface(XP3, YP3, U3, cmap='inferno', edgecolor='none', alpha=0.92, vmin=0.0, vmax=1.0)
ax2.set_title(r'(b) Chapa 3D sem Máscara ($t=2{,}0\,\mathrm{s}$)', fontsize=8.0, pad=3)
ax2.view_init(elev=50, azim=-50)
ax2.set_zlim(-0.8, 1.0)
ax2.tick_params(labelsize=5.5, pad=0.5)
ax2.set_xlabel('$x$', fontsize=7.0, labelpad=-3)
ax2.set_ylabel('$y$', fontsize=7.0, labelpad=-3)
ax2.set_zlabel(r'$\hat{u}$', fontsize=7.0, labelpad=-5)

cbar = fig.colorbar(surf, ax=ax2, shrink=0.68, aspect=12, pad=0.08)
cbar.set_label(r'$\hat{u}(x,y,t)$', fontsize=6.8)
cbar.ax.tick_params(labelsize=5.5)

plt.subplots_adjust(left=0.08, right=0.96, bottom=0.14, top=0.90)
plt.savefig(os.path.join(fig_dir, "fig_loss_3d_duo.pdf"))
plt.savefig(os.path.join(fig_dir, "fig_loss_3d_duo.png"))
plt.close()

# ==============================================================================
# 3. FIGURA DOS 6 TEMPOS: Totalmente sem máscara, tons escuros nos furos como preview_2D_nomask
# ==============================================================================
eval_times = [
    (0.05, r"(a) $t = 0{,}05\,\mathrm{s}$"),
    (0.20, r"(b) $t = 0{,}20\,\mathrm{s}$"),
    (0.50, r"(c) $t = 0{,}50\,\mathrm{s}$"),
    (1.00, r"(d) $t = 1{,}00\,\mathrm{s}$"),
    (2.00, r"(e) $t = 2{,}00\,\mathrm{s}$"),
    (5.00, r"(f) $t = 5{,}00\,\mathrm{s}$ (Extrapolação)")
]

fig, axes = plt.subplots(2, 3, figsize=(6.8, 3.35), dpi=300)

for idx, (t_val, title) in enumerate(eval_times):
    row, col = idx // 3, idx % 3
    ax = axes[row, col]
    TP_val = torch.full_like(XP_val, t_val, device=device)
    with torch.no_grad():
        U_pred = model(XP_val, YP_val, TP_val).cpu().numpy().reshape(nx, ny)
    
    # vmin=0.0, vmax=1.0: exatamente como no script original preview_2D_nomask.png!
    im = ax.imshow(U_pred, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
    
    # Linhas de contorno finas (lw=0.32)
    ax.contour(XP, YP, U_pred, levels=8, colors='cyan', linewidths=0.32, alpha=0.6)
    
    # Circunferências das cavidades bem finas (lw=0.45)
    for (hx, hy, hr) in holes:
        ax.add_patch(plt.Circle((hx, hy), hr, color='#39ff14', fill=False, lw=0.45, ls='--', alpha=0.9))
        
    ax.set_title(title, fontsize=7.2, pad=2)
    ax.set_xlabel("$x$ [m]", fontsize=6.5)
    if col == 0:
        ax.set_ylabel("$y$ [m]", fontsize=6.5)
    ax.tick_params(labelsize=5.5)

cbar_ax = fig.add_axes([0.915, 0.15, 0.012, 0.72])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label(r'$\hat{u}_{\theta}(x, y, t)$', fontsize=7.2)
cbar.ax.tick_params(labelsize=5.5)

plt.subplots_adjust(left=0.08, right=0.90, bottom=0.10, top=0.93, wspace=0.16, hspace=0.28)
out_path = os.path.join(fig_dir, "fig_combined_plate_analysis.pdf")
plt.savefig(out_path)
plt.savefig(os.path.join(fig_dir, "fig_combined_plate_analysis.png"))
plt.close()

print("[OK] Figuras atualizadas com perfeição!")
