#!/home/warley/.venv/pinn-gpu/bin/python3
"""
Treinamento de PINN de Alta Resolução — Equação do Calor 2D Transiente
Parâmetros: alpha = 0.1, Omega = [0, 1]^2, t in [0, 1]
Condição Inicial: u(x, y, 0) = sin(pi*x)*sin(pi*y)
Condição de Contorno: u|_boundary = 0
Solução Analítica Exata: u*(x, y, t) = sin(pi*x)*sin(pi*y)*exp(-2*pi^2*alpha*t)
Épocas: 20.000 (log a cada 20 passos para curva de convergência de alta resolução)
Pesos de Perda: lambda_pde = 1.0, lambda_ic = 20.0, lambda_bc = 20.0
Métricas: Perda MSE, Erro Relativo L2, Erro Máximo L_inf, Latência de Inferência, Tempo por Época
Exporta: .pth, .pdf, .png de alta qualidade para submissão
"""

import os
import time
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Reprodutibilidade
torch.manual_seed(42)
np.random.seed(42)

# Configurações visuais para publicação científica
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

# Dispositivo de processamento (GPU CUDA)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if torch.cuda.is_available():
    torch.cuda.init()
    # Warmup context
    _dummy = torch.zeros(1, device=device) + 1.0
print("="*75, flush=True)
print("PINN 2D HEAT EQUATION — HIGH RESOLUTION TRAINING (20,000 EPOCHS)", flush=True)
print("="*75, flush=True)
print(f"Dispositivo de Treinamento: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})", flush=True)

# ==============================================================================
# 1. PARÂMETROS DO PROBLEMA
# ==============================================================================
alpha = 0.1
L = 1.0
T = 1.0
epochs = 20000
log_interval = 20

# Pesos da Função de Perda (Literatura PINN)
lambda_pde = 1.0
lambda_ic = 20.0
lambda_bc = 20.0

N_f = 12000   # Pontos de colocação interior
N_0 = 3000    # Pontos de condição inicial
N_b = 2400    # Pontos de fronteira

print(f"Alpha: {alpha} | Domínio: [0, {L}]^2 | Tempo: [0, {T}]")
print(f"Pesos de Perda: lambda_pde={lambda_pde}, lambda_ic={lambda_ic}, lambda_bc={lambda_bc}")
print(f"Pontos: N_f={N_f}, N_0={N_0}, N_b={N_b} | Log a cada {log_interval} épocas")

# ==============================================================================
# 2. ARQUITETURA DA REDE NEURAL (MLP com tanh)
# ==============================================================================
class HeatPINN(nn.Module):
    def __init__(self, hidden_dim=64, num_layers=4):
        super().__init__()
        layers = []
        layers.append(nn.Linear(3, hidden_dim))  # Entrada: (x, y, t)
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 1))  # Saída: u(x, y, t)
        self.net = nn.Sequential(*layers)
        
        # Inicialização Xavier
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x, y, t):
        inputs = torch.cat([x, y, t], dim=1)
        return self.net(inputs)

# ==============================================================================
# 3. SOLUÇÃO ANALÍTICA EXATA (C-Infinito Decaimento Suave)
# ==============================================================================
def exact_heat_solution(x_np, y_np, t_np):
    """
    Solução analítica exata fechada:
    u*(x, y, t) = sin(pi*x) * sin(pi*y) * exp(-2 * pi^2 * alpha * t)
    """
    return np.sin(np.pi * x_np) * np.sin(np.pi * y_np) * np.exp(-2.0 * (np.pi ** 2) * alpha * t_np)

def initial_condition_torch(x, y):
    return torch.sin(np.pi * x) * torch.sin(np.pi * y)

# ==============================================================================
# 4. AMOSTRAGEM DE DADOS DE TREINAMENTO
# ==============================================================================
# Interior (x, y in [0, 1], t in (0, 1])
x_f = (torch.rand(N_f, 1) * L).to(device)
y_f = (torch.rand(N_f, 1) * L).to(device)
t_f = (torch.rand(N_f, 1) * T).to(device)
x_f.requires_grad = True
y_f.requires_grad = True
t_f.requires_grad = True

# Condição Inicial (t = 0, u = sin(pi*x)*sin(pi*y))
x_0 = (torch.rand(N_0, 1) * L).to(device)
y_0 = (torch.rand(N_0, 1) * L).to(device)
t_0 = torch.zeros(N_0, 1).to(device)
u_0 = initial_condition_torch(x_0, y_0)

# Condição de Contorno (x=0, x=1, y=0, y=1 -> u = 0)
t_b = torch.rand(N_b, 1) * T
s_b = torch.rand(N_b, 1) * L

x_b1 = torch.zeros(N_b // 4, 1); y_b1 = s_b[:N_b // 4]               # x = 0
x_b2 = torch.full((N_b // 4, 1), L); y_b2 = s_b[N_b // 4: 2*(N_b // 4)] # x = L
x_b3 = s_b[2*(N_b // 4): 3*(N_b // 4)]; y_b3 = torch.zeros(N_b // 4, 1) # y = 0
x_b4 = s_b[3*(N_b // 4):]; y_b4 = torch.full((N_b // 4, 1), L)         # y = L

x_b = torch.cat([x_b1, x_b2, x_b3, x_b4], dim=0).to(device)
y_b = torch.cat([y_b1, y_b2, y_b3, y_b4], dim=0).to(device)
t_b = torch.cat([t_b[:N_b // 4]] * 4, dim=0).to(device)
u_b = torch.zeros_like(x_b).to(device)

# ==============================================================================
# 5. LOOP DE OTIMIZAÇÃO (20.000 ÉPOCAS)
# ==============================================================================
model = HeatPINN(hidden_dim=64, num_layers=4).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

loss_history = {'epoch': [], 'total': [], 'pde': [], 'ic': [], 'bc': []}

print(f"\nIniciando treinamento da PINN ({epochs} épocas)...", flush=True)
start_time = time.time()

for epoch in range(1, epochs + 1):
    optimizer.zero_grad()
    
    # 1. Resíduo da EDP: u_t - alpha * (u_xx + u_yy) = 0
    u = model(x_f, y_f, t_f)
    u_t = torch.autograd.grad(u, t_f, torch.ones_like(u), create_graph=True)[0]
    u_x = torch.autograd.grad(u, x_f, torch.ones_like(u), create_graph=True)[0]
    u_y = torch.autograd.grad(u, y_f, torch.ones_like(u), create_graph=True)[0]
    u_xx = torch.autograd.grad(u_x, x_f, torch.ones_like(u_x), create_graph=True)[0]
    u_yy = torch.autograd.grad(u_y, y_f, torch.ones_like(u_y), create_graph=True)[0]
    
    res_pde = u_t - alpha * (u_xx + u_yy)
    loss_pde = torch.mean(res_pde ** 2)
    
    # 2. Resíduo de Condição Inicial: u(x, y, 0) = sin(pi*x)*sin(pi*y)
    u_pred_0 = model(x_0, y_0, t_0)
    loss_ic = torch.mean((u_pred_0 - u_0) ** 2)
    
    # 3. Resíduo de Condição de Contorno: u|_boundary = 0
    u_pred_b = model(x_b, y_b, t_b)
    loss_bc = torch.mean((u_pred_b - u_b) ** 2)
    
    # Perda Total Ponderada
    total_loss = lambda_pde * loss_pde + lambda_ic * loss_ic + lambda_bc * loss_bc
    total_loss.backward()
    
    optimizer.step()
    scheduler.step()
    
    if epoch % log_interval == 0 or epoch == 1:
        loss_history['epoch'].append(epoch)
        loss_history['total'].append(total_loss.item())
        loss_history['pde'].append(loss_pde.item())
        loss_history['ic'].append(loss_ic.item())
        loss_history['bc'].append(loss_bc.item())
        
    if epoch % 500 == 0 or epoch == 1 or epoch == epochs:
        elapsed = time.time() - start_time
        curr_lr = optimizer.param_groups[0]['lr']
        print(f"[{epoch:5d}/{epochs} ({epoch/epochs*100:5.1f}%)] | Total: {total_loss.item():.5e} | PDE: {loss_pde.item():.5e} | IC: {loss_ic.item():.5e} | BC: {loss_bc.item():.5e} | lr: {curr_lr:.2e} | {elapsed:.1f}s", flush=True)

train_duration = time.time() - start_time
time_per_epoch_ms = (train_duration / epochs) * 1000.0
print(f"\nTreinamento concluído em {train_duration:.2f} s ({train_duration/60:.2f} min).")
print(f"Tempo médio por época: {time_per_epoch_ms:.2f} ms/época.")

# ==============================================================================
# 6. SALVAMENTO DO MODELO (.pth)
# ==============================================================================
models_dir = "./paper1_heat_burgers/models"
os.makedirs(models_dir, exist_ok=True)
pth_path = os.path.join(models_dir, "pinn_heat_2d_20k.pth")
torch.save({
    'epoch': epochs,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': total_loss.item(),
    'alpha': alpha,
    'train_duration': train_duration,
    'time_per_epoch_ms': time_per_epoch_ms,
    'loss_history': loss_history
}, pth_path)
print(f"[OK] Modelo salvo com sucesso em: {pth_path}")

# ==============================================================================
# 7. AVALIAÇÃO QUANTITATIVA CONTRA A SOLUÇÃO ANALÍTICA
# ==============================================================================
nx, ny = 100, 100
x_eval = np.linspace(0, L, nx)
y_eval = np.linspace(0, L, ny)
X_mesh, Y_mesh = np.meshgrid(x_eval, y_eval)

t_test = 0.5
X_flat = X_mesh.flatten()
Y_flat = Y_mesh.flatten()
T_flat = np.full_like(X_flat, t_test)

# Solução exata analítica fechada
u_exact_flat = exact_heat_solution(X_flat, Y_flat, T_flat)

# Predição neural e medição de latência
t_start_inf = time.time()
with torch.no_grad():
    x_t = torch.tensor(X_flat, dtype=torch.float32).unsqueeze(1).to(device)
    y_t = torch.tensor(Y_flat, dtype=torch.float32).unsqueeze(1).to(device)
    t_t = torch.tensor(T_flat, dtype=torch.float32).unsqueeze(1).to(device)
    u_pred_flat = model(x_t, y_t, t_t).cpu().numpy().flatten()
inf_latency_ms = (time.time() - t_start_inf) * 1000.0

# Métricas de Erro
abs_error = np.abs(u_pred_flat - u_exact_flat)
mse_err = np.mean(abs_error ** 2)
l_inf_err = np.max(abs_error)
rel_l2_err = np.linalg.norm(u_pred_flat - u_exact_flat) / np.linalg.norm(u_exact_flat)
rel_l2_pct = rel_l2_err * 100.0

print("\n" + "="*75)
print(f"RELATÓRIO DE DESEMPENHO CIENTÍFICO — CALOR 2D (t = {t_test}s)")
print("="*75)
print(f"Perda Total Final:               {total_loss.item():.5e}")
print(f"Resíduo PDE Final:               {loss_pde.item():.5e}")
print(f"Erro Médio Quadrático (MSE):    {mse_err:.5e}")
print(f"Erro Máximo (L_inf):             {l_inf_err:.5e}")
print(f"Erro Relativo L2:                {rel_l2_err:.5e} ({rel_l2_pct:.3f}%)")
print(f"Tempo de Treinamento Total:      {train_duration:.2f} s ({time_per_epoch_ms:.2f} ms/época)")
print(f"Latência de Inferência (10.000 pts): {inf_latency_ms:.2f} ms")
print("="*75)

# Linha de Tabela LaTeX formatada para o artigo:
print("\n>>> LINHA PARA A TABELA LATEX DO ARTIGO:")
print(f"Calor 2D (Analítico) & 20.000 & {total_loss.item():.2e} & {rel_l2_err:.2e} & {l_inf_err:.2e} & {inf_latency_ms:.2f}\\,ms \\\\")

# ==============================================================================
# 8. GERAÇÃO DE FIGURAS CIENTÍFICAS
# ==============================================================================
fig_dir = "./paper1_heat_burgers/figures"
os.makedirs(fig_dir, exist_ok=True)

# Figura 1: Curva de Convergência das Perdas em Alta Resolução
plt.figure(figsize=(4.8, 2.7))
epochs_arr = loss_history['epoch']
plt.semilogy(epochs_arr, loss_history['total'], label=r'Total $\mathcal{L}_{\mathrm{total}}$', color='#1f77b4', lw=1.5)
plt.semilogy(epochs_arr, loss_history['pde'], label=r'PDE $\mathcal{L}_{\mathrm{pde}}$', color='#d62728', lw=1.0, ls='--')
plt.semilogy(epochs_arr, loss_history['ic'], label=r'Inicial $\mathcal{L}_{\mathrm{ic}}$ ($\times 20$)', color='#2ca02c', lw=1.0, ls=':')
plt.semilogy(epochs_arr, loss_history['bc'], label=r'Contorno $\mathcal{L}_{\mathrm{bc}}$ ($\times 20$)', color='#9467bd', lw=1.0, ls='-.')
plt.xlabel('Época de Treinamento')
plt.ylabel('Erro Quadrático Médio (MSE)')
plt.grid(True, which='both', ls=':', alpha=0.5)
plt.legend(loc='upper right', framealpha=0.9, fontsize=7.5)
plt.title(f'Convergência da PINN — Equação do Calor 2D ({epochs} Épocas)')
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "heat_loss_convergence.pdf"))
plt.savefig(os.path.join(fig_dir, "heat_loss_convergence.png"))
plt.close()

# Figura 2: Comparação 2D Campo Exato vs Predição PINN vs Erro Absoluto
U_pred_grid = u_pred_flat.reshape(nx, ny)
U_exact_grid = u_exact_flat.reshape(nx, ny)
U_err_grid = abs_error.reshape(nx, ny)

fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.2), sharey=True)
im0 = axes[0].imshow(U_exact_grid, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0, vmax=1.0)
axes[0].set_title(r'(a) Solução Exata $u^\star$', fontsize=8.0)
axes[0].set_xlabel('$x$'); axes[0].set_ylabel('$y$')

im1 = axes[1].imshow(U_pred_grid, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0, vmax=1.0)
axes[1].set_title(r'(b) Predição PINN $u_\theta$', fontsize=8.0)
axes[1].set_xlabel('$x$')

im2 = axes[2].imshow(U_err_grid, extent=[0, L, 0, L], origin='lower', cmap='magma')
axes[2].set_title(r'(c) Erro Absoluto $|u_\theta - u^\star|$', fontsize=8.0)
axes[2].set_xlabel('$x$')

fig.colorbar(im0, ax=axes[0:2], shrink=0.8, label='Temperatura $u$')
fig.colorbar(im2, ax=axes[2], shrink=0.8, label='Erro Absoluto')
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "heat_error_comparison.pdf"))
plt.savefig(os.path.join(fig_dir, "heat_error_comparison.png"))
plt.close()

# Figura 3: Evolução de Superfícies 3D ao Longo do Tempo (t=0.0, 0.3, 0.7, 1.0)
fig = plt.figure(figsize=(7.2, 2.2))
time_snapshots = [0.0, 0.3, 0.7, 1.0]
labels = [r'(a) $t = 0{,}0$\,s', r'(b) $t = 0{,}3$\,s', r'(c) $t = 0{,}7$\,s', r'(d) $t = 1{,}0$\,s']

for i, (t_val, lbl) in enumerate(zip(time_snapshots, labels), 1):
    ax = fig.add_subplot(1, 4, i, projection='3d')
    T_snap = np.full_like(X_flat, t_val)
    with torch.no_grad():
        x_t_s = torch.tensor(X_flat, dtype=torch.float32).unsqueeze(1).to(device)
        y_t_s = torch.tensor(Y_flat, dtype=torch.float32).unsqueeze(1).to(device)
        t_t_s = torch.tensor(T_snap, dtype=torch.float32).unsqueeze(1).to(device)
        u_snap = model(x_t_s, y_t_s, t_t_s).cpu().numpy().reshape(nx, ny)
    
    surf = ax.plot_surface(X_mesh, Y_mesh, u_snap, cmap='inferno', vmin=0, vmax=1.0,
                           linewidth=0, antialiased=True, alpha=0.92)
    ax.set_title(lbl, fontsize=7.8, pad=-2)
    ax.set_zlim(0, 1.0)
    ax.set_xlabel('$x$', labelpad=-7, fontsize=7.0)
    ax.set_ylabel('$y$', labelpad=-7, fontsize=7.0)
    ax.set_zlabel('$u$', labelpad=-7, fontsize=7.0)
    ax.tick_params(labelsize=6.0, pad=-2)
    ax.view_init(elev=28, azim=-55)

plt.tight_layout(w_pad=0.2)
plt.savefig(os.path.join(fig_dir, "heat_3d_surfaces.pdf"))
plt.savefig(os.path.join(fig_dir, "heat_3d_surfaces.png"))
plt.close()

# Figura 4: Corte 1D Perfil Transversal (y = 0.5)
plt.figure(figsize=(4.8, 2.7))
y_mid_idx = ny // 2
x_line = x_eval
for t_val, col, ls in zip([0.0, 0.2, 0.5, 1.0], ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'], ['-', '--', '-.', ':']):
    T_l = np.full_like(x_line, t_val)
    u_exact_line = exact_heat_solution(x_line, 0.5, t_val)
    with torch.no_grad():
        x_t_l = torch.tensor(x_line, dtype=torch.float32).unsqueeze(1).to(device)
        y_t_l = torch.full_like(x_t_l, 0.5)
        t_t_l = torch.tensor(T_l, dtype=torch.float32).unsqueeze(1).to(device)
        u_pred_line = model(x_t_l, y_t_l, t_t_l).cpu().numpy().flatten()
    
    plt.plot(x_line, u_exact_line, color=col, ls=ls, lw=1.2, label=f'$t={t_val}$ s (Exato)')
    plt.plot(x_line, u_pred_line, color=col, marker='o', markersize=2.5, ls='none', markevery=5, label=f'$t={t_val}$ s (PINN)')

plt.xlabel('Coordenada Espacial $x$ (com $y = 0{,}5$)')
plt.ylabel('Temperatura $u(x, 0{,}5, t)$')
plt.grid(True, ls=':', alpha=0.5)
plt.legend(ncol=2, fontsize=6.8, loc='upper right')
plt.title('Perfil Transversal Térmico: Solução Exata vs PINN')
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "heat_slice_comparison.pdf"))
plt.savefig(os.path.join(fig_dir, "heat_slice_comparison.png"))
plt.close()

print(f"[OK] Figuras da Equação do Calor salvas em {fig_dir}")
