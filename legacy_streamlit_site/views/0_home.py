"""
Page 0 — Home. The exhibition hook, and the spine the rest of the app hangs from.

A visitor is still deciding whether to stop. This page has to answer one question in
the time it takes to read it — does letting volatility move actually price options
better? — and then show that the answer leads somewhere less comfortable than it
first appears.

That second part is the change from the earlier version of this page. The site used
to end its argument at "Heston fits better". It now continues: fitting better and
recovering the parameters that did the fitting turn out to be different problems, and
the later pages are about that gap rather than a footnote to it.
"""

import datetime as dt

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import models
import snapshot
import utils
from utils import COLORS, INK, RISK_FREE_RATE as R
from views_config import CALIB_DAYS, MONEYNESS_BAND

TICKER = "NIFTY"

st.title("From a Random Walk to Wall Street")
st.markdown(
    "#### Does letting volatility move like a physical random process actually price options "
    "better than assuming it's constant?"
)


@st.cache_data(ttl=3600, show_spinner="Fitting to today's live option chain...")
def calibrate_from(spot, quotes):
    """Fit Heston and a single flat volatility to the same quotes, and score both."""
    weights = models.vega_weights(spot, R, quotes["strike"], quotes["T"],
                                  quotes["kind"], quotes["iv"])
    theta_start = float(quotes["iv"].median() ** 2)
    x0 = [float(np.clip(v, *models.HESTON_BOUNDS[n])) for v, n in
          zip([theta_start, 2.0, theta_start, 0.5, -0.7], models.HESTON_BOUNDS)]
    fit = models.calibrate_heston(spot, R, quotes["strike"], quotes["T"], quotes["kind"],
                                  quotes["price"], x0, weights=weights)
    flat_sigma, _ = models.calibrate_black_scholes(spot, R, quotes["strike"], quotes["T"],
                                                   quotes["kind"], quotes["price"])

    def iv_rmse(price_fn):
        priced = np.empty(len(quotes))
        for T_e, kd, idx in models._group_by_maturity_and_kind(list(quotes["T"]),
                                                               list(quotes["kind"])):
            priced[idx] = price_fn(quotes["strike"].values[idx], T_e, kd)
        return models.implied_vol_rmse(spot, R, quotes["strike"], quotes["T"],
                                       quotes["kind"], quotes["iv"], priced)[0]

    return {
        "fit": fit,
        "flat_sigma": flat_sigma,
        "heston_iv": iv_rmse(lambda k, T_e, kd: models.heston_price(spot, k, T_e, R,
                                                                    *fit["params"], kind=kd)),
        "flat_iv": iv_rmse(lambda k, T_e, kd: models.black_scholes(spot, k, T_e, R,
                                                                   flat_sigma, kd)),
    }


def quotes_from_chains(spot, chains, days_to):
    frames = []
    for expiry, chain in chains.items():
        T_e = days_to[expiry] / 365
        frames.append(
            utils.market_implied_vols(chain, spot, T_e, R).assign(T=T_e)
        )
    quotes = pd.concat(frames, ignore_index=True)
    lo, hi = MONEYNESS_BAND
    return quotes[(quotes["strike"] >= lo * spot) & (quotes["strike"] <= hi * spot)]


@st.cache_data(ttl=3600, show_spinner="Fetching the live option chain...")
def live_chain(ticker):
    prices = utils.load_prices(ticker)
    spot = float(prices["Close"].iloc[-1])
    expiries = utils.load_expiries(ticker)
    days_to = {e: (dt.date.fromisoformat(e) - dt.date.today()).days for e in expiries}
    days_to = {e: d for e, d in days_to.items() if d >= 7}

    chosen = []
    for target in CALIB_DAYS:
        nearest = min(days_to, key=lambda e: abs(days_to[e] - target))
        if nearest not in chosen:
            chosen.append(nearest)

    chains = {e: utils.load_option_chain(ticker, e) for e in chosen}
    return spot, chains, days_to


# --- live first, frozen snapshot as the net -------------------------------------
# The snapshot exists because the live feed is the one thing that can fail on the day:
# venue wifi, a rate limit, a holiday, Upstox maintenance. Whatever is being shown is
# labelled, because telling a visitor prices are live when they are three weeks old
# would be worse than showing no live data at all.

source, stale_note = None, None
if snapshot.is_frozen_requested():
    shot = snapshot.load()
    if shot:
        spot, chains, days_to = shot["spot"], shot["chains"], shot["days_to"]
        source, stale_note = "frozen", snapshot.describe()

if source is None:
    try:
        spot, chains, days_to = live_chain(TICKER)
        source = "live"
    except Exception:
        shot = snapshot.load()
        if shot:
            spot, chains, days_to = shot["spot"], shot["chains"], shot["days_to"]
            source, stale_note = "frozen", snapshot.describe()

if source is None:
    st.warning(
        f"Live {TICKER} data is unavailable and no snapshot has been captured. "
        "Open **Pricing models** and press Calibrate once the connection recovers.",
        icon="📡",
    )
    st.stop()

quotes = quotes_from_chains(spot, chains, days_to)
hero = calibrate_from(spot, quotes)

# ---------------------------------------------------------------------------
# The headline
# ---------------------------------------------------------------------------

ratio = hero["flat_iv"] / hero["heston_iv"]
c1, c2, c3 = st.columns(3)
c1.metric("Fits real market prices", f"{ratio:.1f}× closer",
          help="Heston's implied-volatility fit error against the best possible single "
               f"constant volatility, on this {TICKER} option chain.")
c2.metric("With just one more idea", "5 vs. 1 parameters",
          help="Black-Scholes: one number for volatility, forever. Heston: volatility is "
               "itself random and mean-reverting — the same mathematics Einstein used for "
               "a pollen grain in water.")
c3.metric("Tested against", f"{len(quotes)} {'live' if source == 'live' else 'real'} quotes",
          help=f"Real {TICKER} option prices across {quotes['T'].nunique()} expiries.")

if source == "frozen":
    st.info(f"Showing a **frozen snapshot** — {stale_note}. The live feed is not being "
            f"used right now.", icon="🔒")

st.markdown("")

# --- the smile: the one picture that carries the argument ---
grid = np.linspace(0.82 * spot, 1.18 * spot, 60)
T_mid = quotes["T"].median()
is_put = grid < spot
fit = hero["fit"]

bs_price = np.where(is_put,
                    models.black_scholes(spot, grid, T_mid, R, hero["flat_sigma"], "put"),
                    models.black_scholes(spot, grid, T_mid, R, hero["flat_sigma"], "call"))
he_price = np.where(is_put,
                    models.heston_price(spot, grid, T_mid, R, *fit["params"], kind="put"),
                    models.heston_price(spot, grid, T_mid, R, *fit["params"], kind="call"))

def to_iv(prices):
    return [models.implied_vol(p, spot, k, T_mid, R, "put" if put else "call")
            if p >= 0.05 else np.nan
            for p, k, put in zip(prices, grid, is_put)]

fig = go.Figure()
fig.add_trace(go.Scatter(x=grid, y=100 * np.array(to_iv(bs_price)), mode="lines",
                         name="Black-Scholes (flat)",
                         line=dict(color=COLORS["Black-Scholes"], width=3, dash="dash")))
fig.add_trace(go.Scatter(x=grid, y=100 * np.array(to_iv(he_price)), mode="lines",
                         name="Heston (fitted)",
                         line=dict(color=COLORS["Heston"], width=4)))
near = quotes[(quotes["strike"] >= grid[0]) & (quotes["strike"] <= grid[-1])]
fig.add_trace(go.Scatter(x=near["strike"], y=100 * near["iv"], mode="markers",
                         name=f"Real {TICKER} market prices",
                         marker=dict(color=INK, size=9, line=dict(color=INK, width=1.5))))
utils.style_figure(fig, "Strike price (₹)", "Implied volatility (%)", height=460)
fig.update_layout(font=dict(size=15), legend=dict(font=dict(size=15)))
st.plotly_chart(fig, theme=None, width="stretch")
st.caption("Black-Scholes assumes every strike shares one volatility, so it can only draw "
           "a flat line. The market clearly disagrees. Heston lets volatility be random and "
           "correlated with price, and that alone is enough to bend the line to match.")

st.divider()

# ---------------------------------------------------------------------------
# The arc — what this site is actually about
# ---------------------------------------------------------------------------

st.subheader("Four models, each fixing the last one's flaw — and then a catch")

a1, a2 = st.columns(2)
with a1:
    st.markdown(
        "**Black–Scholes (1973)** — volatility is one fixed number. Elegant, and visibly "
        "wrong: it can only draw the flat line above.\n\n"
        "**Geometric Brownian Motion** — the same model, simulated one path at a time "
        "instead of solved. It is the honest way to check the formula.\n\n"
        "**Heston (1993)** — volatility becomes random and mean-reverting. One extra idea, "
        "and the curve bends to fit the market."
    )
with a2:
    st.markdown(
        "**Double Heston** — two sources of volatility randomness instead of one: a slow "
        "one and a fast one, because real markets move on more than one clock.\n\n"
        "**And the catch.** It fits beautifully. But ask which ten numbers produced that "
        "fit and the answer stops being unique — many completely different parameter sets "
        "reproduce the same prices almost exactly.\n\n"
        "That gap between *fitting* and *knowing* is what the last two pages are about."
    )

st.divider()

# ---------------------------------------------------------------------------
# Where to go
# ---------------------------------------------------------------------------

st.subheader("Explore")
e1, e2, e3 = st.columns(3)
with e1:
    st.page_link("views/1_options.py",
                 label="**Options 101**\n\nCalls, puts, implied volatility.",
                 icon=":material/school:")
with e2:
    st.page_link("views/2_pricing.py",
                 label="**Pricing models**\n\nAll four, side by side.",
                 icon=":material/calculate:")
with e3:
    st.page_link("views/3_forecast.py",
                 label="**Volatility forecast**\n\nEWMA and GARCH, honestly scored.",
                 icon=":material/show_chart:")

f1, f2, f3 = st.columns(3)
with f1:
    st.page_link("views/5_double_heston.py",
                 label="**Double Heston**\n\nThe catch, measured.",
                 icon=":material/trending_up:")
with f2:
    st.page_link("views/6_market.py",
                 label="**Whole market**\n\n210 NSE stocks. Pick one.",
                 icon=":material/candlestick_chart:")
with f3:
    st.page_link("views/4_assumptions.py",
                 label="**Assumptions**\n\nWhat these models get wrong.",
                 icon=":material/rule:")

# The snapshot escape hatch: present, but not competing with anything.
if snapshot.snapshot_exists() and source == "live":
    st.caption(
        "Running on live market data. "
        "[Use the frozen snapshot instead](?data=frozen) if the feed looks wrong."
    )
