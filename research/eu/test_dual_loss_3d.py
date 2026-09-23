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
nx, ny = 160, 160
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

# Layout: 1 linha com 2 colunas: Loss ocupa maior largura (width_ratios=[1.25, 1.0])
fig = plt.figure(figsize=(7.0, 2.3), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[1.28, 1.0], wspace=0.22)

# (a) Loss plot (maior largura, limpo, perfeitamente legível)
ax1 = fig.add_subplot(gs[0, 0])
plot_config = {
    'total': (r'$\mathcal{L}_{\mathrm{total}}$', '#1f77b4', 1.1, '-'),
    'pde': (r'$\mathcal{L}_{\mathrm{pde}}$', '#d62728', 0.8, '-'),
    'bc_holes': (r'$\mathcal{L}_{\mathrm{furos}}$ ($u|_{\partial\mathcal{H}_k}=0$)', '#2ca02c', 0.8, '-'),
    'bc_ext': (r'$\mathcal{L}_{\mathrm{ext}}$ ($u|_{\partial\Omega_{\mathrm{ext}}}=1$)', '#9467bd', 0.8, '-'),
    'ic': (r'$\mathcal{L}_{\mathrm{ic}}$ ($u|_{t=0}=0$)', '#ff7f0e', 0.8, '-')
}
for k, (label, color, lw, ls) in plot_config.items():
    if k in history:
        vals = np.array(history[k])[::jump]
        ax1.semilogy(ep_plot, vals, label=label, color=color, lw=lw, ls=ls)

ax1.axvline(26000, color='crimson', linestyle='--', lw=1.1, alpha=0.85)

# Indicação da rigidez numérica bem clara, nítida e visível
ax1.annotate(r'\textbf{Rigidez Numérica}' + '\n' + r'($\sim 26\mathrm{k}$ épocas)', 
             xy=(26000, 2.2e-3), xytext=(28000, 6e-2),
             arrowprops=dict(arrowstyle="->", color="crimson", lw=1.0),
             fontsize=6.8, color='darkred',
             bbox=dict(boxstyle="round,pad=0.25", fc="#fff5f5", ec="crimson", lw=0.6))

ax1.grid(True, which='major', ls='-', alpha=0.35)
ax1.grid(True, which='minor', ls=':', alpha=0.15)
ax1.legend(loc='upper right', framealpha=0.92, fontsize=5.8, ncol=2)
ax1.set_xlabel('Épocas de Treinamento', fontsize=7.5)
ax1.set_ylabel('MSE', fontsize=7.5)
ax1.set_title(r'(a) Dinâmica de Convergência das Perdas', fontsize=8.0, pad=3)
ax1.tick_params(labelsize=6.5)
ax1.set_xlim(0, 50000)

# (b) Chapa em 3D (t=2.0s) mostrando o relevo e a depressão contínua interna
ax2 = fig.add_subplot(gs[0, 1], projection='3d')
step3d = 2
XP3 = XP[::step3d, ::step3d]; YP3 = YP[::step3d, ::step3d]; U3 = U_pred_2[::step3d, ::step3d]
# Em inferno com vmin=0.0 as cavidades internas ficam bem escuras, mas com zlim=[-0.8, 1.0] vemos a topologia da depressão
surf = ax2.plot_surface(XP3, YP3, U3, cmap='inferno', edgecolor='none', alpha=0.92, vmin=0.0, vmax=1.0)
ax2.set_title(r'(b) Chapa 3D sem Máscara ($t=2{,}0\,\mathrm{s}$)', fontsize=8.0, pad=3)
ax2.view_init(elev=52, azim=-50)
ax2.set_zlim(-0.8, 1.0)
ax2.tick_params(labelsize=5.5, pad=0.5)
ax2.set_xlabel('$x$', fontsize=7.0, labelpad=-3)
ax2.set_ylabel('$y$', fontsize=7.0, labelpad=-3)
ax2.set_zlabel(r'$\hat{u}$', fontsize=7.0, labelpad=-5)

cbar = fig.colorbar(surf, ax=ax2, shrink=0.68, aspect=12, pad=0.08)
cbar.set_label(r'$\hat{u}(x,y,t)$', fontsize=6.8)
cbar.ax.tick_params(labelsize=5.5)

plt.subplots_adjust(left=0.08, right=0.96, bottom=0.14, top=0.90)
plt.savefig("paper2_heat_irregular_domain/figures/fig_loss_3d_duo.pdf")
plt.savefig("paper2_heat_irregular_domain/figures/fig_loss_3d_duo.png")
plt.close()
print("[OK] Duo figure (Loss + 3D) generated successfully!")
