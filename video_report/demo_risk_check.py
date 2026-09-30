"""
Live-demo risk check for the site's pricing engine (legacy_streamlit_site/models.py).

Sweeps the inputs a visitor can actually reach through the Pricing page's controls
(strike 0.01..5x spot, 7..365 days, every Heston slider at both ends of its range,
up to 50,000 Monte Carlo paths) and reports anything a live audience could see go
wrong: NaN or negative prices, put-call parity violations, prices outside
no-arbitrage bounds, implied-vol curves that break, and slow calls.
Reports only; changes nothing.
"""
from __future__ import annotations

import itertools
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "legacy_streamlit_site"))
warnings.filterwarnings("ignore")

import numpy as np
import models as M

S, R = 100.0, 0.053324
B = M.HESTON_BOUNDS
issues: list[str] = []


def flag(msg):
    issues.append(msg)
    print("  !!", msg)


def check_price(label, call, put, K, T):
    fwd_disc = S - K * np.exp(-R * T)
    for name, p in (("call", call), ("put", put)):
        if not np.isfinite(p):
            flag(f"{label}: {name} price is {p}")
        elif p < -1e-9:
            flag(f"{label}: {name} price negative ({p:.3g})")
    if np.isfinite(call) and np.isfinite(put):
        parity = call - put - fwd_disc
        if abs(parity) > 1e-6 * max(1.0, S):
            flag(f"{label}: put-call parity off by {parity:.3g}")
        if call > S + 1e-9:
            flag(f"{label}: call {call:.4g} exceeds spot")
        if put > K * np.exp(-R * T) + 1e-9:
            flag(f"{label}: put {put:.4g} exceeds discounted strike")


print("1) Heston semi-analytic price at every slider corner")
strikes = [0.01, 50, 80, 100, 120, 200, 500]
maturities = [7 / 365, 30 / 365, 365 / 365]
corners = list(itertools.product(*[B[n] for n in ("v0", "kappa", "theta", "xi", "rho")]))
slowest = 0.0
for params in corners:
    for T in maturities:
        t0 = time.perf_counter()
        calls = M.heston_price(S, np.array(strikes), T, R, *params, kind="call")
        puts = M.heston_price(S, np.array(strikes), T, R, *params, kind="put")
        slowest = max(slowest, time.perf_counter() - t0)
        for K, c, p in zip(strikes, np.atleast_1d(calls), np.atleast_1d(puts)):
            check_price(f"Heston {params} T={T*365:.0f}d K={K}", c, p, K, T)
print(f"  {len(corners) * len(maturities)} corner/maturity combos, slowest call pair {slowest*1000:.0f} ms")

print("2) Double Heston semi-analytic price at mixed corners")
slowest = 0.0
rng = np.random.default_rng(0)
for _ in range(400):
    p1 = [B[n][rng.integers(2)] for n in ("v0", "kappa", "theta", "xi", "rho")]
    p2 = [B[n][rng.integers(2)] for n in ("v0", "kappa", "theta", "xi", "rho")]
    T = maturities[rng.integers(3)]
    t0 = time.perf_counter()
    calls = M.double_heston_price(S, np.array(strikes), T, R, *p1, *p2, kind="call")
    puts = M.double_heston_price(S, np.array(strikes), T, R, *p1, *p2, kind="put")
    slowest = max(slowest, time.perf_counter() - t0)
    for K, c, p in zip(strikes, np.atleast_1d(calls), np.atleast_1d(puts)):
        check_price(f"DoubleHeston {p1}+{p2} T={T*365:.0f}d K={K}", c, p, K, T)
print(f"  400 random corner pairs, slowest call pair {slowest*1000:.0f} ms")

print("3) Black-Scholes edge cases")
for K in (0.01, 100, 500):
    for T in (0.0, 1 / 365, 1.0):
        for sig in (0.0, 1e-4, 0.2, 3.0):
            c = M.black_scholes(S, K, T, R, sig, "call")
            p = M.black_scholes(S, K, T, R, sig, "put")
            check_price(f"BS K={K} T={T} sigma={sig}", c, p, K, T)

print("4) Greeks at the Pricing page's shortest expiry and extreme strikes")
for K in (0.01, 50, 100, 500):
    for T in (1 / 365, 7 / 365):
        g = M.greeks(S, K, T, R, 0.2, "call")
        bad = {k: v for k, v in g.items() if not np.isfinite(v)}
        if bad:
            flag(f"greeks K={K} T={T*365:.0f}d non-finite: {bad}")

print("5) Implied vol round-trip on Heston prices across the chart's strike grid")
grid = np.linspace(80, 120, 41)
for params in [(0.04, 2.0, 0.04, 0.5, -0.7), (B["v0"][0], 10.0, B["theta"][0], 2.0, -0.99),
               (1.0, 0.1, 1.0, 2.0, 0.99)]:
    for T in (7 / 365, 365 / 365):
        prices = np.where(grid < S, M.heston_price(S, grid, T, R, *params, kind="put"),
                          M.heston_price(S, grid, T, R, *params, kind="call"))
        ivs = [M.implied_vol(p, S, k, T, R, "put" if k < S else "call") if p >= 0.05 else np.nan
               for p, k in zip(prices, grid)]
        n_ok = int(np.isfinite(ivs).sum())
        if n_ok == 0:
            flag(f"IV curve empty for Heston {params} T={T*365:.0f}d (whole chart line would vanish)")
        elif n_ok < len(grid) // 2:
            print(f"  note: IV curve only {n_ok}/{len(grid)} points for {params} T={T*365:.0f}d "
                  f"(expected where OTM prices fall below the 0.05 floor)")

print("6) Monte Carlo cost at the Pricing page's maximum (50,000 paths, 365 days)")
for name, fn in (
    ("GBM", lambda: M.gbm_paths(S, R, 0.2, 1.0, 50_000, 1, seed=42)),
    ("Heston", lambda: M.heston_paths(S, R, 1.0, 0.04, 2.0, 0.04, 0.5, -0.7, 50_000, 252, seed=42)),
    ("Double Heston", lambda: M.double_heston_paths(S, R, 1.0, 0.02, 5.0, 0.02, 0.5, -0.7,
                                                     0.02, 0.5, 0.02, 0.3, -0.7, 50_000, 252, seed=42)),
):
    t0 = time.perf_counter()
    paths = fn()
    dt = time.perf_counter() - t0
    mb = paths.nbytes / 1e6
    finite = np.isfinite(paths).all()
    print(f"  {name:14s} {dt:6.2f} s  {mb:6.0f} MB of paths  finite={finite}")
    if not finite:
        flag(f"{name} Monte Carlo produced non-finite paths")
    if dt > 5:
        flag(f"{name} Monte Carlo takes {dt:.1f}s at the slider maximum")

print("7) Monte Carlo vs semi-analytic agreement (Heston, default sliders, ATM, 1 year)")
paths = M.heston_paths(S, R, 1.0, 0.04, 2.0, 0.04, 0.5, -0.7, 50_000, 252, seed=42)
mc, se = M.price_from_paths(paths, 100, R, 1.0, "call")
cf = M.heston_price(S, 100, 1.0, R, 0.04, 2.0, 0.04, 0.5, -0.7, kind="call")
print(f"  MC {mc:.4f} ± {se:.4f}  vs formula {cf:.4f}  ({abs(mc-cf)/se:.1f} standard errors apart)")
if abs(mc - cf) > 4 * se:
    flag(f"Heston MC and formula disagree by {abs(mc-cf)/se:.1f} standard errors")

print()
print(f"TOTAL ISSUES: {len(issues)}")
