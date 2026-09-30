"""
streamlit_app.py -- entry point. Run with:  streamlit run streamlit_app.py

Five pages, one story: each pricing model relaxes an assumption the previous one made.
Home is the exhibition hook -- everything else is for a visitor who stops to dig in.
"""

import streamlit as st

st.set_page_config(page_title="Options: Black-Scholes to Heston", layout="wide")

# Exhibition scale: bumped up from default so numbers and headings read from a few feet away,
# where a visitor standing at a laptop actually is. Left as a CSS override rather than baked
# into every page, so it is one place to dial back down for normal desk use.
st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size: 2.4rem; }
  [data-testid="stMetricLabel"] { font-size: 1.05rem; }
  h1 { font-size: 2.6rem !important; }
  h4 { font-size: 1.3rem !important; }
  .stMarkdown p, .stMarkdown li { font-size: 1.05rem; }
</style>
""", unsafe_allow_html=True)

navigation = st.navigation([
    st.Page("views/0_home.py", title="Home", icon=":material/bolt:", default=True),
    st.Page("views/1_options.py", title="Options 101", icon=":material/school:"),
    st.Page("views/2_pricing.py", title="Pricing models", icon=":material/calculate:"),
    st.Page("views/3_forecast.py", title="Volatility forecast", icon=":material/show_chart:"),
    st.Page("views/4_assumptions.py", title="Assumptions", icon=":material/rule:"),
    st.Page("views/5_double_heston.py", title="Double Heston", icon=":material/trending_up:"),
    st.Page("views/6_market.py", title="Whole market", icon=":material/candlestick_chart:"),
])
navigation.run()
