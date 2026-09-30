"""
Generates the figures for double_heston_report.md by calling the project's own
pricing functions directly (legacy_streamlit_site/models.py) and, for the fourth
figure, reading the project's own precomputed real-market ambiguity results
(outputs/ambiguity/ambiguity_surfaces.csv). No internet, no market data fetch,
no rewriting of the model -- every number here comes from running real code.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "legacy_streamlit_site"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import models as M

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 13,
    "axes.titlesize": 15, "axes.titleweight": "bold",
    "axes.labelsize": 13, "figure.facecolor": "white", "axes.facecolor": "white",
})
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

S, R = 100.0, 0.053324  # spot, same flat risk-free rate the project uses throughout
HESTON = dict(v0=0.04, kappa=2.0, theta=0.04, xi=0.5, rho=-0.7)
D1 = dict(v0=0.02, kappa=5.0, theta=0.02, xi=0.5, rho=-0.7)   # fast factor
D2 = dict(v0=0.02, kappa=0.5, theta=0.02, xi=0.3, rho=-0.7)   # slow factor


def iv_curve(price_fn, strikes, T, kind_below, kind_at_above):
    out = []
    for k in strikes:
        kind = kind_below if k < S else kind_at_above
        p = price_fn(k, kind)
        out.append(M.implied_vol(p, S, k, T, R, kind) if p and p > 1e-6 else np.nan)
    return 100 * np.array(out, dtype=float)


# --- Figure 1: the smile, three models, two maturities -----------------------------
strikes = np.linspace(80, 120, 41)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
for ax, T, label in zip(axes, [30 / 365, 180 / 365], ["30 days to expiry", "180 days to expiry"]):
    bs_sigma = np.sqrt(HESTON["v0"])
    bs = np.full_like(strikes, 100 * bs_sigma)
    he = iv_curve(lambda k, kd: M.heston_price(S, k, T, R, *HESTON.values(), kind=kd), strikes, T, "put", "call")
    dh = iv_curve(lambda k, kd: M.double_heston_price(S, k, T, R, *D1.values(), *D2.values(), kind=kd),
                  strikes, T, "put", "call")
    ax.plot(strikes, bs, "--", lw=2.5, color="#3987e5", label="Black-Scholes (flat)")
    ax.plot(strikes, he, lw=3, color="#199e70", label="Heston")
    ax.plot(strikes, dh, lw=2.5, color="#c98500", label="Double Heston")
    ax.axvline(S, color="#999", lw=1, ls=":")
    ax.set_title(label)
    ax.set_xlabel("Strike price")
axes[0].set_ylabel("Implied volatility (%)")
axes[0].legend(loc="upper right", fontsize=10.5, framealpha=0.9)
fig.suptitle("Letting volatility move bends a flat line into the market's actual skew", y=1.03, fontsize=14)
fig.tight_layout()
fig.savefig(OUT / "01_smile_comparison.png", bbox_inches="tight")
plt.close(fig)

# --- Figure 2: smile vs rho -------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
T = 90 / 365
for rho, color in zip([-0.9, -0.4, 0.0, 0.4], ["#8b0000", "#c98500", "#666666", "#2a78d6"]):
    params = dict(HESTON, rho=rho)
    curve = iv_curve(lambda k, kd: M.heston_price(S, k, T, R, *params.values(), kind=kd), strikes, T, "put", "call")
    ax.plot(strikes, curve, lw=2.6, color=color, label=f"rho = {rho:+.1f}")
ax.axvline(S, color="#999", lw=1, ls=":")
ax.set_xlabel("Strike price")
ax.set_ylabel("Implied volatility (%)")
ax.set_title("More negative rho tilts the smile into a downward skew")
ax.legend(fontsize=10.5)
fig.tight_layout()
fig.savefig(OUT / "02_smile_vs_rho.png", bbox_inches="tight")
plt.close(fig)

# --- Figure 3: simulated fast and slow variance paths -----------------------------
paths = M.double_heston_paths(S, R, 1.0, D1["v0"], D1["kappa"], D1["theta"], D1["xi"], D1["rho"],
                              D2["v0"], D2["kappa"], D2["theta"], D2["xi"], D2["rho"],
                              n_paths=4, n_steps=252, seed=7, antithetic=False)
# Re-simulate variance alone (paths above returns stock price, not variance) using the same
# internal step function so the two factors can be plotted directly against each other.
rng_v = np.random.default_rng(7)
n_steps, dt = 252, 1.0 / 252
v1 = np.full(1, D1["v0"]); v2 = np.full(1, D2["v0"])
v1_hist, v2_hist = [float(v1[0])], [float(v2[0])]
for _ in range(n_steps):
    v1, v1p, _ = M._variance_factor_step(v1, D1["kappa"], D1["theta"], D1["xi"], D1["rho"], dt, rng_v, False)
    v2, v2p, _ = M._variance_factor_step(v2, D2["kappa"], D2["theta"], D2["xi"], D2["rho"], dt, rng_v, False)
    v1_hist.append(float(max(v1[0], 0))); v2_hist.append(float(max(v2[0], 0)))
t = np.linspace(0, 1, n_steps + 1) * 252
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(t, np.sqrt(v1_hist) * 100, lw=2.2, color="#c98500", label="Fast factor (annualised vol %)")
ax.plot(t, np.sqrt(v2_hist) * 100, lw=2.6, color="#2a78d6", label="Slow factor (annualised vol %)")
ax.set_xlabel("Trading days")
ax.set_ylabel("Instantaneous volatility (%)")
ax.set_title("The fast factor keeps being pulled back; the slow one wanders for months")
ax.legend(fontsize=10.5)
fig.tight_layout()
fig.savefig(OUT / "03_variance_paths.png", bbox_inches="tight")
plt.close(fig)

# --- Figure 4: real-market ambiguity, from the project's own research results ------
amb = pd.read_csv(ROOT / "outputs" / "ambiguity" / "ambiguity_surfaces.csv")
# Same population as the headline figure in ambiguity_summary.json: surfaces with more
# than one price-equivalent fit (the rest have no pairwise distance and are stored as 0).
amb = amb[amb["price_equivalent_count"] > 1]
fig, ax = plt.subplots(figsize=(8.5, 4.8))
counts, _, _ = ax.hist(amb["median_pairwise_dispersion"], bins=40, color="#c98500", edgecolor="white", linewidth=0.4)
ax.set_ylim(0, counts.max() * 1.35)
ax.axvline(1.0, color="#8b0000", lw=2, ls="--", label="1.0 = as scattered as unrelated stocks")
ax.axvline(amb["median_pairwise_dispersion"].median(), color="#2a78d6", lw=2,
           label=f"median = {amb['median_pairwise_dispersion'].median():.2f}")
ax.set_xlabel("Pairwise dispersion among price-equivalent fits\n(units of the training set's own parameter spread)")
ax.set_ylabel(f"Real option surfaces (n = {len(amb):,})")
ax.set_title("On real NSE surfaces, equally good fits land further apart\nthan two unrelated stocks would")
ax.legend(fontsize=10, loc="upper left", framealpha=0.95)
fig.tight_layout()
fig.savefig(OUT / "04_real_market_ambiguity.png", bbox_inches="tight")
plt.close(fig)

print("wrote 4 figures to", OUT)

# --- worked examples (printed, for the report's Results section) -------------------
print()
print("=== worked examples (Black-Scholes vs Heston vs Double Heston, 1-year ATM call, spot=100) ===")
T = 1.0
bs = M.black_scholes(S, S, T, R, np.sqrt(HESTON["v0"]), "call")
he = M.heston_price(S, S, T, R, *HESTON.values(), kind="call")
dh = M.double_heston_price(S, S, T, R, *D1.values(), *D2.values(), kind="call")
print(f"Black-Scholes: {bs:.2f}   Heston: {he:.2f}   Double Heston: {dh:.2f}")

T2 = 30 / 365
k_otm = 90.0
bs2 = M.black_scholes(S, k_otm, T2, R, np.sqrt(HESTON["v0"]), "put")
he2 = M.heston_price(S, k_otm, T2, R, *HESTON.values(), kind="put")
print(f"30-day 10%-OTM put (strike 90): Black-Scholes {bs2:.3f}   Heston {he2:.3f}")

g = M.greeks(S, S, T, R, np.sqrt(HESTON["v0"]), "call")
print(f"1-year ATM call Greeks (Black-Scholes, sigma={np.sqrt(HESTON['v0']):.0%}): {g}")
