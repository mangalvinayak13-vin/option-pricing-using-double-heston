"""Vercel serverless function: GET /api/live -- live last price/change for the site's 42-symbol
universe (NIFTY 50, NIFTY BANK, 40 stocks), via the Upstox market-quote API.

Self-contained on purpose (the instrument map is embedded below, not read from
website/tools/upstox_instrument_map.json) -- Vercel's Python builder only reliably bundles what a
function's own file references, and a relative file read from a sibling directory at runtime is
not something to depend on here. The map was generated once by website/.shots/work/build_map.py
from Upstox's public NSE instrument master and only changes if a new symbol joins the watchlist.

Reads the token from the UPSTOX_ACCESS_TOKEN environment variable (set in the Vercel project's
own settings, never committed). The response is cached at Vercel's edge for 5s via Cache-Control,
so the real Upstox call rate stays near one per 5 seconds regardless of visitor traffic -- see
website/tools/live_quotes.py, which website/serve.py uses locally; this file mirrors its logic
rather than importing it, for the same bundling reason.
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, quote, urlparse

INSTRUMENT_MAP = {
    "ADANIPOWER": "NSE_EQ|INE814H01029", "ASHOKLEY": "NSE_EQ|INE208A01029", "BAJFINANCE": "NSE_EQ|INE296A01032",
    "BANKBARODA": "NSE_EQ|INE028A01039", "BEL": "NSE_EQ|INE263A01024", "BHARTIARTL": "NSE_EQ|INE397D01024",
    "BHEL": "NSE_EQ|INE257A01026", "BSE": "NSE_EQ|INE118H01025", "CANBK": "NSE_EQ|INE476A01022",
    "COALINDIA": "NSE_EQ|INE522F01014", "DIXON": "NSE_EQ|INE935N01020", "ETERNAL": "NSE_EQ|INE758T01015",
    "HAL": "NSE_EQ|INE066F01020", "HCLTECH": "NSE_EQ|INE860A01027", "HDFCBANK": "NSE_EQ|INE040A01034",
    "HINDALCO": "NSE_EQ|INE038A01020", "HINDUNILVR": "NSE_EQ|INE030A01027", "HINDZINC": "NSE_EQ|INE267A01025",
    "ICICIBANK": "NSE_EQ|INE090A01021", "INFY": "NSE_EQ|INE009A01021", "ITC": "NSE_EQ|INE154A01025",
    "JIOFIN": "NSE_EQ|INE758E01017", "KALYANKJIL": "NSE_EQ|INE303R01014", "KOTAKBANK": "NSE_EQ|INE237A01036",
    "LT": "NSE_EQ|INE018A01030", "MARUTI": "NSE_EQ|INE585B01010", "MCX": "NSE_EQ|INE745G01043",
    "NATIONALUM": "NSE_EQ|INE139A01034", "NIFTY 50": "NSE_INDEX|Nifty 50", "NIFTY BANK": "NSE_INDEX|Nifty Bank",
    "ONGC": "NSE_EQ|INE213A01029", "PFC": "NSE_EQ|INE134E01011", "PNB": "NSE_EQ|INE160A01022",
    "RELIANCE": "NSE_EQ|INE002A01018", "SBICARD": "NSE_EQ|INE018E01016", "SBIN": "NSE_EQ|INE062A01020",
    "TATAPOWER": "NSE_EQ|INE245A01021", "TATASTEEL": "NSE_EQ|INE081A01020", "TCS": "NSE_EQ|INE467B01029",
    "TMPV": "NSE_EQ|INE155A01022", "VEDL": "NSE_EQ|INE205A01025", "WIPRO": "NSE_EQ|INE075A01022",
}
_REVERSE_MAP = {v: k for k, v in INSTRUMENT_MAP.items()}
_IST = timezone(timedelta(hours=5, minutes=30))


def _market_open(now=None):
    now = (now or datetime.now(_IST)).astimezone(_IST)
    if now.weekday() >= 5:
        return False
    hm = now.hour * 60 + now.minute
    return 9 * 60 + 15 <= hm <= 15 * 60 + 30


_HOLIDAYS = {"day": None, "list": []}


def _holiday_today(token, today):
    """Today's NSE trading holiday by name, from Upstox's holiday calendar, fetched once a day per instance."""
    import requests
    if _HOLIDAYS["day"] != today:
        r = requests.get("https://api.upstox.com/v2/market/holidays", headers={"Authorization": f"Bearer {token}",
                         "Accept": "application/json"}, timeout=4)
        r.raise_for_status()
        _HOLIDAYS.update(day=today, list=r.json().get("data") or [])
    return next((h.get("description") for h in _HOLIDAYS["list"] if h.get("date") == today.isoformat()
                 and h.get("holiday_type") == "TRADING_HOLIDAY" and "NSE" in (h.get("closed_exchanges") or [])), None)


def _market_state(token):
    """(open, holiday): NSE's own status via Upstox, so holidays and special sessions count; the clock
    when that can't be read. Mirrors market_state in website/tools/live_quotes.py."""
    import requests
    now = datetime.now(_IST)
    try:
        holiday = _holiday_today(token, now.date())
    except Exception:
        holiday = None
    try:
        r = requests.get("https://api.upstox.com/v2/market/status/NSE", headers={"Authorization": f"Bearer {token}",
                         "Accept": "application/json"}, timeout=4)
        r.raise_for_status()
        return r.json()["data"]["status"] == "NORMAL_OPEN", holiday
    except Exception:
        return (not holiday and _market_open(now)), holiday


def _fetch():
    token = os.getenv("UPSTOX_ACCESS_TOKEN")
    asof = datetime.now(timezone.utc).isoformat()
    if not token:
        return {"status": "no_token", "asof": asof, "market_open": _market_open(), "quotes": {}}
    try:
        import requests
        r = requests.get("https://api.upstox.com/v2/market-quote/quotes",
                          params={"symbol": ",".join(INSTRUMENT_MAP.values())},
                          headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", {})
    except Exception as e:
        return {"status": "error", "error": type(e).__name__, "asof": asof, "market_open": _market_open(), "quotes": {}}

    quotes = {}
    for row in data.values():
        sym = _REVERSE_MAP.get(row.get("instrument_token"))
        if not sym:
            continue
        ohlc = row.get("ohlc") or {}
        last, chg = row.get("last_price"), row.get("net_change")
        # ohlc.close is NOT the previous close (verified against Yahoo Finance's own previous-close
        # field); last_price - net_change is. See website/tools/live_quotes.py for the full note.
        prev = (last - chg) if last is not None and chg is not None else None
        pct = round(chg / prev * 100, 4) if prev and chg is not None else None
        quotes[sym] = {"last": last, "chg": chg, "pct": pct, "open": ohlc.get("open"), "high": ohlc.get("high"),
                        "low": ohlc.get("low"), "prev_close": prev, "volume": row.get("volume")}
    is_open, holiday = _market_state(token)
    return {"status": "live" if quotes else "empty", "asof": asof, "market_open": is_open, "holiday": holiday, "quotes": quotes}


def _candles(sym, since):
    """GET /api/live?candles=SYM&since=YYYY-MM-DD: daily candles from `since` to today, oldest first,
    as [date, open, high, low, close, volume] -- Upstox v3 historical days up to yesterday plus today's
    candle so far from v3 intraday. Mirrors fetch_candles in website/tools/live_quotes.py."""
    asof = datetime.now(timezone.utc).isoformat()
    key, token = INSTRUMENT_MAP.get(sym), os.getenv("UPSTOX_ACCESS_TOKEN")
    if not key or not token or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since or ""):
        return {"status": "bad_request" if token else "no_token", "asof": asof, "sym": sym, "rows": []}
    try:
        import requests
        h = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        today = datetime.now(_IST).date()
        k = quote(key, safe="")
        rows = []
        if since < today.isoformat():
            r = requests.get(f"https://api.upstox.com/v3/historical-candle/{k}/days/1/"
                             f"{(today - timedelta(days=1)).isoformat()}/{since}", headers=h, timeout=8)
            r.raise_for_status()
            rows += r.json().get("data", {}).get("candles", [])
        r = requests.get(f"https://api.upstox.com/v3/historical-candle/intraday/{k}/days/1", headers=h, timeout=8)
        r.raise_for_status()
        rows += r.json().get("data", {}).get("candles", [])
    except Exception as e:
        return {"status": "error", "error": type(e).__name__, "asof": asof, "sym": sym, "rows": []}
    out = {c[0][:10]: [c[0][:10], c[1], c[2], c[3], c[4], c[5]] for c in rows if c[0][:10] >= since}
    return {"status": "live", "asof": asof, "sym": sym, "rows": [out[d] for d in sorted(out)]}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        candles = "candles" in q
        body = json.dumps(_candles(q["candles"][0], q.get("since", [""])[0]) if candles else _fetch()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        # Vercel's edge caches this, shared across every visitor: quotes for 5s, so the real Upstox
        # call rate stays ~1 per 5s regardless of traffic (well inside 500/min, 2000/30min); candles
        # for 60s per symbol, since only today's candle moves.
        self.send_header("Cache-Control", f"public, s-maxage={60 if candles else 5}, stale-while-revalidate=30")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
