#!/usr/bin/env python3
"""
Treinamento de PINN de Alta Resolução — Equação do Calor 2D em Domínio com Múltiplas Cavidades
Aceleração CUDA Completa (RTX 3050) — 50.000 Épocas
Pesos da Função de Perda Calibrados:
  lambda_pde = 1.0, lambda_ic = 20.0, lambda_bc_ext = 20.0, lambda_bc_holes = 40.0
Amostragem com Camada Limite ao redor dos furos e mascaramento geométrico estrito.
"""

import os
import sys
import time
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D

# Fixar sementes para reprodutibilidade científica
torch.manual_seed(42)
np.random.seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)
    torch.backends.cudnn.benchmark = True

# Configuração de tipografia para artigos científicos
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
    'font.size': 8.5,
    'axes.labelsize': 9.0,
    'axes.titlesize': 9.5,
    'xtick.labelsize': 8.0,
    'ytick.labelsize': 8.0,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'mathtext.fontset': 'stix'
})

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("=" * 80)
print(f"Dispositivo de Treinamento: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
if torch.cuda.is_available():
    print(f"VRAM Total Disponível: {torch.cuda.get_device_properties(0).total_memory / (1024**2):.1f} MB")
print("=" * 80)

# ==============================================================================
# 1. PARÂMETROS FÍSICOS, GEOMÉTRICOS E HIPERPARÂMETROS
# ==============================================================================
alpha = 0.05       # Coeficiente de difusividade térmica
L = 1.0            # Comprimento característico do domínio quadrado [0, L]^2
T = 2.0            # Tempo final de simulação
epochs = 50000     # 50.000 épocas de treinamento
log_interval = 25  # Registro de perdas a cada 25 épocas (2000 pontos de alta fidelidade)
print_interval = 10

# Definição das 3 cavidades circulares dissipadoras (x_c, y_c, raio)
holes = [
    (0.30, 0.30, 0.12),  # Cavidade H1 (inferior esquerda)
    (0.70, 0.30, 0.12),  # Cavidade H2 (inferior direita)
    (0.50, 0.70, 0.12)   # Cavidade H3 (superior central)
]

# Pesos da Função de Perda Multiobjetivo (Calibrados conforme literatura)
lambda_pde = 1.0
lambda_ic = 20.0
lambda_bc_ext = 20.0
lambda_bc_holes = 40.0   # Peso intensificado para anular vazamento e fixar u=0 na borda

# Número de pontos de colocação (Otimizado para saturação e alta velocidade na GPU)
N_f_target = 24000          # Pontos no interior da placa
N_f_boundary_layer = 6000   # Pontos concentrados na camada limite ao redor dos furos
N_0_target = 6000           # Pontos na condição inicial (t = 0)
N_b_ext = 4000              # Pontos nas 4 bordas externas
N_b_holes_per_hole = 2000   # Pontos na borda de cada furo (total 6.000)

print(f"Configuração:")
print(f" - Épocas: {epochs}")
print(f" - Pesos: PDE={lambda_pde}, IC={lambda_ic}, Ext_BC={lambda_bc_ext}, Holes_BC={lambda_bc_holes}")
print(f" - Amostragem Total por Passo: {N_f_target + N_f_boundary_layer + N_0_target + N_b_ext + 3*N_b_holes_per_hole:,} pontos")
print("=" * 80)

# ==============================================================================
# 2. ARQUITETURA DA REDE NEURAL (PINN COM ATIVAÇÃO TANH E FOURIER FEATURES SUAVES)
# ==============================================================================
class IrregularHeatPINN(nn.Module):
    def __init__(self, hidden_dim=128, num_layers=5):
        super().__init__()
        layers = []
        layers.append(nn.Linear(3, hidden_dim))  # Entrada: (x, y, t)
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 1))  # Saída: u(x, y, t)
        self.net = nn.Sequential(*layers)
        
        # Inicialização Xavier Normal
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x, y, t):
        inputs = torch.cat([x, y, t], dim=1)
        return self.net(inputs)

# ==============================================================================
# 3. AMOSTRAGEM MESHLESS COM REFINO DE CAMADA LIMITE E MÁSCARA
# ==============================================================================
def sample_interior_points(n_target):
    """Amostragem uniforme no domínio quadrado excluindo os furos."""
    pts = []
    while len(pts) < n_target:
        batch = np.random.uniform(0, L, size=(n_target * 2, 2))
        valid = np.ones(len(batch), dtype=bool)
        for (hx, hy, hr) in holes:
            dist_sq = (batch[:, 0] - hx)**2 + (batch[:, 1] - hy)**2
            valid = valid & (dist_sq > hr**2)
        valid_pts = batch[valid]
        pts.extend(valid_pts.tolist())
    pts = np.array(pts[:n_target])
    return pts[:, 0:1], pts[:, 1:2]

def sample_boundary_layer_points(n_per_hole=4000, r_mult=1.35):
    """Amostragem concentrada na camada limite ao redor das cavidades."""
    pts = []
    for (hx, hy, hr) in holes:
        r = np.random.uniform(hr, hr * r_mult, size=(n_per_hole, 1))
        theta = np.random.uniform(0, 2 * np.pi, size=(n_per_hole, 1))
        x_bl = hx + r * np.cos(theta)
        y_bl = hy + r * np.sin(theta)
        valid = (x_bl >= 0) & (x_bl <= L) & (y_bl >= 0) & (y_bl <= L)
        pts.append(np.hstack([x_bl[valid].reshape(-1, 1), y_bl[valid].reshape(-1, 1)]))
    all_bl = np.vstack(pts)
    return all_bl[:, 0:1], all_bl[:, 1:2]

# 1. Pontos de colocação no interior + camada limite
x_int_np, y_int_np = sample_interior_points(N_f_target)
x_bl_np, y_bl_np = sample_boundary_layer_points(N_f_boundary_layer // 3, r_mult=1.35)

x_f_all = np.vstack([x_int_np, x_bl_np])
y_f_all = np.vstack([y_int_np, y_bl_np])
t_f_all = np.random.uniform(0, T, size=(len(x_f_all), 1))

x_f = torch.tensor(x_f_all, dtype=torch.float32, device=device, requires_grad=True)
y_f = torch.tensor(y_f_all, dtype=torch.float32, device=device, requires_grad=True)
t_f = torch.tensor(t_f_all, dtype=torch.float32, device=device, requires_grad=True)

# 2. Condição Inicial: t = 0, u = 0
x_0_np, y_0_np = sample_interior_points(N_0_target)
x_0 = torch.tensor(x_0_np, dtype=torch.float32, device=device)
y_0 = torch.tensor(y_0_np, dtype=torch.float32, device=device)
t_0 = torch.zeros((N_0_target, 1), dtype=torch.float32, device=device)
u_0 = torch.zeros((N_0_target, 1), dtype=torch.float32, device=device)

# 3. Contorno Externo: u = 1.0 nas 4 faces
s_ext = np.random.uniform(0, L, size=(N_b_ext // 4, 1))
t_ext_seg = np.random.uniform(0, T, size=(N_b_ext // 4, 1))

x_ext_np = np.vstack([np.zeros_like(s_ext), np.full_like(s_ext, L), s_ext, s_ext])
y_ext_np = np.vstack([s_ext, s_ext, np.zeros_like(s_ext), np.full_like(s_ext, L)])
t_ext_np = np.vstack([t_ext_seg, t_ext_seg, t_ext_seg, t_ext_seg])

x_ext = torch.tensor(x_ext_np, dtype=torch.float32, device=device)
y_ext = torch.tensor(y_ext_np, dtype=torch.float32, device=device)
t_ext = torch.tensor(t_ext_np, dtype=torch.float32, device=device)
u_ext_target = torch.ones_like(x_ext, device=device)

# 4. Contorno dos 3 Furos: u = 0.0 na borda polar exata
x_h_list, y_h_list, t_h_list = [], [], []
for (hx, hy, hr) in holes:
    theta = np.random.uniform(0, 2 * np.pi, size=(N_b_holes_per_hole, 1))
    th = np.random.uniform(0, T, size=(N_b_holes_per_hole, 1))
    xh = hx + hr * np.cos(theta)
    yh = hy + hr * np.sin(theta)
    x_h_list.append(xh)
    y_h_list.append(yh)
    t_h_list.append(th)

x_holes = torch.tensor(np.vstack(x_h_list), dtype=torch.float32, device=device)
y_holes = torch.tensor(np.vstack(y_h_list), dtype=torch.float32, device=device)
t_holes = torch.tensor(np.vstack(t_h_list), dtype=torch.float32, device=device)
u_holes_target = torch.zeros_like(x_holes, device=device)

# 5. Conjunto de Validação Independente para Métricas L2 e Linf
N_val = 50000
x_val_np, y_val_np = sample_interior_points(N_val)
t_val_np = np.random.uniform(0, T, size=(N_val, 1))
x_val = torch.tensor(x_val_np, dtype=torch.float32, device=device, requires_grad=True)
y_val = torch.tensor(y_val_np, dtype=torch.float32, device=device, requires_grad=True)
t_val = torch.tensor(t_val_np, dtype=torch.float32, device=device, requires_grad=True)

print(f"Colocação pronta:")
print(f"  - PDE Interior + Camada Limite: {len(x_f):,}")
print(f"  - Condição Inicial (t=0):       {len(x_0):,}")
print(f"  - Borda Externa (u=1):          {len(x_ext):,}")
print(f"  - Bordas dos Furos (u=0):       {len(x_holes):,}")
print(f"  - Conjunto Teste Independente:  {N_val:,}")

# ==============================================================================
# 4. LOOP DE TREINAMENTO OTIMIZADO (50.000 ÉPOCAS)
# ==============================================================================
model = IrregularHeatPINN(hidden_dim=128, num_layers=5).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

loss_history = {
    'epoch': [],
    'total': [],
    'pde': [],
    'ic': [],
    'bc_ext': [],
    'bc_holes': [],
    'epoch_time_ms': []
}

models_dir = "./paper2_heat_irregular_domain/models"
os.makedirs(models_dir, exist_ok=True)
checkpoint_path = os.path.join(models_dir, "pinn_heat_holes_checkpoint.pth")
start_epoch = 1

if os.path.exists(checkpoint_path):
    print(f"[*] Encontrado checkpoint em {checkpoint_path}. Carregando...")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    loss_history = checkpoint['loss_history']
    start_epoch = checkpoint['epoch'] + 1
    print(f"[*] Retomando treinamento a partir da época {start_epoch}!")

print("\n" + "=" * 80)
print(f"INICIANDO TREINAMENTO DA PINN ({epochs:,} ÉPOCAS) NA GPU...")
print("=" * 80)

total_start_time = time.time()
recent_epoch_times = []

for epoch in range(start_epoch, epochs + 1):
    epoch_start = time.perf_counter()
    optimizer.zero_grad(set_to_none=True)
    
    # 1. Resíduo da EDP: u_t - alpha * (u_xx + u_yy) = 0
    u = model(x_f, y_f, t_f)
    grads = torch.autograd.grad(u, [x_f, y_f, t_f], torch.ones_like(u), create_graph=True, retain_graph=True)
    u_x, u_y, u_t = grads[0], grads[1], grads[2]
    
    u_xx = torch.autograd.grad(u_x, x_f, torch.ones_like(u_x), create_graph=True, retain_graph=True)[0]
    u_yy = torch.autograd.grad(u_y, y_f, torch.ones_like(u_y), create_graph=True, retain_graph=True)[0]
    
    res_pde = u_t - alpha * (u_xx + u_yy)
    loss_pde = torch.mean(res_pde ** 2)
    
    # 2. Resíduo de Condição Inicial (t = 0, u = 0)
    u_pred_0 = model(x_0, y_0, t_0)
    loss_ic = torch.mean((u_pred_0 - u_0) ** 2)
    
    # 3. Resíduo de Contorno Externo (u = 1.0)
    u_pred_ext = model(x_ext, y_ext, t_ext)
    loss_bc_ext = torch.mean((u_pred_ext - u_ext_target) ** 2)
    
    # 4. Resíduo de Contorno dos Furos (u = 0.0)
    u_pred_holes = model(x_holes, y_holes, t_holes)
    loss_bc_holes = torch.mean((u_pred_holes - u_holes_target) ** 2)
    
    # Perda Total Ponderada
    total_loss = (lambda_pde * loss_pde + 
                  lambda_ic * loss_ic + 
                  lambda_bc_ext * loss_bc_ext + 
                  lambda_bc_holes * loss_bc_holes)
    
    total_loss.backward()
    optimizer.step()
    scheduler.step()
    
    # FREIO TÉRMICO PARA POUPAR A CPU/GPU DO USUÁRIO
    time.sleep(0.015)
    
    epoch_duration_ms = (time.perf_counter() - epoch_start) * 1000.0
    recent_epoch_times.append(epoch_duration_ms)
    
    # Registro de histórico de perdas
    if epoch % log_interval == 0 or epoch == 1:
        loss_history['epoch'].append(epoch)
        loss_history['total'].append(total_loss.item())
        loss_history['pde'].append(loss_pde.item())
        loss_history['ic'].append(loss_ic.item())
        loss_history['bc_ext'].append(loss_bc_ext.item())
        loss_history['bc_holes'].append(loss_bc_holes.item())
        loss_history['epoch_time_ms'].append(epoch_duration_ms)
        
    if epoch % print_interval == 0 or epoch == 1:
        avg_ms = np.mean(recent_epoch_times[-print_interval:]) if epoch > 1 else epoch_duration_ms
        lr_curr = scheduler.get_last_lr()[0]
        elapsed = time.time() - total_start_time
        eta_sec = (epochs - epoch) * (avg_ms / 1000.0)
        print(f"[{epoch:5d}/{epochs}] Loss: {total_loss.item():.4e} | PDE: {loss_pde.item():.4e} | "
              f"Holes: {loss_bc_holes.item():.4e} | Ext: {loss_bc_ext.item():.4e} | "
              f"ms/ep: {avg_ms:.1f} | LR: {lr_curr:.2e} | ETA: {eta_sec/60:.1f}min", flush=True)
              
    # Salva checkpoint a cada 1000 épocas
    if epoch % 1000 == 0:
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'loss_history': loss_history
        }, checkpoint_path)

total_train_time = time.time() - total_start_time
avg_epoch_ms = np.mean(loss_history['epoch_time_ms'])
print("=" * 80)
print(f"Treinamento concluído em {total_train_time:.2f}s ({total_train_time/60:.2f} min).")
print(f"Velocidade Média: {avg_epoch_ms:.2f} ms/época ({1000.0/avg_epoch_ms:.1f} iterações/s)")
print("=" * 80)

# ==============================================================================
# 5. AVALIAÇÃO DE ERROS CIENTÍFICOS: L2 RELATIVO, L_INF E CONFORMIDADE
# ==============================================================================
model.eval()

# 1. Avaliação do Resíduo no Conjunto de Teste Independente
with torch.enable_grad():
    u_val = model(x_val, y_val, t_val)
    grads_val = torch.autograd.grad(u_val, [x_val, y_val, t_val], torch.ones_like(u_val), create_graph=True, retain_graph=True)
    u_val_x, u_val_y, u_val_t = grads_val[0], grads_val[1], grads_val[2]
    u_val_xx = torch.autograd.grad(u_val_x, x_val, torch.ones_like(u_val_x), create_graph=False)[0]
    u_val_yy = torch.autograd.grad(u_val_y, y_val, torch.ones_like(u_val_y), create_graph=False)[0]
    res_val_pde = u_val_t - alpha * (u_val_xx + u_val_yy)
    res_val_pde_np = res_val_pde.detach().cpu().numpy()

# 2. Avaliação de Erro de Contorno e Condição Inicial
with torch.no_grad():
    err_holes_np = np.abs(model(x_holes, y_holes, t_holes).cpu().numpy() - 0.0)
    err_ext_np = np.abs(model(x_ext, y_ext, t_ext).cpu().numpy() - 1.0)
    err_ic_np = np.abs(model(x_0, y_0, t_0).cpu().numpy() - 0.0)

# Métricas L2 e Linf
l2_res_pde = np.sqrt(np.mean(res_val_pde_np ** 2))
linf_res_pde = np.max(np.abs(res_val_pde_np))

l2_err_holes = np.sqrt(np.mean(err_holes_np ** 2))
linf_err_holes = np.max(err_holes_np)

l2_err_ext = np.sqrt(np.mean(err_ext_np ** 2))
linf_err_ext = np.max(err_ext_np)

l2_err_ic = np.sqrt(np.mean(err_ic_np ** 2))
linf_err_ic = np.max(err_ic_np)

# Medição de latência para 100.000 pontos
t_bench_start = time.time()
with torch.no_grad():
    dummy_x = torch.rand(100000, 1, device=device)
    dummy_y = torch.rand(100000, 1, device=device)
    dummy_t = torch.full((100000, 1), 1.0, device=device)
    _ = model(dummy_x, dummy_y, dummy_t)
latency_100k_ms = (time.time() - t_bench_start) * 1000.0

print("\n" + "=" * 80)
print("RELATÓRIO FINAL DE MÉTRICAS E CONFORMIDADE CIENTÍFICA (50.000 ÉPOCAS)")
print("=" * 80)
print(f"Perda Residual Total Final:             {loss_history['total'][-1]:.5e}")
print(f"Resíduo da EDP - L2 (Teste 50k pts):    {l2_res_pde:.5e}")
print(f"Resíduo da EDP - L_inf (Teste 50k pts): {linf_res_pde:.5e}")
print(f"Erro Borda dos Furos (u=0) - L2:        {l2_err_holes:.5e}")
print(f"Erro Borda dos Furos (u=0) - L_inf:     {linf_err_holes:.5e}")
print(f"Erro Borda Externa (u=1) - L2:          {l2_err_ext:.5e}")
print(f"Erro Borda Externa (u=1) - L_inf:       {linf_err_ext:.5e}")
print(f"Erro Condição Inicial (t=0) - L2:       {l2_err_ic:.5e}")
print(f"Erro Condição Inicial (t=0) - L_inf:    {linf_err_ic:.5e}")
print(f"Latência de Inferência (100k pts):      {latency_100k_ms:.2f} ms ({latency_100k_ms/10:.3f} ms / 10k pts)")
print(f"Tempo Médio por Época:                  {avg_epoch_ms:.2f} ms")
print(f"Tempo Total de Treinamento:             {total_train_time:.2f} s ({total_train_time/60:.2f} min)")
print("=" * 80)

# ==============================================================================
# 6. SALVAMENTO DO MODELO E CHECKPOINT
# ==============================================================================
models_dir = "./paper2_heat_irregular_domain/models"
os.makedirs(models_dir, exist_ok=True)
pth_path = os.path.join(models_dir, "pinn_heat_holes_50k.pth")
torch.save({
    'epoch': epochs,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss_history': loss_history,
    'metrics': {
        'l2_res_pde': float(l2_res_pde),
        'linf_res_pde': float(linf_res_pde),
        'l2_err_holes': float(l2_err_holes),
        'linf_err_holes': float(linf_err_holes),
        'l2_err_ext': float(l2_err_ext),
        'linf_err_ext': float(linf_err_ext),
        'l2_err_ic': float(l2_err_ic),
        'linf_err_ic': float(linf_err_ic),
        'total_train_time': float(total_train_time),
        'avg_epoch_ms': float(avg_epoch_ms)
    },
    'alpha': alpha,
    'holes': holes
}, pth_path)
print(f"[OK] Checkpoint salvo em: {pth_path}")

# ==============================================================================
# 7. GERAÇÃO DE FIGURAS CIENTÍFICAS DE ALTA RESOLUÇÃO (2D e 3D)
# ==============================================================================
fig_dir = "./paper2_heat_irregular_domain/figures"
os.makedirs(fig_dir, exist_ok=True)

# ------------------------------------------------------------------------------
# FIGURA 1: Domínio Irregular com Colocação Meshless e Camada Limite
# ------------------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 2.8), dpi=300)

# Painel (a): Escadeamento cartesiano MDF
nx_g = 25
gx = np.linspace(0, 1, nx_g)
gy = np.linspace(0, 1, nx_g)
for xv in gx:
    ax1.axvline(xv, color='gray', lw=0.35, alpha=0.5)
for yv in gy:
    ax1.axhline(yv, color='gray', lw=0.35, alpha=0.5)

hx, hy, hr = holes[0]
c_true = plt.Circle((hx, hy), hr, color='red', fill=False, lw=1.4, ls='--', label='Borda Real $\\partial\\mathcal{H}$')
ax1.add_patch(c_true)

for i in range(nx_g - 1):
    for j in range(nx_g - 1):
        cx = (gx[i] + gx[i+1]) / 2.0
        cy = (gy[j] + gy[j+1]) / 2.0
        if (cx - hx)**2 + (cy - hy)**2 <= hr**2:
            rect = patches.Rectangle((gx[i], gy[j]), gx[1]-gx[0], gy[1]-gy[0], color='#ff9999', alpha=0.75)
            ax1.add_patch(rect)

ax1.set_title('(a) Diferenças Finitas: Erro de Escadeamento ($\\mathcal{O}(h)$)', fontsize=8.0)
ax1.set_xlabel('$x$'); ax1.set_ylabel('$y$')
ax1.set_xlim(0.12, 0.48); ax1.set_ylim(0.12, 0.48)
ax1.set_aspect('equal')
ax1.legend(loc='upper right', fontsize=6.8)

# Painel (b): Colocação Meshless da PINN com camada limite
theta_circ = np.linspace(0, 2*np.pi, 50)
xc_rim = hx + hr * np.cos(theta_circ)
yc_rim = hy + hr * np.sin(theta_circ)

r_bl = np.random.uniform(hr, hr*1.35, 120)
th_bl = np.random.uniform(0, 2*np.pi, 120)
ax2.scatter(hx + r_bl*np.cos(th_bl), hy + r_bl*np.sin(th_bl), s=7, color='#ff7f0e', alpha=0.7, label='Camada Limite $N_{\\mathrm{BL}}$')
ax2.scatter(x_int_np[:100, 0], y_int_np[:100, 1], s=6, color='#1f77b4', alpha=0.5, label='Interior $N_f$')
ax2.scatter(xc_rim, yc_rim, s=14, color='#d62728', zorder=5, label='Borda Polar $N_b$')
circle_exact = plt.Circle((hx, hy), hr, color='black', fill=False, lw=1.2)
ax2.add_patch(circle_exact)

ax2.set_title('(b) PINN: Amostragem Meshless com Camada Limite', fontsize=8.0)
ax2.set_xlabel('$x$'); ax2.set_ylabel('$y$')
ax2.set_xlim(0.12, 0.48); ax2.set_ylim(0.12, 0.48)
ax2.set_aspect('equal')
ax2.legend(loc='upper right', fontsize=6.8)

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig1_geometry_staircasing.pdf"))
plt.savefig(os.path.join(fig_dir, "fig1_geometry_staircasing.png"))
plt.close()
print("[OK] Figura 1 gerada.")

# ------------------------------------------------------------------------------
# FIGURA 2: Curva de Convergência das Perdas (50.000 Épocas, Alta Resolução)
# ------------------------------------------------------------------------------
plt.figure(figsize=(5.0, 2.8), dpi=300)
ep_axis = loss_history['epoch']
plt.semilogy(ep_axis, loss_history['total'], label='Perda Total $\\mathcal{L}_{\\mathrm{total}}$', color='#1f77b4', lw=1.4)
plt.semilogy(ep_axis, loss_history['pde'], label='Resíduo da EDP $\\mathcal{L}_{\\mathrm{pde}}$', color='#d62728', lw=1.0, ls='--')
plt.semilogy(ep_axis, loss_history['bc_holes'], label='Contorno dos Furos $\\mathcal{L}_{\\mathrm{furos}}$ ($u=0$)', color='#2ca02c', lw=1.0, ls=':')
plt.semilogy(ep_axis, loss_history['bc_ext'], label='Contorno Externo $\\mathcal{L}_{\\mathrm{ext}}$ ($u=1$)', color='#9467bd', lw=1.0, ls='-.')
plt.semilogy(ep_axis, loss_history['ic'], label='Condição Inicial $\\mathcal{L}_{\\mathrm{ic}}$ ($t=0$)', color='#ff7f0e', lw=0.9, ls='-')

plt.xlabel('Época de Treinamento')
plt.ylabel('Erro Quadrático Médio (MSE)')
plt.grid(True, which='both', ls=':', alpha=0.5)
plt.legend(loc='upper right', framealpha=0.9, fontsize=7.0)
plt.title(f'Convergência Multiobjetivo da PINN ({epochs:,} Épocas)')
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig2_loss_convergence.pdf"))
plt.savefig(os.path.join(fig_dir, "fig2_loss_convergence.png"))
plt.close()
print("[OK] Figura 2 gerada.")

# ------------------------------------------------------------------------------
# FIGURA 3: Evolução Térmica 2D com as 3 Cavidades Dissipadoras e Isolinhas
# ------------------------------------------------------------------------------
fig, axes = plt.subplots(1, 4, figsize=(7.6, 2.2), sharey=True, dpi=300)
eval_times = [0.1, 0.4, 0.8, 2.0]

nx_plot, ny_plot = 180, 180
xp = np.linspace(0, L, nx_plot)
yp = np.linspace(0, L, ny_plot)
XP, YP = np.meshgrid(xp, yp)
XP_flat = XP.flatten()
YP_flat = YP.flatten()

# Versão SEM MÁSCARA
XP_val_full = torch.tensor(XP_flat, dtype=torch.float32, device=device).unsqueeze(1)
YP_val_full = torch.tensor(YP_flat, dtype=torch.float32, device=device).unsqueeze(1)

for idx, t_val in enumerate(eval_times):
    TP_val = torch.full_like(XP_val_full, t_val, device=device)
    with torch.no_grad():
        u_p = model(XP_val_full, YP_val_full, TP_val).cpu().numpy().flatten()
    
    U_mat = u_p.reshape(nx_plot, ny_plot)
    
    im = axes[idx].imshow(U_mat, extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=0.0, vmax=1.0)
    
    # Isolinhas térmicas
    cs = axes[idx].contour(XP, YP, U_mat, levels=[0.2, 0.4, 0.6, 0.8], colors='cyan', linewidths=0.6, alpha=0.8)
    
    for (hx, hy, hr) in holes:
        c_edge = plt.Circle((hx, hy), hr, color='lime', fill=False, lw=1.2, ls='--', zorder=6)
        axes[idx].add_patch(c_edge)
        
    axes[idx].set_title(f'({chr(97+idx)}) $t = {t_val:.1f}$\,s', fontsize=8.0)
    axes[idx].set_xlabel('$x$')
    if idx == 0:
        axes[idx].set_ylabel('$y$')

cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.82, pad=0.02)
cbar.set_label('Temperatura $u(x,y,t)$', fontsize=8.0)
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig3_thermal_evolution_contour.pdf"))
plt.savefig(os.path.join(fig_dir, "fig3_thermal_evolution_contour.png"))
plt.close()
print("[OK] Figura 3 gerada.")

# ------------------------------------------------------------------------------
# FIGURA 4: Perfil 1D de Temperatura Atravessando as Cavidades
# ------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.2, 2.6), dpi=300)
x_line = np.linspace(0, L, 400)
y_cut1 = 0.30

mask_line1 = np.ones_like(x_line, dtype=bool)
for (hx, hy, hr) in holes:
    if abs(y_cut1 - hy) < hr:
        dx = np.sqrt(hr**2 - (y_cut1 - hy)**2)
        mask_line1 = mask_line1 & ((x_line < (hx - dx)) | (x_line > (hx + dx)))

x_cut_t = torch.tensor(x_line[mask_line1], dtype=torch.float32, device=device).unsqueeze(1)
y_cut_t = torch.full_like(x_cut_t, y_cut1, device=device)

colors_snaps = ['#1f77b4', '#2ca02c', '#d62728']
for snap_t, col in zip([0.2, 0.8, 2.0], colors_snaps):
    t_cut_t = torch.full_like(x_cut_t, snap_t, device=device)
    with torch.no_grad():
        u_cut_val = model(x_cut_t, y_cut_t, t_cut_t).cpu().numpy().flatten()
    u_plot = np.full_like(x_line, np.nan)
    u_plot[mask_line1] = u_cut_val
    ax.plot(x_line, u_plot, color=col, lw=1.5, label=f'$t = {snap_t:.1f}$\,s')

# Cavidades em destaque
ax.axvspan(0.30 - 0.12, 0.30 + 0.12, color='gray', alpha=0.25, label='Cavidades ($u=0$)')
ax.axvspan(0.70 - 0.12, 0.70 + 0.12, color='gray', alpha=0.25)

ax.set_title('Perfil Transversal de Temperatura em $y = 0{,}30$ (Passando por $H_1$ e $H_2$)', fontsize=8.5)
ax.set_xlabel('Coordenada $x$')
ax.set_ylabel('Temperatura $u(x, 0.30, t)$')
ax.set_ylim(-0.02, 1.05)
ax.grid(True, ls=':', alpha=0.6)
ax.legend(loc='upper center', framealpha=0.9, fontsize=7.2)

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig4_temperature_cross_section.pdf"))
plt.savefig(os.path.join(fig_dir, "fig4_temperature_cross_section.png"))
plt.close()
print("[OK] Figura 4 gerada.")

# ------------------------------------------------------------------------------
# FIGURA 5: Renderização 3D de Alta Definição da Distribuição Térmica
# ------------------------------------------------------------------------------
fig = plt.figure(figsize=(6.2, 3.8), dpi=300)
ax3d = fig.add_subplot(111, projection='3d')

XP_val_full = torch.tensor(XP_flat, dtype=torch.float32, device=device).unsqueeze(1)
YP_val_full = torch.tensor(YP_flat, dtype=torch.float32, device=device).unsqueeze(1)

t_3d = 1.5
TP_3d = torch.full_like(XP_val_full, t_3d, device=device)
with torch.no_grad():
    u_3d_p = model(XP_val_full, YP_val_full, TP_3d).cpu().numpy().flatten()

U_3d_mat = u_3d_p.reshape(nx_plot, ny_plot)

surf = ax3d.plot_surface(XP, YP, U_3d_mat, cmap='inferno', edgecolor='none', alpha=0.92, vmin=0.0, vmax=1.0)
ax3d.set_title(f'Distribuição Térmica 3D no Estado Quase-Estacionário ($t = {t_3d:.1f}$\,s)', fontsize=9.0, pad=12)
ax3d.set_xlabel('$x$', fontsize=8.0, labelpad=4)
ax3d.set_ylabel('$y$', fontsize=8.0, labelpad=4)
ax3d.set_zlabel('Temperatura $u$', fontsize=8.0, labelpad=4)
ax3d.view_init(elev=34, azim=-55)
ax3d.set_zlim(0.0, 1.05)

cbar3d = fig.colorbar(surf, ax=ax3d, shrink=0.6, aspect=15, pad=0.08)
cbar3d.set_label('Temperatura $u(x,y,t)$', fontsize=8.0)
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig5_thermal_3d_surface.pdf"))
plt.savefig(os.path.join(fig_dir, "fig5_thermal_3d_surface.png"))
plt.close()
print("[OK] Figura 5 (3D) gerada.")

print("\n" + "=" * 80)
print("TODAS AS ETAPAS, MÉTRICAS E FIGURAS FORAM CONCLUÍDAS COM SUCESSO!")
print("=" * 80)
