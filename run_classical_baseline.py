"""
Classical least-squares calibration on the same surfaces the networks were scored on.

This is the missing third arm. The project's existing G2 ambiguity diagnostic used
four representative cases; the networks were scored on a 1,500-surface test split.
Until a classical optimizer runs on *that* split, "the networks do badly" and "the
problem is hard" are not distinguishable.

Held identical to the neural runs so the comparison means something:
  - the same frozen production pricer,
  - the same params_v2 latent coordinates (so every iterate is a valid parameter
    vector and the optimizer never has to handle a constraint boundary),
  - the same skill metric, RMSE divided by the parameter's spread in the split.

The optimizer is given a large advantage over the networks on purpose: it sees the
exact prices of the surface it is fitting and may take many multi-starts, while a
network gets one forward pass. If it still fails to recover parameters while fitting
prices to near machine precision, the ceiling is information in the surface, not
model capacity.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from mentor_dh_pinn import params_v2 as P
from src.double_heston import price_double_heston_surface
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
SPOT = 100.0


def price_from_latent(z: np.ndarray, maturities, rate, carry, node_count=64) -> np.ndarray:
    vector = np.asarray(P.to_array(P.decode(z)), float)
    out = np.zeros(len(CANONICAL_SLOT_KEYS), float)
    for rank in R2_EXPIRY_RANKS:
        idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS) if k.expiry_rank == rank]
        keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
        strikes = np.array([SPOT * np.exp(k.target_log_moneyness) for k in keys], float)
        mats = np.full(len(keys), maturities[rank - 1], float)
        out[np.asarray(idx, int)] = price_double_heston_surface(
            SPOT, strikes, mats, rate, carry,
            [k.option_type for k in keys], vector, node_count=node_count,
        )
    return out / SPOT


def calibrate(target_prices, maturities, rate, carry, n_starts, rng):
    """Multi-start least squares in latent coordinates. Returns (best_vector, price_rmse)."""
    best_cost, best_z = np.inf, None

    def residuals(z):
        try:
            return price_from_latent(z, maturities, rate, carry) - target_prices
        except Exception:
            return np.full(len(target_prices), 1e3)

    for _ in range(n_starts):
        z0 = rng.normal(0.0, 1.0, size=10)
        try:
            sol = least_squares(residuals, z0, method="lm", max_nfev=2000)
        except Exception:
            continue
        if sol.cost < best_cost:
            best_cost, best_z = sol.cost, sol.x

    if best_z is None:
        return None, np.nan

    vector = np.asarray(P.to_array(P.decode(best_z)), float)
    rmse = float(np.sqrt(np.mean(residuals(best_z) ** 2)))
    return vector, rmse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surfaces", type=int, default=150,
                    help="How many test surfaces to calibrate (each needs many pricer calls)")
    ap.add_argument("--starts", type=int, default=4, help="Multi-starts per surface")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "classical"))
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Rebuild the exact same split the networks used.
    prices, cond, truth = [], [], []
    with open(PROJECT_ROOT / "data" / "final_r2_clean_10000" / "surfaces.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            if len(rec["prices"]) != 20:
                continue
            mats = sorted(set(rec["maturities"]))
            prices.append(rec["prices"])
            cond.append([mats[0], mats[1], rec["rates"][0], rec["carries"][0]])
            p = rec["metadata"]["parameters_canonical_order"]
            truth.append([p[n] for n in P.CANONICAL])
    prices, cond, truth = np.array(prices), np.array(cond), np.array(truth)

    import torch
    from torch.utils.data import TensorDataset, random_split
    n = len(prices)
    ntr, nva = int(0.7 * n), int(0.15 * n)
    _, _, te = random_split(TensorDataset(torch.zeros(n)), [ntr, nva, n - ntr - nva],
                            generator=torch.Generator().manual_seed(42))
    test_idx = np.asarray(te.indices)

    chosen = rng.choice(test_idx, size=min(args.surfaces, len(test_idx)), replace=False)
    logger.info("calibrating %d of %d test surfaces, %d starts each",
                len(chosen), len(test_idx), args.starts)

    recovered, actual, price_rmses = [], [], []
    for count, i in enumerate(chosen, 1):
        m1, m2, rate, carry = cond[i]
        vec, prmse = calibrate(prices[i], (m1, m2), rate, carry, args.starts, rng)
        if vec is None:
            continue
        recovered.append(vec)
        actual.append(truth[i])
        price_rmses.append(prmse)
        if count % 25 == 0:
            logger.info("  %d/%d done, median price RMSE so far %.3e",
                        count, len(chosen), float(np.median(price_rmses)))

    recovered, actual = np.array(recovered), np.array(actual)

    skill, param_rmse = {}, {}
    for i, name in enumerate(SHORT):
        rmse = float(np.sqrt(np.mean((recovered[:, i] - actual[:, i]) ** 2)))
        sd = float(np.std(actual[:, i]))
        param_rmse[name] = rmse
        skill[name] = rmse / sd if sd > 0 else float("nan")

    metrics = {
        "method": "classical_multistart_least_squares",
        "surfaces_calibrated": int(len(recovered)),
        "starts_per_surface": args.starts,
        "median_price_rmse": float(np.median(price_rmses)),
        "mean_price_rmse": float(np.mean(price_rmses)),
        "max_price_rmse": float(np.max(price_rmses)),
        "param_rmse": param_rmse,
        "param_skill": skill,
        "mean_skill": float(np.mean(list(skill.values()))),
    }
    (out_dir / "classical_baseline_metrics.json").write_text(json.dumps(metrics, indent=2))

    logger.info("")
    logger.info("CLASSICAL BASELINE on %d surfaces", len(recovered))
    logger.info("  median price RMSE : %.3e   (how well it fits the prices)", metrics["median_price_rmse"])
    logger.info("  mean skill        : %.3f     (how well it recovers parameters; 1.0 = useless)",
                metrics["mean_skill"])
    for k in SHORT:
        logger.info("     %-9s skill %.3f", k, skill[k])


if __name__ == "__main__":
    main()
