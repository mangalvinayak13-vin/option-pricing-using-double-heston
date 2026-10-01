"""Run the Double Heston website locally: static pages plus the model API.

    python3 website/serve.py            -> http://localhost:8765
    python3 website/serve.py --port 9000

Pricing uses the project's own pricer, legacy_streamlit_site/models.py, imported unchanged: the same
code the research and the Streamlit site used. Only the Python standard library is used here (plus
numpy/scipy/pandas, which the pricer already needs).

POST /api/price  {"strike": 23150, "kind": "call", "params": {v0_1, kappa1, theta1, xi1, rho1,
                  v0_2, kappa2, theta2, xi2, rho2}, "mc": true}
-> price, implied vol, Greeks, the smile at this expiry, model prices across the chain, the Feller
   condition for each factor, and a 20,000-path Monte Carlo check.

GET  /api/live   -> live last price/change for NIFTY 50, NIFTY BANK and the 40 watchlist stocks,
   via the Upstox market-quote API (website/tools/live_quotes.py), cached server-side for 5s.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import mimetypes
import sys
import threading
import time
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("dh_models", ROOT / "legacy_streamlit_site" / "models.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

SITE = json.loads((HERE / "assets" / "data" / "site.json").read_text())
C = SITE["contract"]
SPOT, T, R, Q = C["spot"], C["dte"] / 365.0, C["rate"], C["carry"]
CHAIN_STRIKES = [row["strike"] for row in SITE["chain"]]
SMILE_STRIKES = list(np.arange(CHAIN_STRIKES[0] - 400, CHAIN_STRIKES[-1] + 401, 25.0))
KEYS = ["v0_1", "kappa1", "theta1", "xi1", "rho1", "v0_2", "kappa2", "theta2", "xi2", "rho2"]
BOUNDS = {"v0": M.HESTON_BOUNDS["v0"], "kappa": M.HESTON_BOUNDS["kappa"], "theta": M.HESTON_BOUNDS["theta"],
          "xi": M.HESTON_BOUNDS["xi"], "rho": M.HESTON_BOUNDS["rho"]}

for ext, typ in ((".js", "text/javascript"), (".mjs", "text/javascript"), (".json", "application/json"),
                 (".woff2", "font/woff2"), (".svg", "image/svg+xml"), (".webmanifest", "application/manifest+json")):
    mimetypes.add_type(typ, ext)

sys.path.insert(0, str(HERE / "tools"))
import live_quotes  # noqa: E402  (website/tools/live_quotes.py)

_LIVE_CACHE: dict = {"t": 0.0, "data": None}
_LIVE_LOCK = threading.Lock()


def live_quotes_cached(max_age=5.0) -> dict:
    now = time.monotonic()
    with _LIVE_LOCK:
        if _LIVE_CACHE["data"] is not None and now - _LIVE_CACHE["t"] < max_age:
            return _LIVE_CACHE["data"]
    result = live_quotes.fetch_live_quotes()
    with _LIVE_LOCK:
        _LIVE_CACHE["t"], _LIVE_CACHE["data"] = now, result
    return result


def clamp_params(p: dict) -> dict:
    out = {}
    for k in KEYS:
        base = k[:-1].rstrip("_")  # v0_1 -> v0, kappa2 -> kappa
        lo, hi = BOUNDS[base]
        v = float(p[k])
        if not math.isfinite(v):
            raise ValueError(f"{k} is not a number")
        out[k] = min(max(v, lo), hi)
    return out


def _dh(p, k, kind, s=SPOT, t=T, r=R):
    return float(np.atleast_1d(M.double_heston_price(s, k, t, r, **p, kind=kind, q=Q))[0])


def _iv(price, k, kind):
    try:
        v = M.implied_vol(price, SPOT, k, T, R, kind, Q)
    except Exception:
        return None
    return round(v * 100, 3) if v is not None and np.isfinite(v) else None


@lru_cache(maxsize=512)
def _price(key: tuple, strike: float, kind: str, mc: bool) -> dict:
    p = dict(zip(KEYS, key))
    t0 = time.perf_counter()
    c0 = _dh(p, strike, kind)
    iv = _iv(c0, strike, kind)
    up, dn = _dh(p, strike, kind, s=SPOT + 1), _dh(p, strike, kind, s=SPOT - 1)
    greeks = {"delta": (up - dn) / 2, "gamma": up - 2 * c0 + dn,
              "theta": _dh(p, strike, kind, t=T - 1 / 365) - c0, "rho": _dh(p, strike, kind, r=R + 0.01) - c0}
    if iv:
        s = iv / 100
        d1 = (math.log(SPOT / strike) + (R - Q + s * s / 2) * T) / (s * math.sqrt(T))
        greeks["vega"] = math.exp(-Q * T) * SPOT * math.exp(-d1 * d1 / 2) / math.sqrt(2 * math.pi) * math.sqrt(T) / 100
    else:
        greeks["vega"] = None
    # the smile at this expiry: out-of-the-money options, the market's convention
    ks = np.array(SMILE_STRIKES)
    calls = np.atleast_1d(M.double_heston_price(SPOT, ks, T, R, **p, kind="call", q=Q))
    puts = np.atleast_1d(M.double_heston_price(SPOT, ks, T, R, **p, kind="put", q=Q))
    smile = []
    for k, c, pu in zip(ks, calls, puts):
        kind_k, px = ("put", pu) if k < SPOT else ("call", c)
        smile.append([float(k), _iv(float(px), float(k), kind_k) if px > 0.05 else None])
    chain = {int(k): {"call": round(float(c), 2), "put": round(float(pu), 2)}
             for k, c, pu in zip(ks, calls, puts) if int(k) in CHAIN_STRIKES}
    feller = {}
    for tag, (kap, th, xi) in (("slow", (p["kappa1"], p["theta1"], p["xi1"])), ("fast", (p["kappa2"], p["theta2"], p["xi2"]))):
        feller[tag] = {"lhs": 2 * kap * th, "rhs": xi * xi, "ok": bool(M.feller_condition(kap, th, xi))}
    out = {"price": c0, "iv": iv, "greeks": greeks, "smile": smile, "chain": chain, "feller": feller}
    if mc:
        paths = M.double_heston_paths(SPOT, R, T, **p, n_paths=20000, n_steps=max(20, C["dte"]), seed=7, q=Q)
        mcp, se = M.price_from_paths(paths, strike, R, T, kind)
        out["mc"] = {"price": float(mcp), "se": float(se), "paths": 20000}
    out["ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return out


def price(body: dict) -> dict:
    p = clamp_params(body["params"])
    strike = float(body.get("strike", C["strike"]))
    if not (SMILE_STRIKES[0] <= strike <= SMILE_STRIKES[-1]):
        raise ValueError("strike outside the listed range")
    kind = body.get("kind", "call")
    if kind not in ("call", "put"):
        raise ValueError("kind must be call or put")
    key = tuple(round(p[k], 6) for k in KEYS)
    res = dict(_price(key, strike, kind, bool(body.get("mc", True))))
    res["params"] = p
    return res


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):  # quiet: only errors
        if args and str(args[1])[:1] in "45":
            super().log_message(fmt, *args)

    def _json(self, code, obj):
        data = json.dumps(obj, allow_nan=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/health"):
            return self._json(200, {"ok": True, "pricer": "legacy_streamlit_site/models.py"})
        if self.path.startswith("/api/live"):
            return self._json(200, live_quotes_cached())
        if self.path.startswith("/api/"):
            return self._json(404, {"error": "unknown endpoint"})
        return super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/price"):
            return self._json(404, {"error": "unknown endpoint"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 20000:
                raise ValueError("request too large")
            body = json.loads(self.rfile.read(n) or b"{}")
            return self._json(200, price(body))
        except (KeyError, ValueError, TypeError) as e:
            return self._json(400, {"error": str(e)})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"Double Heston site: http://localhost:{a.port}   (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
