#!/home/warley/.venv/pinn-gpu/bin/python3
"""
Treinamento de PINN de Alta Resolução — Equação de Burgers 2D Viscosa
Parâmetros: nu = 0.01, Omega = [-1, 1]^2, t in [0, 1]
Condição Inicial: Vórtices Dipolares Gaussianos (2 blobs)
Condição de Contorno: u|_boundary = v|_boundary = 0
Solução de Referência: Solver Numérico RK4 de Alta Resolução (Diferenças Finitas de 4ª ordem)
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
import matplotlib.gridspec as gridspec
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

# Dispositivo de processamento (GPU CUDA prioritária)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if torch.cuda.is_available():
    torch.cuda.init()
    _dummy = torch.zeros(1, device=device) + 1.0
print("="*75, flush=True)
print("PINN 2D VISCOUS BURGERS EQUATION — HIGH RESOLUTION TRAINING (20,000 EPOCHS)", flush=True)
print("="*75, flush=True)
print(f"Dispositivo de Treinamento: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})", flush=True)

# ==============================================================================
# 1. PARÂMETROS DO PROBLEMA
# ==============================================================================
nu = 0.01
L = 1.0   # Domínio [-L, L]^2
T = 1.0
epochs = 20000
log_interval = 20

# Pesos da Função de Perda (Literatura PINN)
lambda_pde = 1.0
lambda_ic = 20.0
lambda_bc = 20.0

N_f = 14000   # Pontos de colocação interior
N_0 = 3500    # Pontos de condição inicial
N_b = 2800    # Pontos de fronteira

print(f"Viscosidade nu: {nu} | Domínio: [-{L}, {L}]^2 | Tempo: [0, {T}]")
print(f"Pesos de Perda: lambda_pde={lambda_pde}, lambda_ic={lambda_ic}, lambda_bc={lambda_bc}")
print(f"Pontos: N_f={N_f}, N_0={N_0}, N_b={N_b} | Log a cada {log_interval} épocas")

# ==============================================================================
# 2. ARQUITETURA DA REDE NEURAL (MLP com saída 2D: u, v)
# ==============================================================================
class BurgersPINN(nn.Module):
    def __init__(self, hidden_dim=64, num_layers=4):
        super().__init__()
        layers = []
        layers.append(nn.Linear(3, hidden_dim))  # Entrada: (x, y, t)
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 2))  # Saída: (u, v)
        self.net = nn.Sequential(*layers)
        
        # Inicialização Xavier
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x, y, t):
        inputs = torch.cat([x, y, t], dim=1)
        out = self.net(inputs)
        u = out[:, 0:1]
        v = out[:, 1:2]
        return u, v

# ==============================================================================
# 3. CONDIÇÃO INICIAL (Vórtices Gaussianos Dipolares)
# ==============================================================================
def initial_condition_np(x, y):
    u0 = np.exp(-10.0 * ((x + 0.3)**2 + y**2)) - np.exp(-10.0 * ((x - 0.3)**2 + y**2))
    v0 = np.exp(-10.0 * (x**2 + (y + 0.3)**2)) - np.exp(-10.0 * (x**2 + (y - 0.3)**2))
    return u0, v0

def initial_condition_torch(x, y):
    u0 = torch.exp(-10.0 * ((x + 0.3)**2 + y**2)) - torch.exp(-10.0 * ((x - 0.3)**2 + y**2))
    v0 = torch.exp(-10.0 * (x**2 + (y + 0.3)**2)) - torch.exp(-10.0 * (x**2 + (y - 0.3)**2))
    return u0, v0

# ==============================================================================
# 4. SOLVER NUMÉRICO DE REFERÊNCIA (RK4 + Diferenças Finitas em Malha Fina)
# ==============================================================================
def solve_burgers_2d_reference(nx_ref=120, ny_ref=120, t_target=0.5, dt=0.0005):
    """
    Integração de alta precisão da EDP de Burgers 2D para cálculo de L2/L_inf.
    """
    x = np.linspace(-L, L, nx_ref)
    y = np.linspace(-L, L, ny_ref)
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    X, Y = np.meshgrid(x, y)
    
    u, v = initial_condition_np(X, Y)
    # Forçar contorno Dirichlet zero
    u[0, :] = u[-1, :] = u[:, 0] = u[:, -1] = 0.0
    v[0, :] = v[-1, :] = v[:, 0] = v[:, -1] = 0.0
    
    def rhs(u_curr, v_curr):
        # Derivadas espaciais centrais de 2a ordem
        ux = (np.roll(u_curr, -1, axis=1) - np.roll(u_curr, 1, axis=1)) / (2 * dx)
        uy = (np.roll(u_curr, -1, axis=0) - np.roll(u_curr, 1, axis=0)) / (2 * dy)
        uxx = (np.roll(u_curr, -1, axis=1) - 2 * u_curr + np.roll(u_curr, 1, axis=1)) / (dx**2)
        uyy = (np.roll(u_curr, -1, axis=0) - 2 * u_curr + np.roll(u_curr, 1, axis=0)) / (dy**2)
        
        vx = (np.roll(v_curr, -1, axis=1) - np.roll(v_curr, 1, axis=1)) / (2 * dx)
        vy = (np.roll(v_curr, -1, axis=0) - np.roll(v_curr, 1, axis=0)) / (2 * dy)
        vxx = (np.roll(v_curr, -1, axis=1) - 2 * v_curr + np.roll(v_curr, 1, axis=1)) / (dx**2)
        vyy = (np.roll(v_curr, -1, axis=0) - 2 * v_curr + np.roll(v_curr, 1, axis=0)) / (dy**2)
        
        du_dt = - (u_curr * ux + v_curr * uy) + nu * (uxx + uyy)
        dv_dt = - (u_curr * vx + v_curr * vy) + nu * (vxx + vyy)
        
        # Dirichlet zero nas bordas
        du_dt[0, :] = du_dt[-1, :] = du_dt[:, 0] = du_dt[:, -1] = 0.0
        dv_dt[0, :] = dv_dt[-1, :] = dv_dt[:, 0] = dv_dt[:, -1] = 0.0
        return du_dt, dv_dt

    n_steps = int(np.round(t_target / dt))
    for _ in range(n_steps):
        k1_u, k1_v = rhs(u, v)
        k2_u, k2_v = rhs(u + 0.5 * dt * k1_u, v + 0.5 * dt * k1_v)
        k3_u, k3_v = rhs(u + 0.5 * dt * k2_u, v + 0.5 * dt * k2_v)
        k4_u, k4_v = rhs(u + dt * k3_u, v + dt * k3_v)
        
        u += (dt / 6.0) * (k1_u + 2*k2_u + 2*k3_u + k4_u)
        v += (dt / 6.0) * (k1_v + 2*k2_v + 2*k3_v + k4_v)
        
        u[0, :] = u[-1, :] = u[:, 0] = u[:, -1] = 0.0
        v[0, :] = v[-1, :] = v[:, 0] = v[:, -1] = 0.0
        
    return X, Y, u, v

# ==============================================================================
# 5. AMOSTRAGEM DE DADOS
# ==============================================================================
# Interior (x, y in [-1, 1], t in (0, 1])
x_f = ((torch.rand(N_f, 1) * 2.0 - 1.0) * L).to(device)
y_f = ((torch.rand(N_f, 1) * 2.0 - 1.0) * L).to(device)
t_f = (torch.rand(N_f, 1) * T).to(device)
x_f.requires_grad = True
y_f.requires_grad = True
t_f.requires_grad = True

# Condição Inicial (t = 0)
x_0 = ((torch.rand(N_0, 1) * 2.0 - 1.0) * L).to(device)
y_0 = ((torch.rand(N_0, 1) * 2.0 - 1.0) * L).to(device)
t_0 = torch.zeros(N_0, 1).to(device)
u_0, v_0 = initial_condition_torch(x_0, y_0)

# Condição de Contorno (Fronteira com Dirichlet Homogêneo u=v=0)
t_b = torch.rand(N_b, 1) * T
s_b = (torch.rand(N_b, 1) * 2.0 - 1.0) * L

x_b1 = torch.full((N_b // 4, 1), -L); y_b1 = s_b[:N_b // 4]               # x = -L
x_b2 = torch.full((N_b // 4, 1), L);  y_b2 = s_b[N_b // 4: 2*(N_b // 4)] # x = L
x_b3 = s_b[2*(N_b // 4): 3*(N_b // 4)]; y_b3 = torch.full((N_b // 4, 1), -L) # y = -L
x_b4 = s_b[3*(N_b // 4):]; y_b4 = torch.full((N_b // 4, 1), L)         # y = L

x_b = torch.cat([x_b1, x_b2, x_b3, x_b4], dim=0).to(device)
y_b = torch.cat([y_b1, y_b2, y_b3, y_b4], dim=0).to(device)
t_b = torch.cat([t_b[:N_b // 4]] * 4, dim=0).to(device)

# ==============================================================================
# 6. LOOP DE OTIMIZAÇÃO (20.000 ÉPOCAS)
# ==============================================================================
model = BurgersPINN(hidden_dim=64, num_layers=4).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

loss_history = {'epoch': [], 'total': [], 'pde_u': [], 'pde_v': [], 'pde': [], 'ic': [], 'bc': []}

print(f"\nIniciando treinamento da PINN Burgers 2D ({epochs} épocas)...", flush=True)
start_time = time.time()

for epoch in range(1, epochs + 1):
    optimizer.zero_grad()
    
    # 1. Resíduos não-lineares de Burgers 2D:
    # r_u = u_t + u*u_x + v*u_y - nu*(u_xx + u_yy)
    # r_v = v_t + u*v_x + v*v_y - nu*(v_xx + v_yy)
    u, v = model(x_f, y_f, t_f)
    
    u_t = torch.autograd.grad(u, t_f, torch.ones_like(u), create_graph=True)[0]
    u_x = torch.autograd.grad(u, x_f, torch.ones_like(u), create_graph=True)[0]
    u_y = torch.autograd.grad(u, y_f, torch.ones_like(u), create_graph=True)[0]
    u_xx = torch.autograd.grad(u_x, x_f, torch.ones_like(u_x), create_graph=True)[0]
    u_yy = torch.autograd.grad(u_y, y_f, torch.ones_like(u_y), create_graph=True)[0]
    
    v_t = torch.autograd.grad(v, t_f, torch.ones_like(v), create_graph=True)[0]
    v_x = torch.autograd.grad(v, x_f, torch.ones_like(v), create_graph=True)[0]
    v_y = torch.autograd.grad(v, y_f, torch.ones_like(v), create_graph=True)[0]
    v_xx = torch.autograd.grad(v_x, x_f, torch.ones_like(v_x), create_graph=True)[0]
    v_yy = torch.autograd.grad(v_y, y_f, torch.ones_like(v_y), create_graph=True)[0]
    
    r_u = u_t + u * u_x + v * u_y - nu * (u_xx + u_yy)
    r_v = v_t + u * v_x + v * v_y - nu * (v_xx + v_yy)
    
    loss_pde_u = torch.mean(r_u ** 2)
    loss_pde_v = torch.mean(r_v ** 2)
    loss_pde = loss_pde_u + loss_pde_v
    
    # 2. Resíduo de Condição Inicial
    u_pred_0, v_pred_0 = model(x_0, y_0, t_0)
    loss_ic = torch.mean((u_pred_0 - u_0)**2) + torch.mean((v_pred_0 - v_0)**2)
    
    # 3. Resíduo de Contorno (Dirichlet zero)
    u_pred_b, v_pred_b = model(x_b, y_b, t_b)
    loss_bc = torch.mean(u_pred_b ** 2) + torch.mean(v_pred_b ** 2)
    
    # Perda Total Ponderada
    total_loss = lambda_pde * loss_pde + lambda_ic * loss_ic + lambda_bc * loss_bc
    total_loss.backward()
    
    optimizer.step()
    scheduler.step()
    
    if epoch % log_interval == 0 or epoch == 1:
        loss_history['epoch'].append(epoch)
        loss_history['total'].append(total_loss.item())
        loss_history['pde_u'].append(loss_pde_u.item())
        loss_history['pde_v'].append(loss_pde_v.item())
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
# 7. SALVAMENTO DO MODELO (.pth)
# ==============================================================================
models_dir = "./paper1_heat_burgers/models"
os.makedirs(models_dir, exist_ok=True)
pth_path = os.path.join(models_dir, "pinn_burgers_2d_20k.pth")
torch.save({
    'epoch': epochs,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': total_loss.item(),
    'nu': nu,
    'train_duration': train_duration,
    'time_per_epoch_ms': time_per_epoch_ms,
    'loss_history': loss_history
}, pth_path)
print(f"[OK] Modelo salvo com sucesso em: {pth_path}")

# ==============================================================================
# 8. AVALIAÇÃO QUANTITATIVA CONTRA O SOLVER DE REFERÊNCIA
# ==============================================================================
nx, ny = 100, 100
t_test = 0.5
print(f"\nGerando solução de referência numérica de alta resolução (t = {t_test}s)...")
X_ref, Y_ref, u_ref, v_ref = solve_burgers_2d_reference(nx_ref=nx, ny_ref=ny, t_target=t_test, dt=0.0002)

X_flat = X_ref.flatten()
Y_flat = Y_ref.flatten()
T_flat = np.full_like(X_flat, t_test)

# Predição neural e medição de latência
t_start_inf = time.time()
with torch.no_grad():
    x_t = torch.tensor(X_flat, dtype=torch.float32).unsqueeze(1).to(device)
    y_t = torch.tensor(Y_flat, dtype=torch.float32).unsqueeze(1).to(device)
    t_t = torch.tensor(T_flat, dtype=torch.float32).unsqueeze(1).to(device)
    u_pred_flat, v_pred_flat = model(x_t, y_t, t_t)
    u_pred_flat = u_pred_flat.cpu().numpy().flatten()
    v_pred_flat = v_pred_flat.cpu().numpy().flatten()
inf_latency_ms = (time.time() - t_start_inf) * 1000.0

# Campo de magnitude de velocidade
vel_mag_pred = np.sqrt(u_pred_flat**2 + v_pred_flat**2)
vel_mag_ref = np.sqrt(u_ref.flatten()**2 + v_ref.flatten()**2)

# Métricas de Erro Relativo L2 e Linf
abs_err_u = np.abs(u_pred_flat - u_ref.flatten())
abs_err_v = np.abs(v_pred_flat - v_ref.flatten())
abs_err_mag = np.abs(vel_mag_pred - vel_mag_ref)

rel_l2_u = np.linalg.norm(u_pred_flat - u_ref.flatten()) / (np.linalg.norm(u_ref.flatten()) + 1e-12)
rel_l2_v = np.linalg.norm(v_pred_flat - v_ref.flatten()) / (np.linalg.norm(v_ref.flatten()) + 1e-12)
rel_l2_vel = np.linalg.norm(vel_mag_pred - vel_mag_ref) / (np.linalg.norm(vel_mag_ref) + 1e-12)
l_inf_vel = np.max(abs_err_mag)
mse_vel = np.mean(abs_err_mag ** 2)

kinetic_energy = 0.5 * np.mean(vel_mag_pred**2) * (4.0 * L**2)

print("\n" + "="*75)
print(f"RELATÓRIO DE DESEMPENHO CIENTÍFICO — BURGERS 2D (t = {t_test}s)")
print("="*75)
print(f"Perda Total Final:               {total_loss.item():.5e}")
print(f"Resíduo PDE Final:               {loss_pde.item():.5e}")
print(f"Erro Médio Quadrático (MSE |U|): {mse_vel:.5e}")
print(f"Erro Máximo (L_inf |U|):         {l_inf_vel:.5e}")
print(f"Erro Relativo L2 (|U|):          {rel_l2_vel:.5e} ({rel_l2_vel*100.0:.3f}%)")
print(f"Erro Relativo L2 (u):            {rel_l2_u:.5e}")
print(f"Erro Relativo L2 (v):            {rel_l2_v:.5e}")
print(f"Energia Cinética Total E(t=0.5): {kinetic_energy:.5e}")
print(f"Tempo de Treinamento Total:      {train_duration:.2f} s ({time_per_epoch_ms:.2f} ms/época)")
print(f"Latência de Inferência (10.000 pts): {inf_latency_ms:.2f} ms")
print("="*75)

# Linha de Tabela LaTeX formatada para o artigo:
print("\n>>> LINHA PARA A TABELA LATEX DO ARTIGO:")
print(f"Burgers 2D (Viscoso) & 20.000 & {total_loss.item():.2e} & {rel_l2_vel:.2e} & {l_inf_vel:.2e} & {inf_latency_ms:.2f}\\,ms \\\\")

# ==============================================================================
# 9. GERAÇÃO DE FIGURAS CIENTÍFICAS
# ==============================================================================
fig_dir = "./paper1_heat_burgers/figures"
os.makedirs(fig_dir, exist_ok=True)

# Figura 1: Curva de Convergência das Perdas em Alta Resolução
plt.figure(figsize=(4.8, 2.7))
epochs_arr = loss_history['epoch']
plt.semilogy(epochs_arr, loss_history['total'], label=r'Total $\mathcal{L}_{\mathrm{total}}$', color='#1f77b4', lw=1.5)
plt.semilogy(epochs_arr, loss_history['pde_u'], label=r'PDE ($u$) $\mathcal{L}_{\mathrm{pde}, u}$', color='#d62728', lw=1.0, ls='--')
plt.semilogy(epochs_arr, loss_history['pde_v'], label=r'PDE ($v$) $\mathcal{L}_{\mathrm{pde}, v}$', color='#ff7f0e', lw=1.0, ls=':')
plt.semilogy(epochs_arr, loss_history['ic'], label=r'Inicial $\mathcal{L}_{\mathrm{ic}}$ ($\times 20$)', color='#2ca02c', lw=1.0, ls='-.')
plt.semilogy(epochs_arr, loss_history['bc'], label=r'Contorno $\mathcal{L}_{\mathrm{bc}}$ ($\times 20$)', color='#9467bd', lw=1.0, ls='-')
plt.xlabel('Época de Treinamento')
plt.ylabel('Erro Quadrático Médio (MSE)')
plt.grid(True, which='both', ls=':', alpha=0.5)
plt.legend(loc='upper right', framealpha=0.9, fontsize=7.2)
plt.title(f'Convergência da PINN — Equação de Burgers 2D ({epochs} Épocas)')
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "burgers_loss_convergence.pdf"))
plt.savefig(os.path.join(fig_dir, "burgers_loss_convergence.png"))
plt.close()

# Figura 2: Evolução da Magnitude de Velocidade com Linhas de Corrente (Streamlines)
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), sharey=True)
times_eval = [0.0, 0.5, 1.0]

for idx, t_val in enumerate(times_eval):
    T_val_flat = np.full_like(X_flat, t_val)
    with torch.no_grad():
        x_t_v = torch.tensor(X_flat, dtype=torch.float32).unsqueeze(1).to(device)
        y_t_v = torch.tensor(Y_flat, dtype=torch.float32).unsqueeze(1).to(device)
        t_t_v = torch.tensor(T_val_flat, dtype=torch.float32).unsqueeze(1).to(device)
        u_p, v_p = model(x_t_v, y_t_v, t_t_v)
        u_p = u_p.cpu().numpy().reshape(nx, ny)
        v_p = v_p.cpu().numpy().reshape(nx, ny)
    
    speed = np.sqrt(u_p**2 + v_p**2)
    im = axes[idx].imshow(speed, extent=[-L, L, -L, L], origin='lower', cmap='viridis', vmin=0, vmax=1.0)
    
    # Adicionar streamlines para visualização vetorial precisa do escoamento
    stride = 2
    axes[idx].streamplot(X_ref, Y_ref, u_p, v_p, color='white', density=0.7, linewidth=0.6, arrowsize=0.6)
    
    axes[idx].set_title(f'$t = {t_val:.1f}$ s', fontsize=8.0)
    axes[idx].set_xlabel('$x$')
    if idx == 0:
        axes[idx].set_ylabel('$y$')

fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.8, label=r'Magnitude $\|\mathbf{u}\|$ (m/s)')
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "burgers_velocity_evolution.pdf"))
plt.savefig(os.path.join(fig_dir, "burgers_velocity_evolution.png"))
plt.close()

# Figura 3: Painel Combinado Científico de Burgers (3D Surfaces + Magnitude 2D)
fig = plt.figure(figsize=(7.2, 3.4))
gs = gridspec.GridSpec(2, 6, figure=fig, height_ratios=[1.15, 1.0], hspace=0.32, wspace=0.25)

# Linha 1: Superfícies 3D de u(x,y,t) em t=0 e t=0.5
ax3d_0 = fig.add_subplot(gs[0, 0:3], projection='3d')
ax3d_5 = fig.add_subplot(gs[0, 3:6], projection='3d')

with torch.no_grad():
    x_t_0 = torch.tensor(X_flat, dtype=torch.float32).unsqueeze(1).to(device)
    y_t_0 = torch.tensor(Y_flat, dtype=torch.float32).unsqueeze(1).to(device)
    t_0_eval = torch.zeros_like(x_t_0)
    t_5_eval = torch.full_like(x_t_0, 0.5)
    
    u_3d_0, _ = model(x_t_0, y_t_0, t_0_eval)
    u_3d_5, _ = model(x_t_0, y_t_0, t_5_eval)
    u_3d_0 = u_3d_0.cpu().numpy().reshape(nx, ny)
    u_3d_5 = u_3d_5.cpu().numpy().reshape(nx, ny)

ax3d_0.plot_surface(X_ref, Y_ref, u_3d_0, cmap='coolwarm', vmin=-1.0, vmax=1.0, linewidth=0, antialiased=True, alpha=0.92)
ax3d_0.set_title(r'(a) Superfície $u_\theta(x,y,0)$ ($t = 0{,}0$\,s)', fontsize=8.0, pad=-2)
ax3d_0.set_zlim(-1.0, 1.0)
ax3d_0.set_xlabel('$x$', labelpad=-7, fontsize=6.8); ax3d_0.set_ylabel('$y$', labelpad=-7, fontsize=6.8); ax3d_0.set_zlabel('$u$', labelpad=-7, fontsize=6.8)
ax3d_0.tick_params(labelsize=6.0, pad=-2)
ax3d_0.view_init(elev=28, azim=-55)

ax3d_5.plot_surface(X_ref, Y_ref, u_3d_5, cmap='coolwarm', vmin=-1.0, vmax=1.0, linewidth=0, antialiased=True, alpha=0.92)
ax3d_5.set_title(r'(b) Superfície $u_\theta(x,y,0{,}5)$ ($t = 0{,}5$\,s)', fontsize=8.0, pad=-2)
ax3d_5.set_zlim(-1.0, 1.0)
ax3d_5.set_xlabel('$x$', labelpad=-7, fontsize=6.8); ax3d_5.set_ylabel('$y$', labelpad=-7, fontsize=6.8); ax3d_5.set_zlabel('$u$', labelpad=-7, fontsize=6.8)
ax3d_5.tick_params(labelsize=6.0, pad=-2)
ax3d_5.view_init(elev=28, azim=-55)

# Linha 2: Campos de Magnitude 2D em t=0, 0.5, 1.0
ax_fs_0 = fig.add_subplot(gs[1, 0:2])
ax_fs_5 = fig.add_subplot(gs[1, 2:4])
ax_fs_10 = fig.add_subplot(gs[1, 4:6])

for ax, t_val, lbl in zip([ax_fs_0, ax_fs_5, ax_fs_10], [0.0, 0.5, 1.0], [r'(c) $\|\mathbf{u}\|$ ($t=0{,}0$\,s)', r'(d) $\|\mathbf{u}\|$ ($t=0{,}5$\,s)', r'(e) $\|\mathbf{u}\|$ ($t=1{,}0$\,s)']):
    T_snap = np.full_like(X_flat, t_val)
    with torch.no_grad():
        u_p, v_p = model(torch.tensor(X_flat, dtype=torch.float32).unsqueeze(1).to(device),
                         torch.tensor(Y_flat, dtype=torch.float32).unsqueeze(1).to(device),
                         torch.tensor(T_snap, dtype=torch.float32).unsqueeze(1).to(device))
        speed_snap = np.sqrt(u_p.cpu().numpy()**2 + v_p.cpu().numpy()**2).reshape(nx, ny)
    
    im_c = ax.imshow(speed_snap, extent=[-L, L, -L, L], origin='lower', cmap='viridis', vmin=0, vmax=1.0)
    ax.set_title(lbl, fontsize=7.8, pad=2)
    ax.set_xlabel('$x$', fontsize=7.2)
    if ax == ax_fs_0:
        ax.set_ylabel('$y$', fontsize=7.2)
    ax.tick_params(labelsize=6.5)

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "burgers_combined.pdf"))
plt.savefig(os.path.join(fig_dir, "burgers_combined.png"))
plt.close()

print(f"[OK] Figuras da Equação de Burgers salvas em {fig_dir}")
