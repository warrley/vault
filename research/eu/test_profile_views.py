import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

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
XP_flat = XP.flatten(); YP_flat = YP.flatten()

mask_valid = np.ones_like(XP_flat, dtype=bool)
for (hx, hy, hr) in holes:
    mask_valid = mask_valid & (((XP_flat - hx)**2 + (YP_flat - hy)**2) >= hr**2)

XP_val = torch.tensor(XP_flat, dtype=torch.float32, device=device).unsqueeze(1)
YP_val = torch.tensor(YP_flat, dtype=torch.float32, device=device).unsqueeze(1)
TP_val = torch.full_like(XP_val, 2.0, device=device)

with torch.no_grad():
    u_p = model(XP_val, YP_val, TP_val).cpu().numpy().flatten()

U_cut = np.full_like(XP_flat, np.nan)
U_cut[mask_valid] = u_p[mask_valid]
U_mat_cut = U_cut.reshape(nx, ny)

# Let's test default view (elev=30, azim=-60), and a bit higher (elev=40, azim=-60), (elev=45, azim=-60)
for elev in [30, 38, 45]:
    fig = plt.figure(figsize=(5, 4), dpi=300)
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(XP, YP, U_mat_cut, cmap='inferno', edgecolor='none', alpha=0.92, vmin=0.0, vmax=1.0)
    ax.view_init(elev=elev, azim=-60)
    ax.set_zlim(0, 1.0)
    ax.set_title(f"elev={elev}, azim=-60")
    plt.savefig(f"/tmp/test_elev_{elev}.png")
    plt.close()
print("Generated test views!")
