"""
Tag every market-wide surface with its front expiry's days to run.

Why this is needed. The models are trained on maturities of 7 to 90 days. On dates
close to a monthly expiry the nearest listed expiry is much shorter than that -- 1
day on 2026-08-24, 4 days on 2026-08-21 -- and those surfaces sit outside the
training support entirely. They duly reprice badly: 165 of 210 stocks exceed 50%
error on 2026-08-24 alone, against 5% of surfaces market-wide.

That is the model meeting an input it was never shown, not a property of the market
or a bug. Reporting it inside the headline figure would misrepresent both. Tagging it
lets the exhibition show in-support performance by default while keeping the
out-of-support surfaces available, since the degradation is itself a real result.

NSE stock options share one monthly expiry cycle, so the front expiry's days to run
is a property of the date rather than the ticker. This was verified across six
unrelated names on two dates before relying on it, which is why this script audits
once per date rather than once per surface -- 60 audits instead of 12,480.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from src.g2_r2r3 import market
from src import g8_evaluation as G8

TRAINING_MIN_DTE = 7          # shortest maturity anywhere in the frozen training set
PROBE_TICKERS = ("NTPC", "RELIANCE", "INFY", "SBIN")


def main() -> int:
    G8.register_g8_dates()
    path = PROJECT_ROOT / "outputs" / "market_wide" / "market_wide_surfaces.csv"
    frame = pd.read_csv(path)

    front: dict[str, int] = {}
    original = market.TICKER
    try:
        for date_id in sorted(frame["date_id"].unique()):
            for ticker in PROBE_TICKERS:
                market.TICKER = ticker
                try:
                    report = market.audit_date(date_id)
                    if not report.get("constructible"):
                        continue
                    details = sorted(report["expiry_details"], key=lambda i: i["rank"])
                    front[date_id] = int(details[0]["dte"])
                    break
                except Exception:
                    continue
    finally:
        market.TICKER = original

    missing = set(frame["date_id"].unique()) - set(front)
    if missing:
        print(f"warning: no front-expiry reading for {sorted(missing)}")

    frame["front_dte"] = frame["date_id"].map(front)
    frame["in_training_support"] = frame["front_dte"] >= TRAINING_MIN_DTE
    frame.to_csv(path, index=False)

    supported = frame["in_training_support"]
    print(f"annotated {len(frame):,} surfaces across {frame['date_id'].nunique()} dates")
    print(f"  dates below the {TRAINING_MIN_DTE}-day training floor: "
          f"{sorted(d for d, v in front.items() if v < TRAINING_MIN_DTE)}")
    print(f"  surfaces in support     : {supported.sum():,} "
          f"({supported.mean() * 100:.1f}%)")
    print(f"  median error in support : {frame.loc[supported, 'repricing_relative'].median() * 100:.1f}%")
    print(f"  median error out of it  : {frame.loc[~supported, 'repricing_relative'].median() * 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
