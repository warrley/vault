import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 10.5,
    'axes.titlesize': 11.0,
    'xtick.labelsize': 9.0,
    'ytick.labelsize': 9.0,
    'legend.fontsize': 9.0,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'cm'
})

fig_dir = "./paper2_heat_irregular_domain/figures"
os.makedirs(fig_dir, exist_ok=True)

# Coordenadas do furo 1
hx, hy, hr = 0.30, 0.30, 0.12

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.2), dpi=300)

# (a) MDF: Malha Cartesiana e Escadeamento
nx_grid = 20
gx = np.linspace(0.14, 0.46, nx_grid)
gy = np.linspace(0.14, 0.46, nx_grid)

for x_val in gx:
    ax1.axvline(x_val, color='lightgray', lw=0.6, alpha=0.8)
for y_val in gy:
    ax1.axhline(y_val, color='lightgray', lw=0.6, alpha=0.8)

# Preencher células escalonadas que caem dentro do furo
dx = gx[1] - gx[0]
dy = gy[1] - gy[0]
for i in range(nx_grid - 1):
    for j in range(nx_grid - 1):
        cx = (gx[i] + gx[i+1]) / 2.0
        cy = (gy[j] + gy[j+1]) / 2.0
        if (cx - hx)**2 + (cy - hy)**2 <= hr**2:
            rect = patches.Rectangle((gx[i], gy[j]), dx, dy, color='#ffaaaa', alpha=0.85)
            ax1.add_patch(rect)

# Desenhar contorno suave teórico por cima
circle_true = plt.Circle((hx, hy), hr, color='darkred', fill=False, lw=1.8, ls='--', label='Contorno Analítico $\\partial\\mathcal{H}_k$')
ax1.add_patch(circle_true)

ax1.set_title('(a) MDF: Degraus e Erro de Escadeamento $\\mathcal{O}(\\Delta x)$', fontsize=10.0, pad=6)
ax1.set_xlabel('$x$ [m]')
ax1.set_ylabel('$y$ [m]')
ax1.set_xlim(0.14, 0.46)
ax1.set_ylim(0.14, 0.46)
ax1.set_aspect('equal')
ax1.legend(loc='upper right', framealpha=0.9, fontsize=8.2)

# (b) PINN: Colocação Contínua Meshless
theta_pts = np.linspace(0, 2*np.pi, 36, endpoint=False)
x_rim = hx + hr * np.cos(theta_pts)
y_rim = hy + hr * np.sin(theta_pts)

np.random.seed(42)
r_int = np.random.uniform(hr, hr + 0.14, 110)
th_int = np.random.uniform(0, 2*np.pi, 110)
xi = hx + r_int * np.cos(th_int)
yi = hy + r_int * np.sin(th_int)

ax2.scatter(xi, yi, s=14, color='#1f77b4', alpha=0.7, label='Colocação Interior $N_f$')
ax2.scatter(x_rim, y_rim, s=24, color='#d62728', zorder=5, label='Colocação Polar Exata $N_{\\mathrm{furos}}$')
circle_exact = plt.Circle((hx, hy), hr, color='black', fill=False, lw=1.5, ls='-')
ax2.add_patch(circle_exact)

ax2.set_title('(b) PINN: Amostragem Analítica Livre de Malha', fontsize=10.0, pad=6)
ax2.set_xlabel('$x$ [m]')
ax2.set_ylabel('$y$ [m]')
ax2.set_xlim(0.14, 0.46)
ax2.set_ylim(0.14, 0.46)
ax2.set_aspect('equal')
ax2.legend(loc='upper right', framealpha=0.9, fontsize=8.2)

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig1_geometry_staircasing.pdf"))
plt.savefig(os.path.join(fig_dir, "fig1_geometry_staircasing.png"))
plt.close()
print("[OK] Figura 1 geométrica atualizada com sucesso!")
