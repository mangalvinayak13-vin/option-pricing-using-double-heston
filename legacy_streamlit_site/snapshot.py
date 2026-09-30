"""
Frozen market snapshot — the exhibition's safety net.

The site calibrates against a live Upstox option chain, and a visitor seeing prices
fetched seconds ago is most of the appeal. It is also the one thing that can fail on
the day: venue wifi, a rate limit, a weekend, an exchange holiday, Upstox maintenance.

So the live path stays primary and this captures a known-good chain to fall back on.

How it is reached, deliberately unobtrusive:
  * automatically, if a live fetch raises — the visitor sees data either way;
  * by URL, `?data=frozen`, which is the one to bookmark on the exhibition laptop;
  * by a small link in the page footer, for when the live feed is up but wrong
    (a stale chain mid-holiday looks live and is not).

Capture a fresh one during market hours with:

    python3 snapshot.py capture

Anything served from a snapshot is labelled as such on the page. A visitor being told
prices are live when they are three weeks old would be worse than no live data at all.
"""

from __future__ import annotations

import json
import pickle
import sys
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
SNAPSHOT_DIR = PROJECT / "snapshots"
SNAPSHOT_FILE = SNAPSHOT_DIR / "market_snapshot.pkl"
MANIFEST_FILE = SNAPSHOT_DIR / "market_snapshot.json"


def is_frozen_requested() -> bool:
    """True when the visitor asked for the snapshot via `?data=frozen`."""
    try:
        import streamlit as st
        return str(st.query_params.get("data", "")).lower() == "frozen"
    except Exception:
        return False


def snapshot_exists() -> bool:
    return SNAPSHOT_FILE.is_file() and MANIFEST_FILE.is_file()


def manifest() -> dict:
    if not MANIFEST_FILE.is_file():
        return {}
    try:
        return json.loads(MANIFEST_FILE.read_text())
    except Exception:
        return {}


def load() -> dict | None:
    """The captured chain, or None if there isn't one."""
    if not snapshot_exists():
        return None
    try:
        with open(SNAPSHOT_FILE, "rb") as fh:
            return pickle.load(fh)
    except Exception:
        return None


def describe() -> str:
    """One line naming what the snapshot is and when it was taken."""
    info = manifest()
    if not info:
        return "no snapshot captured"
    when = info.get("captured_at", "unknown time")[:16].replace("T", " ")
    return (f"{info.get('ticker', '?')} chain captured {when}, "
            f"{info.get('quote_count', '?')} quotes across "
            f"{info.get('expiry_count', '?')} expiries")


def capture(ticker: str = "NIFTY") -> int:
    """Fetch a live chain and store it. Run from the command line, not the app."""
    import pandas as pd
    import utils

    SNAPSHOT_DIR.mkdir(exist_ok=True)

    prices = utils.load_prices(ticker)
    spot = float(prices["Close"].iloc[-1])
    expiries = utils.load_expiries(ticker)
    if not expiries:
        print(f"no expiries returned for {ticker}; is the market open?")
        return 1

    import datetime as dt
    days_to = {e: (dt.date.fromisoformat(e) - dt.date.today()).days for e in expiries}
    days_to = {e: d for e, d in days_to.items() if d >= 7}
    if not days_to:
        print(f"no expiry at least 7 days out for {ticker}")
        return 1

    # Pick the same expiries the live page picks -- one near each target maturity, not
    # simply the six nearest. A fallback that samples different expiries produces a
    # visibly different smile from the thing it is standing in for, which defeats the
    # point of having it.
    from views_config import CALIB_DAYS

    chosen: list[str] = []
    for target in CALIB_DAYS:
        nearest = min(days_to, key=lambda e: abs(days_to[e] - target))
        if nearest not in chosen:
            chosen.append(nearest)

    chains = {}
    for expiry in chosen:
        try:
            chains[expiry] = utils.load_option_chain(ticker, expiry)
        except Exception as exc:
            print(f"  skipped {expiry}: {exc}")

    if not chains:
        print("no chain could be fetched")
        return 1

    payload = {
        "ticker": ticker,
        "spot": spot,
        "prices": prices,
        "expiries": sorted(chains),
        "days_to": {e: days_to[e] for e in chains},
        "chains": chains,
        "captured_at": datetime.now().isoformat(),
    }
    with open(SNAPSHOT_FILE, "wb") as fh:
        pickle.dump(payload, fh)

    MANIFEST_FILE.write_text(json.dumps({
        "ticker": ticker,
        "spot": spot,
        "captured_at": payload["captured_at"],
        "expiry_count": len(chains),
        "quote_count": int(sum(len(c) for c in chains.values())),
        "expiries": sorted(chains),
    }, indent=2))

    print(f"captured {ticker} at spot {spot:,.2f}")
    print(f"  {len(chains)} expiries, {sum(len(c) for c in chains.values())} quotes")
    print(f"  -> {SNAPSHOT_FILE}")
    return 0


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "capture"
    if action == "capture":
        raise SystemExit(capture(sys.argv[2] if len(sys.argv) > 2 else "NIFTY"))
    if action == "describe":
        print(describe())
        raise SystemExit(0)
    print(__doc__)
    raise SystemExit(2)
