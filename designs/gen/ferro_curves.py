"""Dense curves for the two equally good fits in ferro_pair.json, from the research pricer.

- smile at the 39-day expiry (the surface's second expiry), moneyness 0.90-1.10, both fits
- at-the-money implied vol from 1 week to 2 years, both fits (traded expiries: 4 and 39 days)
Adds "smile_dense" and "term" to ferro_pair.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import run_market_ambiguity as A  # noqa: E402
from ferro_pair import iv  # noqa: E402

G8, market = A.G8, A.market


def main():
    path = HERE / "ferro_pair.json"
    d = json.loads(path.read_text())
    G8.register_g8_dates()
    market.TICKER = d["ticker"]
    surface = G8.build_g8_surface(d["date"], market.audit_date(d["date"]))
    mats = sorted(set(surface.maturities))
    r, q = A.rate_and_carry_for_rank(2, surface.rates, surface.carries)
    S = float(surface.spot)
    vec = {k: np.array([d[k][n] for n in A.SHORT]) for k in ("a", "b")}

    def price(v, Ks, T, typ):
        return A.price_double_heston_surface(S, np.asarray(Ks, float), np.full(len(Ks), T), r, q,
                                             [typ] * len(Ks), v, node_count=64) / S

    T2 = mats[1]
    ms = np.round(np.arange(0.90, 1.1001, 0.005), 4)
    dense = {"T": T2, "days": round(T2 * 365), "m": ms.tolist()}
    for k, v in vec.items():
        out = []
        for m in ms:
            typ = "put" if m < 1 else "call"
            p = float(price(v, [m * S], T2, typ)[0])
            out.append(iv(p, 1.0, m, T2, r, q, typ))
        dense[k] = out
    days = [4, 7, 14, 21, 30, 39, 60, 90, 120, 180, 270, 365, 450, 545, 730]
    term = {"days": days, "traded_days": [round(t * 365) for t in mats]}
    for k, v in vec.items():
        term[k] = [iv(float(price(v, [S], t / 365, "call")[0]), 1.0, 1.0, t / 365, r, q, "call") for t in days]
    d["smile_dense"], d["term"], d["rate"], d["carry"] = dense, term, r, q
    path.write_text(json.dumps(d, indent=1))
    for i, t in enumerate(days):
        print(t, round(term["a"][i] * 100, 2), round(term["b"][i] * 100, 2))
    print("smile a", [round(x * 100, 1) for x in dense["a"][::4]])
    print("smile b", [round(x * 100, 1) for x in dense["b"][::4]])


if __name__ == "__main__":
    main()
