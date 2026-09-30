# Legacy Streamlit site (archived reference)

This is the source code of the original Streamlit exhibition site, kept here as
reference for the Vercel rewrite. The site itself (and its GitHub repo,
`stock-price-modeling`) has been retired -- everything it needs going forward
lives in this one repo instead.

It implements a live pricing calculator (`models.py`): Black-Scholes, GBM/Heston/
Double Heston Monte Carlo, semi-analytic Heston/Double Heston pricing via
characteristic-function inversion, Greeks, and live single-Heston calibration to
real NSE/Upstox option chains. `views/` holds the seven Streamlit pages;
`snapshot.py` is the frozen-market-data fallback used when the live feed fails;
`backtest_volatility.py` is a standalone 60-stock, 10-year GARCH backtest.

Not copied here: `double_heston_results/*` and the `.pt` model checkpoints the
site displayed -- those were only ever copies of files already in this repo's own
`outputs/` directory, so nothing was lost by leaving them out. The `report/`
folder (an older, superseded Word-doc report generator) was also left behind
deliberately.

This code is not expected to run as-is from here (it assumes the site's own
directory layout and a `.env` with API keys) -- it's a reference for the rewrite,
not a working app.
