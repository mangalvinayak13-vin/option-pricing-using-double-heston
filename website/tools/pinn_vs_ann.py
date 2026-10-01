"""PINN vs ANN, computed: how much does knowing the physics help a network price options?

Two identical networks (4 inputs -> 3 x 64 tanh -> 1) see the same 48 exact Double Heston call
prices, made by the project's own pricer (legacy_streamlit_site/models.py, unchanged) at random
points of (moneyness s = S/K, slow variance v1, fast variance v2, time to expiry tau).
  * ANN: fits those 48 prices, nothing else.
  * PINN: fits the same 48 prices AND satisfies the Double Heston pricing equation at 4,096
    collocation points AND the payoff max(s - 1, 0) at expiry.
Both are then compared with the exact pricer: on 2,000 fresh points across all four inputs, and on
a slice at today's variances (v1 = v2 = 0.02) drawn in 3D on the home page.

Pricing equation (c = C/K, tau = time to expiry):
  c_tau = 1/2 (v1+v2) s^2 c_ss + (r-q) s c_s - r c
          + sum_i [ k_i (th_i - v_i) c_vi + 1/2 xi_i^2 v_i c_vivi + rho_i xi_i v_i s c_svi ]

python3 website/tools/pinn_vs_ann.py      -> website/assets/data/pinn_vs_ann.json  (~3 min on an M-series CPU)
"""
from __future__ import annotations

import importlib.util
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

torch.set_default_dtype(torch.float64)
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("dh_models", ROOT / "legacy_streamlit_site" / "models.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
SITE = json.loads((HERE / "assets" / "data" / "site.json").read_text())
R, Q = SITE["contract"]["rate"], SITE["contract"]["carry"]
P = dict(v0_1=0.02, kappa1=0.5, theta1=0.02, xi1=0.3, rho1=-0.7, v0_2=0.02, kappa2=5.0, theta2=0.02, xi2=0.5, rho2=-0.7)
LO = np.array([0.70, 0.004, 0.004, 0.03])
HI = np.array([1.30, 0.060, 0.060, 1.00])
SEED, N_DATA, N_COLL, N_IC = 7, 48, 4096, 512


def exact(s, v1, v2, tau):
    """c = C/K for a call, using homogeneity: C(s, 1) = s * C(1, 1/s); vectorised over strikes."""
    s = np.atleast_1d(s)
    p = dict(P, v0_1=float(v1), v0_2=float(v2))
    c1 = np.atleast_1d(M.double_heston_price(1.0, 1.0 / s, float(tau), R, **p, kind="call", q=Q))
    return s * c1


def sample(rng, n):
    return LO + (HI - LO) * rng.random((n, 4))


class Net(torch.nn.Module):
    def __init__(self, w=64):
        super().__init__()
        self.f = torch.nn.Sequential(torch.nn.Linear(4, w), torch.nn.Tanh(), torch.nn.Linear(w, w), torch.nn.Tanh(),
                                     torch.nn.Linear(w, w), torch.nn.Tanh(), torch.nn.Linear(w, 1))
        self.lo, self.hi = torch.tensor(LO), torch.tensor(HI)

    def forward(self, x):  # x: (n, 4) physical inputs
        z = 2 * (x - self.lo) / (self.hi - self.lo) - 1
        return self.f(z).squeeze(-1)


def residual(net, x):
    x = x.clone().requires_grad_(True)
    c = net(x)
    g = torch.autograd.grad(c.sum(), x, create_graph=True)[0]
    cs, cv1, cv2, ct = g[:, 0], g[:, 1], g[:, 2], g[:, 3]
    gs = torch.autograd.grad(cs.sum(), x, create_graph=True)[0]
    css, csv1, csv2 = gs[:, 0], gs[:, 1], gs[:, 2]
    cv1v1 = torch.autograd.grad(cv1.sum(), x, create_graph=True)[0][:, 1]
    cv2v2 = torch.autograd.grad(cv2.sum(), x, create_graph=True)[0][:, 2]
    s, v1, v2 = x[:, 0], x[:, 1], x[:, 2]
    rhs = (0.5 * (v1 + v2) * s * s * css + (R - Q) * s * cs - R * c
           + P["kappa1"] * (P["theta1"] - v1) * cv1 + 0.5 * P["xi1"] ** 2 * v1 * cv1v1 + P["rho1"] * P["xi1"] * v1 * s * csv1
           + P["kappa2"] * (P["theta2"] - v2) * cv2 + 0.5 * P["xi2"] ** 2 * v2 * cv2v2 + P["rho2"] * P["xi2"] * v2 * s * csv2)
    return ct - rhs


def train(physics: bool, xd, yd, xc, xic, yic, steps=10000):
    torch.manual_seed(SEED)
    net = Net()
    opt = torch.optim.Adam(net.parameters(), lr=3e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=1e-4)
    scale = float(yd.std())
    for it in range(steps):
        opt.zero_grad()
        loss = ((net(xd) - yd) ** 2).mean() / scale ** 2
        if physics:
            loss = loss + 1.0 * (residual(net, xc) ** 2).mean() / scale ** 2 + ((net(xic) - yic) ** 2).mean() / scale ** 2
        loss.backward()
        opt.step()
        sched.step()
        if it % 2500 == 0 or it == steps - 1:
            print(f"  {'PINN' if physics else 'ANN '} step {it:5d} loss {loss.item():.3e}")
    return net


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    xd = sample(rng, N_DATA)
    yd = np.array([exact(*row)[0] for row in xd])
    xc = sample(rng, N_COLL)
    xic = sample(rng, N_IC); xic[:, 3] = 0.0
    yic = np.maximum(xic[:, 0] - 1.0, 0.0)
    T = lambda a: torch.tensor(a)
    print(f"data ready ({N_DATA} exact prices) in {time.time() - t0:.1f}s")
    ann = train(False, T(xd), T(yd), None, None, None)
    pinn = train(True, T(xd), T(yd), T(xc), T(xic), T(yic))

    # fresh test points across all four inputs
    xt = sample(np.random.default_rng(99), 2000)
    yt = np.array([exact(*row)[0] for row in xt])
    with torch.no_grad():
        pa, pp = ann(T(xt)).numpy(), pinn(T(xt)).numpy()
    rmse = lambda a: float(np.sqrt(np.mean((a - yt) ** 2)))
    ra, rp = residual(ann, T(xt)).detach().numpy(), residual(pinn, T(xt)).detach().numpy()

    # the slice drawn in 3D: today's variances
    ss = np.round(np.linspace(0.75, 1.25, 41), 4)
    ts = np.round(np.linspace(0.04, 1.0, 31), 4)
    ex = np.array([exact(ss, 0.02, 0.02, t) for t in ts])                       # (31, 41)
    grid = np.array([[s, 0.02, 0.02, t] for t in ts for s in ss])
    with torch.no_grad():
        ga = ann(T(grid)).numpy().reshape(len(ts), len(ss))
        gp = pinn(T(grid)).numpy().reshape(len(ts), len(ss))
    gra = residual(ann, T(grid)).detach().numpy().reshape(len(ts), len(ss))
    grp = residual(pinn, T(grid)).detach().numpy().reshape(len(ts), len(ss))
    viol = lambda g: {"negative_prices": int((g < -1e-4).sum()),
                      "price_falls_as_share_rises": int((np.diff(g, axis=1) < -1e-4).sum())}
    out = {
        "setup": {"data_points": N_DATA, "collocation_points": N_COLL, "payoff_points": N_IC, "network": "4 inputs, 3 x 64 tanh, 1 output",
                  "steps": 10000, "seed": SEED, "rate": R, "carry": Q, "settings": P, "domain_lo": LO.tolist(), "domain_hi": HI.tolist(),
                  "slice": {"v1": 0.02, "v2": 0.02}},
        "test": {"points": 2000,
                 "ann_rmse": rmse(pa), "pinn_rmse": rmse(pp),
                 "ann_rel_rmse": rmse(pa) / float(np.mean(np.abs(yt))), "pinn_rel_rmse": rmse(pp) / float(np.mean(np.abs(yt))),
                 "ann_pde_residual_rms": float(np.sqrt(np.mean(ra ** 2))), "pinn_pde_residual_rms": float(np.sqrt(np.mean(rp ** 2)))},
        "slice": {"s": ss.tolist(), "tau": ts.tolist(), "exact": ex.round(6).tolist(), "ann": ga.round(6).tolist(), "pinn": gp.round(6).tolist(),
                  "ann_residual": gra.round(6).tolist(), "pinn_residual": grp.round(6).tolist(),
                  "ann_rmse": float(np.sqrt(np.mean((ga - ex) ** 2))), "pinn_rmse": float(np.sqrt(np.mean((gp - ex) ** 2))),
                  "ann_violations": viol(ga), "pinn_violations": viol(gp)},
        "seconds": round(time.time() - t0, 1),
    }
    (HERE / "assets" / "data" / "pinn_vs_ann.json").write_text(json.dumps(out))
    print(json.dumps({k: out[k] for k in ("test", "seconds")}, indent=1))
    print("slice rmse", out["slice"]["ann_rmse"], out["slice"]["pinn_rmse"], out["slice"]["ann_violations"], out["slice"]["pinn_violations"])


if __name__ == "__main__":
    main()
