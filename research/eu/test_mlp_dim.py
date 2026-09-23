import torch
import torch.nn as nn

class IrregularHeatPINN(nn.Module):
    def __init__(self, hidden_dim=128, num_layers=5):
        super().__init__()
        layers = []
        layers.append(nn.Linear(3, hidden_dim))
        layers.append(nn.Tanh())
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x, y, t):
        return self.net(torch.cat([x, y, t], dim=1))

m = IrregularHeatPINN(hidden_dim=128, num_layers=5)
# In PyTorch:
# Layer 0: Linear(3, 128) -> W: 128x3 = 384, b: 128 -> total 512
# Layer 1: Linear(128, 128) -> W: 128x128 = 16384, b: 128 -> total 16512
# Layer 2: Linear(128, 128) -> total 16512
# Layer 3: Linear(128, 128) -> total 16512
# Layer 4: Linear(128, 128) -> total 16512
# Layer 5: Linear(128, 1) -> W: 1x128 = 128, b: 1 -> total 129
total = sum(p.numel() for p in m.parameters())
print("Total parameters:", total)
for name, p in m.named_parameters():
    print(name, p.shape)
