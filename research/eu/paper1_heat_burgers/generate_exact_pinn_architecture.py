#!/usr/bin/env python3
"""
Reconstrói o diagrama da arquitetura PINN fielmente ao screenshot-2026-09-20_11-06-31.png.
Estrutura:
  - 4 seções verticais divididas por linhas tracejadas: Input | Hidden layer | Output | Loss
  - Nós com cores pastéis harmoniosas:
      * Input: Laranja / pêssego (x, y, t)
      * Hidden 1 e 2: Cinza com 'θ'
      * Hidden 3 (feature map): Rosa com h_1, h_2, ..., h_k
      * Output: Verde com u, v
      * Loss components: Caixas arredondadas (PDE loss, BC loss, IC loss)
      * Final Loss: Círculo 'loss' (ou L_total)
  - Barra inferior de fluxo com caixas e setas grossas: Input -> Hidden layer -> Output -> Loss
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle

plt.rcParams.update({
    'font.family':        'serif',
    'font.serif':         ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size':          10,
    'mathtext.fontset':   'stix',
    'figure.dpi':         300,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
})

fig = plt.figure(figsize=(7.5, 4.3), facecolor='white')
ax = fig.add_subplot(111)
ax.set_xlim(-0.3, 10.3)
ax.set_ylim(-1.5, 5.8)
ax.axis('off')

# ─── Cores exatas do screenshot ──────────────────────────────────────────────
C_IN_BG      = '#fed7aa'  # Pêssego / Laranja claro
C_IN_BORDER  = '#334155'  # Contorno escuro

C_THETA_BG   = '#e2e8f0'  # Cinza claro
C_THETA_BORDER = '#334155'

C_H_BG       = '#fce7f3'  # Rosa pastel
C_H_BORDER   = '#334155'

C_OUT_BG     = '#dcfce7'  # Verde claro
C_OUT_BORDER = '#334155'

C_LOSS_BG    = '#e2b0b0'  # Rosa queimado / Salmão
C_LOSS_BORDER = '#334155'

EDGE_COLOR   = '#334155'  # Linhas de conexão cinza escuro

# ─── Posições das Colunas no Plano X ─────────────────────────────────────────
x_input  = 0.6
x_hid1   = 2.0
x_hid2   = 3.1
x_hid3   = 4.4
x_out    = 5.7
x_loss_b = 7.4
x_loss_f = 9.4

node_r = 0.26

# Linhas tracejadas de divisão vertical
dash_x = [1.2, 5.0, 6.5]
for dx in dash_x:
    ax.plot([dx, dx], [-1.3, 5.6], color='black', lw=1.2, ls=(0, (6, 6)), zorder=0)

# ─── Posições Y dos Nós ──────────────────────────────────────────────────────
# 1. Inputs: x, y, t (3 nós)
y_in = [4.2, 2.7, 1.2]
lbl_in = [r'$x$', r'$y$', r'$t$']

# 2. Hidden 1 & 2 (5 nós cada com θ)
y_h12 = [5.0, 3.85, 2.7, 1.55, 0.4]

# 3. Hidden 3 (3 nós: h1, h2, hk)
y_h3 = [3.9, 2.7, 1.5]
lbl_h3 = [r'$h_1$', r'$h_2$', r'$h_k$']

# 4. Output (2 nós: u, v)
y_out = [3.3, 2.1]
lbl_out = [r'$u$', r'$v$']

# 5. Loss Boxes (PDE loss, BC loss, IC loss)
y_loss_b = [4.2, 2.7, 1.2]
lbl_loss_b = ['PDE loss', 'BC loss', 'IC loss']

# 6. Final Loss Circle
y_loss_f = [2.7]

# ─── 1. Desenhar Conexões / Arestas ──────────────────────────────────────────
# Input -> Hid 1 (com setas sutis)
for y1 in y_in:
    for y2 in y_h12:
        ax.annotate('', xy=(x_hid1 - node_r, y2), xytext=(x_input + node_r, y1),
                    arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.7, shrinkA=0, shrinkB=0, mutation_scale=6))

# Hid 1 -> Hid 2 (com setas sutis)
for y1 in y_h12:
    for y2 in y_h12:
        ax.annotate('', xy=(x_hid2 - node_r, y2), xytext=(x_hid1 + node_r, y1),
                    arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.7, shrinkA=0, shrinkB=0, mutation_scale=6))

# Hid 2 -> Hid 3 (com setas sutis)
for y1 in y_h12:
    for y2 in y_h3:
        ax.annotate('', xy=(x_hid3 - node_r, y2), xytext=(x_hid2 + node_r, y1),
                    arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.7, shrinkA=0, shrinkB=0, mutation_scale=6))

# Hid 3 -> Output (linhas completas)
for y1 in y_h3:
    for y2 in y_out:
        ax.annotate('', xy=(x_out - node_r, y2), xytext=(x_hid3 + node_r, y1),
                    arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.7, shrinkA=0, shrinkB=0, mutation_scale=6))

# Output -> Loss Boxes
# u conecta a PDE e BC
ax.annotate('', xy=(x_loss_b - 0.75, y_loss_b[0]), xytext=(x_out + node_r, y_out[0]),
            arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))
ax.annotate('', xy=(x_loss_b - 0.75, y_loss_b[1]), xytext=(x_out + node_r, y_out[0]),
            arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))
ax.annotate('', xy=(x_loss_b - 0.75, y_loss_b[2]), xytext=(x_out + node_r, y_out[0]),
            arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))

# v conecta a PDE, BC e IC
ax.annotate('', xy=(x_loss_b - 0.75, y_loss_b[0]), xytext=(x_out + node_r, y_out[1]),
            arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))
ax.annotate('', xy=(x_loss_b - 0.75, y_loss_b[1]), xytext=(x_out + node_r, y_out[1]),
            arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))
ax.annotate('', xy=(x_loss_b - 0.75, y_loss_b[2]), xytext=(x_out + node_r, y_out[1]),
            arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))

# Loss Boxes -> Final Loss Circle
for yb in y_loss_b:
    ax.annotate('', xy=(x_loss_f - 0.38, y_loss_f[0]), xytext=(x_loss_b + 0.75, yb),
                arrowprops=dict(arrowstyle="-|>", color=EDGE_COLOR, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))

# ─── 2. Desenhar os Nós Circulares ───────────────────────────────────────────
def draw_circle_node(x, y, r, bg, border, text, txt_size=10.5, is_italic=True, is_bold=False):
    circ = Circle((x, y), r, facecolor=bg, edgecolor=border, lw=1.1, zorder=3)
    ax.add_patch(circ)
    if text:
        ax.text(x, y, text, ha='center', va='center', fontsize=txt_size,
                fontstyle='italic' if is_italic else 'normal',
                fontweight='bold' if is_bold else 'normal',
                zorder=4, color='#0f172a')

# Inputs (x, y, t)
for y, lbl in zip(y_in, lbl_in):
    draw_circle_node(x_input, y, node_r, C_IN_BG, C_IN_BORDER, lbl, txt_size=11)

# Hidden 1 & 2 (θ)
for y in y_h12:
    draw_circle_node(x_hid1, y, node_r, C_THETA_BG, C_THETA_BORDER, r'$\theta$', txt_size=10.5)
    draw_circle_node(x_hid2, y, node_r, C_THETA_BG, C_THETA_BORDER, r'$\theta$', txt_size=10.5)

# Hidden 3 (h1, h2, hk)
for y, lbl in zip(y_h3, lbl_h3):
    draw_circle_node(x_hid3, y, node_r + 0.02, C_H_BG, C_H_BORDER, lbl, txt_size=10)

# Output (u, v)
for y, lbl in zip(y_out, lbl_out):
    draw_circle_node(x_out, y, node_r + 0.02, C_OUT_BG, C_OUT_BORDER, lbl, txt_size=11)

# ─── 3. Desenhar Caixas de Perda (PDE loss, BC loss, IC loss) ────────────────
for y, lbl in zip(y_loss_b, lbl_loss_b):
    box = FancyBboxPatch((x_loss_b - 0.72, y - 0.22), 1.44, 0.44,
                         boxstyle="round,pad=0.04,rounding_size=0.08",
                         facecolor=C_LOSS_BG, edgecolor=C_LOSS_BORDER, lw=1.1, zorder=3)
    ax.add_patch(box)
    ax.text(x_loss_b, y, lbl, ha='center', va='center', fontsize=9.2, fontweight='bold',
            color='#0f172a', zorder=4)

# Final Loss Circle ('loss')
draw_circle_node(x_loss_f, y_loss_f[0], 0.38, C_LOSS_BG, C_LOSS_BORDER, 'loss', txt_size=10, is_italic=False, is_bold=True)

# ─── 4. Barra de Fluxo Inferior (Pipeline) ───────────────────────────────────
# Input box
box_in = FancyBboxPatch((0.15, -1.0), 0.9, 0.42,
                        boxstyle="round,pad=0.04,rounding_size=0.08",
                        facecolor=C_IN_BG, edgecolor=C_IN_BORDER, lw=1.1, zorder=3)
ax.add_patch(box_in)
ax.text(0.6, -0.79, 'Input', ha='center', va='center', fontsize=9.2, fontweight='bold', color='#0f172a', zorder=4)

# Seta 1
ax.annotate('', xy=(1.7, -0.79), xytext=(1.1, -0.79),
            arrowprops=dict(arrowstyle="-|>", color='#1e293b', lw=2.4, mutation_scale=12))

# Hidden layer box
box_hid = FancyBboxPatch((1.75, -1.0), 3.0, 0.42,
                         boxstyle="round,pad=0.04,rounding_size=0.08",
                         facecolor=C_THETA_BG, edgecolor=C_THETA_BORDER, lw=1.1, zorder=3)
ax.add_patch(box_hid)
ax.text(3.25, -0.79, 'Hidden layer', ha='center', va='center', fontsize=9.2, fontweight='bold', color='#0f172a', zorder=4)

# Seta 2
ax.annotate('', xy=(5.2, -0.79), xytext=(4.8, -0.79),
            arrowprops=dict(arrowstyle="-|>", color='#1e293b', lw=2.4, mutation_scale=12))

# Output box
box_out = FancyBboxPatch((5.25, -1.0), 0.9, 0.42,
                         boxstyle="round,pad=0.04,rounding_size=0.08",
                         facecolor=C_OUT_BG, edgecolor=C_OUT_BORDER, lw=1.1, zorder=3)
ax.add_patch(box_out)
ax.text(5.7, -0.79, 'Output', ha='center', va='center', fontsize=9.2, fontweight='bold', color='#0f172a', zorder=4)

# Seta 3
ax.annotate('', xy=(6.9, -0.79), xytext=(6.2, -0.79),
            arrowprops=dict(arrowstyle="-|>", color='#1e293b', lw=2.4, mutation_scale=12))

# Loss box
box_loss = FancyBboxPatch((6.95, -1.0), 2.2, 0.42,
                          boxstyle="round,pad=0.04,rounding_size=0.08",
                          facecolor=C_LOSS_BG, edgecolor=C_LOSS_BORDER, lw=1.1, zorder=3)
ax.add_patch(box_loss)
ax.text(8.05, -0.79, 'Loss', ha='center', va='center', fontsize=9.2, fontweight='bold', color='#0f172a', zorder=4)

plt.tight_layout()

# Salvar
ROOT = "/home/warley/vault/research/eu/paper1_heat_burgers"
out_pdf = os.path.join(ROOT, "figures", "pinn_architecture.pdf")
out_png = os.path.join(ROOT, "figures", "pinn_architecture.png")
fig.savefig(out_pdf, dpi=300, bbox_inches='tight')
fig.savefig(out_png, dpi=300, bbox_inches='tight')
print(f"[OK] Diagrama PINN reconstruído fielmente em:\n  {out_pdf}\n  {out_png}")
plt.close(fig)
