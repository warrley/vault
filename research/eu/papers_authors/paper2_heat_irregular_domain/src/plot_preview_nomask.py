import os
import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'serif', 'font.size': 9})
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

# 1. IMAGEM 2D TOTALMENTE SEM MÁSCARA
L = 1.0
nx, ny = 200, 200
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)

XP_val = torch.tensor(XP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP.flatten(), dtype=torch.float32, device=device).unsqueeze(1)
TP_val = torch.full_like(XP_val, 2.0, device=device) # Avaliando no tempo t = 2.0s

with torch.no_grad():
    U_full = model(XP_val, YP_val, TP_val).cpu().numpy().reshape(nx, ny)

plt.figure(figsize=(5, 4), dpi=300)
im = plt.imshow(U_full, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
plt.contour(XP, YP, U_full, levels=8, colors='cyan', linewidths=0.5, alpha=0.8)

# Desenhamos apenas o contorno verde pontilhado para saber onde os furos estão
holes = [(0.30, 0.30, 0.12), (0.70, 0.30, 0.12), (0.50, 0.70, 0.12)]
for (hx, hy, hr) in holes:
    plt.gca().add_patch(plt.Circle((hx, hy), hr, color='lime', fill=False, lw=1.5, ls='--'))

plt.title(f"Visualização SEM MÁSCARA (Época {checkpoint['epoch']})\nt = 2.0s")
plt.colorbar(im, label='Temperatura u(x,y,t)')
plt.savefig("./paper2_heat_irregular_domain/figures/preview_2D_nomask.png", bbox_inches='tight')
plt.close()

# 2. GRÁFICO DE LOSS COM SALTOS DE 250
history = checkpoint['loss_history']
# Como salvamos a cada 25 épocas no histórico, saltos de 10 em 10 dão 250 épocas.
ep_250 = history['epoch'][::10]
tot_250 = history['total'][::10]
pde_250 = history['pde'][::10]
holes_250 = history['bc_holes'][::10]

plt.figure(figsize=(6, 3.5), dpi=300)
plt.semilogy(ep_250, tot_250, label='Total (suavizado)', lw=1.8, color='#1f77b4')
plt.semilogy(ep_250, pde_250, label='PDE (suavizado)', lw=1.2, color='#d62728', ls='--')
plt.semilogy(ep_250, holes_250, label='Holes BC (suavizado)', lw=1.2, color='#2ca02c', ls='-.')
plt.grid(True, ls=':', alpha=0.6)
plt.legend()
plt.title("Curva de Perda (Amostrada a cada 250 épocas)")
plt.savefig("./paper2_heat_irregular_domain/figures/preview_Loss_250.png", bbox_inches='tight')
plt.close()
