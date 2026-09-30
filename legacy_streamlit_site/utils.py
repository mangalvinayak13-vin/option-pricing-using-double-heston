"""
utils.py
========
Data loading, caching and constants. Everything that touches yfinance or Streamlit
lives here; the maths lives in models.py.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

import models

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# One flat risk-free rate for every maturity, fixed so results are reproducible.
#
# This is an Indian 91-day Treasury bill yield, because every option this app prices is
# an NSE contract quoted in rupees. It previously used the 13-week US T-bill (3.935%),
# which is the wrong currency's rate: discounting a rupee payoff at a dollar rate
# understated the forward and biased every price and implied volatility on the site.
# The gap is about 1.4 percentage points, which is small next to volatility but is a
# real error rather than an approximation.
#
# Source: RBI 91-day T-bill auction, 5.3324% on 2026-07-15 — the same hash-sealed
# observation the Double Heston research pipeline uses, so both halves of this project
# now discount at the same rate.
RISK_FREE_RATE = 0.053324

TRADING_DAYS = 252  # trading days per year, used to annualise daily volatility

# Option-quote filters. These are judgment calls, not market facts.
MIN_OPTION_PRICE = 0.05   # cheaper quotes are mostly rounding noise when inverted to implied vol
MAX_REL_SPREAD = 0.6      # ignore bid/ask quotes whose spread is over 60% of the mid price


# ---------------------------------------------------------------------------
# Upstox: the option chain source for Indian indices. Yahoo (yfinance) has price history
# for these -- ^NSEI, ^NSEBANK -- but no NSE options data at all, which is the gap this fills.
# A ticker typed here that isn't one of these keys still goes through yfinance untouched, so
# SPY and friends are unaffected.
# ---------------------------------------------------------------------------

UPSTOX_BASE = "https://api.upstox.com/v2"
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

INDIAN_INDICES = {
    "NIFTY": {"yf": "^NSEI", "instrument_key": "NSE_INDEX|Nifty 50"},
    "BANKNIFTY": {"yf": "^NSEBANK", "instrument_key": "NSE_INDEX|Nifty Bank"},
}


def is_indian_index(ticker):
    return ticker.strip().upper() in INDIAN_INDICES


def currency_symbol(ticker):
    """The one place that decides ₹ vs $, so every page agrees with the live-quotes panel."""
    return "₹" if is_indian_index(ticker) else "$"


def _upstox_get(path, params):
    """GET against the Upstox v2 API. Raises on any failure (missing token, HTTP error, bad
    payload) so callers can handle it the same way they already handle a bad yfinance call."""
    if not UPSTOX_ACCESS_TOKEN:
        raise RuntimeError("UPSTOX_ACCESS_TOKEN is not set in .env")
    r = requests.get(f"{UPSTOX_BASE}{path}", params=params,
                     headers={"Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}", "Accept": "application/json"},
                     timeout=15)
    r.raise_for_status()
    body = r.json()
    if body.get("status") != "success":
        raise RuntimeError(f"Upstox API error: {body}")
    return body["data"]


def _upstox_option_chain_raw(ticker, expiry):
    """One expiry's full chain from Upstox, as the raw list of per-strike records."""
    key = INDIAN_INDICES[ticker.strip().upper()]["instrument_key"]
    return _upstox_get("/option/chain", {"instrument_key": key, "expiry_date": expiry})


def _upstox_chain_to_frame(raw):
    """Reshape Upstox's per-strike call+put records into the same columns yfinance's chain
    uses (kind, strike, bid, ask, lastPrice, volume, openInterest), so market_implied_vols
    and everything downstream of it works unchanged regardless of the data source."""
    rows = []
    for row in raw:
        for kind, key in (("call", "call_options"), ("put", "put_options")):
            leg = row.get(key)
            if not leg:
                continue
            # A strike far from the money can arrive with market_data present but
            # completely empty: no book, nothing ever traded. Indexing those keys
            # directly raises, and since that happens mid-parse it discards the entire
            # chain rather than the one dead strike -- twelve untraded far-OTM legs out
            # of 214 were enough to take the live option feed down for the whole site.
            md = leg.get("market_data") or {}
            if not md:
                continue
            rows.append({"kind": kind, "strike": row.get("strike_price"),
                         "bid": md.get("bid_price"), "ask": md.get("ask_price"),
                         "lastPrice": md.get("ltp"), "volume": md.get("volume"),
                         "openInterest": md.get("oi")})
    frame = pd.DataFrame(rows, columns=["kind", "strike", "bid", "ask", "lastPrice",
                                        "volume", "openInterest"])
    if frame.empty:
        return frame
    # Everything downstream needs some usable price; a leg with neither a book nor a
    # last trade cannot supply one, so drop it here rather than let it become a NaN
    # implied volatility later.
    usable = frame[["bid", "ask", "lastPrice"]].notna().any(axis=1)
    return frame.loc[usable & frame["strike"].notna()].reset_index(drop=True)


# Chart colours: the dark steps of one validated categorical palette (checked with the
# dataviz validator: lightness band, chroma, colour-blind separation, 3:1 contrast on the surface).
# A model keeps its colour on every chart; colour follows the model, not its position in a legend.
COLORS = {"Black-Scholes": "#3987e5", "GBM Monte Carlo": "#d95926", "Heston": "#199e70", "Double Heston": "#c98500"}
INK, INK_SECONDARY, SURFACE, GRID = "#ffffff", "#c3c2b7", "#1a1a19", "#2c2c2a"


def style_figure(fig, x_title, y_title, height=440):
    """Apply the shared look to a Plotly figure: dark surface, quiet grid, legend on top, hover tooltips."""
    fig.update_layout(
        height=height, margin=dict(l=70, r=20, t=40, b=60), hovermode="x unified",
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, font=dict(color=INK_SECONDARY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text=x_title, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title_text=y_title, gridcolor=GRID, zeroline=False)
    return fig


# ---------------------------------------------------------------------------
# Shared sidebar input
# ---------------------------------------------------------------------------

def sidebar_ticker():
    """
    Ticker box that remembers its value when you switch pages. (A widget's own state is
    dropped when its page is not on screen, so the value is kept under a plain key.)
    """
    ticker = st.sidebar.text_input("Ticker", value=st.session_state.get("ticker", "NIFTY")).strip().upper()
    st.session_state["ticker"] = ticker
    return ticker


# ---------------------------------------------------------------------------
# Market data (all cached for an hour)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Downloading price history...")
def load_prices(ticker, period="5y"):
    """Daily prices from yfinance as a DataFrame with a 'Close' column (dividend-adjusted). Empty if the ticker is unknown.

    Price history comes from yfinance even for NIFTY/BANKNIFTY (Yahoo has this; it's only the
    options that Yahoo lacks for NSE), via each index's '^NSEI'/'^NSEBANK' Yahoo symbol.
    """
    yf_ticker = INDIAN_INDICES.get(ticker.strip().upper(), {}).get("yf", ticker)
    prices = yf.download(yf_ticker, period=period, progress=False, auto_adjust=True)
    if isinstance(prices.columns, pd.MultiIndex):     # newer yfinance returns (field, ticker) columns
        prices.columns = prices.columns.get_level_values(0)
    prices = prices.dropna(subset=["Close"]) if "Close" in prices else pd.DataFrame()
    # Set once, at the actual download (a cache hit reruns nothing below this line), so it reads
    # as "when this data was fetched" rather than "now".
    prices.attrs["fetched_at"] = datetime.now()
    return prices


@st.cache_data(ttl=3600, show_spinner=False)
def load_expiries(ticker):
    """Option expiry dates listed for the ticker, as 'YYYY-MM-DD' strings (empty list if none)."""
    try:
        if is_indian_index(ticker):
            key = INDIAN_INDICES[ticker.strip().upper()]["instrument_key"]
            contracts = _upstox_get("/option/contract", {"instrument_key": key})
            return sorted({c["expiry"] for c in contracts})
        return list(yf.Ticker(ticker).options)
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner="Downloading option chain...")
def load_option_chain(ticker, expiry):
    """Calls and puts for one expiry, stacked into one DataFrame with a 'kind' column."""
    if is_indian_index(ticker):
        both = _upstox_chain_to_frame(_upstox_option_chain_raw(ticker, expiry))
    else:
        chain = yf.Ticker(ticker).option_chain(expiry)
        both = pd.concat([chain.calls.assign(kind="call"), chain.puts.assign(kind="put")], ignore_index=True)
        both = both[["kind", "strike", "bid", "ask", "lastPrice", "volume", "openInterest"]]
    both.attrs["fetched_at"] = datetime.now()
    return both


# ---------------------------------------------------------------------------
# Live quotes: same data as above, but on a short cache TTL of its own so a "Live quotes"
# panel can poll every few seconds without forcing the heavier calibration data to
# re-download too. yfinance is a REST endpoint, not a push feed, so "live" means "fresh
# if re-fetched" -- this is what makes the re-fetch cheap and frequent.
# ---------------------------------------------------------------------------

LIVE_TTL = 15  # seconds


@st.cache_data(ttl=LIVE_TTL, show_spinner=False)
def load_live_price(ticker):
    """Latest traded price for the underlying, refreshed every LIVE_TTL seconds. None on failure
    (missing token, network error, unknown ticker), so a live panel can show a message instead of crashing."""
    try:
        if is_indian_index(ticker):
            key = INDIAN_INDICES[ticker.strip().upper()]["instrument_key"]
            data = _upstox_get("/market-quote/ltp", {"instrument_key": key})
            price = next(iter(data.values()))["last_price"]
        else:
            price = yf.Ticker(ticker).fast_info["lastPrice"]
        return {"price": float(price), "fetched_at": datetime.now()}
    except Exception:
        return None


@st.cache_data(ttl=LIVE_TTL, show_spinner=False)
def load_live_contract(ticker, expiry, strike, kind):
    """Bid/ask/last/volume/OI for one specific contract, refreshed every LIVE_TTL seconds. None
    if the contract can't be found or the fetch fails.

    Fetches the whole chain for the expiry (neither source has a single-contract endpoint) but
    keeps only the requested row, so the cost is one chain download every LIVE_TTL seconds
    regardless of how many strikes get looked at in that window.
    """
    try:
        if is_indian_index(ticker):
            df = _upstox_chain_to_frame(_upstox_option_chain_raw(ticker, expiry))
        else:
            chain = yf.Ticker(ticker).option_chain(expiry)
            df = (chain.calls if kind == "call" else chain.puts).assign(kind=kind)
        row = df[(df["strike"] == strike) & (df["kind"] == kind)]
        if row.empty:
            return None
        row = row.iloc[0]
        return {"bid": float(row["bid"]), "ask": float(row["ask"]), "last": float(row["lastPrice"]),
                "volume": int(row["volume"]) if pd.notna(row["volume"]) else 0,
                "open_interest": int(row["openInterest"]) if pd.notna(row["openInterest"]) else 0,
                "fetched_at": datetime.now()}
    except Exception:
        return None


def hist_vol(close, window=30):
    """Rolling annualised historical volatility: std of daily log returns over `window` days, times sqrt(252)."""
    return np.log(close).diff().rolling(window).std() * np.sqrt(TRADING_DAYS)


# ---------------------------------------------------------------------------
# Turning a raw option chain into market implied volatilities
# ---------------------------------------------------------------------------

def market_implied_vols(chain, S, T, r):
    """
    Implied vol for each usable quote in a chain, as a DataFrame: strike, kind, price, source, iv.

    Price used, per contract:
      * mid of bid and ask when both are positive and the spread is reasonable ('bid/ask');
      * otherwise the last traded price, if the contract has traded or has open interest
        ('last trade'). Yahoo's free feed often shows bid = ask = 0 (always outside market
        hours), so without this fallback almost nothing would survive. Last trades can be
        stale, so the 'source' column lets the page tell the user how many were used.

    Only out-of-the-money options are kept (puts below the spot, calls at or above it):
    they are the liquid ones, and deep in-the-money prices are mostly intrinsic value, which
    says almost nothing about volatility.
    """
    q = chain.copy()
    mid = (q["bid"] + q["ask"]) / 2.0
    good_quote = (q["bid"] > 0) & (q["ask"] > 0) & ((q["ask"] - q["bid"]) <= MAX_REL_SPREAD * mid)
    traded = (q["lastPrice"] > 0) & ((q["volume"].fillna(0) > 0) | (q["openInterest"].fillna(0) > 0))

    q["price"] = np.where(good_quote, mid, q["lastPrice"])
    q["source"] = np.where(good_quote, "bid/ask", "last trade")
    q = q[(good_quote | traded) & (q["price"] >= MIN_OPTION_PRICE)]
    q = q[((q["kind"] == "put") & (q["strike"] < S)) | ((q["kind"] == "call") & (q["strike"] >= S))]

    q["iv"] = [models.implied_vol(p, S, k, T, r, kind) for p, k, kind in zip(q["price"], q["strike"], q["kind"])]
    q = q.dropna(subset=["iv"])
    return q[["strike", "kind", "price", "source", "iv"]].sort_values("strike").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Cached Monte Carlo
# ---------------------------------------------------------------------------
# We cache only the terminal stock prices (one column), not whole paths: an option's payoff
# needs nothing else, and 50,000 paths x 252 steps would be a ~100 MB cache entry.
# Streamlit keys the cache on every argument, so changing any parameter -- or the seed -- re-simulates,
# and an unchanged rerun returns instantly with identical numbers.

def n_steps_for(model, T):
    """GBM has an exact solution, so one step is enough. Heston models need a fine time grid: about one step per trading day."""
    return 1 if model == "gbm" else int(np.clip(round(T * TRADING_DAYS), 20, TRADING_DAYS))


@st.cache_data(show_spinner=False)
def simulate_terminal(model, S, T, r, params, n_paths, n_steps, seed):
    """
    Terminal prices, shape (n_paths, 1), so models.price_from_paths works on them directly.
    model: 'gbm' (params = (sigma,)), 'heston' (params = v0, kappa, theta, xi, rho),
           or 'double_heston' (params = the same five for factor 1, then for factor 2).
    """
    if model == "gbm":
        paths = models.gbm_paths(S, r, params[0], T, n_paths, n_steps, seed)
    elif model == "heston":
        paths = models.heston_paths(S, r, T, *params, n_paths=n_paths, n_steps=n_steps, seed=seed)
    elif model == "double_heston":
        paths = models.double_heston_paths(S, r, T, *params, n_paths=n_paths, n_steps=n_steps, seed=seed)
    else:
        raise ValueError(f"unknown model {model!r}")
    return paths[:, -1:]


def mc_price(model, S, K, T, r, params, kind, n_paths, seed):
    """Cached Monte Carlo price and standard error for one option."""
    terminal = simulate_terminal(model, S, T, r, tuple(params), n_paths, n_steps_for(model, T), seed)
    return models.price_from_paths(terminal, K, r, T, kind)
