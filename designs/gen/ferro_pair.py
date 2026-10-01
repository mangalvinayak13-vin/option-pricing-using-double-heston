"""Two equally good Double Heston fits to one real NSE surface, for Ferro's "same surface, different magnets".

Re-runs run_market_ambiguity.analyse_surface's loop (same seed, same starts, same tolerance) on one
surface from outputs/ambiguity/ambiguity_surfaces.csv, checks the equivalent count matches the CSV,
and writes the two most distant price-equivalent solutions plus their repriced smiles to
ferro_pair.json. Read-only use of the research code; nothing in the repo is changed.

python3 ferro_pair.py [TICKER DATE]
"""
from __future__ import annotations

import json
import math
import sys
import zlib
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq, least_squares
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import run_market_ambiguity as A  # noqa: E402
from src.plausible_bounds import training_parameter_stats, penalty_residuals  # noqa: E402

P, market, G8 = A.P, A.market, A.G8


def bs(S, K, T, r, q, vol, typ):
    d1 = (math.log(S / K) + (r - q + vol * vol / 2) * T) / (vol * math.sqrt(T))
    d2 = d1 - vol * math.sqrt(T)
    if typ.lower().startswith("c"):
        return S * math.exp(-q * T) * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * math.exp(-q * T) * norm.cdf(-d1)


def iv(price, S, K, T, r, q, typ):
    try:
        return brentq(lambda v: bs(S, K, T, r, q, v, typ) - price, 1e-4, 5.0)
    except Exception:
        return None


def pick_surface():
    df = pd.read_csv(ROOT / "outputs/ambiguity/ambiguity_surfaces.csv")
    med = df.loc[df.price_equivalent_count >= 2, "median_pairwise_dispersion"].median()
    cand = df[(df.price_equivalent_count.between(5, 10)) & (df.usable_slots >= 18)].copy()
    cand["gap"] = (cand.median_pairwise_dispersion - med).abs()
    liquid = ["RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN", "INFY", "TCS", "BHARTIARTL"]
    cand = cand[cand.ticker.isin(liquid)] if cand.ticker.isin(liquid).any() else cand
    row = cand.sort_values("gap").iloc[0]
    return row.ticker, row.date_id, row, med


def main():
    if len(sys.argv) == 3:
        df = pd.read_csv(ROOT / "outputs/ambiguity/ambiguity_surfaces.csv")
        ticker, date_id = sys.argv[1], sys.argv[2]
        row = df[(df.ticker == ticker) & (df.date_id == date_id)].iloc[0]
        med = None
    else:
        ticker, date_id, row, med = pick_surface()
    print("surface", ticker, date_id, "csv equivalents", row.price_equivalent_count,
          "csv dispersion", round(row.median_pairwise_dispersion, 3), "overall median", med)

    spread, phys_lo, phys_hi = training_parameter_stats(margin=2.0)
    box_lo, box_hi = np.full(10, -A.NUMERIC_BOX), np.full(10, A.NUMERIC_BOX)
    G8.register_g8_dates()
    market.TICKER = ticker
    report = market.audit_date(date_id)
    surface = G8.build_g8_surface(date_id, report)
    strikes = np.array([v if v is not None else np.nan
                        for v in surface.metadata["provenance"]["actual_strikes"]], float)
    mask = np.asarray(surface.mask, bool) & np.isfinite(strikes)
    rng = np.random.default_rng(zlib.crc32(f"{ticker}|{date_id}".encode()))
    observed = np.asarray(surface.prices, float)
    mats = sorted(set(surface.maturities))

    def reprice(vec):
        return A.reprice(vec, surface.spot, mats, surface.rates, surface.carries, strikes)

    def price_residuals(z):
        try:
            got = reprice(np.asarray(P.to_array(P.decode(z)), float))
            out = got[mask] - observed[mask]
            return out if np.isfinite(out).all() else np.full(int(mask.sum()), 1e3)
        except Exception:
            return np.full(int(mask.sum()), 1e3)

    def residuals(z):
        vector = np.asarray(P.to_array(P.decode(z)), float)
        return np.concatenate([price_residuals(z), penalty_residuals(vector, phys_lo, phys_hi, spread)])

    sols, rmses = [], []
    for _ in range(16):
        z0 = rng.uniform(np.clip(phys_lo, box_lo, box_hi), np.clip(phys_hi, box_lo, box_hi))
        try:
            sol = least_squares(residuals, z0, bounds=(box_lo, box_hi), method="trf", max_nfev=1200)
        except Exception:
            continue
        rmse = float(np.sqrt(np.mean(price_residuals(sol.x) ** 2)))
        if not np.isfinite(rmse) or rmse > 1e2:
            continue
        sols.append(np.asarray(P.to_array(P.decode(sol.x)), float))
        rmses.append(rmse)
    sols, rmses = np.array(sols), np.array(rmses)
    best = rmses.min()
    keep = rmses <= best * 1.10
    eq, eq_rmse = sols[keep], rmses[keep]
    scaled = eq / spread
    pairs = [(float(np.linalg.norm(scaled[i] - scaled[j]) / np.sqrt(10)), i, j)
             for i, j in combinations(range(len(eq)), 2)]
    dists = [p[0] for p in pairs]
    print("reproduced equivalents", int(keep.sum()), "median dispersion", round(float(np.median(dists)), 3),
          "best rmse", best)
    dmax, i, j = max(pairs)
    a, b = eq[i], eq[j]

    # smiles: every usable slot, observed vs both fits, as implied vols (per spot-normalised price)
    keys = A.CANONICAL_SLOT_KEYS
    pa, pb = reprice(a), reprice(b)
    slots = []
    for k, key in enumerate(keys):
        if not mask[k]:
            continue
        rank = key.expiry_rank
        T = mats[rank - 1]
        r, q = A.rate_and_carry_for_rank(rank, surface.rates, surface.carries)
        S, K, typ = 1.0, strikes[k] / surface.spot, key.option_type
        slots.append({"rank": int(rank), "T": float(T), "days": round(float(T) * 365), "moneyness": float(K),
                      "type": str(typ), "obs_iv": iv(observed[k], S, K, T, r, q, typ),
                      "a_iv": iv(pa[k], S, K, T, r, q, typ), "b_iv": iv(pb[k], S, K, T, r, q, typ),
                      "obs": float(observed[k]), "a": float(pa[k]), "b": float(pb[k])})
    names = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s", "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
    out = {
        "ticker": ticker, "date": date_id, "spot": float(surface.spot),
        "equivalents": int(keep.sum()), "csv_equivalents": int(row.price_equivalent_count),
        "median_dispersion": float(np.median(dists)), "csv_dispersion": float(row.median_pairwise_dispersion),
        "pair_distance": dmax, "names": A.SHORT,
        "a": dict(zip(A.SHORT, map(float, a))), "b": dict(zip(A.SHORT, map(float, b))),
        "a_rmse": float(eq_rmse[i]), "b_rmse": float(eq_rmse[j]),
        "a_scaled": list(map(float, scaled[i])), "b_scaled": list(map(float, scaled[j])),
        "spread": list(map(float, spread)),
        "all_equivalent": [dict(zip(A.SHORT, map(float, s))) for s in eq],
        "slots": slots,
    }
    (HERE / "ferro_pair.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("a", "b", "a_rmse", "b_rmse", "pair_distance")}, indent=1))
    print("slots", len(slots), "sample", slots[:3])


if __name__ == "__main__":
    main()
