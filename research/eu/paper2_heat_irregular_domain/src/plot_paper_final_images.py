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
ckpt_path = "./paper2_heat_irregular_domain/models/pinn_heat_holes_checkpoint.pth"
checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

L = 1.0
holes = [(0.30, 0.30, 0.12), (0.70, 0.30, 0.12), (0.50, 0.70, 0.12)]
nx, ny = 200, 200
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_flat, YP_flat = XP.flatten(), YP.flatten()

XP_val = torch.tensor(XP_flat, dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP_flat, dtype=torch.float32, device=device).unsqueeze(1)
fig_dir = "./paper2_heat_irregular_domain/figures/"

# 1. t=2 without masks 2D
TP_val_2 = torch.full_like(XP_val, 2.0, device=device)
with torch.no_grad():
    U_full_2 = model(XP_val, YP_val, TP_val_2).cpu().numpy().reshape(nx, ny)

plt.figure(figsize=(5, 4), dpi=300)
im = plt.imshow(U_full_2, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
plt.contour(XP, YP, U_full_2, levels=8, colors='cyan', linewidths=0.5, alpha=0.8)
for (hx, hy, hr) in holes:
    plt.gca().add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=1.5, ls='--'))
plt.title("Campo Térmico sem Máscara (t=2.0s)")
plt.colorbar(im, label='Temperatura u(x,y,t)')
plt.savefig(os.path.join(fig_dir, "fig_t2_2D_nomask.png"), bbox_inches='tight')
plt.close()

# 2. t=2 without mask, 3D (high elevation to see inside holes)
fig = plt.figure(figsize=(6, 5), dpi=300)
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(XP, YP, U_full_2, cmap='inferno', edgecolor='none', alpha=0.9, vmin=0.0, vmax=1.0)
ax.set_title("Relevo Térmico e Depressão Interna (t=2.0s)")
# Up the eye to see inside: elev=65
ax.view_init(elev=65, azim=-45)
ax.set_zlim(-0.8, 1.0) # Expand zlim to see the negative values inside the holes
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
plt.savefig(os.path.join(fig_dir, "fig_t2_3D_nomask_topdown.png"), bbox_inches='tight')
plt.close()

# 3. t=5 2D to discuss time extrapolation
TP_val_5 = torch.full_like(XP_val, 5.0, device=device)
with torch.no_grad():
    U_full_5 = model(XP_val, YP_val, TP_val_5).cpu().numpy().reshape(nx, ny)

plt.figure(figsize=(5, 4), dpi=300)
im = plt.imshow(U_full_5, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
plt.contour(XP, YP, U_full_5, levels=8, colors='cyan', linewidths=0.5, alpha=0.8)
for (hx, hy, hr) in holes:
    plt.gca().add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=1.5, ls='--'))
plt.title("Extrapolação Fora do Domínio Treinado (t=5.0s)")
plt.colorbar(im, label='Temperatura u(x,y,t)')
plt.savefig(os.path.join(fig_dir, "fig_t5_2D_extrapol.png"), bbox_inches='tight')
plt.close()

print("Imagens finais geradas com sucesso!")
