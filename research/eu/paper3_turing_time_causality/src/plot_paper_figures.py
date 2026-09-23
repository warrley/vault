#!/usr/bin/env python3
"""
plot_paper_figures.py - Gerador das Figuras do Artigo (Schnakenberg PINN vs MDF ADI)
Você pode editar este arquivo manualmente para ajustar tamanhos de fonte, linhas, cores e dimensões!
"""

import os
import numpy as np
import scipy.fft as fft
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==============================================================================
# 1. PARÂMETROS DE ESTILO TIPOGRÁFICO (AJUSTE AQUI O TAMANHO DAS FONTES)
# ==============================================================================
# Aumente ou diminua estes valores conforme sua preferência visual:
FONT_SIZE_BASE      = 14.0   # Tamanho geral do texto
FONT_SIZE_TITLES    = 15.0   # Título dos subplots (a) e (b)
FONT_SIZE_AXIS      = 14.5   # Nomes dos eixos (x, y, MSE, Tempo)
FONT_SIZE_TICKS     = 13.0   # Números nos eixos (0, 0.5, 1.0, 10^-2)
FONT_SIZE_LEGEND    = 13.0   # Texto dentro da caixinha de legenda
FONT_SIZE_ARROWS    = 12.0   # Texto das anotações e setas
LINE_WIDTH_PRIMARY  = 3.0    # Espessura das curvas principais (Total, ADI)
LINE_WIDTH_SEC      = 2.2    # Espessura das curvas secundárias (PDE, IC, BC)

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size': FONT_SIZE_BASE,
    'axes.labelsize': FONT_SIZE_AXIS,
    'axes.titlesize': FONT_SIZE_TITLES,
    'xtick.labelsize': FONT_SIZE_TICKS,
    'ytick.labelsize': FONT_SIZE_TICKS,
    'legend.fontsize': FONT_SIZE_LEGEND,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'stix'
})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FIG_DIR = os.path.join(ROOT_DIR, 'figures')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets')
os.makedirs(FIG_DIR, exist_ok=True)

# ==============================================================================
# 2. FIGURA 1: CONVERGÊNCIA DAS PERDAS E EVOLUÇÃO DA AMPLITUDE TEMPORAL
# ==============================================================================
print("Gerando Figura 1: fig_analise_convergencia_referencia...")

# Carrega histórico salvo de 20.000 épocas
loss_data = np.load(os.path.join(DATA_DIR, 'loss_history_20000_epochs.npz'))
epochs = loss_data['epoch']
loss_total = loss_data['total_loss']
loss_pde_u = loss_data['pde_u_loss']
loss_pde_v = loss_data['pde_v_loss']
loss_ic = loss_data['ic_loss']
loss_bc = loss_data['bc_loss']

# Parâmetros físicos da tese (Pereira, 2019)
a, b, kappa = 0.1305, 0.7695, 100.0
D1, D2 = 0.05, 1.0
L, t_max = 1.0, 2.0
u_star, v_star = a + b, b / ((a + b)**2)

# Simulação ADI de referência para a curva de amplitude
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

# Amplitude da PINN
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
model.load_state_dict(torch.load(os.path.join(ASSETS_DIR, 'schnakenberg_pinn_20000epochs.pth'), map_location='cpu'))
model.eval()

eval_pts = np.stack([X_mesh.flatten(), Y_mesh.flatten()], axis=1)
amp_pinn = []
with torch.no_grad():
    for t_val in eval_times:
        t_arr = np.full((len(eval_pts), 1), t_val)
        inp = torch.tensor(np.hstack([eval_pts, t_arr]), dtype=torch.float32)
        u_pred = model(inp)[:, 0].numpy()
        amp_pinn.append(np.sqrt(np.mean((u_pred - u_star)**2)))

# Plot Figura 1 (Dimensões otimizadas para ocupar 100% da largura do artigo)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.2), gridspec_kw={'width_ratios': [1.8, 1.0]}, dpi=300)

# Painel (a)
ax1.semilogy(epochs, loss_total, label=r'$\mathcal{L}_{\mathrm{total}}$', color='#1f77b4', lw=LINE_WIDTH_PRIMARY)
ax1.semilogy(epochs, loss_pde_u, label=r'$\mathcal{L}_{\mathrm{pde}, u}$', color='#d62728', lw=LINE_WIDTH_SEC, ls='--')
ax1.semilogy(epochs, loss_pde_v, label=r'$\mathcal{L}_{\mathrm{pde}, v}$', color='#ff7f0e', lw=LINE_WIDTH_SEC, ls=':')
ax1.semilogy(epochs, loss_ic, label=r'$\mathcal{L}_{\mathrm{ic}}$', color='#2ca02c', lw=LINE_WIDTH_SEC, ls='-.')
ax1.semilogy(epochs, loss_bc, label=r'$\mathcal{L}_{\mathrm{bc}}$', color='#9467bd', lw=LINE_WIDTH_SEC, ls='-')

ax1.set_xlabel('Épocas')
ax1.set_ylabel('MSE')
ax1.set_title('(a) Convergência de Perda', pad=6)
ax1.grid(True, which='both', ls=':', alpha=0.6)
ax1.legend(loc='upper right', framealpha=0.92, labelspacing=0.2, borderpad=0.25)

# Painel (b)
ax2.plot(eval_times, amp_adi, label='MDF ADI', color='#2ca02c', lw=LINE_WIDTH_PRIMARY)
ax2.plot(eval_times, amp_pinn, label='PINN', color='#d62728', lw=LINE_WIDTH_PRIMARY, ls='--')
ax2.axhline(0, color='black', ls=':', lw=1.0, alpha=0.6)

ax2.annotate('Crescimento\nExponencial', xy=(0.42, 0.40), xytext=(0.04, 0.62),
             arrowprops=dict(arrowstyle='->', color='#2ca02c', lw=1.6, shrinkA=3, shrinkB=4),
             fontsize=FONT_SIZE_ARROWS, ha='left', va='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9, edgecolor='none'))

ax2.annotate('Saturação\nde Spots', xy=(1.60, 0.60), xytext=(1.05, 0.38),
             arrowprops=dict(arrowstyle='->', color='#2ca02c', lw=1.6, shrinkA=3, shrinkB=4),
             fontsize=FONT_SIZE_ARROWS, ha='center', va='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9, edgecolor='none'))

ax2.annotate('Colapso\nHomogêneo', xy=(1.10, 0.002), xytext=(1.45, 0.18),
             arrowprops=dict(arrowstyle='->', color='#d62728', lw=1.6, shrinkA=3, shrinkB=4),
             fontsize=FONT_SIZE_ARROWS, ha='center', va='center',
             bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.9, edgecolor='none'))

ax2.set_xlabel('t (s)')
ax2.set_ylabel(r'$\| u(t) - u^* \|_{L_2}$')
ax2.set_title('(b) Heterogeneidade Temporal', pad=6)
ax2.set_ylim(-0.04, 0.82)
ax2.set_xlim(0, 2.0)
ax2.grid(True, ls=':', alpha=0.6)
ax2.legend(loc='upper left', framealpha=0.92, labelspacing=0.2, borderpad=0.25)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_analise_convergencia_referencia.png'))
plt.savefig(os.path.join(FIG_DIR, 'fig_analise_convergencia_referencia.pdf'))
plt.close()
print("Figura 1 gerada com sucesso!")

# ==============================================================================
# 3. FIGURA 2: CONFRONTO 2x3 MAPAS DE CONTORNO (MDF ADI vs PINN)
# ==============================================================================
print("Gerando Figura 2: fig_adi_mdf_vs_pinn_2x3...")

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

fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.4), dpi=300, sharex=True, sharey=True)

for j, t_val in enumerate(snap_times):
    vmin_t, vmax_t = snaps_gt[t_val].min(), snaps_gt[t_val].max()
    
    # Row 0: MDF ADI
    im0 = axes[0, j].imshow(snaps_gt[t_val], extent=[0, L, 0, L], origin='lower',
                            cmap='jet', interpolation='bicubic', vmin=vmin_t, vmax=vmax_t)
    axes[0, j].set_title(f't = {t_val:.2f} s', fontsize=FONT_SIZE_TITLES)
    axes[0, j].set_aspect('equal')
    if j == 0:
        axes[0, j].set_ylabel('MDF ADI (Pereira, 2019)', fontsize=FONT_SIZE_AXIS)
    cbar0 = fig.colorbar(im0, ax=axes[0, j], fraction=0.046, pad=0.04)
    cbar0.ax.tick_params(labelsize=FONT_SIZE_TICKS - 1.5)
    cbar0.set_label('u(x,y,t)', fontsize=FONT_SIZE_AXIS - 1.5)
        
    # Row 1: PINN
    im1 = axes[1, j].imshow(snaps_pinn[t_val], extent=[0, L, 0, L], origin='lower',
                            cmap='jet', interpolation='bicubic', vmin=vmin_t, vmax=vmax_t)
    axes[1, j].set_xlabel('x', fontsize=FONT_SIZE_AXIS)
    axes[1, j].set_aspect('equal')
    if j == 0:
        axes[1, j].set_ylabel('PINN (20.000 epochs)', fontsize=FONT_SIZE_AXIS)
    cbar1 = fig.colorbar(im1, ax=axes[1, j], fraction=0.046, pad=0.04)
    cbar1.ax.tick_params(labelsize=FONT_SIZE_TICKS - 1.5)
    cbar1.set_label('u(x,y,t)', fontsize=FONT_SIZE_AXIS - 1.5)

fig.suptitle('MDF ADI x PINN: Campo de Concentração do Ativador u(x,y,t)', fontsize=FONT_SIZE_TITLES, y=0.98)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'fig_adi_mdf_vs_pinn_2x3.png'))
plt.savefig(os.path.join(FIG_DIR, 'fig_adi_mdf_vs_pinn_2x3.pdf'))
plt.close()
print("Figura 2 gerada com sucesso!")
print("Todas as figuras foram geradas em alta resolução e fontes gigantes!")
