---
tags:
  - research/pinns
  - causality
  - optimization
  - scientific-ml
parent: "[[research/PINNs and Reaction-Diffusion Systems]]"
date: 2025-08-26
---

# Causal PINNs and Temporal Weighting

*(Based on: Wang, Sankaran, Perdikaris - "Respecting Causality Is All You Need for Training Physics-Informed Neural Networks", arXiv:2203.07404)*

### 1. Motivation: Physical Causality
In dynamical systems, the physical state at $t_i$ depends strictly on preceding states $\{t_k\}_{k < i}$. Standard PINNs optimize all collocation points simultaneously across $[0, T]$, violating this causal dependence and finding erroneous trivial shortcuts at later times.

### 2. Mathematical Formulation
The temporal domain is partitioned into discrete time buckets $\{t_1, t_2, \dots, t_{N_t}\}$. The weighted residual loss is formulated as:

$$\mathcal{L}_r(\theta) = \frac{1}{N_t} \sum_{i=1}^{N_t} w_i \mathcal{L}(t_i, \theta)$$

where the causality weights $w_i$ are defined as:
$$w_i = \exp\left( -\epsilon \sum_{k=1}^{i-1} \mathcal{L}(t_k, \theta) \right), \quad \text{for } i \ge 2, \quad w_1 = 1$$

- $\epsilon > 0$: Causality parameter controlling steepness.
- If errors at preceding times are large, $w_i \to 0$ (loss at $t_i$ is suppressed).
- As early time steps converge ($\mathcal{L}(t_k) \to 0$), $w_i \to 1$, allowing the optimization frontier to move forward in time.

### 3. Implementation Rule: Stop-Gradient (`detach()`)
The weights $w_i$ must be detached from the computational graph during backpropagation:
```python
# cum_loss accumulates L(t_1) ... L(t_{i-1})
w = torch.exp(-eps * shifted_cum_loss).detach()
loss_causal = torch.mean(w * time_losses)
```
Without `detach()`, gradient descent would artificially increase earlier losses to force $w_i \to 0$.

### 4. Convergence Metric
Monitoring $\min_i(w_i) \in [0, 1]$ serves as an explicit convergence indicator:
- $\min_i(w_i) \approx 0 \implies$ Optimization is blocked at early time steps.
- $\min_i(w_i) \to 1 \implies$ The physical solution has causally propagated across the entire time horizon.

---

### Causality Takeaway

> [!abstract] Causal PINN Takeaway
> Causal PINNs enforce forward-in-time propagation by downweighting future PDE residuals exponentially until past residuals are minimized. `detach()` is mathematically necessary to prevent adversarial weight collapse.
