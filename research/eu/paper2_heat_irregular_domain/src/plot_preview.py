import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Tipografia
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class IrregularHeatPINN(nn.Module):
    def __init__(self, hidden_dim=128, num_layers=5):
        super().__init__()
        layers = []
        layers.append(nn.Linear(3, hidden_dim))
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x, y, t):
        inputs = torch.cat([x, y, t], dim=1)
        return self.net(inputs)

model = IrregularHeatPINN(hidden_dim=128, num_layers=5).to(device)

checkpoint_path = "./paper2_heat_irregular_domain/models/safe_checkpoint_preview.pth"
checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

current_epoch = checkpoint['epoch']
print(f"Gerando imagens do checkpoint da Época {current_epoch}...")

L = 1.0
holes = [(0.30, 0.30, 0.12), (0.70, 0.30, 0.12), (0.50, 0.70, 0.12)]
fig_dir = "./paper2_heat_irregular_domain/figures"

nx, ny = 200, 200
xp = np.linspace(0, L, nx)
yp = np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_flat = XP.flatten()
YP_flat = YP.flatten()

mask_valid = np.ones_like(XP_flat, dtype=bool)
for (hx, hy, hr) in holes:
    mask_valid = mask_valid & (((XP_flat - hx)**2 + (YP_flat - hy)**2) >= hr**2)

XP_val = torch.tensor(XP_flat[mask_valid], dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP_flat[mask_valid], dtype=torch.float32, device=device).unsqueeze(1)
TP_val = torch.full_like(XP_val, 2.0, device=device)

with torch.no_grad():
    u_p = model(XP_val, YP_val, TP_val).cpu().numpy().flatten()

U_full = np.full_like(XP_flat, np.nan)
U_full[mask_valid] = u_p
U_mat = U_full.reshape(nx, ny)

# IMAGEM 1: Contorno 2D
plt.figure(figsize=(5, 4))
im = plt.imshow(U_mat, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0, vmax=1.0)
plt.contour(XP, YP, U_mat, levels=8, colors='cyan', linewidths=0.5, alpha=0.8)
for (hx, hy, hr) in holes:
    circle_h = plt.Circle((hx, hy), hr, color='white', fill=True, zorder=5)
    plt.gca().add_patch(circle_h)
    circle_e = plt.Circle((hx, hy), hr, color='black', fill=False, lw=1.2, zorder=6)
    plt.gca().add_patch(circle_e)

plt.title(f"Visualização Parcial (Época {current_epoch})\nTempo t=2.0s")
plt.colorbar(im, label='Temperatura u(x,y,t)')
plt.savefig(os.path.join(fig_dir, "preview_2D.png"))
plt.close()

# IMAGEM 2: Superfície 3D
fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(XP, YP, U_mat, cmap='inferno', edgecolor='none', alpha=0.9)
ax.set_title(f"Relevo Térmico 3D (Época {current_epoch})")
ax.set_zlim(0, 1.0)
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
plt.savefig(os.path.join(fig_dir, "preview_3D.png"))
plt.close()

# IMAGEM 3: Gráfico de Convergência da Perda
history = checkpoint['loss_history']
plt.figure(figsize=(6, 3.5))
plt.semilogy(history['epoch'], history['total'], label='Total')
plt.semilogy(history['epoch'], history['pde'], label='PDE')
plt.semilogy(history['epoch'], history['bc_holes'], label='Holes BC')
plt.grid(True, ls=':', alpha=0.6)
plt.legend()
plt.title(f"Curva de Perda (Até Época {current_epoch})")
plt.savefig(os.path.join(fig_dir, "preview_Loss.png"))
plt.close()

print("Imagens de preview geradas com sucesso!")
