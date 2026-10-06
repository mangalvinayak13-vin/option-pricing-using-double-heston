"""Vercel serverless function for Price an option, using the project's own pricer (api/_dh).

POST /api/price            {"strike", "kind", "params": {ten settings}, "market": {spot, t, r, q, strikes}, "mc"}
                           -> price, implied vol, Greeks, smile, model chain, Feller check, Monte Carlo check
GET  /api/price?chain=SYM&r=0.0532
                           -> the live option chain for NIFTY 50, NIFTY BANK or one of the site's 40 F&O
                              stocks (SYM as the site names it, URL-encoded; chain=NIFTY means NIFTY 50), for
                              the monthly expiry at least 14 days away, with the expected future price and
                              the project's implied volatilities

Reads the Upstox token from UPSTOX_ACCESS_TOKEN (the Vercel project's own settings, never committed).
The chain is cached at Vercel's edge for 30 s, shared by every visitor; prices are a pure function of
the request, cached for a day.
"""
import importlib.util
import json
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

_spec = importlib.util.spec_from_file_location("dh_pricing", Path(__file__).resolve().parent / "_dh" / "pricing.py")
pricing = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pricing)


class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj, cache):
        body = json.dumps(obj, allow_nan=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if "warm" in q:  # every page asks this once, so the pricer has loaded before Price an option needs it
            return self._send(200, {"warm": True}, "no-store")
        sym ={"NIFTY": "NIFTY 50"}.get(q.get("chain", [""])[0], q.get("chain", [""])[0])
        if sym not in pricing.INSTRUMENT_MAP:
            return self._send(404, {"error": "unknown underlying"}, "no-store")
        token = os.getenv("UPSTOX_ACCESS_TOKEN")
        if not token:
            return self._send(200, {"status": "no_token"}, "no-store")
        try:
            r = float(q.get("r", ["0.0532"])[0])
            if not -0.05 <= r <= 0.2:
                raise ValueError("rate out of range")
            out = {"status": "live", **pricing.live_chain(token, r, sym)}
        except Exception as e:  # expired token, rate limit, network: the page keeps its saved chain
            return self._send(200, {"status": "error", "error": type(e).__name__}, "no-store")
        self._send(200, out, "public, s-maxage=30, stale-while-revalidate=60")

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 20000:
                raise ValueError("request too large")
            res = pricing.price(json.loads(self.rfile.read(n) or b"{}"))
        except (KeyError, ValueError, TypeError) as e:
            return self._send(400, {"error": str(e)}, "no-store")
        self._send(200, res, "public, max-age=86400")
