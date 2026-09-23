import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 8.0,
    'mathtext.fontset': 'cm'
})

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ckpt_path = "./paper2_heat_irregular_domain/models/pinn_heat_holes_checkpoint.pth"
checkpoint = torch.load(ckpt_path, map_location='cpu', weights_only=False)

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
nx, ny = 140, 140
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_val = torch.tensor(XP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
TP_val_2 = torch.full_like(XP_val, 2.0, device=device)

with torch.no_grad():
    U_pred_2 = model(XP_val, YP_val, TP_val_2).cpu().numpy().reshape(nx, ny)

history = checkpoint['loss_history']
ep_raw = np.array(history['epoch'])
step = 50
jump = max(1, int(step / (ep_raw[1] - ep_raw[0])))
ep_plot = ep_raw[::jump]

fig = plt.figure(figsize=(7.2, 2.2), dpi=300)

# (a) Loss plot
ax1 = fig.add_subplot(1, 3, 1)
plot_config = {
    'total': (r'$\mathcal{L}_{\mathrm{total}}$', '#1f77b4', 1.0, '-'),
    'pde': (r'$\mathcal{L}_{\mathrm{pde}}$', '#d62728', 0.75, '-'),
    'bc_holes': (r'$\mathcal{L}_{\mathrm{furos}}$', '#2ca02c', 0.75, '-'),
    'bc_ext': (r'$\mathcal{L}_{\mathrm{ext}}$', '#9467bd', 0.75, '-'),
    'ic': (r'$\mathcal{L}_{\mathrm{ic}}$', '#ff7f0e', 0.75, '-')
}
for k, (label, color, lw, ls) in plot_config.items():
    if k in history:
        vals = np.array(history[k])[::jump]
        ax1.semilogy(ep_plot, vals, label=label, color=color, lw=lw, ls=ls)

ax1.axvline(26000, color='crimson', linestyle=':', lw=1.0, alpha=0.9)
# Box annotation for stiffness
ax1.annotate('Rigidez Numérica\n($\sim 26\\mathrm{k}$ épocas)', 
             xy=(26000, 2e-3), xytext=(28500, 1.2e-1),
             arrowprops=dict(arrowstyle="->", color="crimson", lw=0.9),
             fontsize=6.0, fontweight='bold', color='darkred',
             bbox=dict(boxstyle="round,pad=0.2", fc="#fff5f5", ec="crimson", lw=0.5))

ax1.grid(True, which='major', ls='-', alpha=0.3)
ax1.legend(loc='upper right', framealpha=0.9, fontsize=5.8, ncol=1)
ax1.set_xlabel('Épocas', fontsize=7.2)
ax1.set_ylabel('MSE', fontsize=7.2)
ax1.set_title('(a) Convergência das Perdas', fontsize=7.8, pad=3)
ax1.tick_params(labelsize=6.0)
ax1.set_xlim(0, 50000)

# (b) 2D sem máscara
ax2 = fig.add_subplot(1, 3, 2)
im2 = ax2.imshow(U_pred_2, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=-0.8, vmax=1.0)
ax2.contour(XP, YP, U_pred_2, levels=6, colors='cyan', linewidths=0.35, alpha=0.6)
for (hx, hy, hr) in holes:
    ax2.add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=0.75, ls='--'))
ax2.set_title('(b) Campo 2D Contínuo ($t=2\\,\\mathrm{s}$)', fontsize=7.8, pad=3)
ax2.set_xlabel('$x$ [m]', fontsize=7.0); ax2.set_ylabel('$y$ [m]', fontsize=7.0)
ax2.tick_params(labelsize=6.0)
cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
cbar2.ax.tick_params(labelsize=5.5)

# (c) 3D sem máscara
ax3 = fig.add_subplot(1, 3, 3, projection='3d')
# Downsample for smooth fast 3D plot
step3d = 2
XP3 = XP[::step3d, ::step3d]; YP3 = YP[::step3d, ::step3d]; U3 = U_pred_2[::step3d, ::step3d]
surf = ax3.plot_surface(XP3, YP3, U3, cmap='inferno', edgecolor='none', alpha=0.92, vmin=-0.8, vmax=1.0)
ax3.set_title('(c) Relevo 3D e Depressão ($t=2\\,\\mathrm{s}$)', fontsize=7.8, pad=3)
ax3.view_init(elev=50, azim=-50)
ax3.set_zlim(-0.8, 1.0)
ax3.tick_params(labelsize=5.0, pad=1)
ax3.set_xlabel('$x$', fontsize=6.5, labelpad=-2)
ax3.set_ylabel('$y$', fontsize=6.5, labelpad=-2)
ax3.set_zlabel('$\\hat{u}$', fontsize=6.5, labelpad=-4)

plt.tight_layout()
plt.savefig("paper2_heat_irregular_domain/figures/fig_loss_and_t2_trio.pdf")
plt.savefig("paper2_heat_irregular_domain/figures/fig_loss_and_t2_trio.png")
plt.close()
print("[OK] Trio figure generated successfully!")
