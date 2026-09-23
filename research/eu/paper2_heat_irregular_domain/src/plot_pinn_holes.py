import torch
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_loss_convergence(epochs, loss_total, loss_pde, loss_bc, loss_ic, save_path="figures/loss_convergence.pdf"):
    """
    Função para plotar a curva de convergência das perdas (log-scale)
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.plot(epochs, loss_total, label='Total Loss', color='black', linewidth=2)
    plt.plot(epochs, loss_pde, label='PDE Loss', linestyle='--')
    plt.plot(epochs, loss_bc, label='BC Loss', linestyle='-.')
    plt.plot(epochs, loss_ic, label='IC Loss', linestyle=':')
    
    plt.yscale('log')
    plt.xlabel('Épocas')
    plt.ylabel('Loss')
    plt.title('Convergência das Perdas - PINN (3 Furos)')
    plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"Salvo: {save_path}")
    plt.close()

def generate_heat_2d_holes_figure(model, device, t_val=0.8, save_path="figures/heat_2d_holes_t08.pdf"):
    """
    Função para gerar o mapa de calor da frente térmica no domínio com furos.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    n_plot = 200
    x_plot = torch.linspace(0, 1, n_plot, device=device)
    y_plot = torch.linspace(0, 1, n_plot, device=device)
    X_plot, Y_plot = torch.meshgrid(x_plot, y_plot, indexing="ij")
    
    x_flat = X_plot.reshape(-1, 1)
    y_flat = Y_plot.reshape(-1, 1)
    t_flat = torch.full_like(x_flat, t_val)
    
    # Máscara para buracos: r = 0.12, (0.3, 0.3), (0.7, 0.3), (0.5, 0.7)
    mask_plot = (
        ((x_flat - 0.30)**2 + (y_flat - 0.30)**2 > 0.12**2) &
        ((x_flat - 0.70)**2 + (y_flat - 0.30)**2 > 0.12**2) &
        ((x_flat - 0.50)**2 + (y_flat - 0.70)**2 > 0.12**2)
    ).flatten()
    
    x_filtered = x_flat[mask_plot].reshape(-1, 1)
    y_filtered = y_flat[mask_plot].reshape(-1, 1)
    t_filtered = t_flat[mask_plot].reshape(-1, 1)
    
    with torch.no_grad():
        X_input = torch.cat([x_filtered, y_filtered, t_filtered], dim=1) # Se seu modelo usa x_input conjunto
        # u_pred = model(X_input) 
        # ATENÇÃO: Dependendo da sua implementação, mude para:
        u_pred = model(t_filtered, x_filtered, y_filtered)
        
    x_np = x_filtered.cpu().numpy().flatten()
    y_np = y_filtered.cpu().numpy().flatten()
    u_np = u_pred.cpu().numpy().flatten()
    
    plt.figure(figsize=(6, 5))
    heatmap = plt.tricontourf(x_np, y_np, u_np, levels=100, cmap='inferno')
    plt.colorbar(heatmap, label=f'Temperatura em $t={t_val}$')
    
    # Desenhar contornos brancos e pretos para simular fisicamente os furos
    holes = [(0.30, 0.30, 0.12), (0.70, 0.30, 0.12), (0.50, 0.70, 0.12)]
    for (hx, hy, hr) in holes:
        circle_fill = plt.Circle((hx, hy), hr, color='white', fill=True, zorder=10)
        plt.gca().add_patch(circle_fill)
        circle_edge = plt.Circle((hx, hy), hr, color='black', fill=False, linewidth=1.5, zorder=11)
        plt.gca().add_patch(circle_edge)
        
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title(f'Predição da PINN (3 Furos) - $t={t_val}$')
    plt.gca().set_aspect('equal')
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"Salvo: {save_path}")
    plt.close()

# Exemplo de uso (copie para o fim do seu Notebook/Script de treinamento):
#
# epoch_history = []
# loss_total_history = []
# loss_pde_history = []
# loss_bc_history = []
# loss_ic_history = []
# 
# no loop for:
# if epoch % 100 == 0:
#     epoch_history.append(epoch)
#     loss_total_history.append(loss.item())
#     loss_pde_history.append(loss_pde.item())
#     loss_bc_history.append(loss_bc.item())
#     loss_ic_history.append(loss_ic.item())
#
# Após o treinamento:
# plot_loss_convergence(epoch_history, loss_total_history, loss_pde_history, loss_bc_history, loss_ic_history)
# generate_heat_2d_holes_figure(model, device, t_val=0.8)
