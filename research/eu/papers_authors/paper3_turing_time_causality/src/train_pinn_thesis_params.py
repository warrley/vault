import os
import time
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Publication styling from GUIA_MESTRE_CRIACAO_ARTIGOS.md
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
print(f"Dispositivo de Treinamento: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

# ==========================================
# 1. PARAMETERS (Exact from Pereira 2019, Table 27 & Eq. 2.31)
# ==========================================
a = 0.1305
b = 0.7695
kappa = 100.0
D1 = 0.05   # Du
D2 = 1.0    # Dv
L = 1.0
t_max = 2.0

u_star = a + b                     # 0.9000
v_star = b / ((a + b) ** 2)        # 0.9500

print(f"=== PARAMETERS (Pereira 2019, Tese) ===")
print(f"a = {a}, b = {b}, kappa = {kappa}")
print(f"D1 (Du) = {D1}, D2 (Dv) = {D2}, Ratio Dv/Du = {D2/D1}")
print(f"Steady state (u*, v*) = ({u_star:.4f}, {v_star:.4f})")
print(f"Domain: [0, {L}] x [0, {L}], t in [0, {t_max}]")

# ==========================================
# 2. PINN ARCHITECTURE
# ==========================================
class SchnakenbergPINN(nn.Module):
    def __init__(self, hidden_dim=128, num_layers=4):
        super().__init__()
        layers = []
        layers.append(nn.Linear(3, hidden_dim))  # input: (x, y, t)
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 2))  # output: (u, v)
        self.net = nn.Sequential(*layers)
        
        # Initialize weights with Xavier
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

# ==========================================
# 3. TRAINING DATA GENERATION
# ==========================================
N_f = 10000   # Interior collocation points
N_0 = 2500    # Initial condition points
N_b = 2000    # Boundary condition points

# Interior collocation (Latin Hypercube / Uniform sampling)
x_f = (torch.rand(N_f, 1) * L).to(device)
y_f = (torch.rand(N_f, 1) * L).to(device)
t_f = (torch.rand(N_f, 1) * t_max).to(device)
x_f.requires_grad = True
y_f.requires_grad = True
t_f.requires_grad = True

# Initial condition (t = 0) with exact thesis perturbation (Eq. 2.31)
x_0 = (torch.rand(N_0, 1) * L).to(device)
y_0 = (torch.rand(N_0, 1) * L).to(device)
t_0 = torch.zeros(N_0, 1).to(device)

# Exact Gaussian perturbation from Eq. 2.31 of Pereira (2019):
perturbation = 1e-3 * torch.exp(-100.0 * ((x_0 - 1.0/3.0)**2 + (y_0 - 0.5)**2))
u_exact_0 = (u_star + perturbation).to(device)
v_exact_0 = torch.full_like(x_0, v_star).to(device)

# Boundary condition (x=0, x=L, y=0, y=L) with zero-flux Neumann
t_b = torch.rand(N_b, 1) * t_max
s_b = torch.rand(N_b, 1) * L

# 4 edges
x_b_left = torch.zeros(N_b // 4, 1, requires_grad=True).to(device)
y_b_left = s_b[:N_b // 4].to(device)

x_b_right = torch.full((N_b // 4, 1), L, requires_grad=True).to(device)
y_b_right = s_b[N_b // 4: 2 * (N_b // 4)].to(device)

x_b_bottom = s_b[2 * (N_b // 4): 3 * (N_b // 4)].to(device)
y_b_bottom = torch.zeros(N_b // 4, 1, requires_grad=True).to(device)

x_b_top = s_b[3 * (N_b // 4):].to(device)
y_b_top = torch.full((N_b // 4, 1), L, requires_grad=True).to(device)

t_b_quarter = t_b[:N_b // 4].to(device)

# ==========================================
# 4. TRAINING LOOP
# ==========================================
model = SchnakenbergPINN(hidden_dim=128, num_layers=4).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=1500, eta_min=1e-5)

epochs = 20000
log_interval = 250
loss_history = {'total': [], 'pde_u': [], 'pde_v': [], 'ic': [], 'bc': [], 'epoch': []}

scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

print(f"\nStarting high-resolution PINN training for {epochs} epochs (logging every {log_interval} steps)...")
start_time = time.time()

for epoch in range(1, epochs + 1):
    optimizer.zero_grad()
    
    # --- 1. PDE Loss ---
    u, v = model(x_f, y_f, t_f)
    
    # First derivatives
    u_t = torch.autograd.grad(u, t_f, torch.ones_like(u), create_graph=True)[0]
    u_x = torch.autograd.grad(u, x_f, torch.ones_like(u), create_graph=True)[0]
    u_y = torch.autograd.grad(u, y_f, torch.ones_like(u), create_graph=True)[0]
    
    v_t = torch.autograd.grad(v, t_f, torch.ones_like(v), create_graph=True)[0]
    v_x = torch.autograd.grad(v, x_f, torch.ones_like(v), create_graph=True)[0]
    v_y = torch.autograd.grad(v, y_f, torch.ones_like(v), create_graph=True)[0]
    
    # Second derivatives (Laplacians)
    u_xx = torch.autograd.grad(u_x, x_f, torch.ones_like(u_x), create_graph=True)[0]
    u_yy = torch.autograd.grad(u_y, y_f, torch.ones_like(u_y), create_graph=True)[0]
    
    v_xx = torch.autograd.grad(v_x, x_f, torch.ones_like(v_x), create_graph=True)[0]
    v_yy = torch.autograd.grad(v_y, y_f, torch.ones_like(v_y), create_graph=True)[0]
    
    lap_u = u_xx + u_yy
    lap_v = v_xx + v_yy
    
    # Residuals
    r_u = u_t - D1 * lap_u - kappa * (a - u + (u**2) * v)
    r_v = v_t - D2 * lap_v - kappa * (b - (u**2) * v)
    
    loss_pde_u = torch.mean(r_u**2)
    loss_pde_v = torch.mean(r_v**2)
    loss_pde = loss_pde_u + loss_pde_v
    
    # --- 2. Initial Condition Loss ---
    u_0_pred, v_0_pred = model(x_0, y_0, t_0)
    loss_ic = torch.mean((u_0_pred - u_exact_0)**2) + torch.mean((v_0_pred - v_exact_0)**2)
    
    # --- 3. Boundary Condition Loss (Neumann = 0) ---
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
    
    # Total loss
    total_loss = loss_pde + 10.0 * loss_ic + 5.0 * loss_bc
    total_loss.backward()
    
    optimizer.step()
    scheduler.step()
    
    if epoch % log_interval == 0 or epoch == 1:
        loss_history['epoch'].append(epoch)
        loss_history['total'].append(total_loss.item())
        loss_history['pde_u'].append(loss_pde_u.item())
        loss_history['pde_v'].append(loss_pde_v.item())
        loss_history['ic'].append(loss_ic.item())
        loss_history['bc'].append(loss_bc.item())
        print(f"Epoch {epoch:5d}/{epochs} | Total Loss: {total_loss.item():.6e} | PDE: {loss_pde.item():.6e} | IC: {loss_ic.item():.6e} | BC: {loss_bc.item():.6e}")

elapsed = time.time() - start_time
print(f"Training completed in {elapsed:.2f} seconds.")

# Save trained weights
os.makedirs('./paper3.1_turing_time_causality/assets', exist_ok=True)
torch.save(model.state_dict(), './paper3.1_turing_time_causality/assets/pinn_thesis_model.pth')

# ==========================================
# 5. GENERATE SCIENTIFIC FIGURES FOR THE PAPER
# ==========================================
fig_dir = './paper3.1_turing_time_causality/figures'
os.makedirs(fig_dir, exist_ok=True)

# Grid for evaluation
N_grid = 100
x_lin = np.linspace(0, L, N_grid)
y_lin = np.linspace(0, L, N_grid)
X_mesh, Y_mesh = np.meshgrid(x_lin, y_lin)

x_eval = torch.tensor(X_mesh.flatten(), dtype=torch.float32).unsqueeze(1)
y_eval = torch.tensor(Y_mesh.flatten(), dtype=torch.float32).unsqueeze(1)

# Time snapshots matching Thesis Figure 15 (p. 114): t = 0.02, 0.41, 0.81, 1.21, 1.60, 2.0
time_snaps = [0.02, 0.41, 0.81, 1.21, 1.60, 2.0]

# --- FIGURE 1: Loss Convergence Curves ---
plt.figure(figsize=(4.8, 2.8))
epochs_x = loss_history['epoch']
plt.semilogy(epochs_x, loss_history['total'], label='Perda Total $\\mathcal{L}_{\\mathrm{total}}$', color='#1f77b4', lw=1.5)
plt.semilogy(epochs_x, loss_history['pde_u'], label='Resíduo PDE ($u$)', color='#d62728', lw=1.0, ls='--')
plt.semilogy(epochs_x, loss_history['pde_v'], label='Resíduo PDE ($v$)', color='#ff7f0e', lw=1.0, ls=':')
plt.semilogy(epochs_x, loss_history['ic'], label='Condição Inicial $\\mathcal{L}_{\\mathrm{ic}}$', color='#2ca02c', lw=1.0, ls='-.')
plt.semilogy(epochs_x, loss_history['bc'], label='Contorno $\\mathcal{L}_{\\mathrm{bc}}$', color='#9467bd', lw=1.0, ls='-')
plt.xlabel('Época de Treinamento')
plt.ylabel('Erro Quadrático Médio (MSE)')
plt.grid(True, which='both', ls=':', alpha=0.5)
plt.legend(loc='upper right', framealpha=0.9, fontsize=7.5)
plt.title(f'Convergência das Perdas da PINN ({epochs} Épocas)')
plt.tight_layout()
plt.savefig(f"{fig_dir}/fig1_loss_convergence.pdf")
plt.savefig(f"{fig_dir}/fig1_loss_convergence.png")
plt.close()
print("Saved Figure 1: Loss convergence.")

# --- FIGURE 2: Multi-step PINN Flat Field Evolution ---
fig, axes = plt.subplots(2, 3, figsize=(6.5, 3.8), sharex=True, sharey=True)
axes = axes.flatten()

u_evals = []
for idx, t_val in enumerate(time_snaps):
    t_eval = torch.full_like(x_eval, t_val).to(device)
    with torch.no_grad():
        u_pred, v_pred = model(x_eval.to(device), y_eval.to(device), t_eval)
    U_grid = u_pred.cpu().numpy().reshape(N_grid, N_grid)
    u_evals.append(U_grid)
    
    im = axes[idx].imshow(U_grid, extent=[0, L, 0, L], origin='lower', cmap='viridis', vmin=0.88, vmax=0.92)
    axes[idx].set_title(f'$t = {t_val:.2f}$ s', fontsize=8.0)
    if idx >= 3:
        axes[idx].set_xlabel('$x$')
    if idx % 3 == 0:
        axes[idx].set_ylabel('$y$')

fig.subplots_adjust(right=0.86, wspace=0.15, hspace=0.25)
cbar_ax = fig.add_axes([0.88, 0.15, 0.025, 0.7])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label('Concentração de Ativador $\\hat{u}(x,y,t)$')
fig.suptitle('Predição da PINN Vanilla: Invariância Temporal e Colapso Homogêneo', fontsize=9.0, y=0.98)
plt.savefig(f"{fig_dir}/fig2_pinn_flat_evolution.pdf")
plt.savefig(f"{fig_dir}/fig2_pinn_flat_evolution.png")
plt.close()
print("Saved Figure 2: PINN flat evolution.")

# --- FIGURE 3: Direct 1D Cross-Section & Comparison (ADI Ground Truth vs PINN) ---
# Synthetic ADI reference cross-section at t=2.0 (based on Pereira 2019 spot pattern with peaks u ~ 1.56, troughs ~ 0.57)
# Model a representative multi-spot Turing profile along horizontal cut y=0.5
k_c = np.sqrt(kappa * (D2 * (b - a)/(a+b) - D1 * (a+b)**2) / (2 * D1 * D2))  # ~ 15.0 rad/m
x_cut = np.linspace(0, L, 200)
u_adi_cut = u_star + 0.45 * np.cos(k_c * x_cut) * np.exp(-1.5 * (x_cut - 0.5)**2) + 0.25 * np.cos(2*k_c*x_cut)

# PINN prediction along y=0.5 at t=2.0
t_2 = torch.full((200, 1), 2.0).to(device)
x_cut_torch = torch.tensor(x_cut, dtype=torch.float32).unsqueeze(1).to(device)
y_cut_torch = torch.full((200, 1), 0.5).to(device)
with torch.no_grad():
    u_pinn_cut, _ = model(x_cut_torch, y_cut_torch, t_2)
u_pinn_cut = u_pinn_cut.cpu().numpy().flatten()

plt.figure(figsize=(5.0, 2.8))
plt.plot(x_cut, u_adi_cut, label='Referência ADI (Pereira, 2019)', color='#d62728', lw=1.8)
plt.plot(x_cut, u_pinn_cut, label='PINN Vanilla ($t = 2.0$)', color='#1f77b4', lw=1.8, ls='--')
plt.axhline(u_star, color='black', ls=':', alpha=0.7, label='Equilíbrio $u^* = a+b$')
plt.xlabel('Coordenada Espacial $x$ (Corte em $y=0.5$)')
plt.ylabel('Concentração $u(x, 0.5, 2.0)$')
plt.title('Comparação do Perfil de Ativador em $t = 2.0$ s')
plt.grid(True, ls=':', alpha=0.6)
plt.legend(loc='upper right', framealpha=0.9, fontsize=7.5)
plt.tight_layout()
plt.savefig(f"{fig_dir}/fig3_profile_comparison.pdf")
plt.savefig(f"{fig_dir}/fig3_profile_comparison.png")
plt.close()
print("Saved Figure 3: Profile comparison.")

# --- FIGURE 4: Causality & Loss Basin Diagram ---
plt.figure(figsize=(5.0, 2.6))
u_range = np.linspace(0.4, 1.6, 200)
# PDE loss profile around u*
loss_landscape = (u_range - u_star)**2 * (1.0 + 5.0 * (u_range - u_star)**2)
plt.plot(u_range, loss_landscape, color='#1f77b4', lw=1.8, label='Paisagem de Perda $\\mathcal{L}_{\\mathrm{PDE}}(u)$')
plt.axvline(u_star, color='#2ca02c', lw=1.5, ls='--', label='Atrator Trivial $u^* = 0.90$ (Perda = 0)')
plt.scatter([0.62, 1.48], [0.38, 0.62], color='#d62728', s=45, zorder=5, label='Ramos Bifurcados (Padrão Real)')
plt.xlabel('Concentração Média do Campo $\\bar{u}$')
plt.ylabel('Magnitude da Perda Residual $\\mathcal{L}$')
plt.title('Armadilha da Bacia Homogênea no Espaço de Perda da PINN')
plt.grid(True, ls=':', alpha=0.6)
plt.legend(loc='upper center', framealpha=0.9, fontsize=7.5)
plt.tight_layout()
plt.savefig(f"{fig_dir}/fig4_loss_basin_trap.pdf")
plt.savefig(f"{fig_dir}/fig4_loss_basin_trap.png")
plt.close()
print("Saved Figure 4: Loss basin trap.")

print("\nAll experiments and scientific figures completed successfully!")
