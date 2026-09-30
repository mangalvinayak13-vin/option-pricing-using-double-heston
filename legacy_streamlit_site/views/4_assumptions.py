"""
Page 4 -- Assumptions and limitations.

Black-Scholes is built on a list of assumptions, every one of which is false in some way.
This page states each one, what goes wrong, and which model in this app (if any) does
something about it.
"""

import streamlit as st

st.title("Assumptions and limitations")
st.write("Every model here is built on assumptions about how stocks behave. Knowing which assumption you are "
         "leaning on, and how it fails, matters more than the price the model prints.")

st.subheader("The Black-Scholes assumptions")
st.markdown("""
| Assumption | What actually happens | What this app does about it |
|---|---|---|
| **Volatility is constant** | Volatility moves constantly: it clusters, spikes in crashes, and settles in calm periods. This is why real option prices imply a different volatility at every strike, the "smile" or "skew" on the Pricing page. | **Heston** makes variance a random, mean-reverting process, which produces a smile. **Double Heston** adds a second factor so fast and slow movements can coexist. The Forecast page models the same thing from returns with EWMA and GARCH. |
| **Returns are lognormal** | Real returns have fat tails: crashes far larger than a bell curve allows happen far more often than it predicts. | Partly. Heston's random volatility produces fatter tails than Black-Scholes, and negative rho makes big drops more likely than big rises. Neither model includes sudden jumps, so the very largest one-day moves are still underestimated. |
| **European exercise** (only at expiry) | Some listed options are American and can be exercised early, which can make them worth more. | Nothing needed here. NIFTY and BANKNIFTY index options are themselves European, so this assumption holds exactly for the chains this app prices. NSE single-stock options are European too. |
| **No dividends** | Shares pay dividends, and the price drops when they do, which lowers calls and lifts puts. | Partly. Every pricing function takes a dividend yield `q`, but the app leaves it at zero. Prices here use dividend-adjusted history, which is not the same correction. |
| **No transaction costs, and you can trade continuously** | Every trade crosses a bid/ask spread, and you cannot rebalance a hedge continuously. | Nothing. All prices here are mid-market and frictionless. Real trading costs would eat into any gap a model appears to find. |
| **One constant interest rate** | Rates differ by maturity and move over time. | Nothing. The app uses one fixed rate for every maturity. For options of a few months this matters far less than volatility does. |
""")

st.subheader("Limitations of this app in particular")
st.markdown("""
- **The option data is free, and it shows.** Strikes far from the money often have no bid or ask at all,
  especially outside market hours, so those quotes fall back to the last traded price, which can be hours or
  days stale. The Pricing page reports how many of its points come from each source.
- **Only today's chain is available.** There is no history of option prices here, so no model can be tested
  against how it would have priced options in the past. The forecasting page can be tested out of sample,
  because stock returns do have history; the pricing models cannot.
- **A calibration fits one moment.** The Pricing page fits Heston to a few expiries on one day. Parameters
  refitted tomorrow will differ. A parameter reported as sitting on the edge of its range is a sign the data
  could not pin it down at all.
- **Monte Carlo prices carry sampling error.** The quoted standard error says how much the price would wobble
  if you changed the random seed. Differences smaller than about two standard errors are noise.
- **Double Heston is shown for comparison, not fitted.** Ten parameters cannot be identified from a single
  day's option chain, so its sliders are illustrative. This is not a hunch — the **Double Heston** page
  measures it, and the **Whole market** page shows it happening on every NSE stock with listed options.
""")

st.caption("This is a modelling exercise built for a physics project, not trading advice. Nothing here is a "
           "recommendation to buy or sell anything, and none of the prices should be relied on for real trading.")
