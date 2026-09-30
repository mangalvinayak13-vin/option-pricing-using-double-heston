"""
How much do the market-wide page's parameters really move from day to day?

The exhibition page plots each stock's ten fitted parameters over time after standardising
each parameter within that stock (subtract its own mean, divide by its own standard
deviation). Standardising forces every line to have unit spread by construction, whatever
the real movement was, so a nearly constant parameter and a wildly varying one look the
same. This measures the movement in absolute terms instead: the size of the day-to-day
change in each stock's parameters, in units of the spread of the parameters the model was
trained on.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
COLS = ["p_kappa_s", "p_theta_s", "p_sigma_s", "p_rho_s", "p_v0_s",
        "p_kappa_f", "p_theta_f", "p_sigma_f", "p_rho_f", "p_v0_f"]
SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]


def main() -> int:
    spread = json.loads((ROOT / "outputs/training_results/parameter_std.json").read_text())
    df = pd.read_csv(ROOT / "outputs/market_wide/market_wide_surfaces.csv")
    df = df[df["in_training_support"]].sort_values(["ticker", "date_id"])

    within_sd, day_jump = [], []
    for _, sub in df.groupby("ticker"):
        if len(sub) < 10:
            continue
        v = sub[COLS].to_numpy() / np.array([spread[s] for s in SHORT])
        within_sd.append(v.std(axis=0))                       # spread of that stock's own series
        day_jump.append(np.abs(np.diff(v, axis=0)).mean(axis=0))

    within_sd, day_jump = np.array(within_sd), np.array(day_jump)
    print(f"{len(within_sd)} stocks, in-support surfaces only")
    print()
    print("Per stock, how far each parameter wanders over the whole period, in units of the")
    print("spread of the training distribution (1.0 = as much as parameters differ across")
    print("the entire synthetic training set):")
    print(f"  median over stocks and parameters : {np.median(within_sd):.2f}")
    print(f"  90th percentile                   : {np.percentile(within_sd, 90):.2f}")
    print()
    print(f"Typical day-to-day change, same units: {np.median(day_jump):.2f}")
    print()
    print("By parameter (median across stocks):")
    for i, name in enumerate(SHORT):
        print(f"  {name:8s} wander {np.median(within_sd[:, i]):.2f}   day-to-day {np.median(day_jump[:, i]):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
