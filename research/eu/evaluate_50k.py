import torch, numpy as np
checkpoint = torch.load('./paper2_heat_irregular_domain/models/pinn_heat_holes_checkpoint.pth', map_location='cpu', weights_only=False)
h = checkpoint['loss_history']
print(f"Época Final: {checkpoint['epoch']}")
print(f"Loss Total Final: {h['total'][-1]:.6f}")
print(f"Loss EDP Final:   {h['pde'][-1]:.6f}")
print(f"Loss Furos Final: {h['bc_holes'][-1]:.8f}")
