---
tags:
  - research/pinns
  - inverse-problems
  - parameter-discovery
  - scientific-ml
parent: "[[research/PINNs and Reaction-Diffusion Systems]]"
date: 2025-08-26
---

# PINN Inverse Problems vs Forward Solvers

### 1. The Asymmetry: Forward vs Inverse

| Feature | Forward Problem (Solving PDE) | Inverse Problem (Parameter Discovery) |
| :--- | :--- | :--- |
| **Objective** | Predict $(u, v)$ from initial & boundary conditions | Infer $(D_a, D_b, a, b)$ from noisy pattern data |
| **Classical Competitor** | Julia `DifferentialEquations.jl`, FEM, Spectral methods | Adjoint state methods, Optimization loops (very expensive) |
| **PINN Performance** | ❌ Highly fragile on stiff bifurcations | ✅ **State-of-the-art / Highly robust** |
| **Loss Landscape** | Flat plateaus, stiff local minima | Smooth, well-conditioned quadratic valley |
| **Real-world Value** | Low (classical solvers are 1000x faster) | **High** (experimental microscopy data has unknown rates) |

### 2. Formulating Inverse Discovery in PyTorch
Parameters are instantiated as learnable `nn.Parameter` tensors:
```python
class SchnakenbergInversePINN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = ModifiedMLP(...)
        # Learnable physical parameters initialized with prior guesses
        self.log_Da = nn.Parameter(torch.tensor([0.0]))
        self.log_Db = nn.Parameter(torch.tensor([1.0]))
        self.a = nn.Parameter(torch.tensor([0.5]))
        self.b = nn.Parameter(torch.tensor([0.5]))

    @property
    def Da(self):
        return torch.exp(self.log_Da) # Enforces positivity Da > 0
```

### 3. The "Hidden Physics" Advantage
In multi-species biology (activator $u$, inhibitor $v$):
- Experimental imaging often **only captures $u$** (fluorescent marker).
- The inhibitor $v$ is invisible.
- The PINN loss $\mathcal{L} = \mathcal{L}_{\text{data}}(u) + \mathcal{L}_{\text{pde}}(u, v)$ simultaneously discovers the unknown parameters AND reconstructs the hidden field $v(t, x)$.

---

### Inverse Problem Takeaway

> [!abstract] Inverse Problem Takeaway
> PINNs shine when discovering unknown physical parameters from sparse, noisy observations or reconstructing unmeasured chemical species—turning a fragile forward optimization into a well-posed, publishable discovery framework.
