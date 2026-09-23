import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Styling from GUIA_MESTRE_CRIACAO_ARTIGOS.md
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size': 8.5,
    'axes.labelsize': 8.5,
    'axes.titlesize': 9.0,
    'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'stix'
})

fig_dir = './paper3.1_turing_time_causality/figures'
os.makedirs(fig_dir, exist_ok=True)

# ==============================================================================
# FIGURE 1: CAUSALITY BREAKDOWN & CONFLICTING GRADIENTS SCHEMATIC
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.5), dpi=300)

# Panel A: Physical Causal Time Marching (ADI / Classical Solvers)
t_pts = np.linspace(0, 2.0, 100)
# Growth followed by saturation
growth = 0.01 * np.exp(3.5 * t_pts)
pattern_amp = np.where(t_pts < 1.0, growth, 0.45 * (1.0 - np.exp(-2.0 * (t_pts - 0.7))))
ax1.plot(t_pts, pattern_amp, color='#2ca02c', lw=2.0, label='Evolução Causal Real (ADI)')
ax1.axhline(0, color='black', lw=0.8, ls=':')
ax1.annotate('Perturbação Inicial\n$\\epsilon(x) \\sim 10^{-3}$ ($t=0$)', xy=(0.05, 0.02), xytext=(0.15, 0.20),
             arrowprops=dict(arrowstyle="->", color='#2ca02c', lw=1.2), fontsize=7.0)
ax1.annotate('Crescimento Exponencial\n$\\propto e^{\\lambda t}$ (Modos Instáveis)', xy=(0.8, 0.25), xytext=(0.35, 0.38),
             arrowprops=dict(arrowstyle="->", color='#2ca02c', lw=1.2), fontsize=7.0)
ax1.annotate('Padrão Estável de Spots\n(Saturação Cúbica)', xy=(1.8, 0.45), xytext=(1.1, 0.25),
             arrowprops=dict(arrowstyle="->", color='#2ca02c', lw=1.2), fontsize=7.0)
ax1.set_title('(a) Dinâmica Causal Física (Marcha no Tempo)', fontsize=8.5)
ax1.set_xlabel('Tempo $t$ (s)')
ax1.set_ylabel('Amplitude da Heterogeneidade $\\|u - u^*\\|$')
ax1.set_ylim(-0.05, 0.55)
ax1.grid(True, ls=':', alpha=0.6)

# Panel B: Space-Time PINN Gradient Conflict & Quenching
pinn_pred = np.full_like(t_pts, 0.005)
ax2.plot(t_pts, pinn_pred, color='#d62728', lw=2.0, ls='--', label='Predição PINN Vanilla')
ax2.axhline(0, color='black', lw=0.8, ls=':')
# Draw gradient conflict arrows
ax2.annotate('', xy=(0.1, 0.02), xytext=(1.8, 0.02),
             arrowprops=dict(arrowstyle="<->", color='#1f77b4', lw=1.5, ls='-'))
ax2.text(0.95, 0.08, 'Conflito Global de Gradientes\n(Otimização Simultânea em $[0, T]$)',
         ha='center', fontsize=7.0, color='#1f77b4', fontweight='bold')
ax2.annotate('Resíduos em $t=2$ forçam campo plano\n($\\nabla^2 u \\to 0, \\mathcal{R}_{\\mathrm{pde}} = 0$)',
             xy=(1.6, 0.01), xytext=(0.9, 0.35),
             arrowprops=dict(arrowstyle="->", color='#d62728', lw=1.2), fontsize=7.0)
ax2.annotate('Gradientes futuros aniquilam\no crescimento em $t=0$',
             xy=(0.2, 0.01), xytext=(0.05, 0.25),
             arrowprops=dict(arrowstyle="->", color='#d62728', lw=1.2), fontsize=7.0)
ax2.set_title('(b) Quebra da Causalidade em PINNs (Atrator Trivial)', fontsize=8.5)
ax2.set_xlabel('Tempo $t$ (s)')
ax2.set_ylabel('Amplitude $\\|u - u^*\\|$')
ax2.set_ylim(-0.05, 0.55)
ax2.grid(True, ls=':', alpha=0.6)

plt.tight_layout()
plt.savefig(f"{fig_dir}/fig_causality_mechanism.pdf")
plt.savefig(f"{fig_dir}/fig_causality_mechanism.png")
plt.close()
print("Generated Figure 1: Causality mechanism.")

# ==============================================================================
# FIGURE 2: DISPERSION RELATION & SPECTRAL BIAS ATTENUATION
# ==============================================================================
k_sq = np.linspace(0, 450, 300)
# Turing dispersion curve h(k^2) for Schnakenberg (Pereira 2019 parameters)
# a=0.1305, b=0.7695, kappa=100, D1=0.05, D2=1.0, u*=0.9, v*=0.95
# fu = (b-a)/(a+b) = 0.639/0.9 = 0.71; fv = 0.81
# gu = -2*0.7695/0.9 = -1.71; gv = -0.81
D1 = 0.05
D2 = 1.0
kappa = 100.0
fu = 0.71
fv = 0.81
gu = -1.71
gv = -0.81
det_J = fu*gv - fv*gu  # 0.81
tr_J = fu + gv         # -0.10

# Growth rate lambda(k^2) = 0.5 * (kappa*tr_J - k^2(D1+D2) + sqrt((kappa*tr_J - k^2(D1+D2))^2 - 4*det_J_k))
tr_Jk = kappa * tr_J - k_sq * (D1 + D2)
det_Jk = D1 * D2 * (k_sq**2) - kappa * (D2 * fu + D1 * gv) * k_sq + (kappa**2) * det_J
disc = tr_Jk**2 - 4 * det_Jk
disc = np.maximum(disc, 0)
lambda_k = 0.5 * (tr_Jk + np.sqrt(disc))

fig, ax = plt.subplots(figsize=(5.2, 2.4), dpi=300)
ax.plot(k_sq, lambda_k, color='#1f77b4', lw=2.0, label='Taxa de Crescimento Físico $\\mathrm{Re}(\\lambda(k^2))$')
ax.axhline(0, color='black', lw=0.8, ls='--')
# Highlight unstable band
unstable_mask = lambda_k > 0
if np.any(unstable_mask):
    k_unstable = k_sq[unstable_mask]
    ax.fill_between(k_unstable, 0, lambda_k[unstable_mask], color='#1f77b4', alpha=0.25, label='Faixa Instável de Turing $[k_1^2, k_2^2]$')
    k_crit_sq = k_unstable[np.argmax(lambda_k[unstable_mask])]
    ax.scatter([k_crit_sq], [np.max(lambda_k)], color='#d62728', s=40, zorder=5, label=f'Modo Crítico $k_c^2 \\approx {k_crit_sq:.0f}$')

# Spectral bias filter curve of standard MLP (eigenvalue decay lambda_NTK ~ 1 / k^2)
mlp_filter = 15.0 / (1.0 + 0.03 * k_sq)
ax.plot(k_sq, mlp_filter, color='#ff7f0e', lw=1.5, ls=':', label='Viés Espectral da MLP (Filtro Passa-Baixas)')

ax.set_title('Relação de Dispersão de Turing vs. Viés Espectral de Redes Neurais', fontsize=8.5)
ax.set_xlabel('Quadrado do Número de Onda Espacial $k^2$')
ax.set_ylabel('Taxa de Crescimento $\\lambda$')
ax.set_xlim(0, 400)
ax.set_ylim(-15, 20)
ax.grid(True, ls=':', alpha=0.6)
ax.legend(loc='upper right', framealpha=0.9, fontsize=7.0)

plt.tight_layout()
plt.savefig(f"{fig_dir}/fig_stiffness_dispersion.pdf")
plt.savefig(f"{fig_dir}/fig_stiffness_dispersion.png")
plt.close()
print("Generated Figure 2: Dispersion & Spectral Bias.")

print("All new figures generated successfully!")
