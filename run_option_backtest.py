"""
Out-of-sample option pricing backtest.

Question. The central finding is that a Double Heston surface does not determine its
ten parameters. Does that matter in practice? If parameters fitted on Monday still price
Tuesday's real option quotes about as well as parameters fitted fresh on Tuesday, then the
directions the data cannot pin down are also directions prices do not care about, and the
ambiguity is harmless for pricing even though it makes the parameters uninterpretable.

Method, for every stock and every pair of consecutive trading days (t, t+1):
  stale Double Heston   parameters from day t (the mask-aware network's prediction, already
                        in market_wide_surfaces.csv), then reprice day t+1's REAL quotes at
                        day t+1's own strikes, spot, maturities, rate and carry. Only the
                        ten parameters are stale; everything observable on t+1 is used.
  flat Black-Scholes    one volatility fitted to day t's real quotes by least squares, then
                        used the same way on day t+1. The natural benchmark: one number
                        carried forward instead of ten.
  fresh Double Heston   the network's prediction made on day t+1 itself, taken from the
                        market-wide run. Not a forecast; it is the floor showing how well
                        the same model fits t+1 when it sees t+1.

Error is the same measure used everywhere else in this project: RMSE of spot-normalised
price divided by the mean observed price, over the quotes actually traded on t+1.

Also recorded: how far the parameters moved between t and t+1, in units of the training
distribution's spread, so the size of the jump can be set against the size of the pricing
damage. That is the direct test of whether unstable parameters cost anything.

Pairs are only formed between dates with no excluded date between them (a gap over four
calendar days, or an expiry-day exclusion, breaks the chain), so "tomorrow" always means
the next trading day. Only stocks and dates already in the vetted market-wide run are used.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
import warnings
from datetime import date
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import norm

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

MARKET_CSV = PROJECT_ROOT / "outputs" / "market_wide" / "market_wide_surfaces.csv"
OUT_DIR = PROJECT_ROOT / "outputs" / "option_backtest"
PARAM_COLS = ["p_kappa_s", "p_theta_s", "p_sigma_s", "p_rho_s", "p_v0_s",
              "p_kappa_f", "p_theta_f", "p_sigma_f", "p_rho_f", "p_v0_f"]
MAX_GAP_DAYS = 4

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def black_scholes(spot, strikes, T, rate, carry, sigma, is_call):
    """European price with continuous carry yield; forward is S*exp((r-q)T)."""
    strikes = np.asarray(strikes, float)
    forward = spot * math.exp((rate - carry) * T)
    vol_t = max(sigma, 1e-8) * math.sqrt(T)
    d1 = (np.log(forward / strikes) + 0.5 * vol_t ** 2) / vol_t
    d2 = d1 - vol_t
    disc = math.exp(-rate * T)
    call = disc * (forward * norm.cdf(d1) - strikes * norm.cdf(d2))
    put = call - disc * (forward - strikes)
    return np.where(is_call, call, put)


def surface_arrays(surface):
    """Flat arrays for the quotes actually traded: strikes, spot-normalised prices, calls,
    maturities, rates and carries per quote."""
    from src.r2_representation.contract import CANONICAL_SLOT_KEYS

    strikes = np.array([v if v is not None else np.nan
                        for v in surface.metadata["provenance"]["actual_strikes"]], float)
    mask = np.asarray(surface.mask, bool) & np.isfinite(strikes)
    obs = np.asarray(surface.prices, float)
    is_call = np.array([k.option_type == "call" for k in CANONICAL_SLOT_KEYS])
    return {
        "mask": mask, "strikes": strikes, "obs": obs, "is_call": is_call,
        "T": np.asarray(surface.maturities, float),
        "r": np.asarray(surface.rates, float), "q": np.asarray(surface.carries, float),
        "spot": float(surface.spot),
        "mats": sorted(set(surface.maturities)),
        "rates": surface.rates, "carries": surface.carries,
    }


def flat_vol_fit(a):
    """One volatility fitted to a surface's real quotes by least squares in price."""
    m = a["mask"]

    def loss(sigma):
        model = np.empty(int(m.sum()))
        idx = np.flatnonzero(m)
        for j, i in enumerate(idx):
            model[j] = black_scholes(a["spot"], a["strikes"][i], a["T"][i], a["r"][i],
                                     a["q"][i], sigma, a["is_call"][i]) / a["spot"]
        return float(np.sum((model - a["obs"][m]) ** 2))

    return float(minimize_scalar(loss, bounds=(0.01, 3.0), method="bounded").x)


def flat_vol_error(a, sigma):
    m = a["mask"]
    idx = np.flatnonzero(m)
    model = np.array([black_scholes(a["spot"], a["strikes"][i], a["T"][i], a["r"][i],
                                    a["q"][i], sigma, a["is_call"][i]) / a["spot"] for i in idx])
    return _relative_rmse(model, a["obs"][m])


def _relative_rmse(model, observed):
    rmse = float(np.sqrt(np.mean((model - observed) ** 2)))
    return rmse / float(np.mean(np.abs(observed)))


def heston_error(vector, a):
    from run_market_wide import reprice
    priced = reprice(vector, a["spot"], a["mats"], a["rates"], a["carries"], a["strikes"])
    m = a["mask"]
    return _relative_rmse(priced[m], a["obs"][m])


def _init_worker():
    from src import g8_evaluation as G8
    G8.register_g8_dates()


def process_ticker(args):
    """All consecutive-day pairs for one ticker. Runs in a worker process."""
    ticker, dates, params = args
    from src.g2_r2r3 import market
    from src import g8_evaluation as G8

    market.TICKER = ticker
    cache = {}
    for d in dates:
        try:
            report = market.audit_date(d)
            if not report.get("constructible", False):
                continue
            surface = G8.build_g8_surface(d, report)
            arrays = surface_arrays(surface)
            if arrays["mask"].sum() >= 6:
                cache[d] = arrays
        except Exception:
            continue

    rows = []
    for d0, d1 in zip(dates[:-1], dates[1:]):
        if (date.fromisoformat(d1) - date.fromisoformat(d0)).days > MAX_GAP_DAYS:
            continue
        if d0 not in cache or d1 not in cache or d0 not in params or d1 not in params:
            continue
        a0, a1 = cache[d0], cache[d1]
        v0, v1 = params[d0]["vector"], params[d1]["vector"]
        try:
            sigma = flat_vol_fit(a0)
            rows.append({
                "ticker": ticker, "day_t": d0, "day_t1": d1,
                "slots_t1": int(a1["mask"].sum()),
                "front_dte_t": params[d0]["front_dte"], "front_dte_t1": params[d1]["front_dte"],
                "in_support": bool(params[d0]["in_support"] and params[d1]["in_support"]),
                "err_stale_dh": heston_error(v0, a1),
                "err_fresh_dh": heston_error(v1, a1),
                "err_stale_bs": flat_vol_error(a1, sigma),
                "err_bs_same_day": flat_vol_error(a1, flat_vol_fit(a1)),
                "flat_vol_t": sigma,
                "spot_move": a1["spot"] / a0["spot"] - 1.0,
                "param_jump": float(np.linalg.norm((v1 - v0) / params["_spread"]) / math.sqrt(10)),
            })
        except Exception:
            continue
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", type=int, default=0, help="Limit to N most active (0 = all)")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(MARKET_CSV)
    if args.tickers:
        keep = frame.groupby("ticker")["spot"].count().sort_values(ascending=False).index[:args.tickers]
        frame = frame[frame["ticker"].isin(keep)]

    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from mentor_dh_pinn import params_v2 as P
    spread = np.asarray(
        [[json.loads(line)["metadata"]["parameters_canonical_order"][n] for n in P.CANONICAL]
         for line in open(PROJECT_ROOT / "data" / "final_r2_clean_10000" / "surfaces.jsonl")],
        float).std(axis=0)

    dates = sorted(frame["date_id"].unique())
    jobs = []
    for ticker, sub in frame.groupby("ticker"):
        params = {"_spread": spread}
        for r in sub.itertuples():
            params[r.date_id] = {"vector": np.array([getattr(r, c) for c in PARAM_COLS], float),
                                 "front_dte": int(r.front_dte),
                                 "in_support": bool(r.in_training_support)}
        jobs.append((ticker, dates, params))

    logger.info("%d tickers x %d dates, %d workers", len(jobs), len(dates), args.workers)
    started, rows = time.time(), []
    with Pool(args.workers, initializer=_init_worker) as pool:
        for i, out in enumerate(pool.imap_unordered(process_ticker, jobs), 1):
            rows.extend(out)
            if i % 10 == 0 or i == len(jobs):
                logger.info("  %d/%d tickers, %d pairs, %.1f min", i, len(jobs), len(rows),
                            (time.time() - started) / 60)

    result = pd.DataFrame(rows)
    result.to_csv(OUT_DIR / "option_backtest_pairs.csv", index=False)
    logger.info("wrote %d pairs", len(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
