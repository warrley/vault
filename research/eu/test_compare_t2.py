import torch
import torch.nn as nn
import numpy as np

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

ckpt_preview = torch.load("./paper2_heat_irregular_domain/models/safe_checkpoint_preview.pth", map_location='cpu', weights_only=False)
ckpt_holes = torch.load("./paper2_heat_irregular_domain/models/pinn_heat_holes_checkpoint.pth", map_location='cpu', weights_only=False)

print("safe_checkpoint_preview epoch:", ckpt_preview['epoch'])
print("pinn_heat_holes_checkpoint epoch:", ckpt_holes['epoch'])

m_prev = IrregularHeatPINN()
m_prev.load_state_dict(ckpt_preview['model_state_dict'])
m_prev.eval()

L = 1.0; nx, ny = 200, 200
xp, yp = np.linspace(0, L, nx), np.linspace(0, L, ny)
XP, YP = np.meshgrid(xp, yp)
XP_val = torch.tensor(XP.flatten(), dtype=torch.float32).unsqueeze(1)
YP_val = torch.tensor(YP.flatten(), dtype=torch.float32).unsqueeze(1)
TP_val = torch.full_like(XP_val, 2.0)

with torch.no_grad():
    u_prev = m_prev(XP_val, YP_val, TP_val).numpy().reshape(nx, ny)

print("u_prev (preview_2D_nomask): min=", u_prev.min(), "max=", u_prev.max(), "mean=", u_prev.mean())
# Notice inside the holes:
for hx, hy in [(0.3, 0.3), (0.7, 0.3), (0.5, 0.7)]:
    ix = int(hx * (nx - 1)); iy = int(hy * (ny - 1))
    print(f"Center ({hx}, {hy}): u = {u_prev[iy, ix]}")
