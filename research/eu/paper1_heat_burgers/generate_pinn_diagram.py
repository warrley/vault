#!/usr/bin/env python3
"""
Reconstrói o diagrama da arquitetura PINN com base no screenshot do usuário,
adaptado com precisão vetorial e rigor estético para publicação no Paper 1 (Calor e Burgers 2D).
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

fig = plt.figure(figsize=(7.2, 3.2), facecolor='white')
ax = fig.add_subplot(111)
ax.set_xlim(-0.8, 8.8)
ax.set_ylim(-0.4, 5.4)
ax.axis('off')

# ─── Posições das Colunas / Camadas ──────────────────────────────────────────
# x-coords:
# 0.2: Inputs (x, y, t)
# 1.8: Hidden 1
# 3.2: Hidden 2
# 4.6: Hidden 3 / Output MLP (u, v)
# 6.4: Operadores Diferenciais Autograd (I, ∂/∂t, ∂/∂x, ∇², etc.)
# 8.2: Perdas Físicas (L_pde, L_ic, L_bc)

# Cores fiéis ao screenshot do usuário:
C_INPUT  = '#3b75af'   # Azul puro
C_HIDDEN = '#6b3ba6'   # Roxo / Violeta
C_OUTPUT = '#b83232'   # Vermelho
C_OP     = '#553c9a'   # Roxo escuro / Autograd
C_LOSS   = '#d97706'   # Dourado / Ambar para a perda

# Definição das posições Y para cada coluna
# 1. Entrada (3 nós: x, y, t)
y_in = [3.8, 2.5, 1.2]
lbl_in = [r'$x$', r'$y$', r'$t$']

# 2. Oculta 1 (5 nós)
y_h1 = [4.7, 3.6, 2.5, 1.4, 0.3]

# 3. Oculta 2 (5 nós)
y_h2 = [4.7, 3.6, 2.5, 1.4, 0.3]

# 4. Saída da Rede Neural (2 nós principais: u, v)
y_out = [3.2, 1.8]
lbl_out = [r'$u$', r'$v$']

# 5. Operadores Autograd (5 nós: Identidade, |·|, ∂/∂t, ∂/∂x, ∇²)
y_ops = [4.7, 3.6, 2.5, 1.4, 0.3]
lbl_ops = [r'$I$', r'$|\cdot|$', r'$\partial / \partial t$', r'$\partial / \partial x$', r'$\nabla^2$']

# 6. Perda Multiobjetivo (3 nós: L_pde, L_ic, L_bc)
y_loss = [3.6, 2.5, 1.4]
lbl_loss = [r'$\mathcal{L}_{\mathrm{pde}}$', r'$\mathcal{L}_{\mathrm{ic}}$', r'$\mathcal{L}_{\mathrm{bc}}$']

x_cols = [0.4, 1.9, 3.3, 4.7, 6.4, 8.0]
node_r = 0.22

# ─── 1. Desenhar Conexões (Linhas / Arestas) ─────────────────────────────────
line_color = '#d1d5db'
line_alpha = 0.75
line_lw = 0.9

# In -> H1
for y1 in y_in:
    for y2 in y_h1:
        ax.plot([x_cols[0], x_cols[1]], [y1, y2], color=line_color, lw=line_lw, alpha=line_alpha, zorder=1)

# H1 -> H2
for y1 in y_h1:
    for y2 in y_h2:
        ax.plot([x_cols[1], x_cols[2]], [y1, y2], color=line_color, lw=line_lw, alpha=line_alpha, zorder=1)

# H2 -> Out
for y1 in y_h2:
    for y2 in y_out:
        ax.plot([x_cols[2], x_cols[3]], [y1, y2], color=line_color, lw=line_lw, alpha=line_alpha, zorder=1)

# Out -> Ops (Autograd Graph)
for y1 in y_out:
    for y2 in y_ops:
        ax.plot([x_cols[3], x_cols[4]], [y1, y2], color='#94a3b8', lw=1.1, alpha=0.85, zorder=1)

# Ops -> Loss
for y1 in y_ops:
    for y2 in y_loss:
        ax.plot([x_cols[4], x_cols[5]], [y1, y2], color='#cbd5e1', lw=0.9, alpha=0.7, zorder=1)

# ─── 2. Desenhar os Nós (Círculos com borda) ─────────────────────────────────
def draw_nodes(x, y_list, color, border_color='white', border_lw=1.6):
    for y in y_list:
        # Sombra sutil / contorno
        circ_border = Circle((x, y), node_r + 0.025, color='#64748b', alpha=0.25, zorder=2)
        ax.add_patch(circ_border)
        circ = Circle((x, y), node_r, facecolor=color, edgecolor=border_color, lw=border_lw, zorder=3)
        ax.add_patch(circ)

# Inputs
draw_nodes(x_cols[0], y_in, C_INPUT)
# Hidden 1 & 2
draw_nodes(x_cols[1], y_h1, C_HIDDEN)
draw_nodes(x_cols[2], y_h2, C_HIDDEN)
# Output (u, v)
draw_nodes(x_cols[3], y_out, C_OUTPUT)
# Autograd Ops
draw_nodes(x_cols[4], y_ops, C_OP)
# Loss Nodes
draw_nodes(x_cols[5], y_loss, C_LOSS)

# ─── 3. Textos e Rótulos ─────────────────────────────────────────────────────
# Labels à esquerda dos inputs
for y, lbl in zip(y_in, lbl_in):
    ax.text(x_cols[0] - 0.45, y, lbl, fontsize=13, va='center', ha='center', color='#1e3a8a', fontweight='bold')

# Labels à direita dos outputs (u, v)
for y, lbl in zip(y_out, lbl_out):
    ax.text(x_cols[3] + 0.45, y, lbl, fontsize=13, va='center', ha='center', color='#7f1d1d', fontweight='bold')

# Labels à direita dos operadores Autograd
for y, lbl in zip(y_ops, lbl_ops):
    ax.text(x_cols[4] + 0.45, y, lbl, fontsize=11, va='center', ha='left', color='#3b0764')

# Labels à direita dos nós de Loss
for y, lbl in zip(y_loss, lbl_loss):
    ax.text(x_cols[5] + 0.45, y, lbl, fontsize=11.5, va='center', ha='left', color='#9a3412', fontweight='bold')

# ─── 4. Cabeçalhos e Caixas de Identificação dos Blocos ──────────────────────
# Caixa destacada para Autograd
bbox_props = dict(boxstyle="round,pad=0.25", fc="#f8fafc", ec="#cbd5e1", lw=0.8)
ax.text((x_cols[0]+x_cols[3])/2, 5.15, r'\textbf{Rede Neural Profunda (MLP $4\times 64$, $\tanh$)}',
        ha='center', va='center', fontsize=9.2, color='#1e293b', bbox=bbox_props)

bbox_ops = dict(boxstyle="round,pad=0.25", fc="#fdf4ff", ec="#e879f9", lw=0.8)
ax.text(x_cols[4] + 0.35, 5.15, r'\textbf{Autograd (VJP)}',
        ha='center', va='center', fontsize=9.2, color='#581c87', bbox=bbox_ops)

bbox_loss = dict(boxstyle="round,pad=0.25", fc="#fffbeb", ec="#fde68a", lw=0.8)
ax.text(x_cols[5] + 0.35, 5.15, r'\textbf{Perda $\mathcal{L}(\theta)$}',
        ha='center', va='center', fontsize=9.2, color='#92400e', bbox=bbox_loss)

# Seta indicativa de Retropropagação (Backpropagation)
ax.annotate('', xy=(x_cols[0], -0.15), xytext=(x_cols[5] + 0.2, -0.15),
            arrowprops=dict(arrowstyle="->", color="#c2410c", lw=1.6, ls='--',
                            shrinkA=5, shrinkB=5))
ax.text((x_cols[0] + x_cols[5])/2, -0.32,
        r'\textbf{Retropropagação de Gradientes (\textit{Backpropagation}) $\nabla_\theta \mathcal{L}(\theta)$ para o Otimizador Adam}',
        ha='center', va='center', fontsize=8.2, color='#9a3412')

plt.tight_layout()

# Salvar em alta resolução
ROOT = "/home/warley/vault/research/eu/paper1_heat_burgers"
out_pdf = os.path.join(ROOT, "figures", "pinn_architecture.pdf")
out_png = os.path.join(ROOT, "figures", "pinn_architecture.png")
fig.savefig(out_pdf, dpi=300, bbox_inches='tight')
fig.savefig(out_png, dpi=300, bbox_inches='tight')
print(f"[OK] Diagrama vetorial PINN gerado com sucesso em:\n  {out_pdf}\n  {out_png}")
plt.close(fig)
