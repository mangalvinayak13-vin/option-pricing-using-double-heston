"""
Page 3 -- Volatility forecasting.

This page forecasts VOLATILITY, not direction. Nothing here predicts whether the stock goes
up or down; the models predict how much it will move. Every forecast is scored against the
naive baseline (tomorrow looks like today), on data the models were not fitted to.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import models
import utils
from utils import COLORS, INK_SECONDARY, TRADING_DAYS

HORIZON = 21          # forecast the average volatility over the next 21 trading days (about a month)
TRAIN_FRACTION = 0.7  # GARCH is fitted on the first 70% of history and scored on the rest

# Each forecaster gets a fixed colour, reused in the chart and the table.
FORECAST_COLORS = {"Naive baseline": COLORS["Black-Scholes"], "EWMA": COLORS["GBM Monte Carlo"],
                   "GARCH(1,1)": COLORS["Heston"]}

st.title("Volatility forecast")
st.write("These models forecast **how much** the stock will move over the next month, not which way. "
         "The point of the page is the comparison: a forecast is only worth having if it beats the "
         "naive baseline, which simply assumes the next month looks like the last one.")

ticker = utils.sidebar_ticker()
prices = utils.load_prices(ticker, period="10y")
if prices.empty:
    st.error(f"No price data found for '{ticker}'. Check the ticker symbol.")
    st.stop()

returns = np.log(prices["Close"]).diff().dropna()
if len(returns) < 500:
    st.error(f"Only {len(returns)} days of history for '{ticker}'; this page needs at least 500.")
    st.stop()
n_train = int(len(returns) * TRAIN_FRACTION)

# ---------------------------------------------------------------------------
# Forecasts. All three are daily volatility, indexed by the day the forecast is made.
# ---------------------------------------------------------------------------

forecasts = {"Naive baseline": models.naive_vol(returns, window=HORIZON),
             "EWMA": models.ewma_vol(returns)}
garch_info = None
try:
    forecasts["GARCH(1,1)"], garch_info = models.garch_vol(returns, horizon=HORIZON, n_train=n_train)
except Exception as exc:
    st.warning(f"GARCH could not be fitted ({exc}), so only the baseline and EWMA are shown.")

actual = models.forward_realised_vol(returns, horizon=HORIZON)

# Score on the holdout period only: days after the GARCH training window, where every
# forecast is out-of-sample and the actual outcome is known.
frame = pd.DataFrame({**forecasts, "Actual": actual}).iloc[n_train:].dropna()
if frame.empty:
    st.error("Not enough overlapping data to score the forecasts.")
    st.stop()

annualise = np.sqrt(TRADING_DAYS)
scores = pd.DataFrame({
    "Forecast": list(forecasts),
    "RMSE (annualised vol points)": [100 * annualise * float(np.sqrt(np.mean((frame[n] - frame["Actual"]) ** 2)))
                                     for n in forecasts],
    "Mean error (bias)": [100 * annualise * float(np.mean(frame[n] - frame["Actual"])) for n in forecasts],
})
best = scores.loc[scores["RMSE (annualised vol points)"].idxmin(), "Forecast"]
baseline_rmse = float(scores.loc[scores["Forecast"] == "Naive baseline", "RMSE (annualised vol points)"].iloc[0])

# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

st.subheader("How the forecasts score")
st.write(f"Scored on {len(frame):,} days from {frame.index[0]:%b %Y} to {frame.index[-1]:%b %Y}, none of which "
         f"GARCH was fitted on. RMSE is the typical gap between forecast and outcome, in annualised "
         f"volatility points: **lower is better**. A positive bias means the forecast runs too high on average.")
st.table(scores.assign(**{
    "RMSE (annualised vol points)": scores["RMSE (annualised vol points)"].map("{:.2f}".format),
    "Mean error (bias)": scores["Mean error (bias)"].map("{:+.2f}".format),
}).set_index("Forecast"))

if best == "Naive baseline":
    st.warning(f"**The naive baseline wins on this data.** Neither EWMA nor GARCH beats simply assuming next "
               f"month looks like last month, for {ticker} over this period. That is a real result, not a bug: "
               "volatility is strongly persistent, which makes the baseline hard to beat.")
else:
    margin = baseline_rmse - float(scores["RMSE (annualised vol points)"].min())
    st.success(f"**{best} scores best**, beating the naive baseline by {margin:.2f} annualised volatility points "
               f"({100 * margin / baseline_rmse:.0f}% lower RMSE).")

# ---------------------------------------------------------------------------
# The same question across the market. The scoreboard above is one stock on one split;
# this is the walk-forward backtest from backtest_volatility.py over many stocks.
# ---------------------------------------------------------------------------

import json
from pathlib import Path

_backtest_file = Path(__file__).resolve().parent.parent / "backtest_results.json"
if _backtest_file.is_file():
    bt = json.loads(_backtest_file.read_text())
    full = bt["aggregate"]["full_history"]
    st.subheader("Is one stock a fluke? The same test across the market")
    st.write(f"Ten years of history for **{bt['tickers_scored']} Indian stocks and indices**, refitting the model "
             f"every quarter so each forecast only uses data from before it. A loss below 1.00 beats the naive "
             f"baseline.")
    rows = [{"Forecast": "Naive baseline", "Loss vs naive": "1.00", "Beats naive on": "the benchmark",
             "Clearly better on": "the benchmark"}]
    for key, label in (("ewma", "EWMA"), ("garch", "GARCH(1,1)"), ("long_run", "Long-run average")):
        s = full[key]
        rows.append({"Forecast": label, "Loss vs naive": f"{s['median_qlike_ratio_vs_naive']:.2f}",
                     "Beats naive on": f"{s['share_beating_naive'] * 100:.0f}% of stocks",
                     "Clearly better on": f"{(s['share_significantly_better'] or 0) * 100:.0f}% of stocks"})
    st.table(pd.DataFrame(rows).set_index("Forecast"))
    st.caption(f"Median across the {full['tickers']} stocks with a full ten years. \"Clearly better\" is a "
               f"Diebold-Mariano test at 5%, corrected for the overlap between consecutive one-month windows. "
               f"Loss is QLIKE, the standard measure for volatility forecasts. GARCH has the lower average loss, "
               f"but EWMA is clearly better on more stocks: it is the steadier improvement.")

# ---------------------------------------------------------------------------
# Chart: forecasts against what actually happened
# ---------------------------------------------------------------------------

st.subheader("Forecast against outcome")
plot = frame.iloc[-750:] if len(frame) > 750 else frame
fig = go.Figure()
fig.add_trace(go.Scatter(x=plot.index, y=100 * annualise * plot["Actual"], name="What actually happened",
                         line=dict(color=INK_SECONDARY, width=2), hovertemplate="%{y:.1f}%"))
for name in forecasts:
    fig.add_trace(go.Scatter(x=plot.index, y=100 * annualise * plot[name], name=name,
                             line=dict(color=FORECAST_COLORS[name], width=2,
                                       dash="dash" if name == "Naive baseline" else "solid"),
                             hovertemplate="%{y:.1f}%"))
utils.style_figure(fig, "", "Annualised volatility (%)", height=440)
st.plotly_chart(fig, theme=None, width="stretch")
st.caption("Each line is plotted on the day the forecast was made, against the volatility actually realised over "
           "the following month. The grey line is the outcome, so a good forecast tracks it closely.")
with st.expander("Show the scored data as a table"):
    st.dataframe((100 * annualise * frame).round(2), width="stretch")

# ---------------------------------------------------------------------------
# GARCH's long-run variance vs Heston's theta
# ---------------------------------------------------------------------------

if garch_info:
    st.subheader("GARCH's long-run volatility, and Heston's theta")
    long_run_vol = float(np.sqrt(garch_info["long_run_var_daily"] * TRADING_DAYS))
    persistence = garch_info["alpha"] + garch_info["beta"]
    st.write("GARCH and Heston both say volatility is pulled back toward a long-run level. GARCH calls that level "
             "omega / (1 - alpha - beta); Heston calls it theta. **They are estimates of the same quantity**, "
             "reached from different data: GARCH from this stock's past returns, Heston from today's option prices.")

    fit = st.session_state.get("heston_fit")
    has_heston = bool(fit and fit.get("converged") and fit.get("ticker") == ticker)
    columns = st.columns(3 if has_heston else 2)
    columns[0].metric("GARCH long-run volatility", f"{100 * long_run_vol:.1f}%",
                      help="sqrt(omega / (1 - alpha - beta)), annualised.")
    columns[1].metric("Persistence (alpha + beta)", f"{persistence:.3f}",
                      help="How slowly a volatility shock fades. Close to 1 means shocks last a long time.")
    if has_heston:
        heston_theta_vol = float(np.sqrt(fit["params"][2]))
        columns[2].metric("Heston theta (as volatility)", f"{100 * heston_theta_vol:.1f}%",
                          help="sqrt(theta) from the calibration on the Pricing page.")
        gap = 100 * (heston_theta_vol - long_run_vol)
        st.caption(f"The option market's long-run level is {abs(gap):.1f} volatility points "
                   f"{'higher' if gap > 0 else 'lower'} than the one estimated from past returns. "
                   "A positive gap is the usual finding: option buyers tend to pay for protection, which lifts "
                   "prices above what past returns alone would justify. One comparison on one day is an "
                   "observation, not evidence of that effect.")
    else:
        st.caption("Calibrate Heston on the Pricing page to compare its theta against this number.")
    st.caption(f"Fitted GARCH parameters: omega = {garch_info['omega']:.2e}, alpha = {garch_info['alpha']:.3f}, "
               f"beta = {garch_info['beta']:.3f} (daily, from the first {n_train:,} days)."
               + ("" if garch_info["converged"] else " The optimiser did not report convergence, so treat these with caution."))

# ---------------------------------------------------------------------------
# Hand a forecast to the Pricing page
# ---------------------------------------------------------------------------

st.subheader("Use a forecast to price options")
st.write("Pick a forecast to send to the Pricing page, where it can replace the 30-day historical volatility "
         "in Black-Scholes and GBM.")
choice = st.radio("Forecast to use", list(forecasts), index=list(forecasts).index(best), horizontal=True,
                  help="The best-scoring forecast is selected by default.")
latest = float(pd.Series(forecasts[choice]).dropna().iloc[-1]) * annualise
st.session_state["sigma_forecast"] = latest
st.session_state["sigma_forecast_meta"] = {"ticker": ticker, "model": choice}
st.metric(f"{choice} forecast for the next month", f"{100 * latest:.1f}%")
st.caption(f"Sent to the Pricing page for {ticker}. It appears there as a volatility option in the sidebar.")
