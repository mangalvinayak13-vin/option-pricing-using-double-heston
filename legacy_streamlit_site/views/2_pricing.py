"""
Page 2 -- Pricing models.

The story: Black-Scholes assumes one constant volatility, so its implied-volatility-vs-strike
line is flat. Real option markets are not flat. Heston lets volatility move, and that is what
can bend the line into a skew. The main chart puts all of them next to the market.
"""

from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import models
import utils
from utils import COLORS, INK, SURFACE, RISK_FREE_RATE as R

MODEL_NAMES = ["Black-Scholes", "GBM Monte Carlo", "Heston", "Double Heston"]
HESTON_KEYS = ["h_v0", "h_kappa", "h_theta", "h_xi", "h_rho"]
DOUBLE_KEYS = [f"d{i}_{p}" for i in (1, 2) for p in ("v0", "kappa", "theta", "xi", "rho")]
BOUNDS = models.HESTON_BOUNDS

st.title("Pricing models")
st.write("Each model relaxes an assumption of the one before it. The chart below is the point of the page: "
         "it shows what each model implies about volatility across strikes, next to what the market says.")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

ticker = utils.sidebar_ticker()
ccy = utils.currency_symbol(ticker)
prices = utils.load_prices(ticker)
if prices.empty:
    st.error(f"No price data found for '{ticker}'. Check the ticker symbol.")
    st.stop()
close = prices["Close"]
spot = float(close.iloc[-1])
hist_sigma = float(utils.hist_vol(close).iloc[-1])
price_fetched_at = prices.attrs.get("fetched_at")
if price_fetched_at:
    st.sidebar.caption(f"Price history downloaded {price_fetched_at.strftime('%H:%M:%S')} "
                       "(cached up to 1 hour; reruns until then are instant, not re-downloaded).")

# Snap the requested days-to-expiry to the nearest expiry that actually exists, so the model
# curves and the market points describe the same maturity.
days_to = {e: (date.fromisoformat(e) - date.today()).days for e in utils.load_expiries(ticker)}
days_to = {e: d for e, d in days_to.items() if d >= 1}
target_days = st.sidebar.slider("Days to expiry", 7, 365, 30)
expiry = min(days_to, key=lambda e: abs(days_to[e] - target_days)) if days_to else None
T_days = days_to[expiry] if expiry else target_days
T = T_days / 365
st.sidebar.caption(f"Market expiry used: {expiry} ({T_days} days)" if expiry
                   else "No listed options found, so there is no market data to compare with.")

kind = st.sidebar.radio("Option type", ["call", "put"], horizontal=True)
strike = st.sidebar.number_input("Strike", min_value=0.01, max_value=spot * 5, value=float(round(spot)),
                                 step=1.0, key=f"strike_{ticker}")
model_name = st.sidebar.selectbox("Model", MODEL_NAMES)
n_paths = st.sidebar.slider("Monte Carlo paths", 1_000, 50_000, 20_000, step=1_000)
seed = int(st.sidebar.number_input("Random seed", min_value=0, max_value=1_000_000, value=42, step=1))

# Volatility for Black-Scholes and GBM: historical, or the forecast from the Forecast page.
forecast = st.session_state.get("sigma_forecast")
forecast_meta = st.session_state.get("sigma_forecast_meta", {})
if forecast is not None and forecast_meta.get("ticker") == ticker:
    vol_choice = st.sidebar.radio("Volatility for Black-Scholes / GBM",
                                  ["Historical (30-day)", f"Forecast ({forecast_meta['model']})"])
    sigma = float(forecast) if vol_choice.startswith("Forecast") else hist_sigma
else:
    sigma = hist_sigma
    st.sidebar.caption("Volatility: 30-day historical. Run the Volatility forecast page to price with a forecast instead.")

# ---------------------------------------------------------------------------
# Market data for the chosen expiry
# ---------------------------------------------------------------------------

market, market_error, chain_fetched_at = None, None, None
if expiry:
    try:
        raw_chain = utils.load_option_chain(ticker, expiry)
        chain_fetched_at = raw_chain.attrs.get("fetched_at")
        market = utils.market_implied_vols(raw_chain, spot, T, R)
    except Exception as exc:
        market_error = str(exc)

# ---------------------------------------------------------------------------
# Layout, top to bottom. Containers are created now, in display order, and filled below,
# so widgets further down can feed the charts above them.
# ---------------------------------------------------------------------------

live_area = st.container()
metrics_area = st.container()
params_area = st.container()
chart_area = st.container()
greeks_area = st.container()
controls_area = st.expander("Model controls: GBM check, Heston, Double Heston")
calib_area = st.container()

# ---------------------------------------------------------------------------
# Live quotes: self-refreshing panel, separate from the rest of the page. run_every reruns
# only this fragment on a timer, not the whole page, so the Monte Carlo/calibration work
# above and below is not redone every few seconds just to keep this panel current.
# ---------------------------------------------------------------------------


@st.fragment(run_every=f"{utils.LIVE_TTL}s")
def render_live_quotes():
    live_price = utils.load_live_price(ticker)
    if live_price is None:
        st.warning("Could not fetch a live price for this ticker. For NIFTY/BANKNIFTY, check that "
                   "UPSTOX_ACCESS_TOKEN in .env is set and not expired.")
        return
    st.caption(f"Live · underlying refreshed {live_price['fetched_at'].strftime('%H:%M:%S')}, "
               f"contract refreshed on its own {utils.LIVE_TTL}s cycle · polling, not streaming")
    cols = st.columns(6)
    cols[0].metric(f"{ticker} last price", f"{ccy}{live_price['price']:,.2f}")
    if expiry:
        contract = utils.load_live_contract(ticker, expiry, strike, kind)
        if contract:
            cols[1].metric(f"{kind.title()} {strike:g} bid", f"{ccy}{contract['bid']:.2f}")
            cols[2].metric("Ask", f"{ccy}{contract['ask']:.2f}")
            cols[3].metric("Last traded", f"{ccy}{contract['last']:.2f}")
            cols[4].metric("Volume", f"{contract['volume']:,}")
            cols[5].metric("Open interest", f"{contract['open_interest']:,}")
        else:
            cols[1].caption(f"No listed contract at strike {strike:g} for this expiry.")
    else:
        cols[1].caption("No listed options for this ticker.")


with live_area:
    render_live_quotes()

# Starting values for the Heston sliders. They are illustrative starting points, NOT fitted:
# v0 is today's volatility squared, theta is the long-run variance of this ticker's own returns,
# and kappa, xi and rho are round numbers. Press Calibrate to fit them to the market instead.
theta_start = float(np.log(close).diff().var() * utils.TRADING_DAYS)
clip = lambda name, x: float(np.clip(x, *BOUNDS[name]))
defaults = {"h_v0": clip("v0", sigma**2), "h_kappa": 2.0, "h_theta": clip("theta", theta_start),
            "h_xi": 0.5, "h_rho": -0.7,
            # Double Heston: split the variance in two; factor 1 fast (large kappa), factor 2 slow.
            "d1_v0": clip("v0", sigma**2 / 2), "d1_kappa": 5.0, "d1_theta": clip("theta", theta_start / 2), "d1_xi": 0.5, "d1_rho": -0.7,
            "d2_v0": clip("v0", sigma**2 / 2), "d2_kappa": 0.5, "d2_theta": clip("theta", theta_start / 2), "d2_xi": 0.3, "d2_rho": -0.7}
if st.session_state.get("defaults_for") != ticker:       # new ticker: reset the sliders once
    st.session_state.update(defaults)
    st.session_state["defaults_for"] = ticker


# ---------------------------------------------------------------------------
# e) Calibration (runs only when the button is pressed)
# ---------------------------------------------------------------------------
# This block runs BEFORE the sliders below are created, which is what allows it to write the
# fitted values into the sliders' state.

CALIB_TARGET_DAYS = [21, 45, 90, 150, 250, 360]


def calibration_quotes():
    """
    Usable quotes within 80-120% of spot, across a SPREAD of maturities rather than a few
    adjacent ones. kappa is the speed at which variance reverts, so it is identified only by
    how the smile changes with time to expiry: fitted to three expiries a month apart it runs
    to the edge of its range, and fitted across a month-to-a-year spread it does not.
    """
    upcoming = []
    for target in CALIB_TARGET_DAYS:
        nearest = min(days_to, key=lambda e: abs(days_to[e] - target))
        if nearest not in upcoming:
            upcoming.append(nearest)
    frames = []
    for e in upcoming:
        T_e = days_to[e] / 365
        frames.append(utils.market_implied_vols(utils.load_option_chain(ticker, e), spot, T_e, R)
                      .assign(T=T_e, days=days_to[e]))
    quotes = pd.concat(frames, ignore_index=True)
    return quotes[(quotes["strike"] >= 0.8 * spot) & (quotes["strike"] <= 1.2 * spot)]


def run_calibration():
    """Fit Heston to the market. Never raises: any failure comes back as converged=False with a message."""
    fit = {"ticker": ticker, "expiry": expiry}
    try:
        quotes = calibration_quotes()
        if len(quotes) < 8:
            raise ValueError(f"only {len(quotes)} usable option quotes (need at least 8)")
        data = (spot, R, quotes["strike"], quotes["T"], quotes["kind"], quotes["price"])
        # Weight each quote by its vega, which turns a dollar error into a volatility error.
        # Without it the fit chases expensive at-the-money options and ignores the wings,
        # which are the part of the smile that carries the skew.
        weights = models.vega_weights(spot, R, quotes["strike"], quotes["T"], quotes["kind"], quotes["iv"])
        result = models.calibrate_heston(*data, x0=[st.session_state[k] for k in HESTON_KEYS],
                                         weights=weights)
        flat_sigma, flat_rmse = models.calibrate_black_scholes(*data)

        # Score both in volatility points, the scale the smile chart is drawn on. Prices are
        # built group by group (same maturity and type) so they line up with the quote rows.
        def model_ivs(price_one_group):
            priced = np.empty(len(quotes))
            for T_e, kd, idx in models._group_by_maturity_and_kind(list(quotes["T"]), list(quotes["kind"])):
                priced[idx] = price_one_group(quotes["strike"].values[idx], T_e, kd)
            return models.implied_vol_rmse(spot, R, quotes["strike"], quotes["T"], quotes["kind"],
                                           quotes["iv"], priced)[0]

        heston_iv = model_ivs(lambda k, T_e, kd: models.heston_price(spot, k, T_e, R, *result["params"], kind=kd))
        flat_iv = model_ivs(lambda k, T_e, kd: models.black_scholes(spot, k, T_e, R, flat_sigma, kd))

        fit.update(result, flat_rmse=flat_rmse, flat_sigma=flat_sigma, heston_iv=heston_iv, flat_iv=flat_iv,
                   n=len(quotes), n_expiries=int(quotes["T"].nunique()),
                   days=sorted(int(d) for d in quotes["days"].unique()),
                   n_last=int((quotes["source"] == "last trade").sum()))
    except Exception as exc:
        fit.update(converged=False, message=str(exc))
    if fit["converged"]:                       # only a successful fit replaces the slider values
        for key, value in zip(HESTON_KEYS, fit["params"]):
            st.session_state[key] = value
    return fit


with calib_area:
    st.subheader("Calibrate Heston to the market")
    st.write("Fits the five Heston parameters by least squares to option prices from this expiry and the next two "
             "(strikes within 80-120% of spot). It runs only when you press the button. If the fit fails, "
             "the sliders keep their current values.")
    can_calibrate = market is not None and not market.empty
    if st.button("Calibrate Heston", disabled=not can_calibrate):
        with st.spinner("Fitting Heston to the option chain..."):
            st.session_state["heston_fit"] = run_calibration()

    fit = st.session_state.get("heston_fit")
    if fit and fit["ticker"] == ticker:
        if fit["converged"]:
            st.success(f"Calibration converged. The Heston sliders now hold the fitted values (fitted from the "
                       f"{fit['expiry']} expiry and later ones).")
            c1, c2, c3 = st.columns(3)
            c1.metric("Heston fit error", f"{fit['heston_iv']:.2f} vol pts",
                      help=f"Root-mean-square gap between model and market IMPLIED VOLATILITY, in annualised "
                           f"volatility points. Equivalent price error: {ccy}{fit['rmse']:.3f} per option.")
            c2.metric("Best flat volatility", f"{fit['flat_iv']:.2f} vol pts",
                      help=f"The same error for one constant volatility ({fit['flat_sigma']:.1%}) across every "
                           f"strike and expiry. Equivalent price error: {ccy}{fit['flat_rmse']:.3f}.")
            c3.metric("Quotes fitted", fit["n"],
                      help=f"Across {fit['n_expiries']} expiries ({', '.join(str(d) for d in fit['days'])} days); "
                           f"{fit['n_last']} priced from last trades rather than bid/ask.")
            if fit["heston_iv"] < fit["flat_iv"]:
                st.caption(f"Heston tracks the market smile {fit['flat_iv'] / fit['heston_iv']:.1f} times more closely "
                           "than any single flat volatility can. Errors are measured in volatility points rather than "
                           f"price, because a {ccy}1 error means something very different on a {ccy}20 at-the-money "
                           f"option than on a {ccy}0.10 wing.")
            else:
                st.caption("Heston does not track the market smile any more closely than a single flat volatility does.")
            if fit["at_bounds"]:
                st.caption(f"Parameters sitting on the edge of their allowed range: {', '.join(fit['at_bounds'])}. "
                           "The data cannot pin these down on its own.")
            if fit["n_last"] > fit["n"] / 2:
                st.caption("More than half of these quotes are last-traded prices rather than bid/ask mids, so they may be stale.")
        else:
            st.warning(f"Calibration did not converge ({fit['message']}). Falling back to the slider values.")
    elif not can_calibrate:
        st.info("Calibration needs an option chain with usable quotes for this ticker and expiry.")

# ---------------------------------------------------------------------------
# d) Model controls
# ---------------------------------------------------------------------------

with controls_area:
    tab_gbm, tab_heston, tab_double = st.tabs(["GBM Monte Carlo", "Heston", "Double Heston"])

    with tab_gbm:
        st.write("This checks the simulation engine; it is not a pricing method. GBM has an exact Black-Scholes price, "
                 "so we can test whether the Monte Carlo average lands on it as paths are added. The band is ±2 standard "
                 "errors, so the dashed line should sit inside it most of the time (about 19 runs in 20), and the band should shrink as paths increase. "
                 "The same engine, with more moving parts, prices Heston.")
        counts = [1_000, 2_000, 5_000, 10_000, 20_000, 50_000]
        runs = [utils.mc_price("gbm", spot, strike, T, R, (sigma,), kind, n, seed) for n in counts]
        mc_prices, ses = np.array([p for p, _ in runs]), np.array([s for _, s in runs])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=counts, y=mc_prices + 2 * ses, line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=counts, y=mc_prices - 2 * ses, line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(217, 89, 38, 0.22)", name="±2 standard errors"))
        fig.add_trace(go.Scatter(x=counts, y=mc_prices, mode="lines+markers", name="Monte Carlo price",
                                 line=dict(color=COLORS["GBM Monte Carlo"], width=2),
                                 marker=dict(size=8, line=dict(color=SURFACE, width=2))))
        fig.add_hline(y=models.black_scholes(spot, strike, T, R, sigma, kind),
                      line=dict(color=COLORS["Black-Scholes"], width=2, dash="dash"),
                      annotation_text="Black-Scholes price", annotation_position="top right")
        utils.style_figure(fig, "Number of paths (log scale)", f"Option price ({ccy})", height=340)
        fig.update_xaxes(type="log")
        st.plotly_chart(fig, theme=None, width="stretch")

    with tab_heston:
        st.write("Heston makes volatility random. The variance v is pulled toward a long-run level theta at speed kappa, "
                 "and xi sets how violently it moves. **Negative rho is what creates the skew**: when the stock falls, "
                 "volatility tends to rise, so low-strike options become relatively more expensive.")
        left, right = st.columns(2)
        left.slider("v0: current variance", *BOUNDS["v0"], step=0.001, format="%.4f", key="h_v0")
        left.slider("kappa: speed of mean reversion", *BOUNDS["kappa"], step=0.1, key="h_kappa")
        left.slider("theta: long-run variance", *BOUNDS["theta"], step=0.001, format="%.4f", key="h_theta")
        right.slider("xi: volatility of variance", *BOUNDS["xi"], step=0.05, key="h_xi")
        right.slider("rho: price-variance correlation", *BOUNDS["rho"], step=0.01, key="h_rho")
        kappa_h, theta_h, xi_h = (st.session_state[k] for k in ("h_kappa", "h_theta", "h_xi"))
        feller_text = f"2·kappa·theta = {2 * kappa_h * theta_h:.3f} versus xi² = {xi_h**2:.3f}"
        if models.feller_condition(kappa_h, theta_h, xi_h):
            right.success(f"Feller condition holds ({feller_text}): variance never reaches zero.")
        else:
            right.warning(f"Feller condition fails ({feller_text}): variance can touch zero. "
                          "The simulation handles this with full truncation, so prices remain valid.")

    with tab_double:
        st.write("Optional comparison. Double Heston adds a second, independent variance factor, so volatility can have "
                 "a fast component (short-lived spikes) and a slow one (long swings). The starting values here are "
                 "illustrative, not fitted, and there is no calibrate button for this model: ten parameters cannot be "
                 "pinned down from one chain.")
        for i, col in zip((1, 2), st.columns(2)):
            col.markdown(f"**Factor {i}** ({'fast' if i == 1 else 'slow'})")
            col.slider("v0", *BOUNDS["v0"], step=0.001, format="%.4f", key=f"d{i}_v0")
            col.slider("kappa", *BOUNDS["kappa"], step=0.1, key=f"d{i}_kappa")
            col.slider("theta", *BOUNDS["theta"], step=0.001, format="%.4f", key=f"d{i}_theta")
            col.slider("xi", *BOUNDS["xi"], step=0.05, key=f"d{i}_xi")
            col.slider("rho", *BOUNDS["rho"], step=0.01, key=f"d{i}_rho")
            k_, t_, x_ = (st.session_state[f"d{i}_{p}"] for p in ("kappa", "theta", "xi"))
            (col.success if models.feller_condition(k_, t_, x_) else col.warning)(
                f"Feller {'holds' if models.feller_condition(k_, t_, x_) else 'fails'} for factor {i}")

heston_params = tuple(st.session_state[k] for k in HESTON_KEYS)
double_params = tuple(st.session_state[k] for k in DOUBLE_KEYS)

# ---------------------------------------------------------------------------
# Model price for the selected model
# ---------------------------------------------------------------------------
# Heston models are priced by simulation (so the path count and standard error matter) and the
# semi-analytic formula is shown alongside as an independent reference.

if model_name == "Black-Scholes":
    price, std_err, reference, vol_label, vol_shown = (
        models.black_scholes(spot, strike, T, R, sigma, kind), None, None, "Volatility (σ)", sigma)
elif model_name == "GBM Monte Carlo":
    price, std_err = utils.mc_price("gbm", spot, strike, T, R, (sigma,), kind, n_paths, seed)
    reference, vol_label, vol_shown = models.black_scholes(spot, strike, T, R, sigma, kind), "Volatility (σ)", sigma
elif model_name == "Heston":
    price, std_err = utils.mc_price("heston", spot, strike, T, R, heston_params, kind, n_paths, seed)
    reference = models.heston_price(spot, strike, T, R, *heston_params, kind=kind)
    vol_label, vol_shown = "Current vol (√v0)", np.sqrt(heston_params[0])
else:
    price, std_err = utils.mc_price("double_heston", spot, strike, T, R, double_params, kind, n_paths, seed)
    reference = models.double_heston_price(spot, strike, T, R, *double_params, kind=kind)
    vol_label, vol_shown = "Current vol (√(v0₁+v0₂))", np.sqrt(double_params[0] + double_params[5])
reference_label = "Black-Scholes price" if model_name == "GBM Monte Carlo" else "Formula price"

with metrics_area:
    cols = st.columns(5)
    cols[0].metric("Spot", f"{ccy}{spot:,.2f}", help="Latest close.")
    cols[1].metric(vol_label, f"{vol_shown:.1%}")
    cols[2].metric(f"{model_name} price", f"{ccy}{price:,.2f}")
    cols[3].metric("Standard error", f"{ccy}{std_err:,.3f}" if std_err is not None else "n/a",
                   help="Monte Carlo sampling error. Not defined for a closed-form price.")
    cols[4].metric(reference_label, f"{ccy}{reference:,.2f}" if reference is not None else "n/a",
                   help="An independent calculation of the same model, to check the simulation against.")

# ---------------------------------------------------------------------------
# Parameters: which inputs are observed straight from the market, and which have to be
# estimated (historical/forecast volatility, or calibrated/slider-set Heston parameters).
# ---------------------------------------------------------------------------

with params_area:
    st.subheader("Parameters")
    known_col, unknown_col = st.columns(2)
    with known_col:
        st.markdown("**Known** (read directly from the market)")
        st.table(pd.DataFrame({
            "Symbol": ["S", "K", "T", "r"],
            "Value": [f"{ccy}{spot:,.2f}", f"{ccy}{strike:,.2f}", f"{T_days} days", f"{R:.3%}"],
            "Meaning": ["Spot price, latest close", "Strike you chose", "Time to the expiry used",
                        "Risk-free rate (fixed constant, see utils.py)"],
        }).set_index("Symbol"))
    with unknown_col:
        calibrated = model_name == "Heston" and bool(
            st.session_state.get("heston_fit", {}).get("converged") and
            st.session_state["heston_fit"].get("ticker") == ticker)
        st.markdown(f"**Unknown** (estimated{', now calibrated to the market' if calibrated else ' -- nothing here is directly observed'})")
        if model_name in ("Black-Scholes", "GBM Monte Carlo"):
            unknown_rows = {"Symbol": ["σ"], "Value": [f"{sigma:.2%}"],
                            "Meaning": ["Volatility: 30-day historical, or a forecast from the Volatility page"]}
        elif model_name == "Heston":
            names = {"h_v0": "v₀", "h_kappa": "κ", "h_theta": "θ", "h_xi": "ξ", "h_rho": "ρ"}
            meanings = ["Current variance", "Speed of mean reversion", "Long-run variance",
                       "Volatility of variance", "Price/variance correlation"]
            unknown_rows = {"Symbol": list(names.values()),
                            "Value": [f"{heston_params[i]:.4f}" for i in range(5)], "Meaning": meanings}
        else:
            names = [f"{p}{i}" for i in (1, 2) for p in ("v₀", "κ", "θ", "ξ", "ρ")]
            meanings = [f"Factor {i} ({'fast' if i == 1 else 'slow'}): {m}" for i in (1, 2)
                       for m in ("current variance", "mean-reversion speed", "long-run variance",
                                 "vol of variance", "correlation")]
            unknown_rows = {"Symbol": names, "Value": [f"{v:.4f}" for v in double_params], "Meaning": meanings}
        st.table(pd.DataFrame(unknown_rows).set_index("Symbol"))
        if model_name in ("Black-Scholes", "GBM Monte Carlo"):
            st.caption("Not a slider guess: this is estimated from the actual return series, or from the "
                      "Volatility forecast page.")
        elif not calibrated:
            st.caption("Illustrative starting values (see the sliders below) unless you press Calibrate Heston.")

# ---------------------------------------------------------------------------
# b) THE KEY CHART: implied volatility vs strike
# ---------------------------------------------------------------------------

grid = np.linspace(0.8 * spot, 1.2 * spot, 41)
is_put = grid < spot   # use out-of-the-money options only, the same rule applied to the market quotes


def implied_vols_pct(price_fn):
    """
    Implied vol (%) at each grid strike, from a function kind -> prices over the grid.
    Prices below the same floor used to filter market quotes give nan, so the curve stops
    where a real quote could no longer exist: an option worth a millionth of a cent has a
    mathematical implied volatility, but nothing to compare it against.
    """
    otm = np.where(is_put, price_fn("put"), price_fn("call"))
    return 100 * np.array([models.implied_vol(p, spot, k, T, R, "put" if put else "call")
                           if p >= utils.MIN_OPTION_PRICE else np.nan
                           for p, k, put in zip(otm, grid, is_put)])


terminal = utils.simulate_terminal("gbm", spot, T, R, (sigma,), n_paths, 1, seed)   # one simulation reused for every strike
curves = {
    "Black-Scholes": np.full(len(grid), 100 * sigma),   # constant by assumption
    "GBM Monte Carlo": implied_vols_pct(lambda k: np.array([models.price_from_paths(terminal, s, R, T, k)[0] for s in grid])),
    "Heston": implied_vols_pct(lambda k: models.heston_price(spot, grid, T, R, *heston_params, kind=k)),
    "Double Heston": implied_vols_pct(lambda k: models.double_heston_price(spot, grid, T, R, *double_params, kind=k)),
}

with chart_area:
    st.subheader("Implied volatility vs strike")
    show_double = st.toggle("Also show Double Heston", value=False) or model_name == "Double Heston"
    fig = go.Figure()
    widths = {"Black-Scholes": 2, "GBM Monte Carlo": 2, "Heston": 3, "Double Heston": 2}
    for name, iv in curves.items():
        if name == "Double Heston" and not show_double:
            continue
        fig.add_trace(go.Scatter(x=grid, y=iv, mode="lines", name=name, connectgaps=False,
                                 line=dict(color=COLORS[name], width=widths[name], dash="dash" if name == "Black-Scholes" else "solid"),
                                 hovertemplate="%{y:.1f}%"))
    if market is not None and not market.empty:
        shown = market[(market["strike"] >= grid[0]) & (market["strike"] <= grid[-1])]
        for source, symbol, label in (("bid/ask", "circle", "Market (bid/ask mid)"), ("last trade", "circle-open", "Market (last trade)")):
            part = shown[shown["source"] == source]
            if not part.empty:
                fig.add_trace(go.Scatter(x=part["strike"], y=100 * part["iv"], mode="markers", name=label,
                                         marker=dict(color=INK, size=8, symbol=symbol, line=dict(color=INK, width=1.5)),
                                         hovertemplate="%{y:.1f}%"))
    fig.add_vline(x=spot, line=dict(color="#898781", width=1, dash="dot"),
                  annotation_text="Spot", annotation_position="top left")
    fig.add_vline(x=strike, line=dict(color="#898781", width=1),
                  annotation_text="Your strike", annotation_position="top right")
    utils.style_figure(fig, f"Strike ({ccy})", "Implied volatility (%)", height=480)
    st.plotly_chart(fig, theme=None, width="stretch")

    st.caption("Black-Scholes assumes one volatility for every strike, so its line is flat; GBM Monte Carlo is the same model "
               "priced by simulation, so it is flat apart from sampling noise. Heston lets volatility move with the stock. With "
               "negative rho, low strikes get higher implied volatility, which is the direction real markets often lean; how "
               "closely it matches depends on the parameters. Model curves use the sliders below and the chosen volatility.")
    if market_error:
        st.warning(f"Could not load the option chain ({market_error}), so no market points are shown.")
    elif market is None or market.empty:
        st.info("No usable market quotes for this expiry, so only the model curves are shown.")
    else:
        n_last = int((market["source"] == "last trade").sum())
        fetched_str = f" Option chain downloaded {chain_fetched_at.strftime('%H:%M:%S')}." if chain_fetched_at else ""
        st.caption(f"Market points: {len(market) - n_last} from bid/ask mids and {n_last} from last trades, which can be stale. "
                   f"Yahoo's free feed often shows no bid or ask outside market hours. Out-of-the-money options only.{fetched_str}")
    with st.expander("Show the chart data as a table"):
        table = pd.DataFrame({"Strike": grid.round(2), **{f"{k} IV (%)": v.round(2) for k, v in curves.items()}})
        st.dataframe(table, hide_index=True)

# ---------------------------------------------------------------------------
# c) Greeks
# ---------------------------------------------------------------------------

with greeks_area:
    st.subheader("Greeks")
    if model_name in ("Black-Scholes", "GBM Monte Carlo"):
        greek_sigma = sigma
        st.caption(f"Black-Scholes Greeks at σ = {sigma:.1%}, for the option you selected.")
    else:
        greek_sigma = models.implied_vol(reference, spot, strike, T, R, kind)
        st.caption("Heston has no single volatility, so these are Black-Scholes Greeks evaluated at the volatility "
                   f"implied by the {model_name} closed-form price ({greek_sigma:.1%})." if not np.isnan(greek_sigma) else "")
    if np.isnan(greek_sigma):
        st.info("This model's price has no Black-Scholes implied volatility at this strike, so the Greeks are not shown.")
    else:
        g = models.greeks(spot, strike, T, R, greek_sigma, kind)
        st.table(pd.DataFrame({
            "Greek": ["Delta", "Gamma", "Vega", "Theta", "Rho"],
            "Value": [f"{g['delta']:.4f}", f"{g['gamma']:.5f}", f"{g['vega']:.4f}", f"{g['theta']:.4f}", f"{g['rho']:.4f}"],
            "Meaning": [f"Price change for a {ccy}1 move in the stock", f"Change in delta for a {ccy}1 move in the stock",
                        "Price change for a 1-point rise in volatility", "Price change per calendar day passing",
                        "Price change for a 1-point rise in the interest rate"],
        }).set_index("Greek"))
