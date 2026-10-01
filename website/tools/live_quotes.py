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
    """NSE's equity cash-market hours, 09:15-15:30 IST, Monday-Friday. No holiday calendar here --
    this only drives a UI label ("Live" vs "Market closed"), never whether we trust the quote."""
    now = (now or datetime.now(_IST)).astimezone(_IST)
    if now.weekday() >= 5:
        return False
    hm = now.hour * 60 + now.minute
    return 9 * 60 + 15 <= hm <= 15 * 60 + 30


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
    return {"status": "live" if quotes else "empty", "asof": asof, "market_open": market_open(), "quotes": quotes}
