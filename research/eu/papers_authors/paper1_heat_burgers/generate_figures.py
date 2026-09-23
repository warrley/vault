"""
Generate high-quality publication figures for the 2D Burgers and Heat PINN paper.
"""
import os, warnings
import numpy as np
import torch
import torch.nn as nn
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
warnings.filterwarnings('ignore')

ROOT = "/home/warley/vault/research/eu/paper1_heat_burgers"
OUT  = os.path.join(ROOT, "new_figures")
MDIR = os.path.join(ROOT, "models")
os.makedirs(OUT, exist_ok=True)

DPI = 300

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "text.usetex": False,
    "axes.labelsize": 13, "axes.titlesize": 14,
    "xtick.labelsize": 11, "ytick.labelsize": 11,
    "legend.fontsize": 11,
})

SPEED_CMAP = LinearSegmentedColormap.from_list("speed_hot",
    ["#03001e","#0a1045","#0d47a1","#00bcd4","#76ff03","#ffea00","#ff6f00","#b71c1c"], N=512)

HEAT_CMAP = LinearSegmentedColormap.from_list("heat_plasma",
    ["#0d0221","#240046","#7b2d8b","#c6427a","#ff6e54","#ffd166","#ffffff"], N=512)

def build_pinn(in_dim, out_dim, hidden=64, layers=4):
    seq = []
    seq += [nn.Linear(in_dim, hidden), nn.Tanh()]
    for _ in range(layers - 1):
        seq += [nn.Linear(hidden, hidden), nn.Tanh()]
    seq += [nn.Linear(hidden, out_dim)]
    return nn.Sequential(*seq)

def load_burgers():
    ckpt = torch.load(os.path.join(MDIR,"pinn_burgers_2d_20k.pth"), map_location="cpu", weights_only=False)
    model = build_pinn(3, 2)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model, ckpt.get("nu", 0.01)

def load_heat():
    ckpt = torch.load(os.path.join(MDIR,"pinn_heat_2d_20k.pth"), map_location="cpu", weights_only=False)
    model = build_pinn(3, 1)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    return model, ckpt.get("alpha", 0.01)

def eval_burgers(model, x, y, t):
    with torch.no_grad():
        inp = torch.tensor(np.stack([x, y, t*np.ones_like(x)], axis=1), dtype=torch.float32)
        out = model(inp).numpy()
    u, v = out[:,0], out[:,1]
    return u, v, np.sqrt(u**2+v**2)

def eval_heat(model, x, y, t):
    with torch.no_grad():
        inp = torch.tensor(np.stack([x, y, t*np.ones_like(x)], axis=1), dtype=torch.float32)
        return model(inp).numpy().squeeze()

def make_grid_b(n=256):
    xi = np.linspace(-1,1,n); yi = np.linspace(-1,1,n)
    X,Y = np.meshgrid(xi,yi)
    return X, Y, X.ravel(), Y.ravel(), xi, yi

def make_grid_h(n=200):
    xi = np.linspace(0,1,n); yi = np.linspace(0,1,n)
    X,Y = np.meshgrid(xi,yi)
    return X, Y, X.ravel(), Y.ravel(), xi, yi

def _save(fig, name):
    base = os.path.join(OUT, name)
    fig.savefig(base+".pdf", dpi=DPI, bbox_inches='tight', facecolor=fig.get_facecolor())
    fig.savefig(base+".png", dpi=DPI, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"  saved → {name}.pdf / .png")
    plt.close(fig)

# ── BURGERS FIG 1: 6-snapshot speed field + directional quiver ──────────────
def fig_burgers_snapshots():
    print("[1/8] Burgers 6-snapshot speed + quiver …")
    model, nu = load_burgers()
    times  = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    N, NQ  = 256, 28
    X, Y, xf, yf, _, _ = make_grid_b(N)
    xq = np.linspace(-1,1,NQ); yq = np.linspace(-1,1,NQ)
    Xq, Yq = np.meshgrid(xq, yq)
    xqf, yqf = Xq.ravel(), Yq.ravel()

    data, vmax_g = [], 0
    for t in times:
        u,v,spd = eval_burgers(model, xf, yf, t)
        uq,vq,_ = eval_burgers(model, xqf, yqf, t)
        data.append((spd.reshape(N,N), uq.reshape(NQ,NQ), vq.reshape(NQ,NQ)))
        vmax_g = max(vmax_g, spd.max())

    fig, axes = plt.subplots(2, 3, figsize=(16,11))
    axes = axes.ravel()
    for i,(t,ax) in enumerate(zip(times, axes)):
        SPD, Uq, Vq = data[i]
        cf = ax.contourf(X, Y, SPD, levels=128, cmap=SPEED_CMAP, vmin=0, vmax=vmax_g)
        ax.contour(X, Y, SPD, levels=8, colors='white', alpha=0.12, linewidths=0.5)
        spq = np.sqrt(Uq**2+Vq**2)
        nf  = np.where(spq>1e-6, spq, 1e-6)
        Un, Vn = Uq/nf, Vq/nf
        scale  = spq/(vmax_g+1e-8)
        for ii in range(NQ):
            for jj in range(NQ):
                s = scale[ii,jj]
                if s < 0.02:
                    ax.plot(Xq[ii,jj], Yq[ii,jj], '.', color='white', ms=1.0, alpha=0.3)
                else:
                    ax.annotate("",
                        xy=(Xq[ii,jj]+Un[ii,jj]*0.048*s*2.5, Yq[ii,jj]+Vn[ii,jj]*0.048*s*2.5),
                        xytext=(Xq[ii,jj], Yq[ii,jj]),
                        arrowprops=dict(arrowstyle="-|>", color="white",
                            alpha=min(1.0,0.5+s*0.8), lw=0.6+s*0.8, mutation_scale=5+s*8))
        ax.set_xlim(-1,1); ax.set_ylim(-1,1); ax.set_aspect('equal')
        ax.set_title(fr"$t = {t:.1f}$", fontsize=15, fontweight='bold', pad=8)
        ax.set_xlabel(r"$x$", fontsize=12); ax.set_ylabel(r"$y$", fontsize=12)
        cb = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label(r"$\|\mathbf{u}\|$", fontsize=9)
    fig.suptitle(r"Burgers 2D — velocity field evolution ($\nu = 0.01$)",
                 fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    _save(fig, "burgers_snapshots_speed")

# ── BURGERS FIG 2: 4-panel collision story ───────────────────────────────────
def fig_burgers_collision():
    print("[2/8] Burgers collision 4-panel …")
    model, nu = load_burgers()
    times  = [0.0, 0.3, 0.5, 1.0]
    titles = [r"(a) $t=0.0$ — blobs separados",
              r"(b) $t=0.3$ — aproximando",
              r"(c) $t=0.5$ — colisão / fusão",
              r"(d) $t=1.0$ — fundidos, difundindo"]
    N, NQ = 300, 34
    X, Y, xf, yf, _, _ = make_grid_b(N)
    xq = np.linspace(-1,1,NQ); yq = np.linspace(-1,1,NQ)
    Xq, Yq = np.meshgrid(xq, yq)
    xqf, yqf = Xq.ravel(), Yq.ravel()

    data, vmax_g = [], 0
    for t in times:
        u,v,spd = eval_burgers(model, xf, yf, t)
        uq,vq,_ = eval_burgers(model, xqf, yqf, t)
        data.append((spd.reshape(N,N), uq.reshape(NQ,NQ), vq.reshape(NQ,NQ)))
        vmax_g = max(vmax_g, spd.max())

    fig, axes = plt.subplots(1, 4, figsize=(22, 6))
    im_ref = None
    for i,(ttl,ax) in enumerate(zip(titles, axes)):
        SPD, Uq, Vq = data[i]
        cf = ax.contourf(X, Y, SPD, levels=200, cmap=SPEED_CMAP, vmin=0, vmax=vmax_g)
        ax.contour(X, Y, SPD, levels=6, colors='white', alpha=0.15, linewidths=0.4)
        if i==0: im_ref=cf
        spq = np.sqrt(Uq**2+Vq**2)
        nf  = np.where(spq>1e-6, spq, 1e-6)
        Un, Vn = Uq/nf, Vq/nf
        scale  = spq/(vmax_g+1e-8)
        for ii in range(NQ):
            for jj in range(NQ):
                s = scale[ii,jj]
                if s < 0.025:
                    ax.plot(Xq[ii,jj], Yq[ii,jj], '.', color='white', ms=0.8, alpha=0.25)
                else:
                    ax.annotate("",
                        xy=(Xq[ii,jj]+Un[ii,jj]*0.05*s*2.2, Yq[ii,jj]+Vn[ii,jj]*0.05*s*2.2),
                        xytext=(Xq[ii,jj], Yq[ii,jj]),
                        arrowprops=dict(arrowstyle="-|>", color="white",
                            alpha=min(1.0,0.45+s*0.8), lw=0.5+s*0.9, mutation_scale=5+s*9))
        ax.set_xlim(-1,1); ax.set_ylim(-1,1); ax.set_aspect('equal')
        ax.set_title(ttl, fontsize=12, fontweight='bold', pad=6)
        ax.set_xlabel(r"$x$", fontsize=12); ax.set_ylabel(r"$y$", fontsize=12)
    cbar = fig.colorbar(im_ref, ax=axes.ravel().tolist(), fraction=0.012, pad=0.02)
    cbar.set_label(r"Speed  $\|\mathbf{u}\|$", fontsize=12)
    fig.suptitle(r"Burgers 2D — sequência de colisão dos blobs ($\nu = 0.01$)",
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    _save(fig, "burgers_collision_snapshots")

# ── BURGERS FIG 3: Streamlines ───────────────────────────────────────────────
def fig_burgers_streamlines():
    print("[3/8] Burgers streamlines …")
    model, nu = load_burgers()
    times  = [0.0, 0.5, 1.0]
    N = 200
    X, Y, xf, yf, xi, yi = make_grid_b(N)

    fig, axes = plt.subplots(1, 3, figsize=(17, 6))
    for i,(t,ax) in enumerate(zip(times, axes)):
        u,v,spd = eval_burgers(model, xf, yf, t)
        U, V, SPD = u.reshape(N,N), v.reshape(N,N), spd.reshape(N,N)
        cf = ax.contourf(X, Y, SPD, levels=150, cmap=SPEED_CMAP)
        ax.streamplot(xi, yi, U, V, color=SPD, cmap=SPEED_CMAP,
                      linewidth=1.6, density=1.6, arrowsize=1.4,
                      arrowstyle='->', minlength=0.05)
        ax.set_xlim(-1,1); ax.set_ylim(-1,1); ax.set_aspect('equal')
        ax.set_title(fr"$t = {t:.1f}$", fontsize=14, fontweight='bold', pad=8)
        ax.set_xlabel(r"$x$", fontsize=12); ax.set_ylabel(r"$y$", fontsize=12)
        cb = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label(r"$\|\mathbf{u}\|$", fontsize=10)
    fig.suptitle(r"Burgers 2D — streamlines ($\nu = 0.01$)",
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    _save(fig, "burgers_streamlines")

# ── BURGERS FIG 4: u & v component panels ────────────────────────────────────
def fig_burgers_uv_panels():
    print("[4/8] Burgers u/v panels …")
    model, nu = load_burgers()
    times  = [0.0, 0.5, 1.0]
    N = 256
    X, Y, xf, yf, _, _ = make_grid_b(N)

    data, au, av = [], 0, 0
    for t in times:
        u,v,_ = eval_burgers(model, xf, yf, t)
        U,V   = u.reshape(N,N), v.reshape(N,N)
        data.append((U,V))
        au = max(au, np.abs(U).max()); av = max(av, np.abs(V).max())

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    for col,(t) in enumerate(times):
        U,V = data[col]
        for row,(arr,amax,comp) in enumerate([(U,au,r"$u$"),(V,av,r"$v$")]):
            ax = axes[row,col]
            cf = ax.contourf(X, Y, arr, levels=120, cmap="RdBu_r", vmin=-amax, vmax=amax)
            ax.contour(X, Y, arr, levels=[0], colors='k', linewidths=1.2)
            ax.set_aspect('equal')
            ax.set_xlabel(r"$x$", fontsize=11); ax.set_ylabel(r"$y$", fontsize=11)
            if row==0: ax.set_title(fr"$t = {t:.1f}$", fontsize=13, fontweight='bold', pad=6)
            cb = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
            cb.set_label(comp, fontsize=11)
    fig.suptitle(r"Burgers 2D — componentes $u$ e $v$ ($\nu = 0.01$)",
                 fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    _save(fig, "burgers_uv_components")

# ── HEAT FIG 5: 3D surface evolution 6 snapshots ─────────────────────────────
def fig_heat_3d_evolution():
    print("[5/8] Heat 3D evolution (6 snapshots) …")
    model, alpha = load_heat()
    times = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    N = 80
    xi = np.linspace(0,1,N); yi = np.linspace(0,1,N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    z_data, zmax = [], 0
    for t in times:
        u = eval_heat(model, xf, yf, t).reshape(N,N)
        z_data.append(u); zmax = max(zmax, u.max())

    fig = plt.figure(figsize=(18, 12))
    fig.patch.set_facecolor('#f8f8f8')
    for i,(t,Z) in enumerate(zip(times, z_data)):
        ax = fig.add_subplot(2, 3, i+1, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap=HEAT_CMAP, vmin=0, vmax=zmax,
                               linewidth=0, antialiased=True, alpha=0.96)
        ax.contourf(X, Y, Z, zdir='z', offset=-0.05, cmap=HEAT_CMAP,
                    vmin=0, vmax=zmax, alpha=0.35, levels=30)
        ax.set_zlim(-0.05, zmax*1.05)
        ax.set_xlim(0,1); ax.set_ylim(0,1)
        ax.set_xlabel(r"$x$", fontsize=10, labelpad=4)
        ax.set_ylabel(r"$y$", fontsize=10, labelpad=4)
        ax.set_zlabel(r"$u$", fontsize=10, labelpad=4)
        ax.set_title(fr"$t = {t:.1f}$", fontsize=14, fontweight='bold', pad=10)
        ax.view_init(elev=28, azim=-55)
        ax.tick_params(labelsize=8)
        ax.set_facecolor('#f0f0f0')
        cb = fig.colorbar(surf, ax=ax, fraction=0.03, pad=0.06, shrink=0.7)
        cb.set_label(r"$u$", fontsize=9); cb.ax.tick_params(labelsize=7)
    fig.suptitle(r"Heat Equation 2D — 3D surface evolution ($\alpha = 0.01$)",
                 fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    _save(fig, "heat_3d_evolution")

# ── HEAT FIG 6: 2D heatmap evolution ─────────────────────────────────────────
def fig_heat_heatmap():
    print("[6/8] Heat 2D heatmap evolution …")
    model, alpha = load_heat()
    times = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    N = 250
    X, Y, xf, yf, _, _ = make_grid_h(N)

    z_data, zmax = [], 0
    for t in times:
        u = eval_heat(model, xf, yf, t).reshape(N,N)
        z_data.append(u); zmax = max(zmax, u.max())

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.ravel()
    for i,(lbl_t,Z) in enumerate(zip(times, z_data)):
        ax = axes[i]
        cf = ax.contourf(X, Y, Z, levels=100, cmap=HEAT_CMAP, vmin=0, vmax=zmax)
        ax.contour(X, Y, Z, levels=8, colors='white', alpha=0.25, linewidths=0.6)
        ax.set_aspect('equal')
        ax.set_title(fr"$t = {lbl_t:.1f}$", fontsize=14, fontweight='bold', pad=6)
        ax.set_xlabel(r"$x$", fontsize=12); ax.set_ylabel(r"$y$", fontsize=12)
        cb = fig.colorbar(cf, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label(r"$u(x,y,t)$", fontsize=10)
    fig.suptitle(r"Heat Equation 2D — temperature field evolution ($\alpha = 0.01$)",
                 fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    _save(fig, "heat_heatmap_evolution")

# ── HEAT FIG 7: 3D stacked dark background ───────────────────────────────────
def fig_heat_3d_stacked():
    print("[7/8] Heat 3D stacked dark …")
    model, alpha = load_heat()
    times = [0.0, 0.15, 0.3, 0.5, 0.7, 1.0]
    N = 60
    xi = np.linspace(0,1,N); yi = np.linspace(0,1,N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    surfs, zmax = [], 0
    for t in times:
        u = eval_heat(model, xf, yf, t).reshape(N,N)
        surfs.append(u); zmax = max(zmax, u.max())

    fig = plt.figure(figsize=(14, 9))
    ax  = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#0a0a0a'); fig.patch.set_facecolor('#0a0a0a')

    for idx,(t,Z) in enumerate(zip(times, surfs)):
        frac  = idx/(len(times)-1)
        color = HEAT_CMAP(0.15+frac*0.85)
        ax.plot_surface(X, Y, Z, color=color,
                        alpha=0.60-0.06*idx, linewidth=0, antialiased=True)

    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_zlim(0, zmax*1.1)
    ax.set_xlabel(r"$x$", color='white', fontsize=12, labelpad=8)
    ax.set_ylabel(r"$y$", color='white', fontsize=12, labelpad=8)
    ax.set_zlabel(r"$u$", color='white', fontsize=12, labelpad=8)
    ax.tick_params(colors='white', labelsize=8)
    ax.xaxis.pane.fill = False; ax.yaxis.pane.fill = False; ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('#333333')
    ax.yaxis.pane.set_edgecolor('#333333')
    ax.zaxis.pane.set_edgecolor('#333333')
    ax.grid(True, color='#222222', alpha=0.4)
    ax.view_init(elev=22, azim=-50)
    ax.set_title(r"Heat 2D — superfícies 3D sobrepostas ao longo do tempo",
                 color='white', fontsize=14, fontweight='bold', pad=18)

    # Legend manually
    from matplotlib.lines import Line2D
    handles = [Line2D([0],[0], color=HEAT_CMAP(0.15+i/(len(times)-1)*0.85),
               lw=4, label=f"t={t:.2f}") for i,t in enumerate(times)]
    ax.legend(handles=handles, loc='upper right', framealpha=0.2,
              labelcolor='white', fontsize=9)

    plt.tight_layout()
    _save(fig, "heat_3d_stacked")

# ── HEAT FIG 8: Large 4-panel 3D ─────────────────────────────────────────────
def fig_heat_3d_large():
    print("[8/8] Heat 3D large 4-panel …")
    model, alpha = load_heat()
    times  = [0.0, 0.3, 0.7, 1.0]
    labels = [r"$(a)\; t=0.0$", r"$(b)\; t=0.3$",
              r"$(c)\; t=0.7$", r"$(d)\; t=1.0$"]
    N = 100
    xi = np.linspace(0,1,N); yi = np.linspace(0,1,N)
    X, Y = np.meshgrid(xi, yi)
    xf, yf = X.ravel(), Y.ravel()

    z_data, zmax = [], 0
    for t in times:
        u = eval_heat(model, xf, yf, t).reshape(N,N)
        z_data.append(u); zmax = max(zmax, u.max())

    fig = plt.figure(figsize=(22, 6.5))
    for i,(lbl,Z) in enumerate(zip(labels, z_data)):
        ax = fig.add_subplot(1, 4, i+1, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap=HEAT_CMAP, vmin=0, vmax=zmax,
                               linewidth=0, antialiased=True, alpha=0.97,
                               rstride=1, cstride=1)
        ax.contourf(X, Y, Z, zdir='z', offset=0, cmap=HEAT_CMAP,
                    vmin=0, vmax=zmax, alpha=0.3, levels=20)
        ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_zlim(0, zmax*1.05)
        ax.set_xlabel(r"$x$", fontsize=10, labelpad=3)
        ax.set_ylabel(r"$y$", fontsize=10, labelpad=3)
        ax.set_zlabel(r"$u$", fontsize=10, labelpad=3)
        ax.set_title(lbl, fontsize=13, fontweight='bold', pad=8)
        ax.view_init(elev=30, azim=-60)
        ax.tick_params(labelsize=7)
        if i==len(times)-1:
            cb = fig.colorbar(surf, ax=ax, fraction=0.05, pad=0.12, shrink=0.8)
            cb.set_label(r"$u$", fontsize=11)
    fig.suptitle(r"Heat Equation 2D — 3D surface snapshots ($\alpha = 0.01$)",
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    _save(fig, "heat_3d_snapshots_large")

# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*55)
    print("Generating publication-quality PINN figures")
    print(f"Output: {OUT}")
    print("="*55)
    fig_burgers_snapshots()
    fig_burgers_collision()
    fig_burgers_streamlines()
    fig_burgers_uv_panels()
    fig_heat_3d_evolution()
    fig_heat_heatmap()
    fig_heat_3d_stacked()
    fig_heat_3d_large()
    print("="*55)
    print("Done! All figures saved.")
