import sys
sys.path.append("../../src")

from models import PINN
from utils import derivative, get_device
import torch
# ---

device = get_device()
print(device)
# ---

model = PINN(3, 64, 1, 4).to(device)
optimizer = torch.optim.Adam(model.parameters())
# ---

x_ic = torch.linspace(0, 1, 100, device=device)
y_ic = torch.linspace(0, 1, 100, device=device)

X_ic, Y_ic = torch.meshgrid(x_ic, y_ic,indexing="ij")

x_ic = X_ic
y_ic = Y_ic

mask = (((x_ic-0.30)**2 + (y_ic-0.30)**2 > 0.12**2) &
        ((x_ic-0.70)**2 + (y_ic-0.30)**2 > 0.12**2) &
        ((x_ic-0.50)**2 + (y_ic-0.70)**2 > 0.12**2))

x_ic = x_ic[mask].reshape(-1,1)
y_ic = y_ic[mask].reshape(-1,1)

t_ic = torch.zeros_like(x_ic)

u_ic_true = torch.zeros_like(x_ic)
print(x_ic.shape)
print(y_ic.shape)
print(t_ic.shape)
# ---

Nb = 1000
t_max = 5.0

t_b = t_max * torch.rand(Nb,1,device=device)

# left
x_bl = torch.zeros(Nb,1,device=device)
y_bl = torch.rand(Nb,1,device=device)

# right
x_br = torch.ones(Nb,1,device=device)
y_br = torch.rand(Nb,1,device=device)

# bottom
x_bb = torch.rand(Nb,1,device=device)
y_bb = torch.zeros(Nb,1,device=device)

# top
x_bt = torch.rand(Nb,1,device=device)
y_bt = torch.ones(Nb,1,device=device)

u_bc_true = torch.ones(Nb,1,device=device)
# ---

Nb_hole = 10000

theta1 = 2*torch.pi*torch.rand(Nb_hole,1,device=device)

x_h1 = 0.30 + 0.12*torch.cos(theta1)
y_h1 = 0.30 + 0.12*torch.sin(theta1)

t_h1 = t_max * torch.rand(Nb_hole,1,device=device)

u_h1 = torch.zeros_like(x_h1)


theta2 = 2*torch.pi*torch.rand(Nb_hole,1,device=device)

x_h2 = 0.70 + 0.12*torch.cos(theta2)
y_h2 = 0.30 + 0.12*torch.sin(theta2)

t_h2 = t_max * torch.rand(Nb_hole,1,device=device)

u_h2 = torch.zeros_like(x_h2)


theta3 = 2*torch.pi*torch.rand(Nb_hole,1,device=device)

x_h3 = 0.50 + 0.12*torch.cos(theta3)
y_h3 = 0.70 + 0.12*torch.sin(theta3)

t_h3 = t_max * torch.rand(Nb_hole,1,device=device)

u_h3 = torch.zeros_like(x_h3)
# ---

Nf = 10000

x_f = torch.rand(Nf,1,device=device)
y_f = torch.rand(Nf,1,device=device)
t_f = t_max * torch.rand(Nf,1,device=device)

mask = (
    ((x_f-0.30)**2 + (y_f-0.30)**2 > 0.12**2)
    &
    ((x_f-0.70)**2 + (y_f-0.30)**2 > 0.12**2)
    &
    ((x_f-0.50)**2 + (y_f-0.70)**2 > 0.12**2)
)

x_f = x_f[mask].reshape(-1,1)
y_f = y_f[mask].reshape(-1,1)
t_f = t_f[mask].reshape(-1,1)

x_f.requires_grad_(True)
y_f.requires_grad_(True)
t_f.requires_grad_(True)
# ---

def pde_residual_heat(model, x, y, t, alpha):
    u = model(t,x,y)
    
    u_t = derivative(u, t)
    u_x = derivative(u, x)
    u_y = derivative(u, y)
    
    u_xx = derivative(u_x, x)
    u_yy = derivative(u_y, y)
    
    r_u = u_t - alpha * (u_xx + u_yy)
    
    return r_u
# ---

epochs = 10000
alpha = 0.01  

for epoch in range(epochs):
    optimizer.zero_grad()

    r_u = pde_residual_heat(model, x_f, y_f, t_f, alpha)
    loss_pde = torch.mean(r_u**2)

    u_ic = model(t_ic, x_ic, y_ic)
    loss_ic = torch.mean((u_ic - u_ic_true)**2)

    u_bc_l = model(t_b, x_bl, y_bl)
    u_bc_r = model(t_b, x_br, y_br)
    u_bc_b = model(t_b, x_bb, y_bb)
    u_bc_t = model(t_b, x_bt, y_bt)

    loss_bc_outer = (
        torch.mean((u_bc_l - u_bc_true)**2) +
        torch.mean((u_bc_r - u_bc_true)**2) +
        torch.mean((u_bc_b - u_bc_true)**2) +
        torch.mean((u_bc_t - u_bc_true)**2)
    )

    # Hole boundaries (h1, h2, h3)
    u_bc_h1 = model(t_h1, x_h1, y_h1)
    u_bc_h2 = model(t_h2, x_h2, y_h2)
    u_bc_h3 = model(t_h3, x_h3, y_h3)

    loss_bc_holes = (
        torch.mean((u_bc_h1 - u_h1)**2) +
        torch.mean((u_bc_h2 - u_h2)**2) +
        torch.mean((u_bc_h3 - u_h3)**2)
    )

    loss_bc = loss_bc_outer + loss_bc_holes

    loss = loss_pde + loss_ic + loss_bc

    loss.backward()
    optimizer.step()

    if epoch % 1000 == 0:
        print(f"epoch {epoch} | total loss: {loss.item():.6f} | loss pde: {loss_pde.item():.6f} | loss ic: {loss_ic.item():.6f} | loss bc: {loss_bc.item():.6f}")
# ---

import matplotlib.pyplot as plt
import torch

# 1. Generate a dense grid of points for a high-quality plot
# We do this so the plot looks smooth, regardless of your Nf training points
n_plot = 200
x_plot = torch.linspace(0, 1, n_plot, device=device)
y_plot = torch.linspace(0, 1, n_plot, device=device)
X_plot, Y_plot = torch.meshgrid(x_plot, y_plot, indexing="ij")

x_flat = X_plot.reshape(-1, 1)
y_flat = Y_plot.reshape(-1, 1)

# Set a specific time step to visualize (e.g., t = 0.5)
t_val = 0.8
t_flat = torch.full_like(x_flat, t_val)

# 2. Apply the same mask to carve out the holes for the plot
mask_plot = (
    ((x_flat - 0.30)**2 + (y_flat - 0.30)**2 > 0.12**2) &
    ((x_flat - 0.70)**2 + (y_flat - 0.30)**2 > 0.12**2) &
    ((x_flat - 0.50)**2 + (y_flat - 0.70)**2 > 0.12**2)
).flatten()

# Filter the points
x_filtered = x_flat[mask_plot].reshape(-1, 1)
y_filtered = y_flat[mask_plot].reshape(-1, 1)
t_filtered = t_flat[mask_plot].reshape(-1, 1)

# 3. Predict the temperature using your trained model
with torch.no_grad(): # Disable gradients for inference to save memory
    X_input = torch.cat([x_filtered, y_filtered, t_filtered], dim=1)
    u_pred = model(X_input)

# 4. Convert PyTorch tensors back to NumPy arrays for Matplotlib
x_np = x_filtered.cpu().numpy().flatten()
y_np = y_filtered.cpu().numpy().flatten()
u_np = u_pred.cpu().numpy().flatten()

# 5. Create the visualization
plt.figure(figsize=(8, 6))

# Use tricontourf to create a smooth heatmap from unstructured points
heatmap = plt.tricontourf(x_np, y_np, u_np, levels=100, cmap='inferno')
plt.colorbar(heatmap, label=f'Temperature (u) at t={t_val}')

# 6. Draw the holes visually to make the domain clear
holes = [(0.30, 0.30, 0.12), (0.70, 0.30, 0.12), (0.50, 0.70, 0.12)]
for (hx, hy, hr) in holes:
    # Fill the hole with white
    circle_fill = plt.Circle((hx, hy), hr, color='white', fill=True, zorder=10)
    plt.gca().add_patch(circle_fill)
    # Add a clean black border around the hole
    circle_edge = plt.Circle((hx, hy), hr, color='black', fill=False, linewidth=1.5, zorder=11)
    plt.gca().add_patch(circle_edge)

# 7. Formatting the plot
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.xlabel('X coordinate')
plt.ylabel('Y coordinate')
plt.title(f'PINN Heat Equation Prediction (t = {t_val})')
plt.gca().set_aspect('equal') # Ensures the square domain and circular holes aren't stretched

plt.tight_layout()
plt.show()
# ---

import matplotlib.pyplot as plt

def plot_2d_heatmap(model, t_value=0.5, n=200, device=torch.device("cuda")):
    model.eval()
    x = torch.linspace(0, 1, n, device=device)
    y = torch.linspace(0, 1, n, device=device)
    X, Y = torch.meshgrid(x, y, indexing="ij")
    
    x_test = X.reshape(-1, 1)
    y_test = Y.reshape(-1, 1)
    t_test = torch.full_like(x_test, t_value)
    
    with torch.no_grad():
        u_pred = model(t_test, x_test, y_test)

    U_pred = u_pred.reshape(n, n).cpu().numpy()
    
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    
    # Plot using imshow
    heatmap = ax.imshow(
        U_pred.T, 
        origin='lower', 
        extent=[0, 1, 0, 1], 
        cmap='inferno'
    )
    
    fig.colorbar(heatmap, ax=ax, label='u(x,y)')
    ax.set_title(f"Neural Network Output at t = {t_value}")
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.show()
# ---

plot_2d_heatmap(model, 4.5)
# ---


# ---

