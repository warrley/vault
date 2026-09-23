#!/usr/bin/env python3
"""
train_real_inverse_pinn.py
==========================
Inverse Physics-Informed Neural Network (PINN) for parameter discovery and
hidden state reconstruction in the 2D Schnakenberg Turing system.

Ground-Truth Benchmark: Exact parameters from Ricardo Pereira (2019, Table 27):
  - a = 0.1305, b = 0.7695, kappa = 100.0, Du = 0.05, Dv = 1.00
  - Domain: [0, 1] x [0, 1], t in [0, 2.0] s
  - Initial condition: Gaussian perturbation (Eq. 2.31)
  - Boundary: Zero-flux Neumann (Eq. 2.32)

CUDA GPU Accelerated.
"""

import os
import sys
import time
import numpy as np
import scipy.fft as fft
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# Configuration and Styling
# -----------------------------------------------------------------------------
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("="*78)
print(f"  DEVICE: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
print("="*78)

torch.manual_seed(42)
np.random.seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed(42)

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

out_dir = os.path.dirname(os.path.abspath(__file__))
fig_dir = os.path.join(out_dir, "figures")
models_dir = os.path.join(out_dir, "models")
os.makedirs(fig_dir, exist_ok=True)
os.makedirs(models_dir, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. GROUND TRUTH NUMERICAL SIMULATION (HIGH RESOLUTION FDM / SPECTRAL SPLITTING)
# -----------------------------------------------------------------------------
print("\n[STEP 1/4] Generating Ground-Truth Forward Solution via Spectral-FDM...")

a = 0.1305
b = 0.7695
kappa_true = 100.0
Du_true = 0.05
Dv_true = 1.00
L = 1.0
T_max = 2.0

u_star = a + b              # 0.9000
v_star = b / (u_star ** 2) # 0.9500

N_sim = 128
x_sim = np.linspace(0, L, N_sim)
y_sim = np.linspace(0, L, N_sim)
X_sim, Y_sim = np.meshgrid(x_sim, y_sim)

kx = np.arange(N_sim)
ky = np.arange(N_sim)
KX, KY = np.meshgrid(kx, ky)
Lap_eig = - (np.pi * KX / L)**2 - (np.pi * KY / L)**2

# Gaussian perturbation from thesis (Eq. 2.31)
u_init = u_star + 1e-3 * np.exp(-100.0 * ((X_sim - 1.0/3.0)**2 + (Y_sim - 0.5)**2))
v_init = np.full_like(u_init, v_star)

dt = 1e-4
n_steps = int(T_max / dt)

def reaction_rk4(u_curr, v_curr, dt_sub):
    def f(u_, v_):
        return kappa_true * (a - u_ + (u_**2) * v_), kappa_true * (b - (u_**2) * v_)
    k1u, k1v = f(u_curr, v_curr)
    k2u, k2v = f(u_curr + 0.5*dt_sub*k1u, v_curr + 0.5*dt_sub*k1v)
    k3u, k3v = f(u_curr + 0.5*dt_sub*k2u, v_curr + 0.5*dt_sub*k2v)
    k4u, k4v = f(u_curr + dt_sub*k3u, v_curr + dt_sub*k3v)
    return u_curr + (dt_sub/6.0)*(k1u + 2*k2u + 2*k3u + k4u), v_curr + (dt_sub/6.0)*(k1v + 2*k2v + 2*k3v + k4v)

def diffuse_dct(u_curr, v_curr, dt_sub):
    u_hat = fft.dctn(u_curr, type=2, norm='ortho') * np.exp(Du_true * Lap_eig * dt_sub)
    v_hat = fft.dctn(v_curr, type=2, norm='ortho') * np.exp(Dv_true * Lap_eig * dt_sub)
    return fft.idctn(u_hat, type=2, norm='ortho'), fft.idctn(v_hat, type=2, norm='ortho')

target_snapshots = [0.02, 0.41, 0.81, 1.21, 1.60, 2.00]
target_idx = 0
snapshots_u = {}
snapshots_v = {}

u_c = u_init.copy()
v_c = v_init.copy()
t_c = 0.0

start_fwd = time.time()
for step in range(1, n_steps + 1):
    u_c, v_c = diffuse_dct(u_c, v_c, dt*0.5)
    u_c, v_c = reaction_rk4(u_c, v_c, dt)
    u_c, v_c = diffuse_dct(u_c, v_c, dt*0.5)
    t_c += dt
    
    if target_idx < len(target_snapshots) and abs(t_c - target_snapshots[target_idx]) < dt*0.5:
        ts = target_snapshots[target_idx]
        snapshots_u[f'u_{ts:.2f}'] = u_c.copy()
        snapshots_v[f'v_{ts:.2f}'] = v_c.copy()
        print(f"  --> Saved snapshot t = {ts:.2f}s | u: [{u_c.min():.3f}, {u_c.max():.3f}] | v: [{v_c.min():.3f}, {v_c.max():.3f}]")
        target_idx += 1

print(f"  [OK] Forward solver finished in {time.time()-start_fwd:.2f} s.")

# Save npz
np.savez(
    os.path.join(out_dir, "exact_thesis_turing_solution.npz"),
    x=x_sim, y=y_sim, t_eval=np.array(target_snapshots),
    **snapshots_u, **snapshots_v
)

# -----------------------------------------------------------------------------
# 2. INVERSE PINN ARCHITECTURE
# -----------------------------------------------------------------------------
class InverseSchnakenbergPINN(nn.Module):
    def __init__(self, hidden_dim=64, num_layers=4):
        super().__init__()
        layers = []
        layers.append(nn.Linear(3, hidden_dim))
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 2))
        self.net = nn.Sequential(*layers)
        
        # Trainable log-parameters (uncalibrated initial guesses):
        # Du: real 0.05 -> guess 0.15 (+200%)
        # Dv: real 1.00 -> guess 0.50 (-50%)
        # kappa: real 100.0 -> guess 60.0 (-40%)
        self.log_Du = nn.Parameter(torch.tensor(np.log(0.15), dtype=torch.float32))
        self.log_Dv = nn.Parameter(torch.tensor(np.log(0.50), dtype=torch.float32))
        self.log_kappa = nn.Parameter(torch.tensor(np.log(60.0), dtype=torch.float32))
        
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x, y, t):
        coords = torch.cat([x, y, t], dim=1)
        out = self.net(coords)
        return out[:, 0:1], out[:, 1:2]

    @property
    def Du(self): return torch.exp(self.log_Du)
    @property
    def Dv(self): return torch.exp(self.log_Dv)
    @property
    def kappa(self): return torch.exp(self.log_kappa)

# -----------------------------------------------------------------------------
# 3. TRAINING ENGINE
# -----------------------------------------------------------------------------
def train_inverse_pinn(noise_level=0.0, max_epochs=6000, lr=3e-3, log_every=500):
    print("\n" + "-"*78)
    print(f"  TRAINING INVERSE PINN (Noise: {noise_level*100:.1f}%, Max Epochs: {max_epochs})")
    print("-"*78)
    
    # Sparse observations of activator u ONLY from snapshots t in {0.41, 0.81, 2.00}
    obs_times = [0.41, 0.81, 2.00]
    n_pts_per_snap = 1000
    
    x_obs, y_obs, t_obs, u_obs = [], [], [], []
    for ts in obs_times:
        u_field = snapshots_u[f'u_{ts:.2f}']
        idx_x = np.random.choice(N_sim, size=n_pts_per_snap, replace=True)
        idx_y = np.random.choice(N_sim, size=n_pts_per_snap, replace=True)
        
        for ix, iy in zip(idx_x, idx_y):
            u_val = u_field[iy, ix]
            if noise_level > 0:
                u_val = u_val + np.random.normal(0, noise_level * np.std(u_field))
            x_obs.append(x_sim[ix])
            y_obs.append(y_sim[iy])
            t_obs.append(ts)
            u_obs.append(u_val)

    xd = torch.tensor(x_obs, dtype=torch.float32, device=device).view(-1, 1)
    yd = torch.tensor(y_obs, dtype=torch.float32, device=device).view(-1, 1)
    td = torch.tensor(t_obs, dtype=torch.float32, device=device).view(-1, 1)
    ud = torch.tensor(u_obs, dtype=torch.float32, device=device).view(-1, 1)
    
    model = InverseSchnakenbergPINN(hidden_dim=64, num_layers=4).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max_epochs, eta_min=1e-5)
    
    history = {
        'epoch': [], 'total_loss': [], 'loss_data': [], 'loss_pde': [],
        'Du': [], 'Dv': [], 'kappa': [],
        'err_Du': [], 'err_Dv': [], 'err_kappa': []
    }
    
    N_f = 2500
    N_b = 800
    
    t_start = time.time()
    for epoch in range(1, max_epochs + 1):
        optimizer.zero_grad()
        
        # 1. Observation Data Loss (ACTIVATOR u ONLY)
        u_pred, _ = model(xd, yd, td)
        loss_data = torch.mean((u_pred - ud)**2)
        
        # 2. PDE Residual Collocation
        x_f = torch.rand(N_f, 1, device=device, requires_grad=True)
        y_f = torch.rand(N_f, 1, device=device, requires_grad=True)
        t_f = (torch.rand(N_f, 1, device=device) * T_max).requires_grad_(True)
        
        u, v = model(x_f, y_f, t_f)
        
        u_x = torch.autograd.grad(u, x_f, grad_outputs=torch.ones_like(u), create_graph=True, retain_graph=True)[0]
        u_y = torch.autograd.grad(u, y_f, grad_outputs=torch.ones_like(u), create_graph=True, retain_graph=True)[0]
        u_t = torch.autograd.grad(u, t_f, grad_outputs=torch.ones_like(u), create_graph=True, retain_graph=True)[0]
        
        v_x = torch.autograd.grad(v, x_f, grad_outputs=torch.ones_like(v), create_graph=True, retain_graph=True)[0]
        v_y = torch.autograd.grad(v, y_f, grad_outputs=torch.ones_like(v), create_graph=True, retain_graph=True)[0]
        v_t = torch.autograd.grad(v, t_f, grad_outputs=torch.ones_like(v), create_graph=True, retain_graph=True)[0]
        
        u_xx = torch.autograd.grad(u_x, x_f, grad_outputs=torch.ones_like(u_x), create_graph=True, retain_graph=True)[0]
        u_yy = torch.autograd.grad(u_y, y_f, grad_outputs=torch.ones_like(u_y), create_graph=True, retain_graph=True)[0]
        
        v_xx = torch.autograd.grad(v_x, x_f, grad_outputs=torch.ones_like(v_x), create_graph=True, retain_graph=True)[0]
        v_yy = torch.autograd.grad(v_y, y_f, grad_outputs=torch.ones_like(v_y), create_graph=True, retain_graph=True)[0]
        
        Du_curr = model.Du
        Dv_curr = model.Dv
        k_curr = model.kappa
        
        r_u = u_t - Du_curr * (u_xx + u_yy) - k_curr * (a - u + (u**2) * v)
        r_v = v_t - Dv_curr * (v_xx + v_yy) - k_curr * (b - (u**2) * v)
        loss_pde = torch.mean(r_u**2) + torch.mean(r_v**2)
        
        # 3. Neumann Boundary Conditions
        s_b = torch.rand(N_b // 4, 1, device=device)
        tb_sub = torch.rand(N_b // 4, 1, device=device) * T_max
        
        x_left = torch.zeros(N_b // 4, 1, device=device, requires_grad=True)
        x_right = torch.ones(N_b // 4, 1, device=device, requires_grad=True)
        u_l, _ = model(x_left, s_b, tb_sub)
        u_r, _ = model(x_right, s_b, tb_sub)
        ul_x = torch.autograd.grad(u_l, x_left, grad_outputs=torch.ones_like(u_l), create_graph=True, retain_graph=True)[0]
        ur_x = torch.autograd.grad(u_r, x_right, grad_outputs=torch.ones_like(u_r), create_graph=True, retain_graph=True)[0]
        
        y_bot = torch.zeros(N_b // 4, 1, device=device, requires_grad=True)
        y_top = torch.ones(N_b // 4, 1, device=device, requires_grad=True)
        u_b, _ = model(s_b, y_bot, tb_sub)
        u_t_b, _ = model(s_b, y_top, tb_sub)
        ub_y = torch.autograd.grad(u_b, y_bot, grad_outputs=torch.ones_like(u_b), create_graph=True, retain_graph=True)[0]
        ut_y = torch.autograd.grad(u_t_b, y_top, grad_outputs=torch.ones_like(u_t_b), create_graph=True, retain_graph=True)[0]
        
        loss_bc = torch.mean(ul_x**2) + torch.mean(ur_x**2) + torch.mean(ub_y**2) + torch.mean(ut_y**2)
        
        total_loss = 50.0 * loss_data + 1.0 * loss_pde + 1.0 * loss_bc
        total_loss.backward()
        optimizer.step()
        scheduler.step()
        
        Du_val = Du_curr.item()
        Dv_val = Dv_curr.item()
        k_val = k_curr.item()
        
        err_Du_e = abs(Du_val - Du_true) / Du_true * 100.0
        err_Dv_e = abs(Dv_val - Dv_true) / Dv_true * 100.0
        err_k_e = abs(k_val - kappa_true) / kappa_true * 100.0
        
        if epoch % 25 == 0 or epoch == 1:
            history['epoch'].append(epoch)
            history['total_loss'].append(total_loss.item())
            history['loss_data'].append(loss_data.item())
            history['loss_pde'].append(loss_pde.item())
            history['Du'].append(Du_val)
            history['Dv'].append(Dv_val)
            history['kappa'].append(k_val)
            history['err_Du'].append(err_Du_e)
            history['err_Dv'].append(err_Dv_e)
            history['err_kappa'].append(err_k_e)
            
        if epoch % log_every == 0 or epoch == 1:
            elapsed = time.time() - t_start
            print(f"  Ep {epoch:4d}/{max_epochs} [{elapsed:4.1f}s] | Loss: {total_loss.item():.3e} (Data: {loss_data.item():.3e}, PDE: {loss_pde.item():.3e}) | Du: {Du_val:.5f} ({err_Du_e:4.2f}%) | Dv: {Dv_val:.5f} ({err_Dv_e:4.2f}%) | kappa: {k_val:5.2f} ({err_k_e:4.2f}%)")
            
    # Evaluation at t = 2.0 s
    model.eval()
    with torch.no_grad():
        x_eval = torch.tensor(X_sim.flatten(), dtype=torch.float32, device=device).view(-1, 1)
        y_eval = torch.tensor(Y_sim.flatten(), dtype=torch.float32, device=device).view(-1, 1)
        t_eval = torch.full_like(x_eval, 2.0)
        
        u_rec, v_rec = model(x_eval, y_eval, t_eval)
        u_rec_grid = u_rec.cpu().numpy().reshape(N_sim, N_sim)
        v_rec_grid = v_rec.cpu().numpy().reshape(N_sim, N_sim)
        
    v_true_final = snapshots_v['v_2.00']
    u_true_final = snapshots_u['u_2.00']
    
    rel_l2_v = np.linalg.norm(v_rec_grid - v_true_final) / np.linalg.norm(v_true_final)
    rel_l2_u = np.linalg.norm(u_rec_grid - u_true_final) / np.linalg.norm(u_true_final)
    
    Du_fin = model.Du.item()
    Dv_fin = model.Dv.item()
    k_fin = model.kappa.item()
    
    err_Du = abs(Du_fin - Du_true) / Du_true * 100.0
    err_Dv = abs(Dv_fin - Dv_true) / Dv_true * 100.0
    err_k = abs(k_fin - kappa_true) / kappa_true * 100.0
    
    print(f"\n  >>> EXPERIMENT COMPLETE in {time.time()-t_start:.2f}s:")
    print(f"      Du:    Identified = {Du_fin:.5f} | Ground-Truth = {Du_true:.4f} | Relative Error = {err_Du:.3f}%")
    print(f"      Dv:    Identified = {Dv_fin:.5f} | Ground-Truth = {Dv_true:.4f} | Relative Error = {err_Dv:.3f}%")
    print(f"      kappa: Identified = {k_fin:.3f} | Ground-Truth = {kappa_true:.2f} | Relative Error = {err_k:.3f}%")
    print(f"      Hidden Inhibitor Reconstruction (L2 Relative Error) = {rel_l2_v*100:.3f}%")
    
    return {
        'model': model,
        'history': history,
        'Du': Du_fin, 'Dv': Dv_fin, 'kappa': k_fin,
        'err_Du': err_Du, 'err_Dv': err_Dv, 'err_kappa': err_k,
        'rel_l2_v': rel_l2_v, 'rel_l2_u': rel_l2_u,
        'u_rec': u_rec_grid, 'v_rec': v_rec_grid
    }

# -----------------------------------------------------------------------------
# 4. EXECUTION
# -----------------------------------------------------------------------------
print("\n[STEP 2/4] Running Clean Experiment (Ground-Truth Identification)...")
res_clean = train_inverse_pinn(noise_level=0.0, max_epochs=6000, lr=3e-3, log_every=500)
torch.save(res_clean['model'].state_dict(), os.path.join(models_dir, "clean_inverse_pinn.pth"))

print("\n[STEP 3/4] Running Noise Robustness Campaign...")
noise_levels = [0.01, 0.02, 0.05, 0.10]
noise_results = [res_clean]

for nl in noise_levels:
    res_nl = train_inverse_pinn(noise_level=nl, max_epochs=4000, lr=3e-3, log_every=1000)
    noise_results.append(res_nl)

# -----------------------------------------------------------------------------
# 5. GENERATING PUBLICATION FIGURES FROM REAL EXPERIMENTAL DATA
# -----------------------------------------------------------------------------
print("\n[STEP 4/4] Generating Publication Figures & Verification Plots...")

# --- FIGURA 1: Arquitetura PINN Inversa ---
fig, ax = plt.subplots(figsize=(7.0, 2.4), dpi=300)
ax.axis('off')

bbox_obs = dict(boxstyle="round,pad=0.4", fc="#e1f5fe", ec="#0288d1", lw=1.5)
bbox_net = dict(boxstyle="round,pad=0.4", fc="#ede7f6", ec="#512da8", lw=1.5)
bbox_pde = dict(boxstyle="round,pad=0.4", fc="#e8f5e9", ec="#388e3c", lw=1.5)
bbox_out = dict(boxstyle="round,pad=0.4", fc="#fff3e0", ec="#f57c00", lw=1.5)

ax.text(0.12, 0.50, "Medições Esparsas\nAtivador $u(x, y, t)$\n(Snapshots $t \\in \\{0.41, 0.81, 2.0\\}$)", ha="center", va="center", bbox=bbox_obs, fontsize=7.5)
ax.text(0.40, 0.50, "Rede Neural MLP\n$(x, y, t) \\to (\\hat{u}, \\hat{v})$\n(Ativação $\\tanh$)", ha="center", va="center", bbox=bbox_net, fontsize=7.8)
ax.text(0.68, 0.72, "Resíduos da EDP de Turing\n$\\mathcal{R}_u(u, v, \\hat{D}_u, \\hat{\\kappa}) = 0$\n$\\mathcal{R}_v(u, v, \\hat{D}_v, \\hat{\\kappa}) = 0$", ha="center", va="center", bbox=bbox_pde, fontsize=7.5)
ax.text(0.68, 0.28, "Descoberta de Parâmetros\n$\\hat{D}_u \\to D_u, \\; \\hat{D}_v \\to D_v$\n$\\hat{\\kappa} \\to \\kappa$ (Treináveis)", ha="center", va="center", bbox=bbox_out, fontsize=7.5)
ax.text(0.92, 0.50, "Reconstrução do\nEstado Oculto\nInibidor $v(x,y,t)$\n(Sem Dados de $v$!)", ha="center", va="center", bbox=bbox_obs, fontsize=7.8)

ax.annotate("", xy=(0.26, 0.50), xytext=(0.20, 0.50), arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))
ax.annotate("", xy=(0.54, 0.65), xytext=(0.48, 0.55), arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))
ax.annotate("", xy=(0.54, 0.35), xytext=(0.48, 0.45), arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))
ax.annotate("", xy=(0.82, 0.50), xytext=(0.76, 0.50), arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))

ax.set_xlim(0, 1.0)
ax.set_ylim(0.1, 0.9)
plt.title(r"Arquitetura da PINN Inversa: Identificação de Parâmetros e Descoberta de Estados Ocultos", fontsize=8.5, y=0.98)
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig1_inverse_pinn_architecture.pdf"))
plt.savefig(os.path.join(fig_dir, "fig1_inverse_pinn_architecture.png"))
plt.close()

# --- FIGURA 2: Trajetória Real de Convergência dos Parâmetros ---
hist = res_clean['history']
epochs_arr = hist['epoch']

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(7.2, 2.3), dpi=300)

ax1.plot(epochs_arr, hist['Du'], color='#1f77b4', lw=1.8, label=r'Estimado $\hat{D}_u$')
ax1.axhline(Du_true, color='black', lw=1.2, ls='--', label=f'Real $D_u = {Du_true}$')
ax1.set_title(r'(a) Difusividade Ativador $\hat{D}_u$', fontsize=8.0)
ax1.set_xlabel('Época'); ax1.set_ylabel(r'Valor de $D_u$')
ax1.grid(True, ls=':', alpha=0.6)
ax1.legend(loc='upper right', fontsize=7.0)

ax2.plot(epochs_arr, hist['Dv'], color='#2ca02c', lw=1.8, label=r'Estimado $\hat{D}_v$')
ax2.axhline(Dv_true, color='black', lw=1.2, ls='--', label=f'Real $D_v = {Dv_true}$')
ax2.set_title(r'(b) Difusividade Inibidor $\hat{D}_v$', fontsize=8.0)
ax2.set_xlabel('Época'); ax2.set_ylabel(r'Valor de $D_v$')
ax2.grid(True, ls=':', alpha=0.6)
ax2.legend(loc='lower right', fontsize=7.0)

ax3.plot(epochs_arr, hist['kappa'], color='#d62728', lw=1.8, label=r'Estimado $\hat{\kappa}$')
ax3.axhline(kappa_true, color='black', lw=1.2, ls='--', label=f'Real $\\kappa = {kappa_true}$')
ax3.set_title(r'(c) Taxa Cinética $\hat{\kappa}$', fontsize=8.0)
ax3.set_xlabel('Época'); ax3.set_ylabel(r'Valor de $\kappa$')
ax3.grid(True, ls=':', alpha=0.6)
ax3.legend(loc='lower right', fontsize=7.0)

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig2_parameter_convergence.pdf"))
plt.savefig(os.path.join(fig_dir, "fig2_parameter_convergence.png"))
plt.close()

# --- FIGURA 3: Reconstrução Real do Inibidor Oculto v(x, y, 2.0) ---
v_exact_2 = snapshots_v['v_2.00']
v_pinn_2 = res_clean['v_rec']
err_v_map = np.abs(v_pinn_2 - v_exact_2)

fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), dpi=300)

im0 = axes[0].imshow(v_exact_2, extent=[0, 1, 0, 1], origin='lower', cmap='viridis')
axes[0].set_title(r'(a) Inibidor Exato $v_{\mathrm{ref}}$ ($t=2{,}0$\,s)', fontsize=8.0)
axes[0].set_xlabel('$x$'); axes[0].set_ylabel('$y$')
fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

im1 = axes[1].imshow(v_pinn_2, extent=[0, 1, 0, 1], origin='lower', cmap='viridis')
axes[1].set_title(r'(b) Reconstrução PINN Inversa $\hat{v}$', fontsize=8.0)
axes[1].set_xlabel('$x$'); axes[1].set_ylabel('$y$')
fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

im2 = axes[2].imshow(err_v_map, extent=[0, 1, 0, 1], origin='lower', cmap='magma')
axes[2].set_title(r'(c) Erro Absoluto $|\hat{v} - v_{\mathrm{ref}}|$', fontsize=8.0)
axes[2].set_xlabel('$x$'); axes[2].set_ylabel('$y$')
fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig3_hidden_state_reconstruction.pdf"))
plt.savefig(os.path.join(fig_dir, "fig3_hidden_state_reconstruction.png"))
plt.close()

# --- FIGURA 4: Robustez Frente a Ruído Experimental Real ---
all_noise_pcts = [0.0, 1.0, 2.0, 5.0, 10.0]
err_Du_list = [r['err_Du'] for r in noise_results]
err_Dv_list = [r['err_Dv'] for r in noise_results]
err_k_list = [r['err_kappa'] for r in noise_results]

plt.figure(figsize=(5.0, 2.5), dpi=300)
plt.plot(all_noise_pcts, err_Du_list, marker='o', color='#1f77b4', lw=1.5, label=r'Erro $\hat{D}_u$ (%)')
plt.plot(all_noise_pcts, err_Dv_list, marker='s', color='#2ca02c', lw=1.5, label=r'Erro $\hat{D}_v$ (%)')
plt.plot(all_noise_pcts, err_k_list, marker='^', color='#d62728', lw=1.5, label=r'Erro $\hat{\kappa}$ (%)')
plt.xlabel('Nível de Ruído Gaussiano Adicionado (%)')
plt.ylabel('Erro Relativo de Identificação (%)')
plt.title('Robustez da PINN Inversa a Ruídos Experimentais')
plt.grid(True, ls=':', alpha=0.6)
plt.legend(loc='upper left', framealpha=0.9, fontsize=7.5)
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, "fig4_noise_robustness.pdf"))
plt.savefig(os.path.join(fig_dir, "fig4_noise_robustness.png"))
plt.close()

# Print Table Results
print("\n" + "="*85)
print("  FINAL SCIENTIFIC RESULTS TABLE (GROUND-TRUTH BENCHMARK)")
print("="*85)
print(f"{'Ruído (%)':<10} | {'Du (est)':<10} | {'Dv (est)':<10} | {'kappa (est)':<12} | {'Erro Médio (%)':<16} | {'L2 Err v (%)':<12}")
print("-"*85)
for nl, r in zip(all_noise_pcts, noise_results):
    mean_err = (r['err_Du'] + r['err_Dv'] + r['err_kappa']) / 3.0
    print(f"{nl:<10.1f} | {r['Du']:<10.5f} | {r['Dv']:<10.5f} | {r['kappa']:<12.3f} | {mean_err:<16.2f} | {r['rel_l2_v']*100:<12.2f}")
print("="*85)
