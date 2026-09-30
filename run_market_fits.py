"""
Optimiser-based Double Heston fits for every stock and date, keeping the parameters.

Why this exists. The market-wide page was built on the mask-aware network's predictions.
Two problems turned up when it was checked against a flat Black-Scholes baseline:

  * The network's fit (about 11% median error) is worse than a single flat volatility
    (about 5.5%). Calling it "a good fit" was wrong.
  * A network's parameters are a poor place to look for ambiguity: they move only about
    0.11 training-spreads a day because the network regresses toward the mean, so they show
    stability of the network, not of the market. Equally good OPTIMISER fits to the same
    surface sit 0.7 to 1.6 spreads apart.

So the exhibition needs fits where the parameters actually came from fitting the market.

What each surface gets:
  * 6 random starts uniform inside the plausible (training-range) latent box, plus one start
    at the flat-volatility corner: vol-of-variance small, both variances set to the flat
    volatility squared, no correlation. Double Heston contains Black-Scholes, so refining
    from there cannot end worse than the flat fit. An earlier optimiser without such a start
    was beaten by one flat volatility on 10 of 13 NTPC dates, and its numbers had been
    described as the best any method could reach.
  * The best fit's parameters and relative price error, next to the flat Black-Scholes error
    on the same quotes, so the two are never shown apart.
  * The size of the price-equivalent set (fits within 10% of the best) and how far apart
    those fits sit, in training-spreads: the ambiguity measure, per surface, per date.

Results are appended after every stock, ordered most traded first, so a partial run is
usable and a stopped one loses at most the stocks in flight.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
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
import run_option_backtest as OB
from run_market_ambiguity import reprice
from src.plausible_bounds import training_parameter_stats, penalty_residuals, near_bound_parameters

OUT_DIR = PROJECT_ROOT / "outputs" / "market_fits"
RESULT_CSV = OUT_DIR / "market_fits.csv"
MARKET_CSV = PROJECT_ROOT / "outputs" / "market_wide" / "market_wide_surfaces.csv"
SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
TOLERANCE = 0.10
NUMERIC_BOX = 14.0   # wide safety rail for trf; the physical penalty does the real containing

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_STATE: dict = {}


def _init(spread, phys_lo, phys_hi, date_info, starts):
    from src import g8_evaluation as G8
    G8.register_g8_dates()
    box_lo, box_hi = np.full(10, -NUMERIC_BOX), np.full(10, NUMERIC_BOX)
    _STATE.update(spread=spread, phys_lo=phys_lo, phys_hi=phys_hi,
                  box_lo=box_lo, box_hi=box_hi, date_info=date_info, starts=starts)


def fit_surface(surface, a, rng):
    """Best-of-N fit, plus the flat-volatility corner start. Returns a result dict or None.

    Bounded with a physical-parameter penalty rather than a flat latent box -- see
    src/plausible_bounds.py. A flat box lets the coupled kappa_fast term run to values
    in the thousands on a surface with a genuinely flat direction, which real, partial,
    noisy quotes have far more often than clean synthetic ones. An earlier version of
    this function tracked which solutions ended up pressed against such a box instead,
    which was treating the symptom; this fixes the cause.
    """
    phys_lo, phys_hi = _STATE["phys_lo"], _STATE["phys_hi"]
    box_lo, box_hi = _STATE["box_lo"], _STATE["box_hi"]
    spread = _STATE["spread"]
    mask, obs = a["mask"], a["obs"]

    def price_residuals(z):
        try:
            got = reprice(np.asarray(P.to_array(P.decode(z)), float), a["spot"], a["mats"],
                          a["rates"], a["carries"], a["strikes"])
            out = got[mask] - obs[mask]
            return out if np.isfinite(out).all() else np.full(int(mask.sum()), 1e3)
        except Exception:
            return np.full(int(mask.sum()), 1e3)

    def residuals(z):
        vector = np.asarray(P.to_array(P.decode(z)), float)
        penalty = penalty_residuals(vector, phys_lo, phys_hi, spread)
        return np.concatenate([price_residuals(z), penalty])

    sigma_flat = OB.flat_vol_fit(a)
    flat_rel = OB.flat_vol_error(a, sigma_flat)

    corner = np.zeros(10)
    corner[2] = corner[4] = math.log(sigma_flat ** 2)   # total long-run and initial variance
    corner[6] = corner[7] = -3.0                        # vol-of-variance near zero
    starts = [np.clip(corner, box_lo, box_hi)] + [
        rng.uniform(np.clip(phys_lo, box_lo, box_hi), np.clip(phys_hi, box_lo, box_hi))
        for _ in range(_STATE["starts"])
    ]

    sols, rmses = [], []
    for z0 in starts:
        try:
            sol = least_squares(residuals, z0, bounds=(box_lo, box_hi),
                                method="trf", max_nfev=1200)
        except Exception:
            continue
        r = float(np.sqrt(np.mean(price_residuals(sol.x) ** 2)))
        if np.isfinite(r) and r < 1e2:
            sols.append(np.asarray(P.to_array(P.decode(sol.x)), float))
            rmses.append(r)
    if not sols:
        return None

    sols, rmses = np.array(sols), np.array(rmses)
    best = int(np.argmin(rmses))
    scale = float(np.mean(np.abs(obs[mask])))
    keep = rmses <= rmses[best] * (1.0 + TOLERANCE)

    eq = sols[keep] / spread
    dists = [float(np.linalg.norm(x - y) / math.sqrt(10)) for x, y in combinations(eq, 2)]
    med_disp = float(np.median(dists)) if dists else 0.0
    max_disp = float(np.max(dists)) if dists else 0.0

    # Per-parameter dispersion, not just one aggregate Euclidean number -- see the same
    # field in run_market_ambiguity.py. kappa_fast alone can dominate an aggregate distance
    # when it sits near its physical bound; this makes that visible per parameter instead.
    per_param = {n: float(np.median([abs(a - b) for a, b in combinations(eq[:, i], 2)]))
                for i, n in enumerate(SHORT)} if len(eq) >= 2 else {n: 0.0 for n in SHORT}

    near_bound = near_bound_parameters(sols[best], phys_lo, phys_hi)

    return {
        "best_rel_error": float(rmses[best] / scale),
        "flat_bs_rel_error": float(flat_rel),
        "best_started_at_flat_corner": bool(best == 0),
        "starts_converged": int(len(sols)),
        "equiv_count": int(keep.sum()),
        "median_dispersion": med_disp,
        "max_dispersion": max_disp,
        **{f"disp_{n}": v for n, v in per_param.items()},
        "params_near_bound": ";".join(near_bound),   # empty string if none
        **{f"p_{n}": float(v) for n, v in zip(SHORT, sols[best])},
    }


def process_ticker(ticker):
    from src.g2_r2r3 import market
    from src import g8_evaluation as G8

    market.TICKER = ticker
    rows = []
    for date_id, info in _STATE["date_info"].items():
        try:
            report = market.audit_date(date_id)
            if not report.get("constructible", False):
                continue
            surface = G8.build_g8_surface(date_id, report)
            a = OB.surface_arrays(surface)
            if a["mask"].sum() < 8:
                continue
            rng = np.random.default_rng(zlib.crc32(f"{ticker}|{date_id}".encode()))
            result = fit_surface(surface, a, rng)
        except Exception:
            continue
        if result is None:
            continue
        rows.append({"ticker": ticker, "date_id": date_id, "spot": a["spot"],
                     "usable_slots": int(a["mask"].sum()),
                     "front_dte": info["front_dte"],
                     "in_training_support": info["in_support"], **result})
    return ticker, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--starts", type=int, default=6, help="Random starts, in addition to the flat corner")
    ap.add_argument("--tickers", type=int, default=0, help="Only the N most traded (0 = all)")
    ap.add_argument("--dates", type=int, default=0, help="Only the first N dates (testing)")
    ap.add_argument("--resume", action="store_true", help="Skip stocks already in the results file")
    ap.add_argument("--output-dir", type=str, default=None,
                    help="Write market_fits.csv here instead of outputs/market_fits "
                         "(use a scratch directory for test runs)")
    args = ap.parse_args()

    global RESULT_CSV
    out_dir = Path(args.output_dir) if args.output_dir else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    RESULT_CSV = out_dir / "market_fits.csv"
    market = pd.read_csv(MARKET_CSV)
    per_date = market.groupby("date_id")[["front_dte", "in_training_support"]].first()
    date_info = {d: {"front_dte": int(r.front_dte), "in_support": bool(r.in_training_support)}
                 for d, r in per_date.iterrows()}
    if args.dates:
        date_info = dict(list(date_info.items())[:args.dates])

    # universe() looks the raw-data root up by date, which only exists once the G8 dates
    # are registered. Workers do this in their initialiser; the parent needs it too.
    from src import g8_evaluation as G8
    G8.register_g8_dates()
    from run_market_wide import universe
    order = [t for t in universe("2026-09-23") if t in set(market["ticker"])]
    if args.tickers:
        order = order[:args.tickers]

    done = set()
    if args.resume and RESULT_CSV.exists():
        done = set(pd.read_csv(RESULT_CSV)["ticker"])
        order = [t for t in order if t not in done]
        logger.info("resuming: %d stocks already done", len(done))

    spread, phys_lo, phys_hi = training_parameter_stats(margin=2.0)
    logger.info("%d stocks x %d dates, %d random starts + flat corner, %d workers",
                len(order), len(date_info), args.starts, args.workers)

    started, n_rows = time.time(), 0
    header = not (RESULT_CSV.exists() and args.resume)
    with Pool(args.workers, initializer=_init,
              initargs=(spread, phys_lo, phys_hi, date_info, args.starts)) as pool:
        for i, (ticker, rows) in enumerate(pool.imap(process_ticker, order), 1):
            if rows:
                pd.DataFrame(rows).to_csv(RESULT_CSV, mode="a", header=header, index=False)
                header, n_rows = False, n_rows + len(rows)
            elapsed = (time.time() - started) / 60
            logger.info("  %d/%d  %-12s %3d surfaces  (%d total, %.0f min, ~%.0f min left)",
                        i, len(order), ticker, len(rows), n_rows, elapsed,
                        elapsed / i * (len(order) - i))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
