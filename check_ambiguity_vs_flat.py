"""
Are the ambiguity run's "best fits" actually good fits?

The ambiguity analysis keeps every solution within 10% of the BEST fit it found and reports
how far apart their parameters are. That only says something about identifiability if the
best fit is a genuinely good one. A least-squares Double Heston fit that is beaten by a
single flat volatility has not found the optimum, and "many equally good solutions" then
means "many equally mediocre ones".

For every surface the run has finished, this compares its best price RMSE with the RMSE of
one flat Black-Scholes volatility fitted to the same quotes, in the same units
(spot-normalised price).
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import pandas as pd

import run_option_backtest as R
from src import g8_evaluation as G8
from src.g2_r2r3 import market


def main() -> int:
    G8.register_g8_dates()
    results = pd.read_csv(ROOT / "outputs" / "ambiguity" / "ambiguity_surfaces.csv")
    rows = []
    for r in results.itertuples():
        market.TICKER = r.ticker
        try:
            a = R.surface_arrays(G8.build_g8_surface(r.date_id, market.audit_date(r.date_id)))
            m = a["mask"]
            sigma = R.flat_vol_fit(a)
            rel = R.flat_vol_error(a, sigma)
            flat_abs = rel * float(np.mean(np.abs(a["obs"][m])))
        except Exception:
            continue
        rows.append({"ticker": r.ticker, "date_id": r.date_id,
                     "dh_best_rmse": r.best_price_rmse, "flat_bs_rmse": flat_abs,
                     "dispersion": r.median_pairwise_dispersion})

    d = pd.DataFrame(rows)
    d["dh_over_flat"] = d.dh_best_rmse / d.flat_bs_rmse
    d.to_csv(ROOT / "outputs" / "ambiguity" / "ambiguity_vs_flat.csv", index=False)

    worse = (d.dh_best_rmse > d.flat_bs_rmse).mean()
    print(f"surfaces checked: {len(d)}")
    print(f"median best-DH RMSE      : {d.dh_best_rmse.median():.2e}")
    print(f"median flat-BS RMSE      : {d.flat_bs_rmse.median():.2e}")
    print(f"median (best DH)/(flat)  : {d.dh_over_flat.median():.2f}   (below 1.0 would mean DH is finding the optimum)")
    print(f"best DH fit is WORSE than a single flat vol on {worse * 100:.0f}% of surfaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
