import numpy as np
import torch
import torch.nn as nn
import time

torch.set_num_threads(1)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

sol = np.load('paper3.2_turing_inverse_pinns/exact_thesis_turing_solution.npz')
x_grid, y_grid = sol['x'], sol['y']
N = len(x_grid)

# Sample dense temporal trajectory
x_obs, y_obs, t_obs, u_obs, v_obs = [], [], [], [], []
for ts in [0.02, 0.41, 0.81, 1.21, 1.60, 2.00]:
    u_mat, v_mat = sol[f'u_{ts:.2f}'], sol[f'v_{ts:.2f}']
    for iy in range(0, N, 2):
        for ix in range(0, N, 2):
            x_obs.append(x_grid[ix]); y_obs.append(y_grid[iy]); t_obs.append(ts)
            u_obs.append(u_mat[iy, ix]); v_obs.append(v_mat[iy, ix])

xd = torch.tensor(x_obs, dtype=torch.float32, device=device).view(-1, 1)
yd = torch.tensor(y_obs, dtype=torch.float32, device=device).view(-1, 1)
td = torch.tensor(t_obs, dtype=torch.float32, device=device).view(-1, 1)
ud = torch.tensor(u_obs, dtype=torch.float32, device=device).view(-1, 1)
vd = torch.tensor(v_obs, dtype=torch.float32, device=device).view(-1, 1)

# Using a much larger capacity network to fit the data perfectly
class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(3, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 2))
    def forward(self, x, y, t):
        out = self.net(torch.cat([x, y, t], dim=1))
        return out[:, 0:1], out[:, 1:2]

model = Net().to(device)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)

print("Stage 1: Pre-training network purely on 100% data...")
for ep in range(1, 4001):
    opt.zero_grad()
    u_pred, v_pred = model(xd, yd, td)
    loss = torch.mean((u_pred - ud)**2) + torch.mean((v_pred - vd)**2)
    loss.backward()
    opt.step()
    if ep % 1000 == 0:
        print(f"  Ep {ep} | Data Loss: {loss.item():.2e}")

print("Stage 2: Computing derivatives and solving Linear Regression for Physics...")
# Instead of slow neural backprop for physics, since the network knows the curves perfectly,
# we just evaluate the derivatives and do Least Squares for D_u, D_v, kappa!
xd.requires_grad_(True); yd.requires_grad_(True); td.requires_grad_(True)
u, v = model(xd, yd, td)
u_x = torch.autograd.grad(u, xd, torch.ones_like(u), create_graph=True)[0]
u_y = torch.autograd.grad(u, yd, torch.ones_like(u), create_graph=True)[0]
u_t = torch.autograd.grad(u, td, torch.ones_like(u), create_graph=True)[0]
v_x = torch.autograd.grad(v, xd, torch.ones_like(v), create_graph=True)[0]
v_y = torch.autograd.grad(v, yd, torch.ones_like(v), create_graph=True)[0]
v_t = torch.autograd.grad(v, td, torch.ones_like(v), create_graph=True)[0]

u_xx = torch.autograd.grad(u_x, xd, torch.ones_like(u_x), create_graph=True)[0]
u_yy = torch.autograd.grad(u_y, yd, torch.ones_like(u_y), create_graph=True)[0]
v_xx = torch.autograd.grad(v_x, xd, torch.ones_like(v_x), create_graph=True)[0]
v_yy = torch.autograd.grad(v_y, yd, torch.ones_like(v_y), create_graph=True)[0]

Lap_u = (u_xx + u_yy).detach().cpu().numpy()
Lap_v = (v_xx + v_yy).detach().cpu().numpy()
ut = u_t.detach().cpu().numpy()
vt = v_t.detach().cpu().numpy()
u_val = u.detach().cpu().numpy()
v_val = v.detach().cpu().numpy()

a, b = 0.1305, 0.7695
# u_t = D_u * Lap_u + kappa * (a - u + u^2 v)
# v_t = D_v * Lap_v + kappa * (b - u^2 v)
# This is Ax = b. 
react_u = (a - u_val + (u_val**2)*v_val)
react_v = (b - (u_val**2)*v_val)

A = np.hstack([Lap_u, react_u])  # size (N_pts, 2)
b_vec = ut
res_u = np.linalg.lstsq(A, b_vec, rcond=None)[0]
Du_est = res_u[0][0]
kappa_est_u = res_u[1][0]

A_v = np.hstack([Lap_v, react_v])
b_vec_v = vt
res_v = np.linalg.lstsq(A_v, b_vec_v, rcond=None)[0]
Dv_est = res_v[0][0]
kappa_est_v = res_v[1][0]
kappa_est = (kappa_est_u + kappa_est_v) / 2.0

print(f"Final Discovered Parameters:")
print(f"Du = {Du_est:.5f} (True: 0.05, Err: {abs(Du_est-0.05)/0.05*100:.2f}%)")
print(f"Dv = {Dv_est:.5f} (True: 1.00, Err: {abs(Dv_est-1.0)/1.0*100:.2f}%)")
print(f"kappa = {kappa_est:.2f} (True: 100.0, Err: {abs(kappa_est-100)/100*100:.2f}%)")
