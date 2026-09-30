# Options pricing: Black-Scholes to Heston

A four-page Streamlit app built around one idea: **each pricing model relaxes an assumption
the previous one made.**

| Model | The assumption it drops |
|---|---|
| **Black-Scholes** | — (the baseline: volatility is one fixed number) |
| **GBM Monte Carlo** | nothing. Same model, priced by simulation instead of a formula, to check the simulation engine against an exact answer. |
| **Heston** | volatility is constant. Variance becomes a random, mean-reverting process correlated with the stock price. |
| **Double Heston** | volatility has a single speed. Two independent variance factors, one fast and one slow. |

The centrepiece is the **implied volatility vs strike** chart on the Pricing page. Black-Scholes
and GBM are flat there by construction; Heston bends into a skew; real market quotes are plotted
alongside. That one picture is the argument of the whole project.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run streamlit_app.py    # the app
python3 tests/test_models.py      # the tests (also runs under pytest)
```

No API keys are needed. Price history and option chains come from Yahoo via `yfinance`.

## Layout

```
streamlit_app.py     entry point: st.navigation over the four pages
models.py            all pricing and volatility maths; no Streamlit imports, so it is testable alone
utils.py             data loading, caching, constants, shared chart styling
views/1_options.py   Options 101: vocabulary and an interactive payoff diagram
views/2_pricing.py   the main page: all four models, the smile chart, Greeks, calibration
views/3_forecast.py  volatility forecasting: EWMA and GARCH against a naive baseline
views/4_assumptions.py   what each model assumes, how it fails, and what the app does about it
tests/test_models.py correctness checks for everything in models.py
report/              the semester report, viva sheet, and the scripts that build them
```

## The report, and the `semester-report-v1` tag

`report/` holds the written report for the earlier phase of this project: a returns-based
GMM calibration of Heston and Double Heston, a 30-year walk-forward backtest, and a Kupiec
VaR coverage test. **The code behind those results is not on this branch.** It is preserved
under the annotated tag `semester-report-v1`:

```bash
git show semester-report-v1                       # what it contains and why
git worktree add /tmp/pipeline semester-report-v1 # to re-run it
```

The report has been reconciled with the restructure rather than rewritten: Sections 1–6 are
unchanged, §7 now states which codebase produced which result, and §8 reports the
option-chain calibration below. Rebuild both documents with:

```bash
python3 report/generate_option_calibration.py   # refresh §8's numbers against today's chain
python3 report/build_report.py
python3 report/build_viva_cheatsheet.py
```

`report/generate_figures.py` only runs at the tag, and says so.

### What §8 found

Fitting Heston's five parameters to 405 out-of-the-money SPY quotes across three expiries
gave an RMSE of **$0.298** against market prices, versus **$1.220** for the best single
constant volatility — about four times closer. That is the clearest evidence in the project
for stochastic volatility, and the returns-based calibration could never have measured it,
because it never sees an option price. It rests on one day of stale, one-sided quotes with
`kappa` pinned to its bound, and §8 says so.

This does not contradict the report's §3.2, which rejected options calibration because free
data has no *historical* chains — fatal to a multi-decade backtest, but no obstacle to
fitting a single live snapshot.

Page files live in `views/`, not `pages/`, deliberately: a directory named `pages/` switches on
Streamlit's automatic page discovery, which overrides `st.navigation` and breaks deep links.

## The two checks that matter

`tests/test_models.py` (22 tests) is anchored on two that validate the simulation engine against
exact answers:

- **GBM Monte Carlo converges to Black-Scholes.** At 50,000 antithetic paths the simulated price
  lands within two standard errors of the closed-form price (measured: 0.2-0.6 standard errors).
- **Heston with `xi = 0` reproduces Black-Scholes.** Setting vol-of-vol to zero with `v0 = theta`
  freezes the variance, so Heston must collapse to Black-Scholes. It does.

The rest cover put-call parity, implied-vol round trips, Greeks against finite differences,
Heston's formula against its own Monte Carlo, full truncation surviving a Feller violation, and
that no volatility forecaster can see future returns.

## Two numerical points worth knowing

**Why the integration range is chosen, not fixed.** Heston's semi-analytic price is an integral to
infinity, truncated in practice. Its characteristic function decays only exponentially, and the
decay rate falls with the total variance `v0*T`: for a short-dated option on a calm stock the
function is still around 1e-2 at `u = 300`. Truncating there leaves a tail large enough to swamp
the price of a far out-of-the-money option — which produced *negative* prices and drew pure
integration noise as if it were a volatility smile. The range is now chosen from the function's
measured decay, and prices are floored at their no-arbitrage bound.

**Why the integration grid is evenly spaced.** Gauss-Legendre nodes are marginally more accurate
per point, but `numpy.polynomial.legendre.leggauss` costs seconds to build at the node counts the
wider range needs (3.3 s at 3600 nodes), which made calibration take 40 seconds. An evenly spaced
midpoint rule agrees with it to about 1e-7 of a dollar and is free to construct. Calibration now
takes under 3 seconds.

## Data limitations

Yahoo's free option feed frequently reports `bid = ask = 0`, and always does outside market hours.
Quotes therefore fall back to the last traded price where one exists, and every affected chart
says how many of its points came from each source. There is no *historical* option data available,
so the pricing models cannot be backtested here — only the volatility forecasts, which are scored
out of sample against a naive baseline, can.

This is a modelling exercise, not trading advice.
