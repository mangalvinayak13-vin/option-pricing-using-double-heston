"""Run the Double Heston website locally: static pages plus the model API.

    python3 website/serve.py            -> http://localhost:8765
    python3 website/serve.py --port 9000

Pricing goes through api/_dh/pricing.py, the same module the Vercel function (api/price.py) uses, which
runs the project's own pricer unchanged (a byte-for-byte copy of legacy_streamlit_site/models.py). Only
the Python standard library is used here (plus numpy/scipy/pandas, which the pricer already needs).

POST /api/price  {"strike": 23150, "kind": "call", "params": {v0_1, kappa1, theta1, xi1, rho1,
                  v0_2, kappa2, theta2, xi2, rho2}, "market": {spot, t, r, q, strikes}, "mc": true}
-> price, implied vol, Greeks, the smile at this expiry, model prices across the chain, the Feller
   condition for each factor, and a 20,000-path Monte Carlo check.

GET  /api/price?chain=NIFTY&r=0.0532 -> the live NIFTY option chain (see api/_dh/pricing.py).

GET  /api/live   -> live last price/change for NIFTY 50, NIFTY BANK and the 40 watchlist stocks,
   via the Upstox market-quote API (website/tools/live_quotes.py), cached server-side for 1s.
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
from urllib.parse import parse_qs, urlparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("dh_pricing", HERE / "api" / "_dh" / "pricing.py")
pricing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pricing)

for ext, typ in ((".js", "text/javascript"), (".mjs", "text/javascript"), (".json", "application/json"),
                 (".woff2", "font/woff2"), (".svg", "image/svg+xml"), (".webmanifest", "application/manifest+json")):
    mimetypes.add_type(typ, ext)

sys.path.insert(0, str(HERE / "tools"))
import live_quotes  # noqa: E402  (website/tools/live_quotes.py)

_LIVE_CACHE: dict = {"t": 0.0, "data": None}
_LIVE_LOCK = threading.Lock()


def live_quotes_cached(max_age=1.0) -> dict:
    now = time.monotonic()
    with _LIVE_LOCK:
        if _LIVE_CACHE["data"] is not None and now - _LIVE_CACHE["t"] < max_age:
            return _LIVE_CACHE["data"]
    result = live_quotes.fetch_live_quotes()
    with _LIVE_LOCK:
        _LIVE_CACHE["t"], _LIVE_CACHE["data"] = now, result
    return result


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
            q = parse_qs(urlparse(self.path).query)
            if "candles" in q:  # /api/live?candles=SYM&since=YYYY-MM-DD -> daily candles up to today
                return self._json(200, live_quotes.fetch_candles(q["candles"][0], q.get("since", [""])[0]))
            return self._json(200, live_quotes_cached())
        if self.path.startswith("/api/price"):  # ?chain=NIFTY&r=... -> the live option chain
            q = parse_qs(urlparse(self.path).query)
            token = live_quotes._token()
            if q.get("chain", [""])[0] != "NIFTY" or not token:
                return self._json(200, {"status": "no_token" if not token else "bad_request"})
            try:
                return self._json(200, {"status": "live", **pricing.live_chain(token, float(q.get("r", ["0.0532"])[0]))})
            except Exception as e:
                return self._json(200, {"status": "error", "error": type(e).__name__})
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
            return self._json(200, pricing.price(body))
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
