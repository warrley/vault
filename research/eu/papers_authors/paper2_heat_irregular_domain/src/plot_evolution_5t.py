import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'serif', 'font.size': 10})
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

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
checkpoint = torch.load("./paper2_heat_irregular_domain/models/safe_checkpoint_preview.pth", map_location=device, weights_only=False)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

L = 1.0
holes = [(0.30, 0.30, 0.12), (0.70, 0.30, 0.12), (0.50, 0.70, 0.12)]
nx, ny = 150, 150
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_flat = XP.flatten()
YP_flat = YP.flatten()

XP_val = torch.tensor(XP_flat, dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP_flat, dtype=torch.float32, device=device).unsqueeze(1)

eval_times = [0.1, 1.0, 2.0, 3.5, 5.0]
fig, axes = plt.subplots(1, 5, figsize=(14, 2.8), dpi=300, sharey=True)

for idx, t_val in enumerate(eval_times):
    TP_val = torch.full_like(XP_val, t_val, device=device)
    with torch.no_grad():
        U_full = model(XP_val, YP_val, TP_val).cpu().numpy().reshape(nx, ny)
    
    im = axes[idx].imshow(U_full, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
    axes[idx].contour(XP, YP, U_full, levels=6, colors='cyan', linewidths=0.5, alpha=0.6)
    
    for (hx, hy, hr) in holes:
        axes[idx].add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=1.5, ls='--', zorder=6))
        
    axes[idx].set_title(f"t = {t_val}s", fontsize=12)
    axes[idx].set_xlabel("x")
    if idx == 0:
        axes[idx].set_ylabel("y")

cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85, pad=0.02)
cbar.set_label('Temperatura u(x,y,t)', fontsize=11)

fig.suptitle(f"Evolução Térmica (Com Extrapolação Temporal t>2.0) - Época {checkpoint['epoch']}", fontsize=14, y=1.08)
plt.savefig("./paper2_heat_irregular_domain/figures/preview_evolution_extrapolation.png", bbox_inches='tight')
plt.close()
