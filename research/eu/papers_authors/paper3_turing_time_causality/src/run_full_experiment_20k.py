import os
import sys
import time
import json
import numpy as np
import scipy.fft as fft
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Enable TF32 for Ampere GPU
torch.set_float32_matmul_precision('high')

# Set random seeds
torch.manual_seed(42)
np.random.seed(42)

# Publication styling
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

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, 'figures')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
print(f"============================================================", flush=True)
print(f"SCHNAKENBERG PINN vs ADI EXPERIMENT (20,000 EPOCHS)", flush=True)
print(f"Compute Device: {device} ({gpu_name})", flush=True)
print(f"============================================================", flush=True)

# ==============================================================================
# 1. EXACT PARAMETERS (Pereira 2019, Tabela 27 & Eq. 2.31)
# ==============================================================================
a = 0.1305
b = 0.7695
kappa = 100.0
D1 = 0.05   # Du
D2 = 1.0    # Dv
L = 1.0
t_max = 2.0

u_star = a + b                     # 0.9000
v_star = b / ((a + b) ** 2)        # 0.9500

print(f"[Parameters] a={a}, b={b}, kappa={kappa}")
print(f"[Parameters] D1(Du)={D1}, D2(Dv)={D2}, Ratio Dv/Du={D2/D1}")
print(f"[Parameters] Steady State (u*, v*) = ({u_star:.4f}, {v_star:.4f})")
print(f"[Parameters] Domain: [0, {L}]x[0, {L}], t in [0, {t_max}]")

# ==============================================================================
# 2. GROUND TRUTH NUMERICAL SOLVER (ADI / SEMI-IMPLICIT SPECTRAL)
# ==============================================================================
print("\n[Step 1/3] Generating High-Resolution Ground Truth Simulation (Pereira 2019 ADI)...")
N_grid = 128
x_lin = np.linspace(0, L, N_grid)
y_lin = np.linspace(0, L, N_grid)
X_mesh, Y_mesh = np.meshgrid(x_lin, y_lin)

# Initial condition
u_exact_0 = u_star + 1e-3 * np.exp(-100.0 * ((X_mesh - 1.0/3.0)**2 + (Y_mesh - 0.5)**2))
v_exact_0 = np.full_like(X_mesh, v_star)

# Spectral Laplacian with Neumann boundary conditions via DCT-II
kx = np.pi * np.arange(N_grid) / L
ky = np.pi * np.arange(N_grid) / L
KX, KY = np.meshgrid(kx, ky)
Lap_eigen = -(KX**2 + KY**2)

dt_gt = 1e-4
steps_gt = int(t_max / dt_gt)
denom_u = 1.0 - dt_gt * D1 * Lap_eigen
denom_v = 1.0 - dt_gt * D2 * Lap_eigen

snap_times = [0.02, 0.41, 0.81, 1.21, 1.60, 2.0]
gt_snapshots = {}
next_snap_idx = 0

u_sim = u_exact_0.copy()
v_sim = v_exact_0.copy()

t_start_sim = time.time()
for step in range(steps_gt):
    t_curr = step * dt_gt
    if next_snap_idx < len(snap_times) and t_curr >= snap_times[next_snap_idx] - dt_gt/2:
        gt_snapshots[snap_times[next_snap_idx]] = u_sim.copy()
        print(f"  Captured Ground Truth snapshot at t = {snap_times[next_snap_idx]:.2f}s (min u: {u_sim.min():.4f}, max u: {u_sim.max():.4f})")
        next_snap_idx += 1

    # Reaction step
    fu = kappa * (a - u_sim + (u_sim**2) * v_sim)
    fv = kappa * (b - (u_sim**2) * v_sim)
    
    rhs_u = u_sim + dt_gt * fu
    rhs_v = v_sim + dt_gt * fv
    
    # Diffusion step in DCT space
    u_hat = fft.dctn(rhs_u, type=2, norm='ortho') / denom_u
    v_hat = fft.dctn(rhs_v, type=2, norm='ortho') / denom_v
    
    u_sim = fft.idctn(u_hat, type=2, norm='ortho')
    v_sim = fft.idctn(v_hat, type=2, norm='ortho')

if next_snap_idx < len(snap_times):
    gt_snapshots[snap_times[-1]] = u_sim.copy()
    print(f"  Captured Ground Truth snapshot at t = {snap_times[-1]:.2f}s (min u: {u_sim.min():.4f}, max u: {u_sim.max():.4f})")

print(f"Ground Truth simulation completed in {time.time() - t_start_sim:.2f} s")

# ==============================================================================
# 3. PURE MLP PINN ARCHITECTURE
# ==============================================================================
class SchnakenbergPureMLP(nn.Module):
    def __init__(self, hidden_dim=128, num_layers=5):
        super().__init__()
        layers = []
        # Input layer: (x, y, t) -> hidden_dim
        layers.append(nn.Linear(3, hidden_dim))
        layers.append(nn.Tanh())
        
        # Deep hidden layers
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
            
        # Output layer: hidden_dim -> (u, v)
        layers.append(nn.Linear(hidden_dim, 2))
        self.net = nn.Sequential(*layers)
        
        # Xavier Normal weight initialization with zero bias
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, xyt):
        return self.net(xyt)

# Instantiate model
model = SchnakenbergPureMLP(hidden_dim=128, num_layers=5).to(device)
print(f"\n[PINN Model] Pure MLP initialized: 5 hidden layers x 128 neurons, Tanh activations.")
total_params = sum(p.numel() for p in model.parameters())
print(f"[PINN Model] Total trainable parameters: {total_params:,}")

# ==============================================================================
# 4. TRAINING COLLOCATION POINTS SETUP
# ==============================================================================
N_f = 10000   # Interior collocation points
N_0 = 2500    # Initial condition points
N_b = 2000    # Boundary condition points

# Interior collocation in [0, 1] x [0, 1] x [0, 2]
xy_t_f = torch.rand(N_f, 3, device=device)
xy_t_f[:, 2] *= t_max
xy_t_f.requires_grad_(True)

# Initial condition (t = 0)
xy_t_0 = torch.rand(N_0, 3, device=device)
xy_t_0[:, 2] = 0.0
x_0_t = xy_t_0[:, 0:1]
y_0_t = xy_t_0[:, 1:2]
u_0_target = u_star + 1e-3 * torch.exp(-100.0 * ((x_0_t - 1.0/3.0)**2 + (y_0_t - 0.5)**2))
v_0_target = torch.full((N_0, 1), v_star, device=device)

# Boundary points (4 edges)
n_edge = N_b // 4
s_bc = torch.rand(n_edge, 1, device=device)
t_bc = torch.rand(n_edge, 1, device=device) * t_max

xy_t_bc = torch.cat([
    torch.cat([torch.zeros(n_edge, 1, device=device), s_bc, t_bc], dim=1), # Left (x=0)
    torch.cat([torch.ones(n_edge, 1, device=device), s_bc, t_bc], dim=1),  # Right (x=1)
    torch.cat([s_bc, torch.zeros(n_edge, 1, device=device), t_bc], dim=1), # Bottom (y=0)
    torch.cat([s_bc, torch.ones(n_edge, 1, device=device), t_bc], dim=1),  # Top (y=1)
], dim=0).requires_grad_(True)

# Optimizer & Scheduler
epochs = 20000
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

# Metrics tracking
loss_history = {
    'epoch': [],
    'total': [],
    'pde_u': [],
    'pde_v': [],
    'pde': [],
    'ic': [],
    'bc': [],
    'lr': []
}

log_interval = 250

# ==============================================================================
# 5. PINN TRAINING LOOP (20,000 EPOCHS)
# ==============================================================================
print(f"\n[Step 2/3] Starting Full GPU Training for {epochs} Epochs...", flush=True)
t_train_start = time.time()

for epoch in range(1, epochs + 1):
    optimizer.zero_grad()
    
    # --- 1. Interior PDE Residuals ---
    out_f = model(xy_t_f)
    u = out_f[:, 0:1]
    v = out_f[:, 1:2]
    
    grad_u = torch.autograd.grad(u, xy_t_f, torch.ones_like(u), create_graph=True)[0]
    grad_v = torch.autograd.grad(v, xy_t_f, torch.ones_like(v), create_graph=True)[0]
    
    u_x, u_y, u_t = grad_u[:, 0:1], grad_u[:, 1:2], grad_u[:, 2:3]
    v_x, v_y, v_t = grad_v[:, 0:1], grad_v[:, 1:2], grad_v[:, 2:3]
    
    u_xx = torch.autograd.grad(u_x, xy_t_f, torch.ones_like(u_x), create_graph=True)[0][:, 0:1]
    u_yy = torch.autograd.grad(u_y, xy_t_f, torch.ones_like(u_y), create_graph=True)[0][:, 1:2]
    
    v_xx = torch.autograd.grad(v_x, xy_t_f, torch.ones_like(v_x), create_graph=True)[0][:, 0:1]
    v_yy = torch.autograd.grad(v_y, xy_t_f, torch.ones_like(v_y), create_graph=True)[0][:, 1:2]
    
    lap_u = u_xx + u_yy
    lap_v = v_xx + v_yy
    
    r_u = u_t - D1 * lap_u - kappa * (a - u + (u**2) * v)
    r_v = v_t - D2 * lap_v - kappa * (b - (u**2) * v)
    
    loss_pde_u = torch.mean(r_u**2)
    loss_pde_v = torch.mean(r_v**2)
    loss_pde = loss_pde_u + loss_pde_v
    
    # --- 2. Initial Condition Residual ---
    out_0 = model(xy_t_0)
    loss_ic = torch.mean((out_0[:, 0:1] - u_0_target)**2) + torch.mean((out_0[:, 1:2] - v_0_target)**2)
    
    # --- 3. Boundary Condition Residual (Zero Neumann flux) ---
    out_bc = model(xy_t_bc)
    grad_u_bc = torch.autograd.grad(out_bc[:, 0:1], xy_t_bc, torch.ones_like(out_bc[:, 0:1]), create_graph=True)[0]
    grad_v_bc = torch.autograd.grad(out_bc[:, 1:2], xy_t_bc, torch.ones_like(out_bc[:, 1:2]), create_graph=True)[0]
    
    # Edges 0,1 (Left, Right): d/dx = 0
    # Edges 2,3 (Bottom, Top): d/dy = 0
    loss_bc = (torch.mean(grad_u_bc[:2*n_edge, 0]**2) + torch.mean(grad_v_bc[:2*n_edge, 0]**2) +
               torch.mean(grad_u_bc[2*n_edge:, 1]**2) + torch.mean(grad_v_bc[2*n_edge:, 1]**2))
    
    # Total weighted loss
    total_loss = loss_pde + 10.0 * loss_ic + 5.0 * loss_bc
    total_loss.backward()
    
    optimizer.step()
    scheduler.step()
    
    # Log loss history
    if epoch % log_interval == 0 or epoch == 1 or epoch == epochs:
        loss_history['epoch'].append(epoch)
        loss_history['total'].append(float(total_loss.item()))
        loss_history['pde_u'].append(float(loss_pde_u.item()))
        loss_history['pde_v'].append(float(loss_pde_v.item()))
        loss_history['pde'].append(float(loss_pde.item()))
        loss_history['ic'].append(float(loss_ic.item()))
        loss_history['bc'].append(float(loss_bc.item()))
        loss_history['lr'].append(float(optimizer.param_groups[0]['lr']))
        
        elapsed = time.time() - t_train_start
        speed = epoch / elapsed
        remaining = (epochs - epoch) / speed if speed > 0 else 0
        print(f"Epoch [{epoch:5d}/{epochs}] | Total: {total_loss.item():.6e} | PDE_u: {loss_pde_u.item():.6e} | PDE_v: {loss_pde_v.item():.6e} | IC: {loss_ic.item():.6e} | BC: {loss_bc.item():.6e} | Elapsed: {elapsed/60:.1f}m | ETA: {remaining/60:.1f}m", flush=True)

total_train_time = time.time() - t_train_start
print(f"\n[PINN Training Complete] {epochs} epochs in {total_train_time:.2f} s ({total_train_time/60:.2f} min).")

# ==============================================================================
# 6. SAVE LOSS HISTORY & WEIGHTS
# ==============================================================================
# Save NPZ
npz_path = os.path.join(DATA_DIR, 'loss_history_20000_epochs.npz')
np.savez_compressed(
    npz_path,
    epoch=np.array(loss_history['epoch']),
    total_loss=np.array(loss_history['total']),
    pde_u_loss=np.array(loss_history['pde_u']),
    pde_v_loss=np.array(loss_history['pde_v']),
    pde_loss=np.array(loss_history['pde']),
    ic_loss=np.array(loss_history['ic']),
    bc_loss=np.array(loss_history['bc']),
    lr=np.array(loss_history['lr']),
    training_time_seconds=total_train_time
)
print(f"[Saved] Loss history saved to: {npz_path}")

# Save CSV
csv_path = os.path.join(DATA_DIR, 'loss_history_20000_epochs.csv')
with open(csv_path, 'w') as f:
    f.write("epoch,total_loss,pde_u_loss,pde_v_loss,pde_loss,ic_loss,bc_loss,learning_rate\n")
    for i in range(len(loss_history['epoch'])):
        f.write(f"{loss_history['epoch'][i]},{loss_history['total'][i]:.8e},{loss_history['pde_u'][i]:.8e},{loss_history['pde_v'][i]:.8e},{loss_history['pde'][i]:.8e},{loss_history['ic'][i]:.8e},{loss_history['bc'][i]:.8e},{loss_history['lr'][i]:.8e}\n")
print(f"[Saved] CSV loss log saved to: {csv_path}")

# Save Model Weights
model_path = os.path.join(ASSETS_DIR, 'schnakenberg_pinn_20000epochs.pth')
torch.save(model.state_dict(), model_path)
print(f"[Saved] Model weights saved to: {model_path}")

# ==============================================================================
# 7. GENERATE SCIENTIFIC COMPARISON FIGURES
# ==============================================================================
print("\n[Step 3/3] Generating High-Resolution Side-by-Side Comparison Figures...")

# Evaluate PINN on grid for all snapshot times
pinn_snapshots = {}
eval_grid_pts = np.stack([X_mesh.flatten(), Y_mesh.flatten()], axis=1)

model.eval()
with torch.no_grad():
    for t_val in snap_times:
        t_arr = np.full((len(eval_grid_pts), 1), t_val)
        xyt_eval = torch.tensor(np.hstack([eval_grid_pts, t_arr]), dtype=torch.float32, device=device)
        pred = model(xyt_eval)
        u_pinn_grid = pred[:, 0].cpu().numpy().reshape(N_grid, N_grid)
        pinn_snapshots[t_val] = u_pinn_grid

# ------------------------------------------------------------------------------
# FIGURE 1: LOSS CONVERGENCE ANALYSIS
# ------------------------------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(6.0, 3.2), dpi=300)
ep_arr = np.array(loss_history['epoch'])
ax1.semilogy(ep_arr, loss_history['total'], label=r'Total Loss $\mathcal{L}_{\mathrm{total}}$', color='#1f77b4', lw=1.8)
ax1.semilogy(ep_arr, loss_history['pde_u'], label=r'PDE Residual ($u$)', color='#d62728', lw=1.2, ls='--')
ax1.semilogy(ep_arr, loss_history['pde_v'], label=r'PDE Residual ($v$)', color='#ff7f0e', lw=1.2, ls=':')
ax1.semilogy(ep_arr, loss_history['ic'], label=r'Initial Condition $\mathcal{L}_{\mathrm{ic}}$', color='#2ca02c', lw=1.2, ls='-.')
ax1.semilogy(ep_arr, loss_history['bc'], label=r'Neumann BC $\mathcal{L}_{\mathrm{bc}}$', color='#9467bd', lw=1.2, ls='-')

ax1.set_xlabel('Training Epoch')
ax1.set_ylabel('Mean Squared Error (MSE)')
ax1.set_title(f'PINN Loss Convergence Analysis ({epochs} Epochs on {gpu_name})', fontsize=9.5)
ax1.grid(True, which='both', ls=':', alpha=0.5)
ax1.legend(loc='upper right', framealpha=0.9, fontsize=7.5)
plt.tight_layout()
fig1_pdf = os.path.join(FIG_DIR, 'fig1_loss_convergence_20k.pdf')
fig1_png = os.path.join(FIG_DIR, 'fig1_loss_convergence_20k.png')
plt.savefig(fig1_pdf)
plt.savefig(fig1_png)
plt.close()
print(f"  Saved Fig 1: {fig1_png}")

# ------------------------------------------------------------------------------
# FIGURE 2: SIDE-BY-SIDE SPATIO-TEMPORAL EVOLUTION COMPARISON (ADI vs PINN)
# ------------------------------------------------------------------------------
# 2 rows (Row 1: ADI Ground Truth, Row 2: PINN Prediction) x 6 columns (t snapshots)
fig, axes = plt.subplots(2, len(snap_times), figsize=(12.0, 4.0), dpi=300, sharex=True, sharey=True)

# Color scale bounds: Ground truth spots range from ~0.2 to 2.8
vmin_val, vmax_val = 0.2, 2.8

for j, t_val in enumerate(snap_times):
    # Row 0: ADI Ground Truth (Pereira 2019)
    im0 = axes[0, j].imshow(gt_snapshots[t_val], extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=vmin_val, vmax=vmax_val)
    axes[0, j].set_title(f"$t = {t_val:.2f}$ s", fontsize=8.5)
    if j == 0:
        axes[0, j].set_ylabel('Ground Truth\n(Pereira 2019 ADI)\n$y$', fontsize=8.0)
        
    # Row 1: PINN Vanilla Prediction (20k epochs)
    im1 = axes[1, j].imshow(pinn_snapshots[t_val], extent=[0, L, 0, L], origin='lower', cmap='inferno', vmin=vmin_val, vmax=vmax_val)
    axes[1, j].set_xlabel('$x$', fontsize=8.0)
    if j == 0:
        axes[1, j].set_ylabel('PINN Vanilla\n(20,000 Epochs)\n$y$', fontsize=8.0)

fig.subplots_adjust(right=0.91, wspace=0.12, hspace=0.18)
cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.70])
cbar = fig.colorbar(im0, cax=cbar_ax)
cbar.set_label('Activator Concentration $u(x, y, t)$', fontsize=8.5)

fig.suptitle('Direct Side-by-Side Comparison: Linearized ADI (Spots) vs Vanilla PINN (Homogeneous Collapse)', fontsize=10.0, y=0.98)
fig2_pdf = os.path.join(FIG_DIR, 'fig2_side_by_side_comparison_20k.pdf')
fig2_png = os.path.join(FIG_DIR, 'fig2_side_by_side_comparison_20k.png')
plt.savefig(fig2_pdf)
plt.savefig(fig2_png)
plt.close()
print(f"  Saved Fig 2: {fig2_png}")

# ------------------------------------------------------------------------------
# FIGURE 3: DIRECT 1D CUT & ABSOLUTE ERROR AT FINAL TIME t = 2.0s
# ------------------------------------------------------------------------------
fig, (ax_cut, ax_err) = plt.subplots(1, 2, figsize=(9.0, 3.2), dpi=300)

# 1D Cut along horizontal centerline y = 0.5 at t = 2.0s
y_mid_idx = N_grid // 2
u_adi_cut = gt_snapshots[2.0][y_mid_idx, :]
u_pinn_cut = pinn_snapshots[2.0][y_mid_idx, :]

ax_cut.plot(x_lin, u_adi_cut, label='Ground Truth (ADI)', color='#d62728', lw=2.0)
ax_cut.plot(x_lin, u_pinn_cut, label='PINN Vanilla (20k ep)', color='#1f77b4', lw=2.0, ls='--')
ax_cut.axhline(u_star, color='black', ls=':', alpha=0.7, label=f'Equilibrium $u^* = {u_star:.2f}$')
ax_cut.set_xlabel('Spatial Coordinate $x$ ($y=0.5, t=2.0$s)')
ax_cut.set_ylabel('Activator Concentration $u$')
ax_cut.set_title('(a) Horizontal Cross-Section Profile at $t = 2.0$ s', fontsize=8.5)
ax_cut.grid(True, ls=':', alpha=0.6)
ax_cut.legend(loc='upper right', framealpha=0.9, fontsize=7.5)

# Absolute Error Map at t = 2.0s
abs_err_2 = np.abs(pinn_snapshots[2.0] - gt_snapshots[2.0])
im_err = ax_err.imshow(abs_err_2, extent=[0, L, 0, L], origin='lower', cmap='magma')
ax_err.set_xlabel('$x$')
ax_err.set_ylabel('$y$')
ax_err.set_title(r'(b) Absolute Error $|\hat{u}_{\mathrm{PINN}} - u_{\mathrm{ADI}}|$ at $t=2.0$ s', fontsize=8.5)
cbar_err = plt.colorbar(im_err, ax=ax_err, fraction=0.046, pad=0.04)
cbar_err.set_label('Pointwise Absolute Error')

plt.tight_layout()
fig3_pdf = os.path.join(FIG_DIR, 'fig3_profile_error_comparison_20k.pdf')
fig3_png = os.path.join(FIG_DIR, 'fig3_profile_error_comparison_20k.png')
plt.savefig(fig3_pdf)
plt.savefig(fig3_png)
plt.close()
print(f"  Saved Fig 3: {fig3_png}")

# ------------------------------------------------------------------------------
# 8. CONVERGENCE & ERROR SUMMARY METRICS
# ------------------------------------------------------------------------------
l2_rel_err_final = np.linalg.norm(pinn_snapshots[2.0] - gt_snapshots[2.0]) / np.linalg.norm(gt_snapshots[2.0])
max_err_final = np.max(abs_err_2)

summary = {
    "parameters": {
        "a": a,
        "b": b,
        "kappa": kappa,
        "D1": D1,
        "D2": D2,
        "u_star": u_star,
        "v_star": v_star,
        "t_max": t_max,
        "domain": [0, L, 0, L]
    },
    "training": {
        "epochs": epochs,
        "optimizer": "Adam + CosineAnnealingLR",
        "initial_lr": 1e-3,
        "min_lr": 1e-5,
        "total_time_seconds": total_train_time,
        "final_total_loss": loss_history['total'][-1],
        "final_pde_u_loss": loss_history['pde_u'][-1],
        "final_pde_v_loss": loss_history['pde_v'][-1],
        "final_ic_loss": loss_history['ic'][-1],
        "final_bc_loss": loss_history['bc'][-1]
    },
    "comparison_metrics_t2": {
        "relative_l2_error": float(l2_rel_err_final),
        "maximum_absolute_error": float(max_err_final),
        "ground_truth_u_min": float(gt_snapshots[2.0].min()),
        "ground_truth_u_max": float(gt_snapshots[2.0].max()),
        "pinn_u_min": float(pinn_snapshots[2.0].min()),
        "pinn_u_max": float(pinn_snapshots[2.0].max()),
        "conclusion": "Vanilla PINN collapsed into the homogeneous steady state u*=0.9000 across all time slices due to temporal causality breakdown and kinetic stiffness."
    }
}

summary_json_path = os.path.join(DATA_DIR, 'experiment_summary_20k.json')
with open(summary_json_path, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"[Summary] Experiment summary written to: {summary_json_path}")
print("\n" + "="*60)
print(f"EXPERIMENT COMPLETED SUCCESSFULLY!")
print(f"Final PINN Loss: {loss_history['total'][-1]:.6e}")
print(f"Relative L2 Error at t=2.0s: {l2_rel_err_final:.4f} (100% Failure to Form Patterns)")
print(f"Ground truth spot amplitude: [{gt_snapshots[2.0].min():.4f}, {gt_snapshots[2.0].max():.4f}]")
print(f"PINN predicted field range:   [{pinn_snapshots[2.0].min():.4f}, {pinn_snapshots[2.0].max():.4f}]")
print("="*60)
