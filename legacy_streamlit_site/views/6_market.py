"""
Market-wide view — the exhibition page.

A visitor picks a stock they recognise and sees what a two-factor stochastic
volatility model makes of it. The point it lands, without needing the research
page, is the contrast between two panels: the fit is good on every date, and the
parameters behind that fit jump around anyway.
"""

from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

PROJECT = Path(__file__).parent.parent
DATA = PROJECT / "double_heston_results" / "market_wide_surfaces.csv"
SUMMARY = PROJECT / "double_heston_results" / "market_wide_summary.json"

# Validated categorical slots 1 and 2 (see dataviz reference palette); the two
# dark steps are the same hues restepped for a dark surface.
BLUE, ORANGE = "#2a78d6", "#eb6834"

PARAM_LABELS = {
    "p_kappa_s": "κ slow — mean reversion",
    "p_theta_s": "θ slow — long-run variance",
    "p_sigma_s": "σ slow — vol of vol",
    "p_rho_s": "ρ slow — correlation",
    "p_v0_s": "V₀ slow — initial variance",
    "p_kappa_f": "κ fast — mean reversion",
    "p_theta_f": "θ fast — long-run variance",
    "p_sigma_f": "σ fast — vol of vol",
    "p_rho_f": "ρ fast — correlation",
    "p_v0_f": "V₀ fast — initial variance",
}

st.title("The Indian options market, one stock at a time")

if not DATA.exists():
    st.info(
        "Market-wide results have not been generated yet. Run "
        "`python3 run_market_wide.py` in the double-heston repo and copy "
        "`outputs/market_wide/` into `double_heston_results/`.",
        icon="⏳",
    )
    st.stop()

raw = pd.read_csv(DATA)

# The model is trained on 7-90 day maturities. Near a monthly expiry the nearest
# listed expiry is far shorter than that, so those surfaces are outside the training
# support and reprice about twice as badly. Showing them inside the headline figure
# would blame the market for the model meeting an input it was never shown, so the
# default view is in-support and the rest is surfaced as its own result below.
has_support_flag = "in_training_support" in raw.columns
df = raw[raw["in_training_support"]].copy() if has_support_flag else raw.copy()

st.markdown("""
Every NSE stock with listed options, calibrated to a **Double Heston** model — two
independent sources of randomness in volatility, one slow and one fast. Pick a stock
below.
""")

# ---------------------------------------------------------------- market scale
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stocks covered", f"{df['ticker'].nunique()}")
c2.metric("Surfaces calibrated", f"{len(df):,}")
c3.metric("Median price error", f"{df['repricing_relative'].median() * 100:.1f}%")
c4.metric("Valid parameter sets", f"{df['parameters_valid'].mean() * 100:.0f}%")

st.caption(
    "Roughly 1,800 NSE listings have no options at all, so they cannot appear here — "
    "there is nothing to calibrate against. This is the whole set for which the "
    "question is askable."
)

if has_support_flag and (~raw["in_training_support"]).any():
    out = raw[~raw["in_training_support"]]
    with st.expander(
        f"Why {len(out):,} of {len(raw):,} surfaces are held back from these figures"
    ):
        st.markdown(f"""
The model is trained on options with **7 to 90 days** left to run. In the days before
a monthly expiry the nearest listed expiry is much shorter than that — one day on
2026-08-24 — and those surfaces fall outside what the model was ever shown.

| | Surfaces | Median price error |
|---|---|---|
| Within 7–90 days (shown above) | {len(df):,} | **{df['repricing_relative'].median() * 100:.1f}%** |
| Front expiry under 7 days | {len(out):,} | **{out['repricing_relative'].median() * 100:.1f}%** |

Twice the error, on {out['date_id'].nunique()} expiry-week dates. That is the model's
support boundary showing up in real market data, which is a result rather than a
defect — but it is not what the model does on the maturities it was built for, so it
is reported separately instead of averaged in.
""")

st.divider()

# ---------------------------------------------------------------- stock picker
tickers = sorted(df["ticker"].unique())
default = "NTPC" if "NTPC" in tickers else tickers[0]
ticker = st.selectbox("Pick a stock", tickers, index=tickers.index(default))

sub = df[df["ticker"] == ticker].sort_values("date_id").reset_index(drop=True)

if sub.empty:
    st.warning("No calibrated surfaces for this stock.")
    st.stop()

by_stock = df.groupby("ticker")["repricing_relative"].median()
here_med = float(sub["repricing_relative"].median())
percentile = float((by_stock > here_med).mean() * 100)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Latest spot", f"₹{sub['spot'].iloc[-1]:,.2f}")
m2.metric("Dates calibrated", f"{len(sub)}")
m3.metric("Median price error", f"{here_med * 100:.1f}%")
# A percentile reads at a glance and, unlike "better/worse than median", does not
# get clipped by the metric component at exhibition font sizes.
m4.metric("Fits better than", f"{percentile:.0f}% of stocks", delta_color="off")

st.divider()

# ---------------------------------------------------------------- the two panels
st.subheader(f"The fit is good. The parameters are not.")

left, right = st.columns(2)

with left:
    st.markdown("**How well the model matches observed prices**")
    fit = sub[["date_id", "repricing_relative"]].copy()
    fit["Price error"] = fit["repricing_relative"] * 100

    chart = (
        alt.Chart(fit)
        .mark_line(point=alt.OverlayMarkDef(size=90, filled=True), strokeWidth=2,
                   color=BLUE)
        .encode(
            x=alt.X("date_id:O", title=None,
                    axis=alt.Axis(labelAngle=-45, grid=False)),
            y=alt.Y("Price error:Q", title="price error (% of mean price)",
                    scale=alt.Scale(zero=True)),
            tooltip=[alt.Tooltip("date_id:O", title="Date"),
                     alt.Tooltip("Price error:Q", format=".1f", title="Error %")],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)
    lo_q, hi_q = (sub["repricing_relative"].quantile([0.1, 0.9]) * 100)
    st.caption(
        f"Median {here_med * 100:.0f}%, with most dates between {lo_q:.0f}% and "
        f"{hi_q:.0f}%. The model reproduces this stock's option prices to roughly the "
        f"same accuracy each date."
    )

with right:
    st.markdown("**The parameters that produced those fits**")
    present = [c for c in PARAM_LABELS if c in sub.columns]
    tidy = sub.melt(id_vars="date_id", value_vars=present,
                    var_name="param", value_name="value")
    # Each parameter lives on its own scale, so standardise within parameter —
    # otherwise kappa_fast (spread ~1.6) would flatten theta_fast (spread ~0.03)
    # into a straight line and hide exactly the movement worth showing.
    tidy["z"] = tidy.groupby("param")["value"].transform(
        lambda s: (s - s.mean()) / (s.std() if s.std() > 0 else 1.0))
    tidy["Parameter"] = tidy["param"].map(PARAM_LABELS)

    jitter = (
        alt.Chart(tidy)
        .mark_line(strokeWidth=1.6, opacity=0.75, color=ORANGE)
        .encode(
            x=alt.X("date_id:O", title=None,
                    axis=alt.Axis(labelAngle=-45, grid=False)),
            y=alt.Y("z:Q", title="parameter, standardised"),
            detail="Parameter:N",
            tooltip=[alt.Tooltip("Parameter:N"), alt.Tooltip("date_id:O", title="Date"),
                     alt.Tooltip("value:Q", format=".4f", title="Value")],
        )
        .properties(height=260)
    )
    st.altair_chart(jitter, use_container_width=True)
    st.caption(
        "Ten lines, one per parameter, each standardised so they share an axis. "
        "They move — often a lot — between dates where the fit barely changed."
    )

st.info(
    "**That contrast is the project's finding.** Many different parameter sets "
    "reproduce the same option prices almost exactly, so fitting the prices well "
    "does not pin down the parameters. Hover either chart to read the numbers.",
    icon="🔍",
)

# ---------------------------------------------------------------- the numbers
with st.expander(f"{ticker} — fitted parameters by date"):
    show = sub[["date_id", "spot", "usable_slots", "repricing_relative"] +
               [c for c in PARAM_LABELS if c in sub.columns]].copy()
    show["repricing_relative"] = (show["repricing_relative"] * 100).round(1)
    show = show.rename(columns={
        "date_id": "Date", "spot": "Spot", "usable_slots": "Quotes used",
        "repricing_relative": "Price error %", **PARAM_LABELS})
    st.dataframe(show, use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------- market context
st.subheader("Where this stock sits in the market")

hist_src = df.groupby("ticker")["repricing_relative"].median().reset_index()
hist_src["Price error"] = hist_src["repricing_relative"] * 100
here = float(sub["repricing_relative"].median() * 100)

bars = (
    alt.Chart(hist_src)
    .mark_bar(color=BLUE, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("Price error:Q", bin=alt.Bin(maxbins=34),
                title="median price error per stock (%)"),
        y=alt.Y("count():Q", title="number of stocks"),
        tooltip=[alt.Tooltip("count():Q", title="Stocks")],
    )
    .properties(height=280)
)
marker = (
    alt.Chart(pd.DataFrame({"x": [here], "label": [ticker]}))
    .mark_rule(color=ORANGE, strokeWidth=3)
    .encode(x="x:Q", tooltip=[alt.Tooltip("label:N", title="Stock"),
                              alt.Tooltip("x:Q", format=".1f", title="Error %")])
)
text = (
    alt.Chart(pd.DataFrame({"x": [here], "label": [f"{ticker} — {here:.1f}%"]}))
    .mark_text(align="left", dx=7, dy=-118, fontSize=13, fontWeight=600, color=ORANGE)
    .encode(x="x:Q", text="label:N")
)
st.altair_chart(bars + marker + text, use_container_width=True)

rank = int((hist_src["Price error"] < here).sum()) + 1
st.caption(
    f"**{ticker}** is the {rank}ᵗʰ best-fitting of "
    f"{len(hist_src)} stocks. Stocks further right are ones this model struggles "
    f"with more — typically thinner option books, where a closing price is a weaker "
    f"signal of what anything actually trades at."
)

with st.expander("Every stock, ranked by fit"):
    table = hist_src.sort_values("Price error").reset_index(drop=True)
    table.index += 1
    table["Median price error"] = table["Price error"].round(1).astype(str) + "%"
    st.dataframe(table[["ticker", "Median price error"]]
                 .rename(columns={"ticker": "Stock"}),
                 use_container_width=True)

st.caption(
    "Calibrated on official NSE bhavcopy closing prices. Free bhavcopy carries no "
    "bid/ask, so part of the error above is the gap between a closing print and a "
    "tradeable level, not model error. Nothing here is investment advice."
)
