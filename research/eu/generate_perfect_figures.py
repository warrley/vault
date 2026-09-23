import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D

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
# Modelo PINN
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
nx, ny = 200, 200
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_val = torch.tensor(XP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
TP_val_2 = torch.full_like(XP_val, 2.0, device=device)

with torch.no_grad():
    U_pred_2 = model(XP_val, YP_val, TP_val_2).cpu().numpy().reshape(nx, ny)

# ==============================================================================
# 1. FIGURA DUPLA: Dinâmica das Perdas (esticada pros lados) + Chapa 3D (elev=65, azim=-45)
# ==============================================================================
history = checkpoint['loss_history']
ep_raw = np.array(history['epoch'])
step = 50
jump = max(1, int(step / (ep_raw[1] - ep_raw[0])))
ep_plot = ep_raw[::jump]

# Largura 7.4 e width_ratios=[1.65, 1.0] para esticar a loss
fig = plt.figure(figsize=(7.4, 2.4), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[1.65, 1.0], wspace=0.18)

# (a) Loss plot esticado horizontalmente
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

ax1.axvline(26000, color='#b22222', linestyle='--', lw=0.9, alpha=0.75)

# Anotação de rigidez numérica discreta e leve (menos carregada)
ax1.annotate('Rigidez numérica\n' + r'($\sim 26\mathrm{k}$ épocas)', 
             xy=(26000, 2.2e-3), xytext=(28000, 4e-2),
             arrowprops=dict(arrowstyle="->", color="#b22222", lw=0.75),
             fontsize=6.5, color='#8b0000',
             bbox=dict(boxstyle="round,pad=0.2", fc="#fafafa", ec="#dcdcdc", lw=0.5))

ax1.grid(True, which='major', ls='-', alpha=0.35)
ax1.grid(True, which='minor', ls=':', alpha=0.15)
ax1.legend(loc='upper right', framealpha=0.92, fontsize=6.2, ncol=2)
ax1.set_xlabel('Épocas de Treinamento', fontsize=7.5)
ax1.set_ylabel('MSE', fontsize=7.5)
ax1.set_title(r'(a) Dinâmica de Convergência das Perdas', fontsize=8.2, pad=3)
ax1.tick_params(labelsize=6.5)
ax1.set_xlim(0, 50000)

# (b) Chapa em 3D: exatamente como em fig_t2_3D_nomask_topdown.png (elev=65, azim=-45, zlim=[-0.8, 1.0])
ax2 = fig.add_subplot(gs[0, 1], projection='3d')
step3d = 2
XP3 = XP[::step3d, ::step3d]; YP3 = YP[::step3d, ::step3d]; U3 = U_pred_2[::step3d, ::step3d]
surf = ax2.plot_surface(XP3, YP3, U3, cmap='inferno', edgecolor='none', alpha=0.92, vmin=0.0, vmax=1.0)
ax2.set_title(r'(b) Relevo Térmico 3D ($t=2{,}0\,\mathrm{s}$)', fontsize=8.2, pad=3)
ax2.view_init(elev=65, azim=-45)
ax2.set_zlim(-0.8, 1.0)
ax2.tick_params(labelsize=5.5, pad=0.5)
ax2.set_xlabel('$x$', fontsize=7.0, labelpad=-3)
ax2.set_ylabel('$y$', fontsize=7.0, labelpad=-3)
ax2.set_zlabel(r'$\hat{u}$', fontsize=7.0, labelpad=-5)

cbar = fig.colorbar(surf, ax=ax2, shrink=0.72, aspect=12, pad=0.08)
cbar.set_label(r'$\hat{u}(x,y,t)$', fontsize=6.8)
cbar.ax.tick_params(labelsize=5.5)

plt.subplots_adjust(left=0.07, right=0.96, bottom=0.14, top=0.91)
plt.savefig(os.path.join(fig_dir, "fig_loss_3d_duo.pdf"))
plt.savefig(os.path.join(fig_dir, "fig_loss_3d_duo.png"))
plt.close()

# ==============================================================================
# 2. FIGURA DOS 6 TEMPOS: Totalmente limpa, sem sobreposição nos eixos e títulos
# ==============================================================================
eval_times = [
    (0.05, r"(a) $t = 0{,}05\,\mathrm{s}$"),
    (0.20, r"(b) $t = 0{,}20\,\mathrm{s}$"),
    (0.50, r"(c) $t = 0{,}50\,\mathrm{s}$"),
    (1.00, r"(d) $t = 1{,}00\,\mathrm{s}$"),
    (2.00, r"(e) $t = 2{,}00\,\mathrm{s}$"),
    (5.00, r"(f) $t = 5{,}00\,\mathrm{s}$ (Extrapolação)")
]

fig, axes = plt.subplots(2, 3, figsize=(6.8, 3.45), dpi=300)

for idx, (t_val, title) in enumerate(eval_times):
    row, col = idx // 3, idx % 3
    ax = axes[row, col]
    TP_val = torch.full_like(XP_val, t_val, device=device)
    with torch.no_grad():
        U_pred = model(XP_val, YP_val, TP_val).cpu().numpy().reshape(nx, ny)
    
    im = ax.imshow(U_pred, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
    ax.contour(XP, YP, U_pred, levels=8, colors='cyan', linewidths=0.32, alpha=0.6)
    
    for (hx, hy, hr) in holes:
        ax.add_patch(plt.Circle((hx, hy), hr, color='#39ff14', fill=False, lw=0.45, ls='--', alpha=0.9))
        
    ax.set_title(title, fontsize=7.2, pad=3)
    
    # O label x [m] é colocado apenas na linha inferior (row == 1), evitando qualquer conflito com os títulos!
    if row == 1:
        ax.set_xlabel("$x$ [m]", fontsize=6.5, labelpad=2)
    else:
        ax.set_xlabel("")
        
    if col == 0:
        ax.set_ylabel("$y$ [m]", fontsize=6.5, labelpad=2)
    else:
        ax.set_ylabel("")
        
    ax.tick_params(labelsize=5.5)

cbar_ax = fig.add_axes([0.915, 0.15, 0.012, 0.72])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label(r'$\hat{u}_{\theta}(x, y, t)$', fontsize=7.2)
cbar.ax.tick_params(labelsize=5.5)

# hspace aumentado para 0.34 para dar folga vertical total entre linhas
plt.subplots_adjust(left=0.08, right=0.90, bottom=0.10, top=0.93, wspace=0.16, hspace=0.34)
out_path = os.path.join(fig_dir, "fig_combined_plate_analysis.pdf")
plt.savefig(out_path)
plt.savefig(os.path.join(fig_dir, "fig_combined_plate_analysis.png"))
plt.close()

print("[OK] Figuras geradas com perfeição absoluta!")
