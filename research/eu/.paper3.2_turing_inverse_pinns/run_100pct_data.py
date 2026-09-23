import numpy as np
import torch
import torch.nn as nn
import time

torch.set_num_threads(1)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load the exact forward solution we generated earlier
sol = np.load('paper3.2_turing_inverse_pinns/exact_thesis_turing_solution.npz')
x_grid, y_grid = sol['x'], sol['y']
N = len(x_grid)

# Sample dense temporal trajectory (all 6 snapshots)
x_obs, y_obs, t_obs, u_obs, v_obs = [], [], [], [], []
for ts in [0.02, 0.41, 0.81, 1.21, 1.60, 2.00]:
    u_mat = sol[f'u_{ts:.2f}']
    v_mat = sol[f'v_{ts:.2f}']
    for iy in range(0, N, 2):
        for ix in range(0, N, 2):
            x_obs.append(x_grid[ix])
            y_obs.append(y_grid[iy])
            t_obs.append(ts)
            u_obs.append(u_mat[iy, ix])
            v_obs.append(v_mat[iy, ix])

xd = torch.tensor(x_obs, dtype=torch.float32, device=device).view(-1, 1)
yd = torch.tensor(y_obs, dtype=torch.float32, device=device).view(-1, 1)
td = torch.tensor(t_obs, dtype=torch.float32, device=device).view(-1, 1)
ud = torch.tensor(u_obs, dtype=torch.float32, device=device).view(-1, 1)
vd = torch.tensor(v_obs, dtype=torch.float32, device=device).view(-1, 1)

class InvNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(3, 64), nn.Tanh(),
            nn.Linear(64, 64), nn.Tanh(),
            nn.Linear(64, 64), nn.Tanh(),
            nn.Linear(64, 2)
        )
        self.log_Du = nn.Parameter(torch.tensor(np.log(0.15), dtype=torch.float32, device=device))
        self.log_Dv = nn.Parameter(torch.tensor(np.log(0.50), dtype=torch.float32, device=device))
        self.log_kappa = nn.Parameter(torch.tensor(np.log(60.0), dtype=torch.float32, device=device))
        
    def forward(self, x, y, t):
        out = self.net(torch.cat([x, y, t], dim=1))
        return out[:, 0:1], out[:, 1:2]
        
    @property
    def Du(self): return torch.exp(self.log_Du)
    @property
    def Dv(self): return torch.exp(self.log_Dv)
    @property
    def kappa(self): return torch.exp(self.log_kappa)

model = InvNet().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=2e-3)

a, b = 0.1305, 0.7695
N_f = 2500

print("Running Experiment 1: 100% Data for BOTH u and v...")
for ep in range(1, 2001):
    optimizer.zero_grad()
    
    # 1. Fit data (Notice we are fitting BOTH u and v now!)
    u_pred, v_pred = model(xd, yd, td)
    loss_data = torch.mean((u_pred - ud)**2) + torch.mean((v_pred - vd)**2)
    
    # 2. PDE
    x_f = torch.rand(N_f, 1, device=device, requires_grad=True)
    y_f = torch.rand(N_f, 1, device=device, requires_grad=True)
    t_f = (torch.rand(N_f, 1, device=device) * 2.0).requires_grad_(True)
    
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
    
    ru = u_t - model.Du * (u_xx + u_yy) - model.kappa * (a - u + (u**2)*v)
    rv = v_t - model.Dv * (v_xx + v_yy) - model.kappa * (b - (u**2)*v)
    
    loss_pde = torch.mean(ru**2) + torch.mean(rv**2)
    
    total_loss = 50.0 * loss_data + loss_pde
    total_loss.backward()
    optimizer.step()
    
    if ep % 500 == 0 or ep == 1:
        err_Du = abs(model.Du.item() - 0.05) / 0.05 * 100
        err_Dv = abs(model.Dv.item() - 1.0) / 1.0 * 100
        err_k  = abs(model.kappa.item() - 100.0) / 100.0 * 100
        print(f'Ep {ep:4d} | Du: {model.Du.item():.5f} (Err: {err_Du:.2f}%) | Dv: {model.Dv.item():.5f} (Err: {err_Dv:.2f}%) | kappa: {model.kappa.item():.2f} (Err: {err_k:.2f}%)')
