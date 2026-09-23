import os
import numpy as np
import scipy.fft as fft
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size': 7.0,
    'axes.labelsize': 7.0,
    'axes.titlesize': 7.5,
    'xtick.labelsize': 6.0,
    'ytick.labelsize': 6.0,
    'legend.fontsize': 5.8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'cm'
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FIG_DIR = os.path.join(ROOT_DIR, 'figures')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets')
os.makedirs(FIG_DIR, exist_ok=True)

# 1. FIGURA 1
loss_data = np.load(os.path.join(DATA_DIR, 'loss_history_20000_epochs.npz'))
epochs = loss_data['epoch']
loss_total = loss_data['total_loss']
loss_pde_u = loss_data['pde_u_loss']
loss_pde_v = loss_data['pde_v_loss']
loss_ic = loss_data['ic_loss']
loss_bc = loss_data['bc_loss']

a, b, kappa = 0.1305, 0.7695, 100.0
D1, D2 = 0.05, 1.0
L, t_max = 1.0, 2.0
u_star, v_star = a + b, b / ((a + b)**2)

N_grid = 128
x_lin = np.linspace(0, L, N_grid)
y_lin = np.linspace(0, L, N_grid)
X_mesh, Y_mesh = np.meshgrid(x_lin, y_lin)

u_sim = u_star + 1e-3 * np.exp(-100.0 * ((X_mesh - 1.0/3.0)**2 + (Y_mesh - 0.5)**2))
v_sim = np.full_like(u_sim, v_star)

kx = np.pi * np.arange(N_grid) / L
ky = np.pi * np.arange(N_grid) / L
KX, KY = np.meshgrid(kx, ky)
Lap_eigen = -(KX**2 + KY**2)
dt = 1e-4
steps = int(t_max / dt)
denom_u = 1.0 - dt * D1 * Lap_eigen
denom_v = 1.0 - dt * D2 * Lap_eigen

eval_times = np.linspace(0, t_max, 100)
amp_adi = []
next_t = 0

for step in range(steps):
    t_curr = step * dt
    if next_t < len(eval_times) and t_curr >= eval_times[next_t] - dt/2:
        amp_adi.append(np.sqrt(np.mean((u_sim - u_star)**2)))
        next_t += 1
    fu = kappa * (a - u_sim + (u_sim**2)*v_sim)
    fv = kappa * (b - (u_sim**2)*v_sim)
    rhs_u = u_sim + dt * fu
    rhs_v = v_sim + dt * fv
    u_sim = fft.idctn(fft.dctn(rhs_u, type=2, norm='ortho') / denom_u, type=2, norm='ortho')
    v_sim = fft.idctn(fft.dctn(rhs_v, type=2, norm='ortho') / denom_v, type=2, norm='ortho')

if next_t < len(eval_times):
    amp_adi.append(np.sqrt(np.mean((u_sim - u_star)**2)))

class SchnakenbergPureMLP(nn.Module):
    def __init__(self, hidden_dim=128, num_layers=5):
        super().__init__()
        layers = [nn.Linear(3, hidden_dim), nn.Tanh()]
        for _ in range(num_layers - 1):
            layers.extend([nn.Linear(hidden_dim, hidden_dim), nn.Tanh()])
        layers.append(nn.Linear(hidden_dim, 2))
        self.net = nn.Sequential(*layers)

    def forward(self, xyt):
        return self.net(xyt)

model = SchnakenbergPureMLP()
model.load_state_dict(torch.load(os.path.join(ASSETS_DIR, 'schnakenberg_pinn_20000epochs.pth'), map_location='cpu', weights_only=True))
model.eval()

eval_pts = np.stack([X_mesh.flatten(), Y_mesh.flatten()], axis=1)
amp_pinn = []
with torch.no_grad():
    for t_val in eval_times:
        t_arr = np.full((len(eval_pts), 1), t_val)
        inp = torch.tensor(np.hstack([eval_pts, t_arr]), dtype=torch.float32)
        u_pred = model(inp)[:, 0].numpy()
        amp_pinn.append(np.sqrt(np.mean((u_pred - u_star)**2)))

fig = plt.figure(figsize=(7.5, 2.7), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[2.5, 1.35], wspace=0.22)

# (a) Loss
ax1 = fig.add_subplot(gs[0, 0])
ax1.semilogy(epochs, loss_total, label=r'$\mathcal{L}_{\mathrm{total}}$', color='#1f77b4', lw=1.1)
ax1.semilogy(epochs, loss_pde_u, label=r'$\mathcal{L}_{\mathrm{pde}, u}$', color='#d62728', lw=0.8, ls='--')
ax1.semilogy(epochs, loss_pde_v, label=r'$\mathcal{L}_{\mathrm{pde}, v}$', color='#ff7f0e', lw=0.8, ls=':')
ax1.semilogy(epochs, loss_ic, label=r'$\mathcal{L}_{\mathrm{ic}}$', color='#2ca02c', lw=0.8, ls='-.')
ax1.semilogy(epochs, loss_bc, label=r'$\mathcal{L}_{\mathrm{bc}}$', color='#9467bd', lw=0.8, ls='-')

ax1.set_xlabel('Épocas de Treinamento', fontsize=6.8)
ax1.set_ylabel('MSE', fontsize=6.8)
ax1.set_title(r'(a) Dinâmica de Convergência das Perdas', fontsize=9.5, pad=2)
ax1.grid(True, which='major', ls='-', alpha=0.35)
ax1.grid(True, which='minor', ls=':', alpha=0.15)
ax1.legend(loc='upper right', framealpha=0.92, fontsize=5.5, ncol=2)
ax1.set_xlim(0, 20000)
ax1.tick_params(labelsize=5.8)

# (b) Heterogeneidade
ax2 = fig.add_subplot(gs[0, 1])
ax2.plot(eval_times, amp_adi, label='MDF ADI (Pereira, 2019)', color='#2ca02c', lw=1.1)
ax2.plot(eval_times, amp_pinn, label='PINN Padrão', color='#d62728', lw=1.1, ls='--')
ax2.axhline(0, color='black', ls=':', lw=0.7, alpha=0.6)

ax2.annotate('Crescimento\nExponencial', xy=(0.42, 0.40), xytext=(0.04, 0.56),
             arrowprops=dict(arrowstyle='->', color='#2ca02c', lw=0.8, shrinkA=2, shrinkB=3),
             fontsize=5.5, ha='left', va='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='#f4fff4', alpha=0.9, edgecolor='#2ca02c', lw=0.4))

ax2.annotate('Saturação\nde Spots', xy=(1.60, 0.60), xytext=(1.05, 0.35),
             arrowprops=dict(arrowstyle='->', color='#2ca02c', lw=0.8, shrinkA=2, shrinkB=3),
             fontsize=5.5, ha='center', va='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='#f4fff4', alpha=0.9, edgecolor='#2ca02c', lw=0.4))

ax2.annotate('Colapso\nHomogêneo', xy=(1.10, 0.002), xytext=(1.48, 0.18),
             arrowprops=dict(arrowstyle='->', color='#d62728', lw=0.8, shrinkA=2, shrinkB=3),
             fontsize=5.5, ha='center', va='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='#fff5f5', alpha=0.9, edgecolor='#d62728', lw=0.4))

ax2.set_xlabel('Tempo $t$ (s)', fontsize=6.8)
ax2.set_ylabel(r'$\| u(t) - u^* \|_{L_2}$', fontsize=6.8)
ax2.set_title(r'(b) Heterogeneidade Temporal', fontsize=9.5, pad=2)
ax2.set_ylim(-0.04, 0.82)
ax2.set_xlim(0, 2.0)
ax2.grid(True, ls=':', alpha=0.6)
ax2.legend(loc='upper left', framealpha=0.92, fontsize=5.5)
ax2.tick_params(labelsize=5.8)

plt.subplots_adjust(left=0.08, right=0.98, bottom=0.18, top=0.88)
plt.savefig(os.path.join(FIG_DIR, 'fig_loss_heterogeneity_duo.pdf'))
plt.savefig(os.path.join(FIG_DIR, 'fig_loss_heterogeneity_duo.png'))
plt.close()

# 2. FIGURA 2
N_eval = 256
x_e = np.linspace(0, L, N_eval)
y_e = np.linspace(0, L, N_eval)
X_e, Y_e = np.meshgrid(x_e, y_e)

snap_times = [0.02, 0.41, 2.00]
snaps_gt = {}
u_sim2 = u_star + 1e-3 * np.exp(-100.0 * ((X_e - 1.0/3.0)**2 + (Y_e - 0.5)**2))
v_sim2 = np.full_like(u_sim2, v_star)

kx2 = np.pi * np.arange(N_eval) / L
ky2 = np.pi * np.arange(N_eval) / L
KX2, KY2 = np.meshgrid(kx2, ky2)
Lap_e2 = -(KX2**2 + KY2**2)
denom_u2 = 1.0 - dt * D1 * Lap_e2
denom_v2 = 1.0 - dt * D2 * Lap_e2

next_snap = 0
for step in range(steps):
    t_curr = step * dt
    if next_snap < len(snap_times) and t_curr >= snap_times[next_snap] - dt/2:
        snaps_gt[snap_times[next_snap]] = u_sim2.copy()
        next_snap += 1
    fu = kappa * (a - u_sim2 + (u_sim2**2)*v_sim2)
    fv = kappa * (b - (u_sim2**2)*v_sim2)
    u_sim2 = fft.idctn(fft.dctn(u_sim2 + dt*fu, type=2, norm='ortho') / denom_u2, type=2, norm='ortho')
    v_sim2 = fft.idctn(fft.dctn(v_sim2 + dt*fv, type=2, norm='ortho') / denom_v2, type=2, norm='ortho')

if next_snap < len(snap_times):
    snaps_gt[snap_times[-1]] = u_sim2.copy()

eval_pts2 = np.stack([X_e.flatten(), Y_e.flatten()], axis=1)
snaps_pinn = {}
with torch.no_grad():
    for t_val in snap_times:
        t_arr = np.full((len(eval_pts2), 1), t_val)
        out = model(torch.tensor(np.hstack([eval_pts2, t_arr]), dtype=torch.float32))
        snaps_pinn[t_val] = out[:, 0].numpy().reshape(N_eval, N_eval)

fig = plt.figure(figsize=(7.5, 3.8), dpi=300)
gs_main = gridspec.GridSpec(1, 2, width_ratios=[1.75, 1.0], wspace=0.28)
gs_left = gridspec.GridSpecFromSubplotSpec(2, 3, subplot_spec=gs_main[0], wspace=0.14, hspace=0.24)

titles_col = [r'$t = 0{,}02\,\mathrm{s}$', r'$t = 0{,}41\,\mathrm{s}$', r'$t = 2{,}00\,\mathrm{s}$']

for j, t_val in enumerate(snap_times):
    vmin_t, vmax_t = snaps_gt[t_val].min(), snaps_gt[t_val].max()
    
    ax_top = fig.add_subplot(gs_left[0, j])
    im0 = ax_top.imshow(snaps_gt[t_val], extent=[0, L, 0, L], origin='lower',
                        cmap='jet', interpolation='bicubic', vmin=vmin_t, vmax=vmax_t)
    ax_top.set_title(titles_col[j], fontsize=6.5, pad=1.5)
    ax_top.set_aspect('equal')
    ax_top.tick_params(labelsize=4.8)
    if j == 0:
        ax_top.set_ylabel('MDF ADI\n(Pereira, 2019)', fontsize=5.8)
    else:
        ax_top.set_yticklabels([])
    ax_top.set_xticklabels([])
    
    ax_bot = fig.add_subplot(gs_left[1, j])
    im1 = ax_bot.imshow(snaps_pinn[t_val], extent=[0, L, 0, L], origin='lower',
                        cmap='jet', interpolation='bicubic', vmin=vmin_t, vmax=vmax_t)
    ax_bot.set_xlabel('$x$', fontsize=6.0, labelpad=1)
    ax_bot.set_aspect('equal')
    ax_bot.tick_params(labelsize=4.8)
    if j == 0:
        ax_bot.set_ylabel('PINN Padrão\n$y$', fontsize=5.8)
    else:
        ax_bot.set_yticklabels([])

ax_cut = fig.add_subplot(gs_main[1])
y_mid_idx = N_eval // 2
u_adi_cut = snaps_gt[2.00][y_mid_idx, :]
u_pinn_cut = snaps_pinn[2.00][y_mid_idx, :]

ax_cut.plot(x_e, u_adi_cut, label='MDF ADI (Pereira, 2019)', color='#2ca02c', lw=1.1)
ax_cut.plot(x_e, u_pinn_cut, label='PINN Padrão', color='#d62728', lw=1.1, ls='--')
ax_cut.axhline(u_star, color='black', ls=':', lw=0.7, alpha=0.7, label=f'Equilíbrio $u^* = {u_star:.2f}$')
ax_cut.set_xlabel('Coordenada $x$ [m]', fontsize=6.5, labelpad=1)
ax_cut.set_ylabel('Concentração $u(x, 0.5, 2.0)$', fontsize=6.5, labelpad=1)
ax_cut.set_title(r'(b) Perfil Transversal ($y=0{,}5\,\mathrm{m}, t=2{,}0\,\mathrm{s}$)', fontsize=6.8, pad=2)
ax_cut.grid(True, ls=':', alpha=0.6)
ax_cut.legend(loc='upper right', framealpha=0.92, fontsize=5.2)
ax_cut.set_xlim(0, 1.0)
ax_cut.set_ylim(0.0, 3.0)
ax_cut.tick_params(labelsize=5.5)

plt.subplots_adjust(left=0.06, right=0.98, bottom=0.16, top=0.88)
plt.savefig(os.path.join(FIG_DIR, 'fig_combined_snapshots_profile.pdf'))
plt.savefig(os.path.join(FIG_DIR, 'fig_combined_snapshots_profile.png'))
plt.close()
print("Figuras geradas com sucesso!")
