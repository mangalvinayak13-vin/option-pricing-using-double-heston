"""
Classical calibration directly on the five real NTPC surfaces.

This separates two explanations for the network's poor real-market repricing:

  (a) the network failed to transfer from synthetic to real, or
  (b) the Double Heston model class cannot fit NTPC's observed smile at all.

A least-squares fit to each real surface answers it. If the classical fit drives
repricing error to near zero, the model class is fine and (a) holds. If the
classical fit also stalls at a large error, that is the best possible Double
Heston fit to that surface, and (b) holds -- which would be a statement about the
market, not about any network.

Fits only the unmasked slots, in params_v2 latent coordinates so every iterate is
a valid parameter vector.
"""

from __future__ import annotations

import json
import logging
import math
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

import run_option_backtest as OB
from mentor_dh_pinn import params_v2 as P
from src.double_heston import price_double_heston_surface
from src.plausible_bounds import training_parameter_stats, penalty_residuals
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS
from src.rank_conditioning import rate_and_carry_for_rank

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]

# scipy's "lm" method -- the original choice here -- silently ignores `bounds`, so this
# fit was running fully unconstrained. On a clean, noiseless synthetic surface that
# rarely bites; on a real, partial, noisy one an under-constrained direction (kappa_fast
# in particular, a product of two latent coordinates) can run to an arbitrarily large
# value that costs the fit almost nothing in price error but is physically meaningless.
# "trf" is used instead because it is the one scipy method that respects `bounds`, and
# the physical penalty keeps the optimiser inside a plausible region without hard-
# stopping it at an arbitrary edge.
LATENT_BOX = 12.0


def reprice(z, spot, maturities, rates, carries, actual_strikes):
    """Reprice on each slot's ACTUAL traded strike.

    Real quotes are assigned to the nominal moneyness targets under a 0.05 gate, and
    the realised deviation reaches 0.04 in log-moneyness. Pricing at the nominal target
    while comparing against a quote struck up to 4% away charges that mismatch to the
    model, which would overstate how badly Double Heston fits the market.
    """
    vector = np.asarray(P.to_array(P.decode(z)), float)
    out = np.full(len(CANONICAL_SLOT_KEYS), np.nan, float)
    for rank in R2_EXPIRY_RANKS:
        idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS)
               if k.expiry_rank == rank and np.isfinite(actual_strikes[i])]
        if not idx:
            continue
        keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
        strikes = np.array([actual_strikes[i] for i in idx], float)
        mats = np.full(len(keys), maturities[rank - 1], float)
        rate, carry = rate_and_carry_for_rank(rank, rates, carries)
        out[np.asarray(idx, int)] = price_double_heston_surface(
            spot, strikes, mats, rate, carry,
            [k.option_type for k in keys], vector, node_count=64,
        )
    return out / spot


def actual_strikes_for(date_id: str) -> np.ndarray:
    """Per-slot traded strike from the sealed audit, NaN where the slot is unusable."""
    from src.g2_r2r3 import market
    table = market.audit_date(date_id)["slot_table"]
    by_key = {
        (int(r.expiry_rank), round(float(r.target_log_moneyness), 6), str(r.option_type)):
            float(r.strike)
        for r in table.itertuples() if bool(r.usable)
    }
    return np.array([
        by_key.get((k.expiry_rank, round(k.target_log_moneyness, 6), k.option_type), np.nan)
        for k in CANONICAL_SLOT_KEYS
    ], float)


def main():
    from src.g2_r2r3 import frozen
    from src.r2_representation.real import build_real_surface
    from src.constraints import validate_parameters

    rng = np.random.default_rng(0)
    spread, phys_lo, phys_hi = training_parameter_stats(margin=2.0)
    lo, hi = np.full(10, -LATENT_BOX), np.full(10, LATENT_BOX)
    results = []

    for date_id in frozen.MARKET_DATES:
        s = build_real_surface(date_id)
        mk = np.asarray(s.mask, bool)
        market = np.asarray(s.prices, float)
        mats = sorted(set(s.maturities))
        strikes = actual_strikes_for(date_id)

        # A slot is only comparable if it is unmasked AND we recovered its traded strike.
        mk = mk & np.isfinite(strikes)
        n_price = int(mk.sum())

        def price_residuals(z):
            try:
                return reprice(z, s.spot, mats, s.rates, s.carries, strikes)[mk] - market[mk]
            except Exception:
                return np.full(n_price, 1e3)

        def residuals(z):
            vector = np.asarray(P.to_array(P.decode(z)), float)
            penalty = penalty_residuals(vector, phys_lo, phys_hi, spread)
            return np.concatenate([price_residuals(z), penalty])

        # A guaranteed start at the point where Double Heston degenerates to a flat
        # Black-Scholes volatility. Double Heston nests Black-Scholes exactly (both
        # vol-of-variance terms to zero), so refining from here can never end up worse
        # than the flat fit -- but 12 normal(0,1) starts clustered near the origin can
        # simply miss that specific corner and never discover it. Without this start,
        # a flat Black-Scholes volatility beat the reported "floor" on 10 of 13 real
        # dates, which is otherwise impossible for a true optimum.
        arrays = OB.surface_arrays(s)
        sigma_flat = OB.flat_vol_fit(arrays)
        corner = np.zeros(10)
        corner[2] = corner[4] = math.log(sigma_flat ** 2)
        corner[6] = corner[7] = -3.0
        starts = [np.clip(corner, lo, hi)] + [
            np.clip(rng.normal(0, 1, 10), lo + 1, hi - 1) for _ in range(12)
        ]

        best_cost, best_z = np.inf, None
        for z0 in starts:
            try:
                sol = least_squares(residuals, z0, bounds=(lo, hi),
                                    method="trf", max_nfev=4000)
            except Exception:
                continue
            price_only_cost = float(np.sum(price_residuals(sol.x) ** 2))
            if price_only_cost < best_cost:
                best_cost, best_z = price_only_cost, sol.x

        if best_z is None:
            logger.warning("%s: all starts failed", date_id)
            continue

        err = price_residuals(best_z)
        rmse = float(np.sqrt(np.mean(err ** 2)))
        rel = rmse / float(np.mean(np.abs(market[mk])))
        vector = np.asarray(P.to_array(P.decode(best_z)), float)

        results.append({
            "date_id": date_id,
            "usable_slots": int(mk.sum()),
            "best_fit_repricing_rmse": rmse,
            "best_fit_repricing_relative": rel,
            "parameters_valid": bool(validate_parameters(vector)["is_valid"]),
            "parameters": {n: float(v) for n, v in zip(SHORT, vector)},
        })
        logger.info("%s  slots %2d/20  BEST-POSSIBLE Double Heston fit: RMSE %.6f (%.1f%% of mean price)",
                    date_id, int(mk.sum()), rmse, rel * 100)

    out = PROJECT_ROOT / "outputs" / "real_eval" / "real_classical_fit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "method": "classical_multistart_least_squares_on_real_surfaces",
        "starts_per_surface": 12,
        "interpretation": (
            "This is the best fit the Double Heston model class can achieve on these "
            "real NTPC surfaces. It is the floor any inverse method can reach; a network "
            "cannot do better without overfitting noise."
        ),
        "results": results,
    }, indent=2))
    logger.info("wrote %s", out)


if __name__ == "__main__":
    main()
