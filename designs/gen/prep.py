"""Build site_data.json: every number the 20 designs show, from real sources only.

- Research results: outputs/ambiguity/*, outputs/consolidated_results.json (verified).
- Market: official NSE bhavcopy files (CM equity OHLC, FO options), 1 Jul - 25 Sep 2026.
- Model numbers: legacy_streamlit_site/models.py (the project's pricer), unchanged.
Option IVs follow the research protocol (src/g2_r2r3/market.py): closing price, activity
filters, Black IV on the matched futures forward, dated T-bill rate.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("site_models", ROOT / "legacy_streamlit_site" / "models.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
from src.g2_r2r3 import frozen  # noqa: E402

out: dict = {}

# ---------------------------------------------------------------- research (verified) ----
prev = json.loads((ROOT / ".design_canvas" / "gen" / "data.json").read_text())
for k in ("smile_30d", "skew_by_T", "hist", "per_param", "random_pair_median", "ratio_to_random",
          "ambiguity_summary", "dh_over_flat_median", "dh_worse_than_flat_share", "half_life", "per_stock"):
    out[k] = prev[k]
cons = json.loads((ROOT / "outputs" / "consolidated_results.json").read_text())
out["consolidated"] = cons

# ---------------------------------------------------------------- NSE files -------------
BHAV = json.loads((HERE / "bhav_index.json").read_text())  # every complete trading day (find_bhav.py)
days = sorted(BHAV)
out["days"] = [days[0], days[-1], len(days)]


def cm_file(d):
    return ROOT / BHAV[d]["CM"]


def fo_file(d):
    return ROOT / BHAV[d]["FO"]


tickers = sorted(out["per_stock"].keys())
equity: dict[str, list] = {t: [] for t in tickers}
index_close: dict[str, list] = {"NIFTY": [], "BANKNIFTY": []}
for d in days:
    cm = pd.read_csv(cm_file(d), usecols=["TckrSymb", "SctySrs", "OpnPric", "HghPric", "LwPric", "ClsPric", "PrvsClsgPric", "TtlTradgVol"])
    cm = cm[(cm.SctySrs == "EQ") & cm.TckrSymb.isin(tickers)]
    for r in cm.itertuples():
        equity[r.TckrSymb].append([d, float(r.OpnPric), float(r.HghPric), float(r.LwPric), float(r.ClsPric),
                                   float(r.TtlTradgVol), float(r.PrvsClsgPric)])
    fo = pd.read_csv(fo_file(d), usecols=["TckrSymb", "FinInstrmTp", "UndrlygPric"])
    for ix in index_close:
        u = fo[(fo.TckrSymb == ix) & (fo.FinInstrmTp == "IDO")].UndrlygPric.dropna()
        if len(u):
            index_close[ix].append([d, float(u.mode().iloc[0])])
out["equity"] = equity
out["index_close"] = index_close
names = {"NIFTY": "NIFTY 50", "BANKNIFTY": "NIFTY BANK"}
watch = []
for ix, rows in index_close.items():
    c, p = rows[-1][1], rows[-2][1]
    watch.append({"sym": names[ix], "last": c, "chg": c - p, "pct": (c - p) / p * 100, "closes": [r[1] for r in rows]})
for t in tickers:
    rows = equity[t]
    if len(rows) < 2:
        continue
    c, p = rows[-1][4], rows[-1][6]
    watch.append({"sym": t, "last": c, "chg": c - p, "pct": (c - p) / p * 100, "closes": [r[4] for r in rows],
                  "vol": rows[-1][5]})
out["watch"] = watch

# ---------------------------------------------------------------- option chain ----------
d = days[-1]
valuation = date.fromisoformat(d)
fo = pd.read_csv(fo_file(d))
spot = index_close["NIFTY"][-1][1]
fut = fo[(fo.TckrSymb == "NIFTY") & (fo.FinInstrmTp == "IDF")].copy()
fut["exp"] = pd.to_datetime(fut["FininstrmActlXpryDt"]).dt.date
opts = fo[(fo.TckrSymb == "NIFTY") & (fo.FinInstrmTp == "IDO")].copy()
opts["exp"] = pd.to_datetime(opts["FininstrmActlXpryDt"]).dt.date
# the monthly contract (it has a matching future) that is at least 20 days out
futs = sorted(e for e in fut.exp.unique() if (e - valuation).days >= 20)
expiry = futs[0]
forward = float(fut[fut.exp == expiry].ClsPric.iloc[0])
dte = (expiry - valuation).days
T = dte / 365.0
src = frozen.RATE_SOURCE_BY_VALUATION.get(d)
if src is None:  # nearest earlier rate observation
    src = max(k for k in frozen.RATE_OBSERVATIONS if k <= d)
simple = float(frozen.RATE_OBSERVATIONS[src]["yield"])
disc = 1.0 / (1.0 + simple * T)
r = -math.log(disc) / T
q = r - math.log(forward / spot) / T
chain = opts[opts.exp == expiry].copy()
chain = chain[(chain.ClsPric > 0) & (chain.TtlTradgVol > 0) & (chain.OpnIntrst > 0) & (chain.TtlNbOfTxsExctd > 0)]
atm = round(spot / 50) * 50
strikes = [atm + 50 * i for i in range(-8, 9)]
S_ = dict(v0_1=0.02, kappa1=0.5, theta1=0.02, xi1=0.3, rho1=-0.7)
F_ = dict(v0_2=0.02, kappa2=5.0, theta2=0.02, xi2=0.5, rho2=-0.7)


def dh(k, kind, s=spot, t=T, rr=r):
    return float(np.atleast_1d(M.double_heston_price(s, k, t, rr, **S_, **F_, kind=kind, q=q))[0])


rows = []
for k in strikes:
    row = {"strike": k}
    for kind, tag in (("call", "CE"), ("put", "PE")):
        x = chain[(chain.StrkPric == k) & (chain.OptnTp == tag)]
        if len(x):
            px = float(x.ClsPric.iloc[0])
            row[kind] = px
            row[kind + "_oi"] = float(x.OpnIntrst.iloc[0])
            row[kind + "_vol"] = float(x.TtlTradgVol.iloc[0])
            iv = M.implied_vol(px, spot, k, T, r, kind, q)
            row[kind + "_iv"] = None if not np.isfinite(iv) else round(iv * 100, 2)
        row["dh_" + kind] = round(dh(k, kind), 2)
    otm_kind = "put" if k < spot else "call"
    row["dh_iv"] = round(M.implied_vol(row["dh_" + otm_kind], spot, k, T, r, otm_kind, q) * 100, 2)
    row["mkt_iv"] = row.get(otm_kind + "_iv")
    rows.append(row)
K0 = atm
c0 = dh(K0, "call")
paths = M.double_heston_paths(spot, r, T, **S_, **F_, n_paths=20000, n_steps=max(20, dte), seed=7, q=q)
mc, se = M.price_from_paths(paths, K0, r, T, "call")
civ = M.implied_vol(c0, spot, K0, T, r, "call", q)
d1 = (math.log(spot / K0) + (r - q + civ ** 2 / 2) * T) / (civ * math.sqrt(T))
atm_row = next(x for x in rows if x["strike"] == K0)
out["contract"] = {
    "date": d, "spot": spot, "forward": forward, "expiry": expiry.isoformat(), "dte": dte, "rate": r,
    "rate_simple": simple, "rate_source": src, "carry": q, "strike": K0,
    "dh": round(c0, 2), "mc": round(mc, 2), "mc_se": round(se, 2), "market": atm_row.get("call"),
    "market_iv": atm_row.get("call_iv"), "dh_iv": round(civ * 100, 2),
    "oi": atm_row.get("call_oi"), "volume": atm_row.get("call_vol"),
    "delta": round((dh(K0, "call", s=spot + 1) - dh(K0, "call", s=spot - 1)) / 2, 3),
    "gamma": round(dh(K0, "call", s=spot + 1) - 2 * c0 + dh(K0, "call", s=spot - 1), 5),
    "vega": round(math.exp(-q * T) * spot * math.exp(-d1 ** 2 / 2) / math.sqrt(2 * math.pi) * math.sqrt(T) / 100, 1),
    "theta": round(dh(K0, "call", t=T - 1 / 365) - c0, 2),
    "rho": round(dh(K0, "call", rr=r + 0.01) - c0, 1),
}
out["chain"] = rows

# a fan of real simulated paths for the Brownian design (NIFTY, 1 year, 60 paths shown)
fan = M.double_heston_paths(100.0, r, 1.0, **S_, **F_, n_paths=400, n_steps=120, seed=11, q=0.0)
out["fan"] = {"paths": np.round(fan[:60], 2).tolist(),
              "quantiles": {str(p): np.round(np.percentile(fan, p, axis=0), 2).tolist() for p in (5, 25, 50, 75, 95)}}

# the model's price distribution at expiry vs lognormal at the same ATM vol (Probability design)
ST = paths[:, -1] / spot
hist_, edges_ = np.histogram(np.log(ST), bins=60, range=(-0.25, 0.2), density=True)
out["density"] = {"edges": edges_.round(4).tolist(), "dh": hist_.round(3).tolist(), "atm_vol": round(civ, 4), "T": T}

# IV surface (strike x maturity) at the default settings, S = 100 (Surface design)
mats = [7, 14, 30, 60, 90, 180, 365]
ks = [80, 85, 90, 95, 100, 105, 110, 115, 120]
surf = []
for m in mats:
    tm = m / 365
    rowv = []
    for k in ks:
        kind = "put" if k < 100 else "call"
        p = float(np.atleast_1d(M.double_heston_price(100.0, k, tm, 0.0533, **S_, **F_, kind=kind))[0])
        iv = M.implied_vol(p, 100.0, k, tm, 0.0533, kind) if p > 1e-6 else float("nan")
        rowv.append(None if not np.isfinite(iv) else round(iv * 100, 2))
    surf.append(rowv)
out["surface"] = {"days": mats, "strikes": ks, "iv": surf}

(HERE / "site_data.json").write_text(json.dumps(out))
c = out["contract"]
print("days", out["days"], "watch", len(watch), "tickers with equity", sum(1 for t in equity if equity[t]))
print("NIFTY spot", spot, "expiry", expiry, "dte", dte, "fwd", forward, "r", round(r, 5), "q", round(q, 5), "rate src", src)
print("contract", {k: c[k] for k in ("strike", "dh", "mc", "mc_se", "market", "market_iv", "dh_iv", "delta", "gamma", "vega", "theta", "rho")})
print("chain", [(x["strike"], x.get("call"), x.get("put"), x["mkt_iv"], x["dh_iv"]) for x in rows])
print("consolidated keys", list(cons.keys())[:30])
print("surface 30d", surf[2])
