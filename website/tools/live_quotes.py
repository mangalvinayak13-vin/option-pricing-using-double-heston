"""Live last-price/change for the site's 42-symbol universe (NIFTY 50, NIFTY BANK, 40 stocks),
via the Upstox market-quote API. Shared by website/serve.py (local dev) and website/api/live.py
(the Vercel serverless function) -- both import this module and just add their own caching layer.

The symbol -> Upstox instrument key map (upstox_instrument_map.json, no secret in it) was built
once from Upstox's public NSE instrument master; see .shots/work/build_map.py in git history if
it ever needs rebuilding (e.g. a new stock enters the watchlist).

The access token itself is never read from argv or printed; it comes from the UPSTOX_ACCESS_TOKEN
environment variable (set this in Vercel's project settings for production), falling back locally
to the Physics project SEM 1 .env file the same way src/upstox_data_fetcher.py already does.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
INSTRUMENT_MAP: dict[str, str] = __import__("json").loads((HERE / "upstox_instrument_map.json").read_text())
_REVERSE_MAP = {v: k for k, v in INSTRUMENT_MAP.items()}
_IST = timezone(timedelta(hours=5, minutes=30))

def _physics_env() -> Path | None:
    """Find Physics project SEM 1/.env by walking up from here, not a fixed parent-count: this
    file's depth from the repo root differs when running inside a git worktree (nested under
    .claude/worktrees/<name>/) versus a plain checkout."""
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor.parent / "Physics project SEM 1" / ".env"
        if candidate.exists():
            return candidate
    return None


def _token() -> str | None:
    tok = os.getenv("UPSTOX_ACCESS_TOKEN")
    if tok:
        return tok
    env_path = _physics_env()
    if env_path:
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("UPSTOX_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip()
    return None


def market_open(now: datetime | None = None) -> bool:
    """NSE's equity cash-market hours by the clock, 09:15-15:30 IST, Monday-Friday: the fallback when
    NSE's own status (market_state) can't be read. It only drives a label, never whether we trust a quote."""
    now = (now or datetime.now(_IST)).astimezone(_IST)
    if now.weekday() >= 5:
        return False
    hm = now.hour * 60 + now.minute
    return 9 * 60 + 15 <= hm <= 15 * 60 + 30


_HOLIDAYS: dict = {"day": None, "list": []}


def _holiday_today(token: str, today) -> str | None:
    """Today's NSE trading holiday by name (e.g. "Gandhi Jayanti"), from Upstox's holiday calendar,
    fetched once a day."""
    import requests
    if _HOLIDAYS["day"] != today:
        r = requests.get("https://api.upstox.com/v2/market/holidays", headers={"Authorization": f"Bearer {token}",
                         "Accept": "application/json"}, timeout=4)
        r.raise_for_status()
        _HOLIDAYS.update(day=today, list=r.json().get("data") or [])
    return next((h.get("description") for h in _HOLIDAYS["list"] if h.get("date") == today.isoformat()
                 and h.get("holiday_type") == "TRADING_HOLIDAY" and "NSE" in (h.get("closed_exchanges") or [])), None)


def market_state(token: str, now: datetime | None = None) -> tuple[bool, str | None]:
    """(open, holiday): NSE's own status via Upstox, so holidays and special sessions count; when that
    can't be read, the clock. `holiday` names today's trading holiday when there is one."""
    import requests
    now = (now or datetime.now(_IST)).astimezone(_IST)
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
        return (not holiday and market_open(now)), holiday


def fetch_live_quotes() -> dict:
    """One batched call for all 42 symbols. Returns {status, asof, market_open, quotes}; quotes is
    {} (not an exception) on any failure, so a caller can always render something."""
    token = _token()
    asof = datetime.now(timezone.utc).isoformat()
    if not token:
        return {"status": "no_token", "asof": asof, "market_open": market_open(), "quotes": {}}
    try:
        import requests
        r = requests.get("https://api.upstox.com/v2/market-quote/quotes",
                          params={"symbol": ",".join(INSTRUMENT_MAP.values())},
                          headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", {})
    except Exception as e:  # network error, 401/expired token, rate limit -- never crash the page over this
        return {"status": "error", "error": type(e).__name__, "asof": asof, "market_open": market_open(), "quotes": {}}

    quotes = {}
    for row in data.values():
        sym = _REVERSE_MAP.get(row.get("instrument_token"))
        if not sym:
            continue
        ohlc = row.get("ohlc") or {}
        last, chg = row.get("last_price"), row.get("net_change")
        # ohlc.close is NOT the previous close -- checked against Upstox live mid-session (it sat
        # between the other OHLC values, not behind them) and again after the close (it then
        # equalled last_price exactly); last_price - net_change is the one that matches an
        # independent source (Yahoo Finance's own previous-close field) in both cases.
        prev = (last - chg) if last is not None and chg is not None else None
        pct = round(chg / prev * 100, 4) if prev and chg is not None else None
        quotes[sym] = {"last": last, "chg": chg, "pct": pct, "open": ohlc.get("open"), "high": ohlc.get("high"),
                        "low": ohlc.get("low"), "prev_close": prev, "volume": row.get("volume")}
    is_open, holiday = market_state(token)
    return {"status": "live" if quotes else "empty", "asof": asof, "market_open": is_open, "holiday": holiday, "quotes": quotes}


def fetch_candles(sym: str, since: str) -> dict:
    """Daily candles for one symbol from `since` (YYYY-MM-DD) to today, oldest first, as
    [date, open, high, low, close, volume]: Upstox v3 historical days up to yesterday, plus
    today's candle so far from v3 intraday. Fills the gap between the saved NSE history and now.
    Index volume comes back 0 from Upstox (it isn't traded); the page shows that as a dash."""
    asof = datetime.now(timezone.utc).isoformat()
    key, token = INSTRUMENT_MAP.get(sym), _token()
    if not key or not token or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", since or ""):
        return {"status": "bad_request" if token else "no_token", "asof": asof, "sym": sym, "rows": []}
    try:
        import requests
        from urllib.parse import quote
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
