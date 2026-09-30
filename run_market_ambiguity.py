"""
Multi-start ambiguity on real market surfaces.

The strongest result available on real data, and the one the earlier real-market
work left out.

Parameter recovery cannot be scored on real data, because no one knows NTPC's true
Double Heston parameters. That framing made real data look like a credibility check
rather than evidence. It is the wrong framing: ambiguity needs no truth vector. If
many starting points converge to materially different parameter sets that all price
the same observed surface equally well, the surface does not determine the
parameters -- and that is demonstrated entirely from what the market printed.

This is the G2 protocol, moved from four synthetic cases to the traded market.

Method, per surface:
  1. Fit from N random starts in the canonical latent coordinates.
  2. Take the best price fit found.
  3. Keep every solution within `--tolerance` of it in relative price RMSE. These
     are the price-equivalent set: on the evidence of this surface, a calibrator
     has no basis to prefer one over another.
  4. Measure how far apart that set is in parameter space, standardised per
     parameter so incomparable scales do not dominate.

A relative tolerance is used rather than G2's absolute 2.5e-7, which was calibrated
against clean synthetic surfaces fitting to machine precision. Real surfaces fit to
around 1e-3, so an absolute cut inherited from synthetic data would admit either
everything or nothing.

Dispersion is reported as the median pairwise distance between price-equivalent
solutions, in units of the training distribution's own parameter spread. A value
near 0 means the surface pins the parameters down. A value near or above 1 means
price-equivalent solutions are as far apart as randomly drawn ones.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import warnings
import zlib
from itertools import combinations
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from mentor_dh_pinn import params_v2 as P
from src.double_heston import price_double_heston_surface
from src.plausible_bounds import training_parameter_stats, penalty_residuals, near_bound_parameters
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS
from src.rank_conditioning import rate_and_carry_for_rank
from src.g2_r2r3 import frozen, market
from src import g8_evaluation as G8

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
# Wide numeric safety rail for trf; the physical penalty in analyse_surface is what
# actually contains the search (see src/plausible_bounds.py for why a flat box alone
# does not).
NUMERIC_BOX = 14.0

# (superseded: a flat latent-space box used to live here; see src/plausible_bounds.py
# for why a physical-parameter penalty replaced it.)


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


def analyse_surface(surface, strikes, mask, spread, phys_lo, phys_hi, box_lo, box_hi,
                    starts, tolerance, rng):
    """Fit from many starts; measure the spread of the price-equivalent solutions.

    Bounded with a physical-parameter penalty (src/plausible_bounds.py), not a flat
    latent box. A flat box lets the coupled kappa_fast term run to values in the
    thousands on real, partial, noisy surfaces that have a genuinely flat direction in
    that coordinate; the reported dispersion then measures the box's shape rather than
    the market's. box_lo/box_hi is only a generous numeric safety rail so `trf` never
    has to handle an unbounded problem; phys_lo/phys_hi is what actually contains the
    search.
    """
    observed = np.asarray(surface.prices, float)
    mats = sorted(set(surface.maturities))

    def price_residuals(z):
        try:
            got = reprice(np.asarray(P.to_array(P.decode(z)), float), surface.spot,
                          mats, surface.rates, surface.carries, strikes)
            out = got[mask] - observed[mask]
            return out if np.isfinite(out).all() else np.full(int(mask.sum()), 1e3)
        except Exception:
            return np.full(int(mask.sum()), 1e3)

    def residuals(z):
        vector = np.asarray(P.to_array(P.decode(z)), float)
        penalty = penalty_residuals(vector, phys_lo, phys_hi, spread)
        return np.concatenate([price_residuals(z), penalty])

    solutions, rmses = [], []
    for _ in range(starts):
        # Start uniformly inside the plausible region, not the wide numeric box, so
        # starts actually sample where the physical penalty keeps the search.
        z0 = rng.uniform(np.clip(phys_lo, box_lo, box_hi), np.clip(phys_hi, box_lo, box_hi))
        try:
            sol = least_squares(residuals, z0, bounds=(box_lo, box_hi),
                                method="trf", max_nfev=1200)
        except Exception:
            continue
        rmse = float(np.sqrt(np.mean(price_residuals(sol.x) ** 2)))
        if not np.isfinite(rmse) or rmse > 1e2:
            continue
        solutions.append(np.asarray(P.to_array(P.decode(sol.x)), float))
        rmses.append(rmse)

    if len(solutions) < 2:
        return None

    solutions, rmses = np.array(solutions), np.array(rmses)
    best_idx = int(np.argmin(rmses))
    best = float(rmses[best_idx])
    keep = rmses <= best * (1.0 + tolerance)
    equivalent = solutions[keep]
    near_bound = near_bound_parameters(solutions[best_idx], phys_lo, phys_hi)

    if len(equivalent) < 2:
        return {
            "starts_converged": int(len(solutions)),
            "best_price_rmse": best,
            "price_equivalent_count": int(keep.sum()),
            "median_pairwise_dispersion": 0.0,
            "max_pairwise_dispersion": 0.0,
            "price_spread_within_equivalent": 0.0,
            "params_near_bound": ";".join(near_bound),
        }

    scaled = equivalent / spread          # standardise so scales are comparable
    dists = [float(np.linalg.norm(a - b) / np.sqrt(10))
             for a, b in combinations(scaled, 2)]

    # Per-parameter dispersion, not just one aggregate Euclidean number. kappa_fast is
    # near-bound on almost every real surface tried so far -- an aggregate distance
    # would fold that single dominant coordinate together with the other nine and hide
    # which parameter is actually driving the "ambiguity" figure.
    per_param = {n: float(np.median([abs(a - b) for a, b in combinations(scaled[:, i], 2)]))
                for i, n in enumerate(SHORT)}

    return {
        "starts_converged": int(len(solutions)),
        "best_price_rmse": best,
        "price_equivalent_count": int(keep.sum()),
        "median_pairwise_dispersion": float(np.median(dists)),
        **{f"disp_{n}": v for n, v in per_param.items()},
        "max_pairwise_dispersion": float(np.max(dists)),
        "params_near_bound": ";".join(near_bound),
        "price_spread_within_equivalent": float(rmses[keep].max() - rmses[keep].min()),
    }


_STATE: dict = {}


def _init(spread, phys_lo, phys_hi, box_lo, box_hi, dates, starts, tolerance):
    G8.register_g8_dates()
    _STATE.update(spread=spread, phys_lo=phys_lo, phys_hi=phys_hi, box_lo=box_lo,
                  box_hi=box_hi, dates=dates, starts=starts, tolerance=tolerance)


def process_ticker(ticker):
    """All dates for one ticker. Runs in a worker process; one rng per (ticker, date)
    seeded off both so results are reproducible regardless of worker scheduling."""
    market.TICKER = ticker
    rows = []
    for date_id in _STATE["dates"]:
        try:
            report = market.audit_date(date_id)
            if not report.get("constructible", False):
                continue
            surface = G8.build_g8_surface(date_id, report)
        except Exception:
            continue

        strikes = np.array(
            [v if v is not None else np.nan
             for v in surface.metadata["provenance"]["actual_strikes"]], float)
        mask = np.asarray(surface.mask, bool) & np.isfinite(strikes)
        if mask.sum() < 8:
            continue

        rng = np.random.default_rng(zlib.crc32(f"{ticker}|{date_id}".encode()))
        result = analyse_surface(surface, strikes, mask, _STATE["spread"], _STATE["phys_lo"],
                                 _STATE["phys_hi"], _STATE["box_lo"], _STATE["box_hi"],
                                 _STATE["starts"], _STATE["tolerance"], rng)
        if result is None:
            continue
        rows.append({"ticker": ticker, "date_id": date_id,
                     "usable_slots": int(mask.sum()), **result})
    return ticker, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--starts", type=int, default=16)
    ap.add_argument("--tolerance", type=float, default=0.10,
                    help="Price-equivalent if within this relative margin of the best fit")
    ap.add_argument("--tickers", type=int, default=40,
                    help="Most-active underlyings to cover (0 = all)")
    ap.add_argument("--dates", nargs="*", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "ambiguity"))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    spread, phys_lo, phys_hi = training_parameter_stats(margin=2.0)
    box_lo, box_hi = np.full(10, -NUMERIC_BOX), np.full(10, NUMERIC_BOX)

    G8.register_g8_dates()
    dates = args.dates or (list(frozen.MARKET_DATES) + list(G8.G8_CANDIDATE_DATES))

    catalogue = pd.read_csv(PROJECT_ROOT / "outputs" / "market_wide" /
                            "market_wide_surfaces.csv")
    order = (catalogue.groupby("ticker")["usable_slots"].mean()
             .sort_values(ascending=False).index.tolist())
    tickers = order[:args.tickers] if args.tickers else order

    logger.info("%d tickers x %d dates, %d starts each, tolerance %.0f%%, %d workers",
                len(tickers), len(dates), args.starts, args.tolerance * 100, args.workers)

    out_csv = out_dir / "ambiguity_surfaces.csv"
    rows = []
    started = time.time()
    header = True
    with Pool(args.workers, initializer=_init,
              initargs=(spread, phys_lo, phys_hi, box_lo, box_hi, dates, args.starts,
                        args.tolerance)) as pool:
        for i, (ticker, ticker_rows) in enumerate(pool.imap_unordered(process_ticker, tickers), 1):
            if ticker_rows:
                pd.DataFrame(ticker_rows).to_csv(out_csv, mode="a", header=header, index=False)
                header = False
                rows.extend(ticker_rows)
            elapsed = (time.time() - started) / 60
            logger.info("  %d/%d  %-12s %2d surfaces  (%d total, %.1f min, ~%.1f min left)",
                        i, len(tickers), ticker, len(ticker_rows), len(rows), elapsed,
                        elapsed / i * (len(tickers) - i))

    frame = pd.DataFrame(rows)

    multi = frame[frame["price_equivalent_count"] >= 2]
    summary = {
        "surfaces_analysed": int(len(frame)),
        "starts_per_surface": args.starts,
        "equivalence_tolerance": args.tolerance,
        "median_price_equivalent_count": float(frame["price_equivalent_count"].median()),
        "share_with_multiple_equivalents": float(
            (frame["price_equivalent_count"] >= 2).mean()),
        "median_dispersion": float(multi["median_pairwise_dispersion"].median())
                             if len(multi) else None,
        "median_max_dispersion": float(multi["max_pairwise_dispersion"].median())
                                 if len(multi) else None,
        "median_best_price_rmse": float(frame["best_price_rmse"].median()),
        "share_with_any_param_near_bound": float(
            (frame["params_near_bound"].fillna("") != "").mean()),
        "interpretation": (
            "Dispersion is in units of the training distribution's own parameter "
            "spread. Near 0 means the surface pins the parameters; near or above 1 "
            "means price-equivalent solutions sit as far apart as unrelated ones."
        ),
    }
    (out_dir / "ambiguity_summary.json").write_text(json.dumps(summary, indent=2))

    logger.info("")
    logger.info("REAL-MARKET AMBIGUITY over %d surfaces", summary["surfaces_analysed"])
    logger.info("  median best price RMSE          : %.2e", summary["median_best_price_rmse"])
    logger.info("  surfaces with >1 equivalent fit : %.0f%%",
                summary["share_with_multiple_equivalents"] * 100)
    logger.info("  median equivalent solutions     : %.0f",
                summary["median_price_equivalent_count"])
    if summary["median_dispersion"] is not None:
        logger.info("  median pairwise dispersion      : %.3f",
                    summary["median_dispersion"])
        logger.info("  median worst-pair dispersion    : %.3f",
                    summary["median_max_dispersion"])


if __name__ == "__main__":
    main()
