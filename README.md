# Option Pricing Using Double Heston

A B.Tech physics capstone project asking a single question: given a real option
price surface, can you actually recover the ten parameters of a Double Heston
stochastic-volatility model that fits it? The answer, proven two independent
ways, is no.

## The core finding

**A good price fit does not mean the underlying parameters were recovered.**

- **On synthetic data**, where the true parameters are known because this
  project's own pricing engine generated the surfaces: a classical least-squares
  optimizer, given every advantage (exact target prices, many multi-starts), fits
  prices to machine precision (median RMSE 9.16e-08) and still recovers
  parameters at a median **skill of 1.80**, where 1.0 means doing no better than
  guessing the population average and above 1.0 means doing worse than that.
- **On 2,400 real option surfaces** — 40 of the most liquid NSE-listed stocks,
  63 separately audited trading dates, 16 optimizer starts per surface — 99%
  produce more than one price-equivalent solution, and the median pairwise
  dispersion among those solutions is **4.636x** the training distribution's own
  parameter spread. Price-equivalent fits to the same real surface routinely
  land further apart than two completely unrelated stocks' parameters would.

Neither finding depends on the other. The real-market result needs no assumed
ground truth at all — it's established directly from what NSE actually printed.

Trained neural networks that attempt the same inverse mapping score a mean skill
of about 0.80 (worse than perfect, but *better* than the classical optimizer's
1.80) — because a network trained across many surfaces regresses toward the
population average, and when a surface doesn't determine its parameters, that
average is closer to the truth than an arbitrary price-equivalent solution the
optimizer might land on. See `outputs/consolidated_results.json` and the
**Double Heston** page of the archived site (`legacy_streamlit_site/`) for the
full numbers.

## Repository layout

- `src/double_heston.py` — the canonical Double Heston pricing engine
  (characteristic function + Gauss-Laguerre integration).
- `mentor_dh_pinn/params_v2.py` — the canonical latent parameterization: a
  bijection between R^10 and the ten physical parameters that makes every
  decoded vector structurally valid by construction.
- `run_*.py` (repo root) — the real-market evaluation scripts: dev-date and G8
  held-out floor fits, the market-wide 210-stock/60-date calibration, the
  option-repricing backtest, and the 40-stock/63-date parameter-ambiguity study.
- `check_*.py` (repo root) — diagnostic scripts, kept deliberately rather than
  deleted, since each one documents how a real bug was found and verified fixed.
- `outputs/` — every experiment's results. `outputs/ambiguity/`,
  `outputs/g8/`, `outputs/market_wide/`, and `outputs/option_backtest/` hold the
  current, verified-correct real-market results; a handful of `*_backup` and
  `*_smoke` subdirectories are deliberately-kept scratch output from debugging,
  not part of any reported result.
- `legacy_streamlit_site/` — the source of the project's exhibition website
  (a live Black-Scholes/Heston/Double Heston pricing calculator, calibrated
  against real NSE/Upstox option chains), archived here as reference for a
  planned rewrite. See its own README for what is and isn't included.
- `video_report/` — a report written for Google NotebookLM's Video Overview
  feature, explaining the project to a non-finance audience, with figures
  generated directly from this project's own code.
- `docs/` — the research log from earlier phases of this project. Written
  incrementally over months of work; treat any specific number in it as
  possibly superseded by `outputs/consolidated_results.json` unless you've
  checked the two agree.

## Three bugs found and fixed in the real-market pipeline

Documented in detail in `check_corner_bug.py`, `check_corner_bug2.py`, and the
commit history, but summarized here since they materially changed every
real-market number this project reports:

1. **A flat latent-coordinate box didn't bound composite parameters** like
   `kappa_fast`, which is a product of two coordinates — real, partial option
   surfaces have flat-enough directions that an optimizer actually ran to the
   box edge. Fixed with a physical-parameter penalty (`src/plausible_bounds.py`)
   derived from the training set's own parameter range, replacing the flat box.
2. **Real-market "floor" fits lacked a guaranteed flat-Black-Scholes-corner
   start.** Double Heston nests Black-Scholes exactly, so a genuine optimum can
   never lose to a single fitted flat volatility on the same quotes — but random
   starts near the origin could simply miss that corner, and did.
3. **Every real-market repricing function indexed interest rate and carry by
   `rates[rank - 1]`**, which is correct by coincidence for the first (nearer)
   expiry and wrong for the second — every longer-dated option leg in the whole
   real-market pipeline was priced with the *shorter* expiry's rate and carry.
   Fixed with `src/rank_conditioning.py`, which looks up the correct slot from
   the canonical representation itself rather than assuming an index formula.

Every real-market result in `outputs/` postdates all three fixes, verified by
timestamp and, where a script bundled training with evaluation, by re-running
just the affected evaluation step against the existing trained weights.

## Reproducing the headline results

```bash
python3 run_real_classical_fit.py      # 5 dev-date floor vs flat Black-Scholes
python3 run_g8_eval.py                 # 8 held-out G8 dates, network + floor
python3 run_market_wide.py             # 210 stocks x 60 dates
python3 run_option_backtest.py         # does yesterday's fit still price today?
python3 run_market_ambiguity.py        # the 2,400-surface ambiguity study (~15 hours)
python3 consolidate_results.py         # gathers everything into one JSON
```

Each script's own docstring explains what it measures and why. `annotate_front_dte.py`
must be re-run after any fresh `run_market_wide.py` run, before anything downstream
reads its output — it tags each surface with whether its nearest expiry falls inside
the training window, which several later scripts and the exhibition site both rely on.
