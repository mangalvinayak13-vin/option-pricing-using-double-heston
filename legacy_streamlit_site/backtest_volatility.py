"""
Walk-forward volatility backtest on Indian stocks, ten years of history.

Question: does a fitted volatility model forecast the next month's volatility better
than the trivial guess that next month looks like last month?

How it differs from the Forecast page. That page fits GARCH once on the first 70% of one
stock's history and scores the remainder. This refits GARCH every 63 trading days on an
expanding window, so every forecast uses only parameters estimated from data before it,
and it repeats the exercise over an index and 60 of the most traded F&O stocks, so the
answer does not hinge on one ticker.

Forecast target. The average daily volatility realised over the next 21 trading days,
measured from the same day the forecast is made. Nothing here forecasts direction.

Forecasters (all reuse models.py, so the site and the backtest cannot disagree):
  naive       trailing 21-day realised volatility
  ewma        RiskMetrics exponentially weighted, lambda = 0.94
  garch       GARCH(1,1), refit every 63 days on an expanding window
  long_run    expanding-window standard deviation of all returns so far -- the "do
              nothing clever" benchmark. A model that cannot beat this has learned
              nothing about how volatility moves.

Scoring.
  QLIKE, on variance. The standard loss for volatility forecasts because realised
  variance is a noisy proxy for true variance and QLIKE stays reliable under that
  noise where squared error does not (Patton 2011).
  RMSE, on volatility, as the loss people find intuitive.

Significance. Diebold-Mariano test on the QLIKE differences with a Newey-West variance.
The 21-day forward windows overlap, so consecutive daily losses are strongly correlated
and an ordinary standard error would overstate confidence by a wide margin.

Run:  python3 backtest_volatility.py            (full run, writes backtest_results.json)
      python3 backtest_volatility.py --selfcheck (verifies no forecast can see the future)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import models

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "backtest_results.json"

HORIZON = 21
MIN_TRAIN = 750          # about three years before the first out-of-sample forecast
REFIT_EVERY = 63         # about one quarter
FULL_HISTORY_ROWS = 1500 # at or above this a stock gets the full three-year training window

# Stocks listed less than about six years ago are not dropped: they are scored on whatever
# history exists, with the training window shrunk to half of it (never under 200 days) so
# there is still a real out-of-sample stretch left to score. They are labelled "partial" and
# reported separately, because a short test has less power and should not be pooled
# silently with the ten-year names.
MIN_PARTIAL_ROWS = 330   # below roughly 16 months there is nothing left to score honestly
MIN_OOS_DAYS = 100

# A single-day move beyond this in log terms (roughly -39% or +65%) on a liquid F&O stock is
# a corporate action the price feed failed to adjust -- a consolidation, demerger or
# relisting -- not a real return. Left in, one such day poisons every 21-day window that
# contains it. Patanjali shows a +298% "return" on 2020-01-27 from exactly this.
MAX_ABS_LOG_RETURN = 0.5

# The 60 most traded F&O stock underlyings by option turnover on 2026-09-23 (NSE bhavcopy),
# plus the two indices. Recently listed names are kept and scored on whatever history exists.
UNIVERSE = ("NIFTY", "BANKNIFTY") + tuple(f"{t}.NS" for t in (
    "SOLARINDS", "HDFCBANK", "RELIANCE", "MCX", "BSE", "BAJFINANCE", "TATASTEEL", "DIVISLAB",
    "SBIN", "PAYTM", "TCS", "ICICIBANK", "APOLLOHOSP", "MARUTI", "BHARTIARTL", "DIXON", "INFY",
    "BANDHANBNK", "ITC", "POLICYBZR", "IDFCFIRSTB", "HINDALCO", "LAURUSLABS", "KEI", "TITAN",
    "OFSS", "ATHERENERG", "LT", "ADANIENT", "ETERNAL", "MOTILALOFS", "RADICO", "PERSISTENT",
    "INDIGO", "BHEL", "COALINDIA", "HCLTECH", "HAL", "360ONE", "JINDALSTEL", "BAJAJ-AUTO", "M&M",
    "HEROMOTOCO", "RBLBANK", "VEDL", "JSWSTEEL", "IDEA", "SONACOMS", "AXISBANK", "ADANIPORTS",
    "PATANJALI", "COFORGE", "POLYCAB", "DLF", "POWERINDIA", "HINDZINC", "SWIGGY", "KALYANKJIL",
    "KOTAKBANK", "NATIONALUM"))

MODELS = ("naive", "ewma", "garch", "long_run")


def train_window(n_rows: int) -> int:
    """Training days before the first forecast: full for long histories, half otherwise."""
    if n_rows >= FULL_HISTORY_ROWS:
        return MIN_TRAIN
    return max(200, n_rows // 2)


def clean_returns(returns: pd.Series):
    """Drop unadjusted corporate-action artefacts, and say which days were dropped."""
    bad = returns[returns.abs() > MAX_ABS_LOG_RETURN]
    notes = [{"date": str(i.date()), "log_return": round(float(v), 4)} for i, v in bad.items()]
    return returns.drop(bad.index), notes


def walk_forward_garch(returns: pd.Series, min_train: int = MIN_TRAIN) -> pd.Series:
    """GARCH(1,1) forecasts where every parameter set is fitted only on earlier data.

    At each refit point t the model is fitted on returns[:t] and then run forward with
    those frozen parameters for the next REFIT_EVERY days. models.garch_vol already
    guarantees that forecasts after n_train use only n_train-window parameters and a
    causal recursion, so refitting means calling it with a larger n_train.
    """
    n = len(returns)
    pieces = []
    for t in range(min_train, n, REFIT_EVERY):
        try:
            series, _ = models.garch_vol(returns, horizon=HORIZON, n_train=t)
        except Exception:
            continue
        pieces.append(series.iloc[t:t + REFIT_EVERY])
    return pd.concat(pieces) if pieces else pd.Series(dtype=float)


def all_forecasts(returns: pd.Series, min_train: int = MIN_TRAIN) -> pd.DataFrame:
    return pd.DataFrame({
        "naive": models.naive_vol(returns, window=HORIZON),
        "ewma": models.ewma_vol(returns),
        "garch": walk_forward_garch(returns, min_train),
        "long_run": returns.expanding(min_train).std(),
    })


def qlike(realised_vol: np.ndarray, forecast_vol: np.ndarray) -> np.ndarray:
    """QLIKE on variance: f/h - ln(f/h) - 1, zero when the forecast is exact."""
    ratio = (realised_vol ** 2) / (forecast_vol ** 2)
    return ratio - np.log(ratio) - 1.0


def diebold_mariano(loss_base: np.ndarray, loss_model: np.ndarray, lag: int):
    """DM statistic and two-sided p-value for 'model beats base', Newey-West variance.

    Positive statistic means the model has the lower loss. `lag` should be horizon - 1
    because forecasts made on consecutive days share all but one day of their outcome.
    """
    d = loss_base - loss_model
    n = len(d)
    if n < lag + 30:
        return float("nan"), float("nan")
    d_c = d - d.mean()
    gamma0 = float(np.dot(d_c, d_c) / n)
    var = gamma0
    for k in range(1, lag + 1):
        weight = 1.0 - k / (lag + 1.0)                      # Bartlett kernel
        var += 2.0 * weight * float(np.dot(d_c[k:], d_c[:-k]) / n)
    if var <= 0:
        return float("nan"), float("nan")
    stat = float(d.mean() / math.sqrt(var / n))
    p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(stat) / math.sqrt(2.0))))
    return stat, p


def score_one(name: str, returns: pd.Series) -> dict | None:
    """All four forecasters against the realised outcome, out of sample."""
    returns, dropped_returns = clean_returns(returns)
    n_rows = len(returns)
    min_train = train_window(n_rows)
    fc = all_forecasts(returns, min_train)
    actual = models.forward_realised_vol(returns, horizon=HORIZON)
    frame = pd.concat([fc, actual.rename("actual")], axis=1).iloc[min_train:].dropna()

    # QLIKE takes the log of a variance ratio, so a window with exactly zero volatility
    # (a suspended or frozen stock: the price does not move for a month) has no defined
    # loss. Those days are removed and counted rather than left to turn a whole ticker's
    # average into inf.
    positive = (frame > 0).all(axis=1)
    frozen_days = int((~positive).sum())
    frame = frame[positive]
    if len(frame) < MIN_OOS_DAYS:
        return None

    a = frame["actual"].to_numpy()
    out = {"ticker": name, "n_days": int(len(frame)),
           "history_rows": int(n_rows),
           "tier": "full" if n_rows >= FULL_HISTORY_ROWS else "partial",
           "train_days": int(min_train),
           "start": str(frame.index[0].date()), "end": str(frame.index[-1].date()),
           "dropped_artefact_returns": dropped_returns,
           "dropped_zero_variance_days": frozen_days,
           "models": {}}
    base_loss = qlike(a, frame["naive"].to_numpy())

    for m in MODELS:
        f = frame[m].to_numpy()
        loss = qlike(a, f)
        entry = {
            "qlike": float(loss.mean()),
            "rmse": float(np.sqrt(np.mean((a - f) ** 2))),
            "mae": float(np.mean(np.abs(a - f))),
            "bias": float(np.mean(f - a)),
        }
        if m != "naive":
            stat, p = diebold_mariano(base_loss, loss, lag=HORIZON - 1)
            entry["dm_stat_vs_naive"], entry["dm_p_vs_naive"] = stat, p
        out["models"][m] = entry
    return out


def _worker(args):
    name, values, index = args
    returns = pd.Series(values, index=pd.to_datetime(index))
    try:
        return score_one(name, returns)
    except Exception as exc:                       # one bad ticker must not sink the run
        return {"ticker": name, "error": f"{type(exc).__name__}: {exc}"}


def load_returns(tickers):
    import utils
    loaded, skipped = {}, {}
    for t in tickers:
        try:
            prices = utils.load_prices(t, period="10y")
        except Exception as exc:
            skipped[t] = f"download failed: {type(exc).__name__}"
            continue
        if prices is None or len(prices) < MIN_PARTIAL_ROWS:
            skipped[t] = (f"only {0 if prices is None else len(prices)} rows of history; "
                          f"needs at least {MIN_PARTIAL_ROWS} to leave anything to score")
            continue
        loaded[t] = np.log(prices["Close"]).diff().dropna()
    return loaded, skipped


def _finite(r: dict) -> bool:
    return all(math.isfinite(v["qlike"]) and math.isfinite(v["rmse"])
               for v in r["models"].values())


def aggregate(results: list[dict], tier: str | None = None) -> dict:
    """Summary across tickers, optionally restricted to the 'full' or 'partial' tier.

    A ticker with any non-finite loss is left out and counted, never averaged in: one inf
    turns a median into nan and makes the whole table unreadable, which is exactly how the
    first run of this backtest failed.
    """
    ok = [r for r in results if "models" in r and (tier is None or r["tier"] == tier)]
    excluded = [r["ticker"] for r in ok if not _finite(r)]
    ok = [r for r in ok if _finite(r)]
    agg = {"tickers": len(ok), "excluded_non_finite": excluded}
    for m in MODELS:
        if m == "naive":
            continue
        q_ratio = [r["models"][m]["qlike"] / r["models"]["naive"]["qlike"] for r in ok]
        r_ratio = [r["models"][m]["rmse"] / r["models"]["naive"]["rmse"] for r in ok]
        wins = [r["models"][m]["qlike"] < r["models"]["naive"]["qlike"] for r in ok]
        sig_better = [r["models"][m]["dm_p_vs_naive"] < 0.05 and r["models"][m]["dm_stat_vs_naive"] > 0
                      for r in ok if not math.isnan(r["models"][m]["dm_p_vs_naive"])]
        sig_worse = [r["models"][m]["dm_p_vs_naive"] < 0.05 and r["models"][m]["dm_stat_vs_naive"] < 0
                     for r in ok if not math.isnan(r["models"][m]["dm_p_vs_naive"])]
        agg[m] = {
            "median_qlike_ratio_vs_naive": float(np.median(q_ratio)),
            "median_rmse_ratio_vs_naive": float(np.median(r_ratio)),
            "share_beating_naive": float(np.mean(wins)),
            "share_significantly_better": float(np.mean(sig_better)) if sig_better else None,
            "share_significantly_worse": float(np.mean(sig_worse)) if sig_worse else None,
        }
    return agg


def selfcheck() -> int:
    """A forecast made on day d must not change if every later day is deleted.

    This is the test that a walk-forward backtest is worth anything. It takes a real
    series, forecasts on the full history, then again on history truncated at several
    earlier dates, and requires the forecast on the last kept day to match to numerical
    precision. Any leak of future data into a parameter fit or a recursion breaks it.
    """
    import utils
    r = np.log(utils.load_prices("NIFTY", period="10y")["Close"]).diff().dropna()
    full = all_forecasts(r)
    bad = 0
    for cut in (1200, 1500, 1900, 2200):
        part = all_forecasts(r.iloc[:cut])
        d = part.index[-1]
        for m in MODELS:
            a, b = full.loc[d, m], part.loc[d, m]
            if np.isnan(a) and np.isnan(b):
                continue
            if not np.isclose(a, b, rtol=1e-9, atol=1e-12):
                print(f"LEAK  {m:9s} at {d.date()}: full={a:.10f} truncated={b:.10f}")
                bad += 1
    print("no lookahead detected in any forecaster" if bad == 0 else f"{bad} leak(s) found")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfcheck", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="Only the first N tickers (testing)")
    args = ap.parse_args()

    if args.selfcheck:
        return selfcheck()

    tickers = UNIVERSE[:args.limit] if args.limit else UNIVERSE
    print(f"downloading {len(tickers)} tickers...")
    loaded, skipped = load_returns(tickers)
    print(f"  usable {len(loaded)}, skipped {len(skipped)}")

    jobs = [(n, r.to_numpy(), [str(i) for i in r.index]) for n, r in loaded.items()]
    print(f"scoring on {args.workers} workers (GARCH refit every {REFIT_EVERY} days)...")
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(_worker, jobs))

    ok = [r for r in results if r and "models" in r]
    failed = {r["ticker"]: r["error"] for r in results if r and "error" in r}
    too_short_after_cleaning = [n for n in loaded if n not in {r["ticker"] for r in ok}
                                and n not in failed]

    aggregates = {"all": aggregate(ok), "full_history": aggregate(ok, "full"),
                  "partial_history": aggregate(ok, "partial")}

    OUT.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "horizon_days": HORIZON, "min_train_days": MIN_TRAIN, "refit_every_days": REFIT_EVERY,
        "full_history_rows": FULL_HISTORY_ROWS, "max_abs_log_return": MAX_ABS_LOG_RETURN,
        "universe_requested": len(tickers), "tickers_scored": len(ok),
        "skipped_too_little_history": skipped,
        "too_little_out_of_sample_after_cleaning": too_short_after_cleaning,
        "failed": failed, "aggregate": aggregates, "per_ticker": ok,
    }, indent=2))

    print(f"\nscored {len(ok)} of {len(tickers)} tickers, wrote {OUT.name}")
    if skipped or too_short_after_cleaning:
        print(f"  not scored: {list(skipped) + too_short_after_cleaning}")
    for label, block in aggregates.items():
        print(f"\n  {label}  ({block['tickers']} tickers)")
        for m in MODELS:
            if m == "naive":
                continue
            s = block[m]
            print(f"    {m:9s} QLIKE vs naive {s['median_qlike_ratio_vs_naive']:.3f}   "
                  f"RMSE vs naive {s['median_rmse_ratio_vs_naive']:.3f}   "
                  f"beats naive on {s['share_beating_naive'] * 100:.0f}%   "
                  f"significantly better on {(s['share_significantly_better'] or 0) * 100:.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
