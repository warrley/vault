import torch
import torch.nn as nn
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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

# 6 tempos sem NENHUMA máscara visual
# Exatamente no estilo de preview_2D_nomask.png: vmin=0.0, vmax=1.0, permitindo que os furos fiquem escuros/pretos naturais
eval_times = [
    (0.05, r"(a) $t = 0{,}05\,\mathrm{s}$"),
    (0.20, r"(b) $t = 0{,}20\,\mathrm{s}$"),
    (0.50, r"(c) $t = 0{,}50\,\mathrm{s}$"),
    (1.00, r"(d) $t = 1{,}00\,\mathrm{s}$"),
    (2.00, r"(e) $t = 2{,}00\,\mathrm{s}$"),
    (5.00, r"(f) $t = 5{,}00\,\mathrm{s}$ (Extrapolação)")
]

fig, axes = plt.subplots(2, 3, figsize=(6.8, 3.35), dpi=300)

for idx, (t_val, title) in enumerate(eval_times):
    row, col = idx // 3, idx % 3
    ax = axes[row, col]
    TP_val = torch.full_like(XP_val, t_val, device=device)
    with torch.no_grad():
        U_pred = model(XP_val, YP_val, TP_val).cpu().numpy().reshape(nx, ny)
    
    # vmin=0.0 e vmax=1.0: exatamente como em preview_2D_nomask.png!
    # Os furos ficam naturalmente escuros como sumidouros (u <= 0 -> preto no inferno)
    im = ax.imshow(U_pred, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
    
    # Linhas de contorno finas (lw=0.35)
    ax.contour(XP, YP, U_pred, levels=8, colors='cyan', linewidths=0.32, alpha=0.6)
    
    # Circunferências das cavidades finas e elegantes (lw=0.45, ls='--', cor lime suave)
    for (hx, hy, hr) in holes:
        ax.add_patch(plt.Circle((hx, hy), hr, color='#39ff14', fill=False, lw=0.45, ls='--', alpha=0.9))
        
    ax.set_title(title, fontsize=7.2, pad=2)
    ax.set_xlabel("$x$ [m]", fontsize=6.5)
    if col == 0:
        ax.set_ylabel("$y$ [m]", fontsize=6.5)
    ax.tick_params(labelsize=5.5)

cbar_ax = fig.add_axes([0.915, 0.15, 0.012, 0.72])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label(r'$\hat{u}_{\theta}(x, y, t)$', fontsize=7.2)
cbar.ax.tick_params(labelsize=5.5)

plt.subplots_adjust(left=0.08, right=0.90, bottom=0.10, top=0.93, wspace=0.16, hspace=0.28)
plt.savefig("paper2_heat_irregular_domain/figures/fig_combined_plate_analysis.pdf")
plt.savefig("paper2_heat_irregular_domain/figures/fig_combined_plate_analysis.png")
plt.close()
print("[OK] 6-time figure generated with vmin=0.0 (natural dark holes like preview_2D_nomask)!")
