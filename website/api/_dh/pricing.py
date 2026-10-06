"""Price an option: the one pricing module behind both the Vercel function (api/price.py) and the local
server (website/serve.py), so the site prices the same way everywhere.

models.py beside this file is a byte-for-byte copy of legacy_streamlit_site/models.py -- the project's
tested pricer, unchanged -- because a Vercel function only ships what sits inside the deployed
website/ folder. tools/check_pricer_copy.py fails if the two ever differ.

Two jobs:
  price(body)          the model's side: price, implied vol, Greeks, the smile, model prices across the
                       chain, the Feller check and a 20,000-path Monte Carlo check, for a market the
                       request describes (NIFTY level, time to expiry, rate, carry, listed strikes)
  live_chain(token, r) the market's side, live: NIFTY options from Upstox for the monthly expiry at
                       least 14 days away, the expected future level from put-call parity, and every
                       implied volatility worked out with the project's own implied_vol
"""
from __future__ import annotations

import importlib.util
import math
import time
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np

_spec = importlib.util.spec_from_file_location("dh_models", Path(__file__).resolve().parent / "models.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

KEYS = ["v0_1", "kappa1", "theta1", "xi1", "rho1", "v0_2", "kappa2", "theta2", "xi2", "rho2"]
BOUNDS = {k: M.HESTON_BOUNDS[k] for k in ("v0", "kappa", "theta", "xi", "rho")}
IST = timezone(timedelta(hours=5, minutes=30))
NIFTY = "NSE_INDEX|Nifty 50"
STEP = 50          # NIFTY strike spacing
WINDOW = 1000      # live chain rows returned: today's level ± this
MIN_DAYS = 14      # the contract: the monthly expiry at least this many days away


# ------------------------------------------------------------------ the model's side
def clamp_params(p: dict) -> dict:
    out = {}
    for k in KEYS:
        lo, hi = BOUNDS[k[:-1].rstrip("_")]  # v0_1 -> v0, kappa2 -> kappa
        v = float(p[k])
        if not math.isfinite(v):
            raise ValueError(f"{k} is not a number")
        out[k] = min(max(v, lo), hi)
    return out


def check_market(m: dict) -> tuple:
    """(spot, t, r, q, strikes) from a request, within sane bounds, rounded so equal markets cache together."""
    spot, t, r, q = float(m["spot"]), float(m["t"]), float(m["r"]), float(m["q"])
    strikes = tuple(sorted({float(k) for k in m["strikes"]}))
    if not (1000 < spot < 200000 and 0.5 / 365 <= t <= 2 and -0.05 <= r <= 0.2 and -0.2 <= q <= 0.2):
        raise ValueError("market outside the supported range")
    if not (3 <= len(strikes) <= 41 and all(0.5 * spot < k < 1.5 * spot for k in strikes)):
        raise ValueError("strikes outside the supported range")
    return round(spot, 2), round(t, 6), round(r, 6), round(q, 6), strikes


def _dh(p, k, kind, s, t, r, q):
    return float(np.atleast_1d(M.double_heston_price(s, k, t, r, **p, kind=kind, q=q))[0])


def _iv(price, s, k, t, r, kind, q):
    try:
        v = M.implied_vol(price, s, k, t, r, kind, q)
    except Exception:
        return None
    return round(v * 100, 3) if v is not None and np.isfinite(v) else None


@lru_cache(maxsize=512)
def _price(key: tuple, market: tuple, strike: float, kind: str, mc: bool) -> dict:
    p = dict(zip(KEYS, key))
    spot, t, r, q, chain_strikes = market
    t0 = time.perf_counter()
    c0 = _dh(p, strike, kind, spot, t, r, q)
    iv = _iv(c0, spot, strike, t, r, kind, q)
    up, dn = _dh(p, strike, kind, spot + 1, t, r, q), _dh(p, strike, kind, spot - 1, t, r, q)
    greeks = {"delta": (up - dn) / 2, "gamma": up - 2 * c0 + dn,
              "theta": _dh(p, strike, kind, spot, max(t - 1 / 365, 0.25 / 365), r, q) - c0,
              "rho": _dh(p, strike, kind, spot, t, r + 0.01, q) - c0}
    if iv:
        s = iv / 100
        d1 = (math.log(spot / strike) + (r - q + s * s / 2) * t) / (s * math.sqrt(t))
        greeks["vega"] = math.exp(-q * t) * spot * math.exp(-d1 * d1 / 2) / math.sqrt(2 * math.pi) * math.sqrt(t) / 100
    else:
        greeks["vega"] = None
    # the smile at this expiry: out-of-the-money options, the market's convention
    ks = np.arange(chain_strikes[0] - 400, chain_strikes[-1] + 401, 25.0)
    calls = np.atleast_1d(M.double_heston_price(spot, ks, t, r, **p, kind="call", q=q))
    puts = np.atleast_1d(M.double_heston_price(spot, ks, t, r, **p, kind="put", q=q))
    smile = []
    for k, c, pu in zip(ks, calls, puts):
        kind_k, px = ("put", pu) if k < spot else ("call", c)
        smile.append([float(k), _iv(float(px), spot, float(k), t, r, kind_k, q) if px > 0.05 else None])
    listed = {int(k) for k in chain_strikes}
    chain = {int(k): {"call": round(float(c), 2), "put": round(float(pu), 2)}
             for k, c, pu in zip(ks, calls, puts) if int(k) in listed}
    feller = {}
    for tag, (kap, th, xi) in (("slow", (p["kappa1"], p["theta1"], p["xi1"])), ("fast", (p["kappa2"], p["theta2"], p["xi2"]))):
        feller[tag] = {"lhs": 2 * kap * th, "rhs": xi * xi, "ok": bool(M.feller_condition(kap, th, xi))}
    out = {"price": c0, "iv": iv, "greeks": greeks, "smile": smile, "chain": chain, "feller": feller}
    if mc:
        paths = M.double_heston_paths(spot, r, t, **p, n_paths=20000, n_steps=max(20, round(t * 365)), seed=7, q=q)
        mcp, se = M.price_from_paths(paths, strike, r, t, kind)
        out["mc"] = {"price": float(mcp), "se": float(se), "paths": 20000}
    out["ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return out


def price(body: dict) -> dict:
    p = clamp_params(body["params"])
    market = check_market(body["market"])
    strike = float(body["strike"])
    if not (market[4][0] - 400 <= strike <= market[4][-1] + 400):
        raise ValueError("strike outside the listed range")
    kind = body.get("kind", "call")
    if kind not in ("call", "put"):
        raise ValueError("kind must be call or put")
    res = dict(_price(tuple(round(p[k], 6) for k in KEYS), market, strike, kind, bool(body.get("mc", True))))
    res["params"] = p
    return res


# ------------------------------------------------------------------ the market's side, live
def _get(path: str, token: str, params: dict | None = None):
    import requests
    r = requests.get(f"https://api.upstox.com/v2/{path}", params=params or {},
                     headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=8)
    r.raise_for_status()
    return r.json().get("data")


def pick_expiry(expiries: list[str], today: date) -> str:
    """The monthly contract (the last expiry listed in its month) at least MIN_DAYS away -- the same kind
    of contract the research priced (27 Oct 2026 from 25 Sep). Rolls to the next month on its own."""
    by_month: dict[str, str] = {}
    for e in sorted(expiries):
        by_month[e[:7]] = e
    ok = [e for e in sorted(by_month.values()) if (date.fromisoformat(e) - today).days >= MIN_DAYS]
    if not ok:
        raise ValueError("no monthly expiry far enough away")
    return ok[0]


def _px(md: dict) -> tuple[float | None, str]:
    """A live option price: the middle of the best bid and ask when both are quoted, else the last trade."""
    bid, ask, ltp = md.get("bid_price") or 0, md.get("ask_price") or 0, md.get("ltp") or 0
    if bid > 0 and ask >= bid:
        return round((bid + ask) / 2, 2), "mid"
    return (round(ltp, 2), "last") if ltp > 0 else (None, "none")


def live_chain(token: str, r: float, now: datetime | None = None) -> dict:
    now = (now or datetime.now(IST)).astimezone(IST)
    expiry = pick_expiry([c["expiry"] for c in _get("option/contract", token, {"instrument_key": NIFTY})], now.date())
    raw = _get("option/chain", token, {"instrument_key": NIFTY, "expiry_date": expiry})
    spot = float(raw[0]["underlying_spot_price"])
    close = datetime.fromisoformat(expiry).replace(hour=15, minute=30, tzinfo=IST)
    t = max((close - now).total_seconds() / (365 * 86400), 0.5 / 365)
    rows = []
    for x in sorted(raw, key=lambda x: x["strike_price"]):
        k = float(x["strike_price"])
        if abs(k - spot) > WINDOW or k % STEP:
            continue
        row = {"strike": int(k)}
        for side, key in (("call", "call_options"), ("put", "put_options")):
            md = (x.get(key) or {}).get("market_data") or {}
            row[side], row[f"{side}_src"] = _px(md)
            row.update({f"{side}_bid": md.get("bid_price"), f"{side}_ask": md.get("ask_price"), f"{side}_ltp": md.get("ltp"),
                        f"{side}_oi": md.get("oi"), f"{side}_vol": md.get("volume")})
        rows.append(row)
    # the expected NIFTY level at expiry, from put-call parity at the strike nearest today's level:
    # F = K + e^(rT) (C - P); the carry q then follows from F = S e^((r - q) T)
    near = min((x for x in rows if x["call"] and x["put"]), key=lambda x: abs(x["strike"] - spot))
    fwd = near["strike"] + math.exp(r * t) * (near["call"] - near["put"])
    if not (0.97 < fwd / spot < 1.03):  # a stale or crossed quote: assume no carry rather than a wild one
        fwd = spot * math.exp(r * t)
    q = r - math.log(fwd / spot) / t
    for x in rows:
        for side in ("call", "put"):
            px = x[side]
            x[f"{side}_iv"] = _iv(px, spot, x["strike"], t, r, side, q) if px and px > 0.05 else None
        x["mkt_iv"] = x["put_iv"] if x["strike"] < spot else x["call_iv"]
    return {"expiry": expiry, "dte": (date.fromisoformat(expiry) - now.date()).days, "t": t, "spot": spot,
            "forward": round(fwd, 2), "rate": r, "carry": q, "parity_strike": near["strike"],
            "asof": datetime.now(timezone.utc).isoformat(), "rows": rows}
