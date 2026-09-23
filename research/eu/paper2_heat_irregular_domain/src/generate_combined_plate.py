import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 8.5,
    'axes.labelsize': 9.0,
    'axes.titlesize': 9.5,
    'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5,
    'legend.fontsize': 7.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'cm'
})

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
ckpt_path = "./paper2_heat_irregular_domain/models/pinn_heat_holes_checkpoint.pth"
fig_dir = "./paper2_heat_irregular_domain/figures"
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

mask_holes = np.zeros_like(XP, dtype=bool)
for (hx, hy, hr) in holes:
    mask_holes |= ((XP - hx)**2 + (YP - hy)**2 <= hr**2)

# Painel consolidado 2x3
fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.4), dpi=300)

# Linha 1: t=0.1s, t=0.5s, t=1.0s (evolução)
eval_t1 = [0.1, 0.5, 1.0]
for idx, t_val in enumerate(eval_t1):
    TP_val = torch.full_like(XP_val, t_val, device=device)
    with torch.no_grad():
        U_pred = model(XP_val, YP_val, TP_val).cpu().numpy().reshape(nx, ny)
    U_vis = np.ma.masked_array(U_pred, mask=mask_holes)
    im1 = axes[0, idx].imshow(U_vis, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
    axes[0, idx].contour(XP, YP, U_pred, levels=[0.2, 0.4, 0.6, 0.8], colors='cyan', linewidths=0.4, alpha=0.7)
    for (hx, hy, hr) in holes:
        axes[0, idx].add_patch(plt.Circle((hx, hy), hr, color='lime', fill=True, facecolor='white', lw=0.8, ls='--', zorder=4))
    axes[0, idx].set_title(f"(a.{idx+1}) $t = {t_val}\\,\\mathrm{{s}}$", fontsize=8.2, pad=2)
    axes[0, idx].set_xlabel("$x$ [m]", fontsize=7.2)
    if idx == 0:
        axes[0, idx].set_ylabel("$y$ [m]", fontsize=7.2)
    axes[0, idx].tick_params(labelsize=6.5)

# Linha 2: t=2.0s mascarado, t=2.0s SEM máscara, t=5.0s EXTRAPOLAÇÃO
TP_val_2 = torch.full_like(XP_val, 2.0, device=device)
with torch.no_grad():
    U_pred_2 = model(XP_val, YP_val, TP_val_2).cpu().numpy().reshape(nx, ny)

# (b.1) t=2.0s mascarado
U_vis_2 = np.ma.masked_array(U_pred_2, mask=mask_holes)
axes[1, 0].imshow(U_vis_2, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
axes[1, 0].contour(XP, YP, U_pred_2, levels=[0.2, 0.4, 0.6, 0.8], colors='cyan', linewidths=0.4, alpha=0.7)
for (hx, hy, hr) in holes:
    axes[1, 0].add_patch(plt.Circle((hx, hy), hr, color='lime', fill=True, facecolor='white', lw=0.8, ls='--', zorder=4))
axes[1, 0].set_title("(b.1) $t = 2{,}0\\,\\mathrm{s}$ (Solução Física)", fontsize=8.2, pad=2)
axes[1, 0].set_xlabel("$x$ [m]", fontsize=7.2); axes[1, 0].set_ylabel("$y$ [m]", fontsize=7.2)
axes[1, 0].tick_params(labelsize=6.5)

# (b.2) t=2.0s SEM MÁSCARA
axes[1, 1].imshow(U_pred_2, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=-0.8, vmax=1.0)
axes[1, 1].contour(XP, YP, U_pred_2, levels=6, colors='cyan', linewidths=0.4, alpha=0.7)
for (hx, hy, hr) in holes:
    axes[1, 1].add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=0.9, ls='--'))
axes[1, 1].set_title("(b.2) $t = 2{,}0\\,\\mathrm{s}$ (Sem Máscara Visual)", fontsize=8.2, pad=2)
axes[1, 1].set_xlabel("$x$ [m]", fontsize=7.2)
axes[1, 1].tick_params(labelsize=6.5)

# (b.3) t=5.0s EXTRAPOLAÇÃO
TP_val_5 = torch.full_like(XP_val, 5.0, device=device)
with torch.no_grad():
    U_pred_5 = model(XP_val, YP_val, TP_val_5).cpu().numpy().reshape(nx, ny)
axes[1, 2].imshow(U_pred_5, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
axes[1, 2].contour(XP, YP, U_pred_5, levels=6, colors='cyan', linewidths=0.4, alpha=0.7)
for (hx, hy, hr) in holes:
    axes[1, 2].add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=0.9, ls='--'))
axes[1, 2].set_title("(b.3) $t = 5{,}0\\,\\mathrm{s}$ (Extrapolação Cega)", fontsize=8.2, pad=2)
axes[1, 2].set_xlabel("$x$ [m]", fontsize=7.2)
axes[1, 2].tick_params(labelsize=6.5)

# Colorbar única
cbar_ax = fig.add_axes([0.92, 0.18, 0.015, 0.68])
cbar = fig.colorbar(im1, cax=cbar_ax)
cbar.set_label('Temperatura $u(x, y, t)$', fontsize=8.0)
cbar.ax.tick_params(labelsize=6.5)

plt.subplots_adjust(left=0.08, right=0.90, bottom=0.10, top=0.92, wspace=0.15, hspace=0.30)
out_path = os.path.join(fig_dir, "fig_combined_plate_analysis.pdf")
plt.savefig(out_path)
plt.savefig(os.path.join(fig_dir, "fig_combined_plate_analysis.png"))
plt.close()
print(f"[OK] Painel consolidado da chapa gerado em: {out_path}")
