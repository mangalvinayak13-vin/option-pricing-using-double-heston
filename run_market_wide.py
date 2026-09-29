"""
Market-wide calibration across the NSE F&O universe.

Built for the exhibition, where a visitor picks a stock rather than reading about
one. It runs the same sealed quote-selection contract over every stock with listed
options, on every date already downloaded, and records what happens -- including
where it fails, which is itself the interesting part for most of the market.

Scope. "Every Indian stock" is not available to a calibration of an option pricing
model: roughly 1,800 NSE listings have no options at all. The universe here is the
~210 stock underlyings with listed options in the F&O segment, which is the whole
set for which this question is even askable.

Cost. The audit is about 0.45s per ticker-date, so the full grid is around twenty
minutes. The classical best-fit floor is about 10s per surface and is therefore
sampled rather than run everywhere; the network path runs on everything.

Results are written incrementally so a long run can be inspected or resumed.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from mentor_dh_pinn import params_v2 as P
from src.double_heston import price_double_heston_surface
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS
from src.g2_r2r3 import frozen, market
from src import g8_evaluation as G8

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
REAL_COVERAGE = [11, 12, 18, 18, 19]


def build_mlp(input_dim, hidden=(384, 384, 384), output_dim=10):
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def universe(date_id: str) -> list[str]:
    """Stock underlyings with listed options on this date, most active first."""
    root = PROJECT_ROOT / frozen.MARKET_RAW_ROOTS[date_id] / date_id
    stamp = date_id.replace("-", "")
    fo = pd.read_csv(root / f"BhavCopy_NSE_FO_0_0_0_{stamp}_F_0000.csv", low_memory=False)
    stock_opts = fo[
        fo["OptnTp"].isin(["CE", "PE"])
        & fo["FinInstrmTp"].astype(str).str.contains("STO", na=False)
    ]
    # Order by traded value so the exhibition's default view leads with names a
    # visitor recognises, and so a truncated run still covers the liquid market.
    activity = stock_opts.groupby("TckrSymb")["TtlTrfVal"].sum().sort_values(ascending=False)
    return list(activity.index)


def training_statistics(seed: int = 0):
    """Rebuild the mask-aware model's normalisation, identical to run_real_market_eval."""
    rng = np.random.default_rng(seed)
    prices, cond, params = [], [], []
    with open(PROJECT_ROOT / "data" / "final_r2_clean_10000" / "surfaces.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            if len(rec["prices"]) != 20:
                continue
            mats = sorted(set(rec["maturities"]))
            prices.append(rec["prices"])
            cond.append([mats[0], mats[1], rec["rates"][0], rec["carries"][0]])
            p = rec["metadata"]["parameters_canonical_order"]
            params.append([p[n] for n in P.CANONICAL])
    prices, cond, params = np.array(prices), np.array(cond), np.array(params)
    z = np.stack([P.encode(r) for r in params])

    masks = np.ones((len(prices), 20), dtype=bool)
    for i in np.flatnonzero(rng.random(len(prices)) < 0.5):
        keep = rng.choice(REAL_COVERAGE)
        masks[i, rng.choice(20, size=20 - keep, replace=False)] = False

    X = np.concatenate([prices * masks, masks.astype(float), cond], axis=1)
    return (X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0),
            z.mean(0), np.where(z.std(0) > 0, z.std(0), 1.0), X.shape[1])


def reprice(vector, spot, maturities, rates, carries, strikes):
    out = np.full(len(CANONICAL_SLOT_KEYS), np.nan)
    for rank in R2_EXPIRY_RANKS:
        idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS)
               if k.expiry_rank == rank and np.isfinite(strikes[i])]
        if not idx:
            continue
        keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
        out[np.asarray(idx, int)] = price_double_heston_surface(
            spot, np.array([strikes[i] for i in idx], float),
            np.full(len(keys), maturities[rank - 1], float),
            rates[rank - 1], carries[rank - 1],
            [k.option_type for k in keys], vector, node_count=64,
        )
    return out / spot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", type=int, default=0,
                    help="Limit to the N most active underlyings (0 = all)")
    ap.add_argument("--dates", nargs="*", default=None)
    ap.add_argument("--checkpoint", default=str(
        PROJECT_ROOT / "outputs" / "real_eval" /
        "MaskAware_Model_2_canonical_latent_checkpoint.pt"))
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "market_wide"))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    G8.register_g8_dates()
    if args.dates:
        dates = args.dates
    else:
        # Use the dates the G8 audit already vetted rather than every candidate.
        # Otherwise a date NSE never traded, or a monthly expiry day whose front
        # expiry has zero days to run, fails once per ticker and buries 210
        # identical rejections in the log.
        selection = PROJECT_ROOT / "outputs" / "g8" / "g8_date_selection.json"
        if selection.exists():
            usable = json.loads(selection.read_text())["usable"]
            dates = list(frozen.MARKET_DATES) + usable
            logger.info("using %d vetted G8 dates + %d development dates",
                        len(usable), len(frozen.MARKET_DATES))
        else:
            dates = list(frozen.MARKET_DATES) + list(G8.G8_CANDIDATE_DATES)
            logger.warning("no g8_date_selection.json; using all %d candidates "
                           "(run `python -m src.g8_evaluation` first)", len(dates))

    x_mu, x_sd, t_mu, t_sd, in_dim = training_statistics()
    model = build_mlp(in_dim)
    model.load_state_dict(torch.load(args.checkpoint, map_location="cpu"))
    model.eval()

    from src.constraints import validate_parameters

    tickers = universe(dates[-1])
    if args.tickers:
        tickers = tickers[:args.tickers]
    logger.info("%d underlyings x %d dates = %d combinations",
                len(tickers), len(dates), len(tickers) * len(dates))

    original_ticker = market.TICKER
    rows, rejects = [], {}
    started = time.time()

    try:
        for di, date_id in enumerate(dates, 1):
            for ti, ticker in enumerate(tickers, 1):
                market.TICKER = ticker
                try:
                    report = market.audit_date(date_id)
                except Exception as exc:
                    rejects[f"{ticker}|{date_id}"] = f"audit error: {type(exc).__name__}"
                    continue
                if not report.get("constructible", False):
                    rejects[f"{ticker}|{date_id}"] = str(
                        report.get("hard_failure", "not constructible"))[:120]
                    continue
                try:
                    surface = G8.build_g8_surface(date_id, report)
                except Exception as exc:
                    rejects[f"{ticker}|{date_id}"] = f"surface: {str(exc)[:110]}"
                    continue

                mk = np.asarray(surface.mask, bool)
                strikes = np.array(
                    [v if v is not None else np.nan
                     for v in surface.metadata["provenance"]["actual_strikes"]], float)
                cmp_mask = mk & np.isfinite(strikes)
                if cmp_mask.sum() < 6:
                    rejects[f"{ticker}|{date_id}"] = f"only {int(cmp_mask.sum())} usable slots"
                    continue

                mats = sorted(set(surface.maturities))
                feat = np.concatenate([
                    np.asarray(surface.prices, float) * mk,
                    mk.astype(float),
                    [mats[0], mats[1], surface.rates[0], surface.carries[0]],
                ])
                with torch.no_grad():
                    raw = model(torch.tensor((feat - x_mu) / x_sd,
                                             dtype=torch.float32).unsqueeze(0)).numpy()[0]
                vector = np.asarray(P.to_array(P.decode(raw * t_sd + t_mu)), float)

                try:
                    got = reprice(vector, surface.spot, mats, surface.rates,
                                  surface.carries, strikes)
                    obs = np.asarray(surface.prices, float)
                    rmse = float(np.sqrt(np.mean((got[cmp_mask] - obs[cmp_mask]) ** 2)))
                    rel = rmse / float(np.mean(np.abs(obs[cmp_mask])))
                except Exception as exc:
                    rejects[f"{ticker}|{date_id}"] = f"repricing: {type(exc).__name__}"
                    continue

                rows.append({
                    "ticker": ticker,
                    "date_id": date_id,
                    "held_out": date_id in G8.G8_CANDIDATE_DATES,
                    "spot": surface.spot,
                    "usable_slots": int(cmp_mask.sum()),
                    "repricing_rmse": rmse,
                    "repricing_relative": rel,
                    "parameters_valid": bool(validate_parameters(vector)["is_valid"]),
                    **{f"p_{n}": float(v) for n, v in zip(SHORT, vector)},
                })

            elapsed = time.time() - started
            logger.info("[%d/%d] %s done -- %d surfaces, %d rejected, %.1f min elapsed",
                        di, len(dates), date_id, len(rows), len(rejects), elapsed / 60)
            pd.DataFrame(rows).to_csv(out_dir / "market_wide_surfaces.csv", index=False)
            (out_dir / "market_wide_rejections.json").write_text(json.dumps(rejects, indent=2))
    finally:
        market.TICKER = original_ticker

    frame = pd.DataFrame(rows)
    frame.to_csv(out_dir / "market_wide_surfaces.csv", index=False)

    by_ticker = (frame.groupby("ticker")
                 .agg(surfaces=("date_id", "count"),
                      median_relative=("repricing_relative", "median"),
                      median_slots=("usable_slots", "median"),
                      all_valid=("parameters_valid", "all"))
                 .sort_values("median_relative"))
    by_ticker.to_csv(out_dir / "market_wide_by_ticker.csv")

    summary = {
        "universe_size": len(tickers),
        "dates": len(dates),
        "attempted": len(tickers) * len(dates),
        "surfaces_built": int(len(frame)),
        "tickers_with_any_surface": int(frame["ticker"].nunique()),
        "rejected": len(rejects),
        "median_repricing_relative": float(frame["repricing_relative"].median()),
        "all_parameters_valid": bool(frame["parameters_valid"].all()),
        "held_out_share": float(frame["held_out"].mean()),
        "runtime_minutes": (time.time() - started) / 60,
    }
    (out_dir / "market_wide_summary.json").write_text(json.dumps(summary, indent=2))

    logger.info("")
    logger.info("MARKET-WIDE RUN")
    logger.info("  universe            : %d underlyings", summary["universe_size"])
    logger.info("  surfaces built      : %d of %d attempted",
                summary["surfaces_built"], summary["attempted"])
    logger.info("  tickers represented : %d", summary["tickers_with_any_surface"])
    logger.info("  median repricing    : %.1f%%", summary["median_repricing_relative"] * 100)
    logger.info("  all params valid    : %s", summary["all_parameters_valid"])


if __name__ == "__main__":
    main()
