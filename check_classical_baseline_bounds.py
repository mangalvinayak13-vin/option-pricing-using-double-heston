"""
Does run_classical_baseline.py's flat +/-8 latent z-box ever bind?

run_classical_baseline.py bounds the optimizer the same way the REAL-market scripts
did before bug 1 was fixed there: a flat box on each latent coordinate independently,
not a physical-parameter penalty from src/plausible_bounds.py. That was fine on real
data ONLY after adding the physical-bound penalty, because a flat box does not bound
composite/derived parameters like kappa_fast = kappa_slow * (1 + exp(z_i)), a product
of two coordinates, and partial/noisy real surfaces have flat-enough directions that
the optimizer actually ran to the box edge there.

This script re-runs the exact same calibration (same data split, same seed=0) but
additionally records, per surface, whether any of the 10 recovered latent coordinates
sits within 3% of the +/-8 box edge -- the same near-bound diagnostic used elsewhere
in this project (src/plausible_bounds.near_bound_parameters), applied here to the
latent box itself rather than a physical range, since that is what LATENT_BOX=8.0
actually constrains in this script.

The published "decisive result" (median skill 1.80, price-equivalent solutions worse
than guessing the mean) came from this script's summary metrics, which do not persist
per-surface recovered vectors, so there was no artifact to check this against without
re-running.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
from scipy.optimize import least_squares

import run_classical_baseline as B
from mentor_dh_pinn import params_v2 as P

REL_TOL = 0.03  # within 3% of the box edge counts as "at the bound"


def calibrate_with_z(target_prices, maturities, rate, carry, n_starts, rng):
    """Same as run_classical_baseline.calibrate(), but also returns best_z directly
    instead of re-deriving it by round-tripping through P.encode() afterward."""
    best_cost, best_z = np.inf, None
    lo, hi = np.full(10, -B.LATENT_BOX), np.full(10, B.LATENT_BOX)

    def residuals(z):
        try:
            out = B.price_from_latent(z, maturities, rate, carry) - target_prices
            return out if np.isfinite(out).all() else np.full(len(target_prices), 1e3)
        except Exception:
            return np.full(len(target_prices), 1e3)

    for _ in range(n_starts):
        z0 = np.clip(rng.normal(0.0, 1.0, size=10), -B.LATENT_BOX + 1, B.LATENT_BOX - 1)
        try:
            sol = least_squares(residuals, z0, bounds=(lo, hi), method="trf", max_nfev=1500)
        except Exception:
            continue
        if sol.cost < best_cost:
            best_cost, best_z = sol.cost, sol.x

    if best_z is None:
        return None, np.nan, None

    vector = np.asarray(P.to_array(P.decode(best_z)), float)
    rmse = float(np.sqrt(np.mean(residuals(best_z) ** 2)))
    return vector, rmse, best_z


def main() -> int:
    rng = np.random.default_rng(0)

    prices, cond, truth = [], [], []
    with open(ROOT / "data" / "final_r2_clean_10000" / "surfaces.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            if len(rec["prices"]) != 20:
                continue
            mats = sorted(set(rec["maturities"]))
            prices.append(rec["prices"])
            cond.append([mats[0], mats[1], rec["rates"][0], rec["carries"][0]])
            p = rec["metadata"]["parameters_canonical_order"]
            truth.append([p[n] for n in P.CANONICAL])
    prices, cond = np.array(prices), np.array(cond)

    import torch
    from torch.utils.data import TensorDataset, random_split
    n = len(prices)
    ntr, nva = int(0.7 * n), int(0.15 * n)
    _, _, te = random_split(TensorDataset(torch.zeros(n)), [ntr, nva, n - ntr - nva],
                            generator=torch.Generator().manual_seed(42))
    test_idx = np.asarray(te.indices)

    n_surfaces = 150
    starts = 4
    chosen = rng.choice(test_idx, size=min(n_surfaces, len(test_idx)), replace=False)
    print(f"re-calibrating {len(chosen)} surfaces, {starts} starts each, "
          f"checking latent-box proximity (box = +/-{B.LATENT_BOX})")

    edge = B.LATENT_BOX * (1 - REL_TOL)
    near_bound_surfaces = 0
    near_bound_axis_counts = np.zeros(10, int)
    max_abs_z = []

    for count, i in enumerate(chosen, 1):
        m1, m2, rate, carry = cond[i]
        vec, prmse, z = calibrate_with_z(prices[i], (m1, m2), rate, carry, starts, rng)
        if vec is None:
            continue
        hit = np.abs(z) >= edge
        if hit.any():
            near_bound_surfaces += 1
            near_bound_axis_counts += hit.astype(int)
        max_abs_z.append(float(np.max(np.abs(z))))
        if count % 25 == 0:
            print(f"  {count}/{len(chosen)} done")

    print()
    print(f"surfaces with >=1 latent coordinate within {REL_TOL*100:.0f}% of the "
          f"+/-{B.LATENT_BOX} box edge: {near_bound_surfaces} / {len(max_abs_z)} "
          f"({near_bound_surfaces / len(max_abs_z) * 100:.1f}%)")
    print(f"per-axis near-bound counts (kappa_s theta_s sigma_s rho_s v0_s "
          f"kappa_f theta_f sigma_f rho_f v0_f):")
    print(" ", near_bound_axis_counts.tolist())
    print(f"median max|z| across surfaces: {np.median(max_abs_z):.2f} "
          f"(box is {B.LATENT_BOX})")
    print(f"max max|z| across surfaces: {np.max(max_abs_z):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
