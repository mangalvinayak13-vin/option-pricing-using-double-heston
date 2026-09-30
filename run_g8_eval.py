"""
G8 evaluation: the frozen models against real dates they have never seen.

The earlier real-market run used the five development dates, whose own metadata
marks them excluded from G8. This is the actual held-out test: eight Wednesdays
after the development window, downloaded and audited through the same sealed
quote-selection contract.

For each date it reports the network's repricing error and, alongside it, the
best fit the Double Heston model class can reach on that same surface. The gap
between them is the part attributable to the network; the floor is the part
attributable to the model.

Only repricing is measurable. NTPC's true parameters are unknown on any real
date, so parameter recovery is undefined here.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import torch
from torch import nn
from scipy.optimize import least_squares

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

import math
import run_option_backtest as OB
from mentor_dh_pinn import params_v2 as P
from src.double_heston import price_double_heston_surface
from src.plausible_bounds import training_parameter_stats, penalty_residuals
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS
from src.rank_conditioning import rate_and_carry_for_rank
from src import g8_evaluation as G8
from src.mask_aware import build_mlp, training_statistics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
LATENT_BOX = 12.0


def reprice(vector, spot, maturities, rates, carries, strikes):
    out = np.full(len(CANONICAL_SLOT_KEYS), np.nan)
    for rank in R2_EXPIRY_RANKS:
        idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS)
               if k.expiry_rank == rank and np.isfinite(strikes[i])]
        if not idx:
            continue
        keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
        rate, carry = rate_and_carry_for_rank(rank, rates, carries)
        out[np.asarray(idx, int)] = price_double_heston_surface(
            spot, np.array([strikes[i] for i in idx], float),
            np.full(len(keys), maturities[rank - 1], float),
            rate, carry,
            [k.option_type for k in keys], vector, node_count=64,
        )
    return out / spot


def best_possible_fit(market, mask, spot, maturities, rates, carries, strikes, rng,
                      surface, starts=12):
    """Least-squares floor: the closest any Double Heston fit gets to this surface.

    Bounded with a physical-parameter penalty rather than a flat latent box (see
    src/plausible_bounds.py): a flat +/-8 box lets the coupled kappa_fast term run to
    millions, and real, partial, noisy surfaces have flat-enough directions that the
    optimiser actually does run there.

    Also seeded with a guaranteed start at the point where Double Heston degenerates
    to a flat Black-Scholes volatility. Double Heston nests Black-Scholes exactly, so
    refining from that corner can never end up worse than the flat fit -- but bounding
    alone was not enough: 12 normal(0,1) starts clustered near the origin can simply
    miss that specific corner and never discover it, and without this seed a flat
    volatility still beat the reported "floor" on most real dates, which is otherwise
    impossible for a true optimum.
    """
    spread, phys_lo, phys_hi = training_parameter_stats(margin=2.0)
    lo, hi = np.full(10, -LATENT_BOX), np.full(10, LATENT_BOX)

    def price_residuals(z):
        try:
            got = reprice(np.asarray(P.to_array(P.decode(z)), float),
                          spot, maturities, rates, carries, strikes)[mask] - market[mask]
            return got if np.isfinite(got).all() else np.full(int(mask.sum()), 1e3)
        except Exception:
            return np.full(int(mask.sum()), 1e3)

    def residuals(z):
        vector = np.asarray(P.to_array(P.decode(z)), float)
        penalty = penalty_residuals(vector, phys_lo, phys_hi, spread)
        return np.concatenate([price_residuals(z), penalty])

    sigma_flat = OB.flat_vol_fit(OB.surface_arrays(surface))
    corner = np.zeros(10)
    corner[2] = corner[4] = math.log(sigma_flat ** 2)
    corner[6] = corner[7] = -3.0
    starts_z0 = [np.clip(corner, lo, hi)] + [
        np.clip(rng.normal(0, 1, 10), -LATENT_BOX + 1, LATENT_BOX - 1)
        for _ in range(starts)
    ]

    best_cost, best_z = np.inf, None
    for z0 in starts_z0:
        try:
            sol = least_squares(residuals, z0, bounds=(lo, hi), method="trf", max_nfev=2000)
        except Exception:
            continue
        price_only_cost = float(np.sum(price_residuals(sol.x) ** 2))
        if price_only_cost < best_cost:
            best_cost, best_z = price_only_cost, sol.x

    if best_z is None:
        return np.nan
    return float(np.sqrt(np.mean(price_residuals(best_z) ** 2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=str(
        PROJECT_ROOT / "outputs" / "real_eval" /
        "MaskAware_Model_2_canonical_latent_checkpoint.pt"))
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "g8"))
    ap.add_argument("--all-dates", action="store_true",
                    help="Use every vetted candidate date instead of the original 8 Wednesdays")
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    x_mu, x_sd, t_mu, t_sd, in_dim = training_statistics()
    model = build_mlp(in_dim)
    model.load_state_dict(torch.load(args.checkpoint, map_location="cpu"))
    model.eval()
    logger.info("loaded %s (%d inputs)", Path(args.checkpoint).name, in_dim)

    rate_sources = G8.register_g8_dates()
    logger.info("G8 rate observations in use: %s", sorted(set(rate_sources.values())))

    from src.constraints import validate_parameters

    # The headline G8 figures (8 dates, +10.1pp median gap) were produced on the original
    # eight Wednesdays. When the candidate window was widened to every weekday, this loop
    # silently switched to all of them, so re-running would have changed the headline
    # without anyone asking. Default to the original set; widening is now opt-in and
    # written to a separate file so it can never overwrite the headline.
    if args.all_dates:
        selection = PROJECT_ROOT / "outputs" / "g8" / "g8_date_selection.json"
        dates = json.loads(selection.read_text())["usable"] if selection.exists() \
            else list(G8.G8_CANDIDATE_DATES)
        result_name = "g8_evaluation_all_dates.json"
    else:
        dates = list(G8.G8_WEDNESDAY_SUBSET)
        result_name = "g8_evaluation.json"
    logger.info("evaluating %d dates -> %s", len(dates), result_name)

    rows = []
    for date_id in dates:
        try:
            s = G8.build_g8_surface(date_id)
        except Exception as exc:
            logger.warning("%s skipped: %s", date_id, exc)
            continue

        mk = np.asarray(s.mask, bool)
        strikes = np.array(
            [v if v is not None else np.nan
             for v in s.metadata["provenance"]["actual_strikes"]], float)
        mk = mk & np.isfinite(strikes)
        market = np.asarray(s.prices, float)
        mats = sorted(set(s.maturities))

        feat = np.concatenate([
            np.asarray(s.prices, float) * np.asarray(s.mask, bool),
            np.asarray(s.mask, bool).astype(float),
            [mats[0], mats[1], s.rates[0], s.carries[0]],
        ])
        with torch.no_grad():
            raw = model(torch.tensor((feat - x_mu) / x_sd,
                                     dtype=torch.float32).unsqueeze(0)).numpy()[0]
        vector = np.asarray(P.to_array(P.decode(raw * t_sd + t_mu)), float)

        net = reprice(vector, s.spot, mats, s.rates, s.carries, strikes)
        net_rmse = float(np.sqrt(np.mean((net[mk] - market[mk]) ** 2)))
        scale = float(np.mean(np.abs(market[mk])))
        floor = best_possible_fit(market, mk, s.spot, mats, s.rates, s.carries,
                                  strikes, rng, s)

        rows.append({
            "date_id": date_id,
            "usable_slots": int(mk.sum()),
            "spot": s.spot,
            "network_rmse": net_rmse,
            "network_relative": net_rmse / scale,
            "best_fit_rmse": floor,
            "best_fit_relative": floor / scale,
            "gap_pp": (net_rmse - floor) / scale * 100,
            "parameters_valid": bool(validate_parameters(vector)["is_valid"]),
            "rate_carry_forward_from": rate_sources[date_id],
        })
        logger.info("  %s  slots %2d/20  network %5.1f%%  floor %5.1f%%  gap %+5.1fpp",
                    date_id, int(mk.sum()), rows[-1]["network_relative"] * 100,
                    rows[-1]["best_fit_relative"] * 100, rows[-1]["gap_pp"])

    net_rel = np.array([r["network_relative"] for r in rows])
    floor_rel = np.array([r["best_fit_relative"] for r in rows])

    report = {
        "milestone": "G8_FROZEN_REAL_MARKET_EVALUATION",
        "held_out": True,
        "dates_evaluated": len(rows),
        "rate_observations_used": sorted(set(rate_sources.values())),
        "median_network_relative": float(np.median(net_rel)),
        "median_best_fit_relative": float(np.median(floor_rel)),
        "median_gap_pp": float(np.median(net_rel - floor_rel) * 100),
        "all_parameters_valid": bool(all(r["parameters_valid"] for r in rows)),
        "rows": rows,
        "caveat": (
            "Repricing only; NTPC's true parameters are unknown so recovery is "
            "undefined on real data. The rate is carried forward from the latest "
            "sealed RBI observation, which shifts only the discount factor because "
            "the forward is futures-implied."
        ),
    }
    (out_dir / result_name).write_text(json.dumps(report, indent=2))

    logger.info("")
    logger.info("G8 HELD-OUT EVALUATION on %d dates", len(rows))
    logger.info("  median network repricing : %.1f%%", report["median_network_relative"] * 100)
    logger.info("  median model-class floor : %.1f%%", report["median_best_fit_relative"] * 100)
    logger.info("  median gap               : %+.1fpp", report["median_gap_pp"])
    logger.info("  all parameter sets valid : %s", report["all_parameters_valid"])


if __name__ == "__main__":
    main()
