#!/usr/bin/env python3
"""
Geração de figuras científicas para o artigo PINNs (Calor e Burgers 2D):
  - Fig. 3: Calor 2D — superfícies 3D preditas pela PINN em t=0, t=0.3, t=0.7 e t=1.0
  - Fig. 4: Burgers 2D — superfícies 3D em t=0 e t=0.5 + campo/magnitude de velocidade em t=0, t=0.5 e t=1.0
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image
import os

FIGURES_DIR = "/home/warley/vault/research/eu/drafts/figures"
SRC_HEAT    = "/home/warley/development/projects/pinns/heat/2D/assets/edges_1deg_center_0deg"
SRC_BURG    = "/home/warley/development/projects/pinns/burger/2D/2blobs"

plt.rcParams.update({
    'font.family':        'serif',
    'font.serif':         ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size':          8.5,
    'axes.labelsize':     8.5,
    'axes.titlesize':     9,
    'xtick.labelsize':    7.5,
    'ytick.labelsize':    7.5,
    'figure.dpi':         300,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'savefig.pad_inches': 0.03,
})

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURA 3: Calor 2D — Superfícies 3D preditas pela PINN ao longo do tempo
# ═══════════════════════════════════════════════════════════════════════════════
heat_times  = ['0', '0_3', '0_7', '1']
heat_labels = [r'(a) $t = 0{,}0$', r'(b) $t = 0{,}3$', r'(c) $t = 0{,}7$', r'(d) $t = 1{,}0$']

fig, axes = plt.subplots(1, 4, figsize=(7.2, 1.85))
for ax, t_str, lbl in zip(axes, heat_times, heat_labels):
    p = os.path.join(SRC_HEAT, f'prediction_t_{t_str}.png')
    img = np.array(Image.open(p))
    ax.imshow(img)
    ax.axis('off')
    ax.set_title(lbl, fontsize=8.5, pad=2)

fig.suptitle(r'Equação do Calor 2D: evolução da distribuição térmica $u_\theta(x,y,t)$ predita pela PINN ($\alpha = 0{,}1$)',
             fontsize=8.5, y=1.02)
plt.tight_layout(w_pad=0.4)

out_heat = os.path.join(FIGURES_DIR, "heat_3d_surfaces.pdf")
fig.savefig(out_heat, format='pdf')
fig.savefig(os.path.join(FIGURES_DIR, "heat_3d_surfaces.png"), format='png')
plt.close(fig)
print(f"[OK] {out_heat}")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURA 4: Burgers 2D — Superfícies 3D e Campo de Velocidade
# ═══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.2, 3.4))
gs = gridspec.GridSpec(2, 3, figure=fig, height_ratios=[1.1, 1.0], hspace=0.28, wspace=0.15)

# Linha 1: 3D surfaces em t=0 e t=0.5 (ocupando 1.5 colunas cada)
ax_3d_0 = fig.add_subplot(gs[0, :])
# Dividindo a linha superior em 2 sub-plots
ax_3d_0.axis('off')

# Criação com GridSpec mais detalhado:
plt.close(fig)

fig = plt.figure(figsize=(7.2, 3.2))
gs = gridspec.GridSpec(2, 6, figure=fig, height_ratios=[1.15, 1.0], hspace=0.32, wspace=0.20)

# Linha 1: 3D surfaces (t=0 e t=0.5)
ax_3d_0  = fig.add_subplot(gs[0, 0:3])
ax_3d_05 = fig.add_subplot(gs[0, 3:6])

img_3d_0  = np.array(Image.open(os.path.join(SRC_BURG, '3d_u(x,y,0).png')))
img_3d_05 = np.array(Image.open(os.path.join(SRC_BURG, '3d_u(x,y,0.5).png')))

ax_3d_0.imshow(img_3d_0)
ax_3d_0.axis('off')
ax_3d_0.set_title(r'(a) Superfície 3D $u_\theta(x,y,0)$ ($t = 0{,}0$)', fontsize=8.2, pad=2)

ax_3d_05.imshow(img_3d_05)
ax_3d_05.axis('off')
ax_3d_05.set_title(r'(b) Superfície 3D $u_\theta(x,y,0{,}5)$ ($t = 0{,}5$)', fontsize=8.2, pad=2)

# Linha 2: Velocidade / Flow Speed em t=0, t=0.5, t=1.0
ax_fs_0  = fig.add_subplot(gs[1, 0:2])
ax_fs_5  = fig.add_subplot(gs[1, 2:4])
ax_fs_10 = fig.add_subplot(gs[1, 4:6])

img_fs_0  = np.array(Image.open(os.path.join(SRC_BURG, 'flow_speedt0.png')))
img_fs_5  = np.array(Image.open(os.path.join(SRC_BURG, 'flow_speedt5.png')))
img_fs_10 = np.array(Image.open(os.path.join(SRC_BURG, 'flow_speedt10.png')))

ax_fs_0.imshow(img_fs_0)
ax_fs_0.axis('off')
ax_fs_0.set_title(r'(c) $\|\mathbf{u}\|$ ($t = 0{,}0$)', fontsize=8.0, pad=2)

ax_fs_5.imshow(img_fs_5)
ax_fs_5.axis('off')
ax_fs_5.set_title(r'(d) $\|\mathbf{u}\|$ ($t = 0{,}5$)', fontsize=8.0, pad=2)

ax_fs_10.imshow(img_fs_10)
ax_fs_10.axis('off')
ax_fs_10.set_title(r'(e) $\|\mathbf{u}\|$ ($t = 1{,}0$)', fontsize=8.0, pad=2)

fig.suptitle(r'Eq. de Burgers 2D: dissipação do dipolo — (a,b) superfícies $u_\theta$ e (c--e) magnitude da velocidade $\|\mathbf{u}\|$',
             fontsize=8.5, y=1.01)

out_burg = os.path.join(FIGURES_DIR, "burgers_combined.pdf")
fig.savefig(out_burg, format='pdf')
fig.savefig(os.path.join(FIGURES_DIR, "burgers_combined.png"), format='png')
plt.close(fig)
print(f"[OK] {out_burg}")

print("\nFiguras geradas com sucesso.")

