"""
Page 1 -- Options 101. The vocabulary the rest of the app uses, and nothing more.
The payoff diagram is the centrepiece: everything else on this page explains it.
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import utils
from utils import COLORS, INK_SECONDARY

# Profit and loss are shaded with the fixed good/critical status pair, never a series colour.
PROFIT_FILL, LOSS_FILL = "rgba(12, 163, 12, 0.18)", "rgba(208, 59, 59, 0.18)"

st.title("Options 101")
st.write("An option is a contract that gives you the **right, but not the obligation**, to buy or sell a stock "
         "at a fixed price on a fixed date. You pay for that right up front. The rest of this app is about "
         "working out what that right is worth.")

# ---------------------------------------------------------------------------
# The payoff diagram
# ---------------------------------------------------------------------------

st.subheader("What you get at expiry")

controls, _ = st.columns([2, 1])
with controls:
    kind = st.radio("Option type", ["call", "put"], horizontal=True,
                    help="A call is the right to buy. A put is the right to sell.")
    strike = st.slider("Strike price ($)", 60, 140, 100, step=1)
    premium = st.slider("Premium you pay ($)", 0.0, 25.0, 8.0, step=0.5)

spot_grid = np.linspace(50, 150, 401)
# Payoff at expiry: what the contract is worth on the last day. A call is worth whatever the
# stock is above the strike; a put whatever it is below. Never negative, because you can walk away.
payoff = np.maximum(spot_grid - strike, 0.0) if kind == "call" else np.maximum(strike - spot_grid, 0.0)
profit = payoff - premium                      # subtract what you paid to get the profit
breakeven = strike + premium if kind == "call" else strike - premium

fig = go.Figure()
fig.add_trace(go.Scatter(x=spot_grid, y=np.maximum(profit, 0), line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=spot_grid, y=np.zeros_like(spot_grid), line=dict(width=0), fill="tonexty",
                         fillcolor=PROFIT_FILL, name="Profit", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=spot_grid, y=np.minimum(profit, 0), line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=spot_grid, y=np.zeros_like(spot_grid), line=dict(width=0), fill="tonexty",
                         fillcolor=LOSS_FILL, name="Loss", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=spot_grid, y=profit, mode="lines", name="Your profit",
                         line=dict(color=COLORS["Heston"], width=3), hovertemplate="$%{y:.2f}"))
fig.add_hline(y=0, line=dict(color=INK_SECONDARY, width=1))
fig.add_vline(x=strike, line=dict(color=INK_SECONDARY, width=1, dash="dot"),
              annotation_text=f"Strike ${strike}", annotation_position="top left")
fig.add_vline(x=breakeven, line=dict(color=INK_SECONDARY, width=1, dash="dash"),
              annotation_text=f"Breakeven ${breakeven:.2f}", annotation_position="top right")
utils.style_figure(fig, "Stock price at expiry ($)", "Profit or loss ($)", height=430)
fig.update_layout(hovermode="x")
st.plotly_chart(fig, theme=None, width="stretch")

left, right = st.columns(2)
if kind == "call":
    left.markdown(f"**You profit if the stock finishes above \\${breakeven:.2f}.** The option itself pays off "
                  f"above \\${strike}, but you first need to earn back the \\${premium:.2f} you paid.")
else:
    left.markdown(f"**You profit if the stock finishes below \\${breakeven:.2f}.** The option itself pays off "
                  f"below \\${strike}, but you first need to earn back the \\${premium:.2f} you paid.")
right.markdown(f"**The most you can lose is the \\${premium:.2f} premium**, however far the stock moves the wrong "
               "way, because you can simply let the option expire. That one-sided shape is what makes options "
               "worth pricing carefully.")

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

st.subheader("The words this app uses")
st.markdown(f"""
| Term | What it means |
|---|---|
| **Call** | The right to **buy** the stock at the strike price. |
| **Put** | The right to **sell** the stock at the strike price. |
| **Strike** | The fixed price written into the contract (\\${strike} above). |
| **Expiry** | The date the contract ends. Time left is written as *T*, in years. |
| **Premium** | What the option costs today (\\${premium:.2f} above). This is what a pricing model predicts. |
| **Moneyness** | Where the stock sits relative to the strike. At the money means they are equal; out of the money means the option would pay nothing today. |
| **Implied volatility** | The volatility that makes a pricing formula agree with the option's market price. It is the market's opinion about future movement, read backwards out of the price. |
""")

st.info("**Why volatility is the whole story.** To price an option you need the stock price, the strike, the time "
        "left, the interest rate, and how much the stock is likely to move. You can look up the first four. The "
        "last one, volatility, has to be estimated or inferred, and that is what every model in this app is "
        "really arguing about.")
