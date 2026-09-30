"""
Does a single flat volatility beat the "best possible Double Heston fit"?

The real-market results describe a least-squares Double Heston fit as the floor any method
could reach on a surface. That is only true if the fit is at least as good as every simpler
model it should contain. Black-Scholes with one volatility is such a model: Double Heston
reduces to it when both volatilities-of-variance go to zero. So if a flat volatility fits a
surface better than the reported floor, the floor is not a floor.

Compares, on the NTPC development and held-out dates already reported:
  flat Black-Scholes    one volatility, fitted by least squares to that day's real quotes
  classical DH "floor"  the multi-start least-squares Double Heston fit reported earlier
  network DH            the mask-aware network's prediction, reported earlier
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

    dev = {r["date_id"]: r["best_fit_repricing_relative"] for r in
           json.loads((ROOT / "outputs/real_eval/real_classical_fit.json").read_text())["results"]}
    g8 = {r["date_id"]: r for r in
          json.loads((ROOT / "outputs/g8/g8_evaluation.json").read_text())["rows"]}

    print(f"{'date':12s} {'flat BS (1 param)':>18s} {'classical DH floor':>20s} {'network DH':>12s}")
    wins, n, gaps = 0, 0, []
    for d in list(dev) + list(g8):
        try:
            surface = G8.build_g8_surface(d, market.audit_date(d))
            a = R.surface_arrays(surface)
            bs = R.flat_vol_error(a, R.flat_vol_fit(a))
        except Exception:
            continue
        floor = dev[d] if d in dev else g8[d]["best_fit_relative"]
        net = g8[d]["network_relative"] if d in g8 else float("nan")
        n += 1
        wins += bs < floor
        gaps.append(floor - bs)
        print(f"{d:12s} {bs * 100:17.1f}% {floor * 100:19.1f}% {net * 100:11.1f}%")

    print(f"\nflat Black-Scholes beats the reported Double Heston 'floor' on {wins} of {n} dates")
    print(f"median amount by which the 'floor' sits above flat BS: {np.median(gaps) * 100:+.1f} points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
