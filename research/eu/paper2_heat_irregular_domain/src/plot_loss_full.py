import os
import torch
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'serif', 'font.size': 9})

checkpoint = torch.load("./paper2_heat_irregular_domain/models/safe_checkpoint_preview.pth", map_location='cpu', weights_only=False)
history = checkpoint['loss_history']

# Pula de 4 em 4 (25 * 4 = 100 épocas)
ep_100 = history['epoch'][::4]
tot_100 = history['total'][::4]
pde_100 = history['pde'][::4]
holes_100 = history['bc_holes'][::4]
ext_100 = history['bc_ext'][::4]
ic_100 = history['ic'][::4]

plt.figure(figsize=(6.5, 4.0), dpi=300)
plt.semilogy(ep_100, tot_100, label='Loss Total', lw=1.0, color='#1f77b4', ls='-')
plt.semilogy(ep_100, pde_100, label='EDP (Física)', lw=0.7, color='#d62728', ls='-')
plt.semilogy(ep_100, holes_100, label='Furos (u=0)', lw=0.7, color='#2ca02c', ls='-')
plt.semilogy(ep_100, ext_100, label='Borda Ext (u=1)', lw=0.7, color='#9467bd', ls='-')
plt.semilogy(ep_100, ic_100, label='Cond. Inicial (t=0)', lw=0.7, color='#ff7f0e', ls='-')

plt.grid(True, ls=':', alpha=0.6)
plt.legend(loc='upper right', fontsize=8)
plt.xlabel("Épocas")
plt.ylabel("MSE Loss")
plt.title(f"Decomposição Completa das Perdas (Até Época {checkpoint['epoch']})")
plt.savefig("./paper2_heat_irregular_domain/figures/preview_Loss_Completo.png", bbox_inches='tight')
plt.close()

print("Gráfico de perdas completo gerado!")
