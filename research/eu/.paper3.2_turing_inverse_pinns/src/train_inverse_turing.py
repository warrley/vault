#!/usr/bin/env python3
"""
PINN Inversa para Descoberta de Parâmetros e Reconstrução de Estados Ocultos
Parâmetros Reais (Ground Truth da Tese de Ricardo Pereira 2019, Tabela 27):
  a = 0.1305
  b = 0.7695
  kappa = 100.0 (Taxa Cinética)
  Du = 0.05     (Difusividade do Ativador)
  Dv = 1.00     (Difusividade do Inibidor)
  Domínio: [0, 1] x [0, 1], t in [0, 2.0]
  Ponto de Equilíbrio: (u*, v*) = (0.9000, 0.9500)

Dados de Entrada: Medições esparsas APENAS do ativador u(x, y, t) em 3 snapshots (t = 0.5, 1.0, 2.0).
Objetivo:
  1. Descobrir os parâmetros desconhecidos (Du, Dv, kappa) via nn.Parameter.
  2. Reconstruir o campo espacial completo do inibidor oculto v(x, y, t) sem medições de v.
GPU CUDA habilitada.
"""

import os
import time
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Reprodutibilidade
torch.manual_seed(42)
np.random.seed(42)

# Configurações visuais
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

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Dispositivo de Treinamento: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

# ==============================================================================
# 1. PARÂMETROS REAIS DA TESE DE PEREIRA (2019, TABELA 27)
# ==============================================================================
a = 0.1305
b = 0.7695
kappa_true = 100.0
Du_true = 0.05
Dv_true = 1.00
L = 1.0
T = 2.0

u_star = a + b                     # 0.9000
v_star = b / ((a + b) ** 2)        # 0.9500

print("="*75)
print("INVERSE PINN — PARÂMETROS DA TESE DE RICARDO PEREIRA (LNCC, 2019)")
print("="*75)
print(f"Valores Reais (Ground Truth): Du = {Du_true}, Dv = {Dv_true}, kappa = {kappa_true}")
print(f"Constantes Cinéticas: a = {a}, b = {b} | Equilíbrio (u*, v*) = ({u_star:.4f}, {v_star:.4f})")
print(f"Domínio: [0, {L}]^2 | Horizonte Temporal: [0, {T}] s")

# ==============================================================================
# 2. CARREGAMENTO DOS DADOS REAIS DA SOLUÇÃO NUMÉRICA DA TESE
# ==============================================================================
# Carregar dados exatos da simulação numérica do sistema de Schnakenberg
sol_data = np.load('./paper3.2_turing_inverse_pinns/exact_thesis_turing_solution.npz')

x_grid = sol_data['x']
y_grid = sol_data['y']
N_grid = len(x_grid)
X_grid, Y_grid = np.meshgrid(x_grid, y_grid)

N_obs = 2000
snapshot_times = [0.41, 0.81, 2.0]

def sample_exact_thesis_data(n_pts, t_snaps, noise_level=0.0):
    x_list, y_list, t_list, u_list, v_list = [], [], [], [], []
    pts_per_snap = n_pts // len(t_snaps)
    
    for t_val in t_snaps:
        U_mat = sol_data[f'u_{t_val}']
        V_mat = sol_data[f'v_{t_val}']
        
        # Sorteia índices pontuais na malha da tese
        idx_x = np.random.randint(0, N_grid, size=(pts_per_snap,))
        idx_y = np.random.randint(0, N_grid, size=(pts_per_snap,))
        
        x_pts = x_grid[idx_x].reshape(-1, 1)
        y_pts = y_grid[idx_y].reshape(-1, 1)
        t_pts = np.full((pts_per_snap, 1), t_val)
        
        u_exact = U_mat[idx_y, idx_x].reshape(-1, 1)
        v_exact = V_mat[idx_y, idx_x].reshape(-1, 1)
        
        if noise_level > 0:
            noise = np.random.normal(0, noise_level * np.std(u_exact), size=u_exact.shape)
            u_obs = u_exact + noise
        else:
            u_obs = u_exact
            
        x_list.append(x_pts); y_list.append(y_pts); t_list.append(t_pts)
        u_list.append(u_obs); v_list.append(v_exact)
        
    X = np.vstack(x_list)
    Y = np.vstack(y_list)
    T_arr = np.vstack(t_list)
    U_obs = np.vstack(u_list)
    V_hidden = np.vstack(v_list)
    
    return (torch.tensor(X, dtype=torch.float32),
            torch.tensor(Y, dtype=torch.float32),
            torch.tensor(T_arr, dtype=torch.float32),
            torch.tensor(U_obs, dtype=torch.float32),
            torch.tensor(V_hidden, dtype=torch.float32))

# Amostras de medição do ativador u (Inibidor v NUNCA é passado para treino!)
x_data, y_data, t_data, u_data, v_hidden_test = sample_exact_thesis_data(N_obs, snapshot_times, noise_level=0.0)

x_data = x_data.to(device)
y_data = y_data.to(device)
t_data = t_data.to(device)
u_data = u_data.to(device)

print(f"Medições geradas: {len(x_data)} pontos em t in {snapshot_times} (Apenas ativador u)")

# ==============================================================================
# 3. PONTOS DE COLOCAÇÃO INTERIOR E FRONTEIRA
# ==============================================================================
N_f = 10000
x_f = (torch.rand(N_f, 1) * L).to(device)
y_f = (torch.rand(N_f, 1) * L).to(device)
t_f = (torch.rand(N_f, 1) * T).to(device)
x_f.requires_grad = True
y_f.requires_grad = True
t_f.requires_grad = True

# Fronteira Neumann
N_b = 2000
t_b = (torch.rand(N_b, 1) * T).to(device)
s_b = (torch.rand(N_b, 1) * L).to(device)

x_b_left = torch.zeros(N_b // 4, 1, requires_grad=True, device=device)
y_b_left = s_b[:N_b // 4]
x_b_right = torch.full((N_b // 4, 1), L, requires_grad=True, device=device)
y_b_right = s_b[N_b // 4: 2 * (N_b // 4)]
x_b_bottom = s_b[2 * (N_b // 4): 3 * (N_b // 4)]
y_b_bottom = torch.zeros(N_b // 4, 1, requires_grad=True, device=device)
x_b_top = s_b[3 * (N_b // 4):]
y_b_top = torch.full((N_b // 4, 1), L, requires_grad=True, device=device)
t_b_quarter = t_b[:N_b // 4]

# ==============================================================================
# 4. ARQUITETURA DA PINN INVERSA COM PARÂMETROS TREINÁVEIS
# ==============================================================================
class InverseTuringPINN(nn.Module):
    def __init__(self, hidden_dim=64, num_layers=4):
        super().__init__()
        # Rede Neural para (u, v)
        layers = []
        layers.append(nn.Linear(3, hidden_dim))
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 2))  # Saída: u e v
        self.net = nn.Sequential(*layers)
        
        # Parâmetros físicos desconhecidos instanciados com chutes iniciais
        # Chutes iniciais descalibrados:
        # Du: real 0.05 -> chute 0.20 (+300%)
        # Dv: real 1.00 -> chute 0.40 (-60%)
        # kappa: real 100.0 -> chute 50.0 (-50%)
        self.log_Du = nn.Parameter(torch.tensor(np.log(0.20), dtype=torch.float32))
        self.log_Dv = nn.Parameter(torch.tensor(np.log(0.40), dtype=torch.float32))
        self.log_kappa = nn.Parameter(torch.tensor(np.log(50.0), dtype=torch.float32))
        
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

    @property
    def Du(self):
        return torch.exp(self.log_Du)

    @property
    def Dv(self):
        return torch.exp(self.log_Dv)

    @property
    def kappa(self):
        return torch.exp(self.log_kappa)

model = InverseTuringPINN(hidden_dim=64, num_layers=4).to(device)

print("\nChutes Iniciais dos Parâmetros Desconhecidos:")
print(f"  Du_inicial    = {model.Du.item():.4f} (Real: {Du_true})")
print(f"  Dv_inicial    = {model.Dv.item():.4f} (Real: {Dv_true})")
print(f"  kappa_inicial = {model.kappa.item():.4f} (Real: {kappa_true})")

# ==============================================================================
# 5. OTIMIZAÇÃO (10.000 ÉPOCAS)
# ==============================================================================
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10000, eta_min=1e-5)

epochs = 10000
log_interval = 250

history = {
    'epoch': [], 'total_loss': [], 'data_loss': [], 'pde_loss': [],
    'Du_est': [], 'Dv_est': [], 'kappa_est': []
}

print(f"\nIniciando treinamento da PINN Inversa ({epochs} épocas em GPU)...")
start_time = time.time()

for epoch in range(1, epochs + 1):
    optimizer.zero_grad()
    
    # 1. Perda de Dados (Apenas no Ativador u)
    u_pred_data, _ = model(x_data, y_data, t_data)
    loss_data = torch.mean((u_pred_data - u_data) ** 2)
    
    # 2. Resíduos da EDP com parâmetros dinâmicos
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
    
    lap_u = u_xx + u_yy
    lap_v = v_xx + v_yy
    
    Du_curr = model.Du
    Dv_curr = model.Dv
    kappa_curr = model.kappa
    
    r_u = u_t - Du_curr * lap_u - kappa_curr * (a - u + (u**2) * v)
    r_v = v_t - Dv_curr * lap_v - kappa_curr * (b - (u**2) * v)
    
    loss_pde = torch.mean(r_u ** 2) + torch.mean(r_v ** 2)
    
    # 3. Contorno Neumann
    u_l, v_l = model(x_b_left, y_b_left, t_b_quarter)
    u_lx = torch.autograd.grad(u_l, x_b_left, torch.ones_like(u_l), create_graph=True)[0]
    v_lx = torch.autograd.grad(v_l, x_b_left, torch.ones_like(v_l), create_graph=True)[0]
    
    u_r, v_r = model(x_b_right, y_b_right, t_b_quarter)
    u_rx = torch.autograd.grad(u_r, x_b_right, torch.ones_like(u_r), create_graph=True)[0]
    v_rx = torch.autograd.grad(v_r, x_b_right, torch.ones_like(v_r), create_graph=True)[0]
    
    u_b, v_b = model(x_b_bottom, y_b_bottom, t_b_quarter)
    u_by = torch.autograd.grad(u_b, y_b_bottom, torch.ones_like(u_b), create_graph=True)[0]
    v_by = torch.autograd.grad(v_b, y_b_bottom, torch.ones_like(v_b), create_graph=True)[0]
    
    u_t_b, v_t_b = model(x_b_top, y_b_top, t_b_quarter)
    u_ty = torch.autograd.grad(u_t_b, y_b_top, torch.ones_like(u_t_b), create_graph=True)[0]
    v_ty = torch.autograd.grad(v_t_b, y_b_top, torch.ones_like(v_t_b), create_graph=True)[0]
    
    loss_bc = (torch.mean(u_lx**2) + torch.mean(v_lx**2) +
               torch.mean(u_rx**2) + torch.mean(v_rx**2) +
               torch.mean(u_by**2) + torch.mean(v_by**2) +
               torch.mean(u_ty**2) + torch.mean(v_ty**2))
    
    # Perda Total Inversa
    total_loss = 20.0 * loss_data + loss_pde + 2.0 * loss_bc
    total_loss.backward()
    
    optimizer.step()
    scheduler.step()
    
    if epoch % log_interval == 0 or epoch == 1:
        history['epoch'].append(epoch)
        history['total_loss'].append(total_loss.item())
        history['data_loss'].append(loss_data.item())
        history['pde_loss'].append(loss_pde.item())
        history['Du_est'].append(Du_curr.item())
        history['Dv_est'].append(Dv_curr.item())
        history['kappa_est'].append(kappa_curr.item())
        
        if epoch % 2000 == 0 or epoch == 1:
            print(f"Época {epoch:5d}/{epochs} | Total Loss: {total_loss.item():.5e} | Du: {Du_curr.item():.5f} | Dv: {Dv_curr.item():.5f} | kappa: {kappa_curr.item():.2f}")

duration = time.time() - start_time
print(f"\nTreinamento concluído em {duration:.2f} segundos ({duration/60:.2f} minutos).")

# ==============================================================================
# 6. RESULTADOS FINAIS DE IDENTIFICAÇÃO E RECONSTRUÇÃO
# ==============================================================================
Du_final = model.Du.item()
Dv_final = model.Dv.item()
kappa_final = model.kappa.item()

err_Du_pct = abs(Du_final - Du_true) / Du_true * 100.0
err_Dv_pct = abs(Dv_final - Dv_true) / Dv_true * 100.0
err_kappa_pct = abs(kappa_final - kappa_true) / kappa_true * 100.0

# Avaliar reconstrução do inibidor oculto v(x, y, t)
with torch.no_grad():
    _, v_reconstructed = model(x_data, y_data, t_data)
    v_rec_np = v_reconstructed.cpu().numpy().flatten()
    v_true_np = v_hidden_test.numpy().flatten()

rel_l2_v = np.linalg.norm(v_rec_np - v_true_np) / np.linalg.norm(v_true_np)
max_err_v = np.max(np.abs(v_rec_np - v_true_np))

print("\n" + "="*75)
print("RELATÓRIO DE IDENTIFICAÇÃO DA PINN INVERSA (PARÂMETROS DA TESE)")
print("="*75)
print(f"Parâmetro Du:    Real = {Du_true:.4f} | Estimado = {Du_final:.5f} | Erro: {err_Du_pct:.3f}%")
print(f"Parâmetro Dv:    Real = {Dv_true:.4f} | Estimado = {Dv_final:.5f} | Erro: {err_Dv_pct:.3f}%")
print(f"Parâmetro kappa: Real = {kappa_true:.2f} | Estimado = {kappa_final:.3f} | Erro: {err_kappa_pct:.3f}%")
print(f"Reconstrução do Inibidor v (Estado Oculto):")
print(f"  Erro Relativo L2: {rel_l2_v:.5e} ({rel_l2_v*100:.3f}%)")
print(f"  Erro Máximo L_inf: {max_err_v:.5e}")
print("="*75)

# Salvar modelo
models_dir = "./paper3.2_turing_inverse_pinns/models"
os.makedirs(models_dir, exist_ok=True)
torch.save({
    'model_state': model.state_dict(),
    'Du_est': Du_final,
    'Dv_est': Dv_final,
    'kappa_est': kappa_final,
    'history': history
}, os.path.join(models_dir, "pinn_inverse_turing_2019.pth"))
print(f"[OK] Modelo salvo em: {models_dir}/pinn_inverse_turing_2019.pth")
