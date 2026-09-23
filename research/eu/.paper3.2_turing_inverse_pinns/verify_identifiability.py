import numpy as np

# Load exact data
sol = np.load('paper3.2_turing_inverse_pinns/exact_thesis_turing_solution.npz')
dx = 1.0 / 127.0
target_snaps = [0.02, 0.41, 0.81, 1.21, 1.60, 2.00]

# We will use the snapshot at t = 1.60 and t = 2.00 to approximate an average, 
# or just do a spatial analysis if we assume steady state. 
# Actually, Turing patterns at t=2.0 are nearly steady state (u_t ~ 0).
u = sol['u_2.00']
v = sol['v_2.00']

# Compute spatial Laplacian using 5-point FDM
lap_u = (np.roll(u, 1, axis=0) + np.roll(u, -1, axis=0) + 
         np.roll(u, 1, axis=1) + np.roll(u, -1, axis=1) - 4*u) / (dx**2)
lap_v = (np.roll(v, 1, axis=0) + np.roll(v, -1, axis=0) + 
         np.roll(v, 1, axis=1) + np.roll(v, -1, axis=1) - 4*v) / (dx**2)

# Ignore boundaries
lap_u = lap_u[1:-1, 1:-1].flatten()
lap_v = lap_v[1:-1, 1:-1].flatten()
u_inner = u[1:-1, 1:-1].flatten()
v_inner = v[1:-1, 1:-1].flatten()

a, b = 0.1305, 0.7695

# At near steady state (t=2.0), u_t approx 0, v_t approx 0.
# So: 0 = D_u * lap_u + kappa * (a - u + u^2 v)
#     0 = D_v * lap_v + kappa * (b - u^2 v)
# Let's solve for D_u, kappa using least squares
A_u = np.vstack([lap_u, (a - u_inner + (u_inner**2)*v_inner)]).T
# We want A_u * [D_u, kappa]^T = 0. But this is homogeneous.
# We need actual time derivatives to do this perfectly.
