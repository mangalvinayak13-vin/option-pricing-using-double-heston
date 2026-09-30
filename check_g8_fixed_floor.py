"""
Same sanity check as check_flat_vol_floor.py, but against the corrected G8 run
(outputs/g8_fixed/g8_evaluation.json) produced after fixing the rank-2 rate/carry
bug (see src/rank_conditioning.py). A genuine Double Heston floor can never lose
to a single fitted flat volatility on the same quotes, since flat BS is a
degenerate point Double Heston's parameter space reaches exactly.
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

import run_option_backtest as R
from src import g8_evaluation as G8
from src.g2_r2r3 import market


def main() -> int:
    G8.register_g8_dates()
    market.TICKER = "NTPC"

    g8 = {r["date_id"]: r for r in
          json.loads((ROOT / "outputs/g8_fixed/g8_evaluation.json").read_text())["rows"]}

    print(f"{'date':12s} {'flat BS (1 param)':>18s} {'classical DH floor':>20s} {'network DH':>12s}")
    wins, n, gaps = 0, 0, []
    for d in list(g8):
        try:
            surface = G8.build_g8_surface(d, market.audit_date(d))
            a = R.surface_arrays(surface)
            bs = R.flat_vol_error(a, R.flat_vol_fit(a))
        except Exception as exc:
            print(f"{d:12s} skipped: {exc}")
            continue
        floor = g8[d]["best_fit_relative"]
        net = g8[d]["network_relative"]
        n += 1
        wins += bs < floor
        gaps.append(floor - bs)
        print(f"{d:12s} {bs * 100:17.1f}% {floor * 100:19.1f}% {net * 100:11.1f}%")

    print(f"\nflat Black-Scholes beats the reported Double Heston 'floor' on {wins} of {n} dates")
    if gaps:
        print(f"median amount by which the 'floor' sits above flat BS: {np.median(gaps) * 100:+.1f} points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
