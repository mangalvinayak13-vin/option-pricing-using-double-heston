# Double Heston page — deployment and results

**Last updated:** 29 September 2026

Covers the Double Heston page in the Streamlit app, the experiments behind it, and
what the results do and do not support. Read "What this establishes" before
presenting any of it.

---

## Running it

```bash
cd "~/Everything related to my projects/Physics project SEM 1"
./venv/bin/streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. Use the project's `venv/` — system `python3` has no
Streamlit. Verified working in a browser: all six pages load and the Double Heston page
renders every section.

If the port is busy, pass `--server.port 8532`. Note that a busy port makes Streamlit
exit with "Port ... is not available" while *another* server may still answer there, so
a 200 from `curl` does not prove your app is up.

---

## Headline result

**The 20-quote option surface does not determine the ten Double Heston parameters.**

Skill = RMSE ÷ that parameter's spread in the test set. 0.0 is perfect recovery, 1.0 is
no better than ignoring the prices and predicting the average, above 1.0 is worse than
that. This matches the project's existing `standardized_parameter_rmse` convention.

| Model | Mean skill | Structural validity |
|---|---|---|
| Model 1 — direct | 0.796 | 99.9% |
| Model 2 — canonical latent bijection | 0.801 | **100.0%** |

Four independent lines of evidence agree:

1. **Four training setups, five seeds each**, all land at 0.80 ± 0.02.
2. **The project's own canonical latent bijection gives no improvement**, which rules out
   parameterization as the explanation.
3. **A classical optimizer is far worse at recovery** despite fitting prices to machine
   precision (see below).
4. **The existing G2 diagnostic** reached a median price RMSE of `4.708e-08` and still
   landed in 39 separated parameter clusters.

---

## Classical calibration — the decisive experiment

60 test surfaces, 4 bounded multi-starts each, identical pricer and identical latent
coordinates to the networks. The optimizer is given a deliberate advantage: it sees the
exact surface it is fitting and may iterate freely, where a network gets one forward pass.

| Measure | Value | Reading |
|---|---|---|
| Median price RMSE | `9.16e-08` | machine precision |
| Price-equivalent fits | 82% | below the G2 threshold `2.5e-07` |
| Median parameter skill | **1.80** | worse than guessing the mean |
| …restricted to price-equivalent fits (n=49) | **1.85** | restriction does not rescue it |

The optimizer matches the surface to eight decimal places and lands **further from the
truth than a constant predictor**. Parameter vectors exist that reproduce the surface
almost exactly while being badly wrong, and least squares finds one of them essentially
at random.

**The ordering across methods is the interesting part.** The networks score ~0.80 and this
optimizer 1.80 — the networks recover parameters *better* precisely because they fit
prices *worse*. Training across 10,000 surfaces pulls a network toward the population
average, and when the surface does not identify the parameters, that average is closer to
the truth than an arbitrary price-equivalent solution. Fitting prices better is actively
harmful to recovery here.

---

## The repricing sweep

Model 2 completed as specified — constraints **and** a differentiable repricing term via
the Torch mirror, puts by put-call parity.

| Price weight in loss | Mean skill | Test price RMSE |
|---|---|---|
| 0.0 — parameters only | 0.7932 | 7.93e-04 |
| 0.5 — balanced | 0.7926 | 6.48e-04 |
| 0.9 — mostly repricing | 0.7924 | **4.13e-04** |

Price fit improves **48%**; recovery moves 0.0008, against a seed-to-seed spread of 0.003.
The physics-informed loss buys price accuracy and delivers no recovery, because the extra
gradient lands entirely in directions the surface already constrained.

---

## Multi-seed: the model gap is real

Five seeds per model. The ranges do not overlap.

| Model | Mean skill | SD |
|---|---|---|
| Model 1 — direct | 0.7926 | 0.0028 |
| Model 2 — canonical latent | 0.8018 | 0.0020 |

Welch t = −6.01, **p = 0.00046**.

The canonical constraint parameterization costs about 0.009 mean skill and buys 100%
structural validity against 99.9%. That is a real, quantified trade-off — not a wash.
An earlier version of this document called the gap noise; that was wrong.

---

## Noise robustness

Models held fixed; multiplicative noise applied to test prices.

| Noise | 0% | 0.5% | 1% | 2% | 5% |
|---|---|---|---|---|---|
| Model 1 | 0.796 | 0.805 | 0.832 | 0.908 | **1.239** |
| Model 2 | 0.801 | 0.811 | 0.835 | 0.917 | **1.319** |

Past about 2% there is no usable recovery. At 5% skill **exceeds 1.0** — the models do
worse than ignoring the prices, because the noise actively misleads them.

This matters because NSE bhavcopy carries close prices with no bid-ask, so the effective
quote noise on real data sits in exactly this range. It is also the strong form of the
project's own position: strict-precision identification can be good while
market-tolerance identification is not available.

---

## Real NSE market data

Official NSE UDiFF bhavcopies for the five frozen NTPC dates, downloaded by
`src/nse_bhavcopy_fetch.py`. All five are R2-constructible.

**Why not Upstox.** Upstox's REST API serves live and recent quotes, not dated historical
option chains, so the original plan could not work through it. NSE publishes the same
UDiFF CSVs the sealed Stage A contract already parses, so the fetcher writes those
directly into the layout `frozen.MARKET_RAW_ROOTS` expects. Nothing new parses the data.

**Mask-aware models were required.** Real surfaces populate 11–19 of the 20 nominal slots
and the R2 contract forbids filling a missing quote with a model price. The 24-input
models structurally could not consume one. R2 specifies explicit mask semantics, so the
network now takes 20 prices + 20 mask flags + 4 conditioning = 44 inputs. That is not
imputation; it tells the network which slots exist.

Repricing error as a percentage of mean observed price, at each slot's **actual traded
strike**:

| Date | Slots | Network | Best possible DH fit | Gap |
|---|---|---|---|---|
| 2026-07-01 | 11/20 | 15.8% | 4.8% | +11.0pp |
| 2026-07-08 | 18/20 | 17.5% | 11.5% | +6.0pp |
| 2026-07-15 | 19/20 | 9.3% | 4.8% | +4.5pp |
| 2026-07-22 | 18/20 | 12.1% | 2.0% | +10.0pp |
| 2026-07-29 | 12/20 | 13.6% | 1.4% | +12.1pp |

"Best possible fit" is a 12-start least-squares fit to that same surface — the floor any
method could reach.

**"Transfer quality tracks slot coverage" did not replicate.** With the corrected
rate/carry conditioning (see below), the 18–19-slot dates now show gaps of 4.5–10.0
points, not the tight 1.8–5.6 range this table originally suggested, and the later
G8 held-out evaluation confirms there is no such relationship (Spearman rho = 0.000,
p = 1.00) — the earlier pattern was an artefact of reading five points. Double
Heston fits these real surfaces to 1.4–11.5%, so the model class is workable on
NTPC; the remaining error is synthetic-to-real transfer, not model inadequacy.

**Only repricing is measurable on real data.** NTPC's true parameters are unknown, so
parameter recovery is undefined there. Given the central finding, a good repricing number
must not be read as successful calibration.

---

## Two corrections made during this work

Both changed conclusions, and both are worth stating in a write-up.

**Missing conditioning.** An initial run fed the network only the 20 prices. Maturity,
rate and carry vary across surfaces (56, 6 and 18 distinct values), so omitting them left
the inverse map ambiguous *by input construction*, independent of any physics. Fixing it
moved mean skill from about 0.90 to 0.80. Part of the original poor result was a setup
defect, not the problem being hard.

**Repricing at the wrong strikes.** Real-market repricing first priced at nominal
moneyness targets while comparing against quotes struck up to 0.04 away in log-moneyness.
That charged the mismatch to the model and inflated the error roughly threefold: the
best-possible Double Heston fit read 16–35% of mean price, when at actual traded strikes
it is 1.4–11.5%. Uncorrected, this would have supported a false claim that Double Heston
cannot fit NTPC's smile.

---

## What this establishes, and what it does not

**Established**
- Recovery is not available from this surface under any setup tried.
- The canonical bijection buys structural validity, not recovery.
- Recovery collapses entirely past 2% quote noise.
- Double Heston can fit real NTPC surfaces; the network gets close to that floor when
  slot coverage is good.

**Not established**
- No hyperparameter sweep was run, so "no architecture does better" is not proven — only
  that several reasonable ones do not.
- Real-market evaluation used the five frozen development dates. The G8 protocol reserves
  separate untouched dates; those remain unused.
- Free bhavcopy has no bid-ask or quote sizes, which limits what can be claimed about
  real quote quality.

---

## File layout

```
Physics project SEM 1/
├── streamlit_app.py                      # nav includes the Double Heston page
├── double_heston_results/
│   └── consolidated_results.json         # everything the page reads
└── views/5_double_heston.py              # the page
```

The page reads `double_heston_results/` inside this project, not the training worktree,
which is temporary.

---

## Regenerating

On branch `worktree-complete-training` in the double-heston repo:

```bash
python3 run_latent_training.py --model 1 --epochs 300 --output-dir outputs/run_v4
python3 run_latent_training.py --model 2 --epochs 300 --output-dir outputs/run_v4
./run_multiseed.sh                        # 5 seeds x 2 models
python3 run_noise_robustness.py
python3 -m src.nse_bhavcopy_fetch         # downloads ~37MB from NSE
python3 run_real_market_eval.py --model 2 --epochs 300
python3 run_real_classical_fit.py
python3 run_classical_baseline.py --surfaces 150 --starts 4
python3 run_repricing_model.py --price-weight 0.5 --epochs 60
python3 consolidate_results.py            # writes consolidated_results.json
```

Then copy `outputs/consolidated_results.json` into `double_heston_results/` here.

Two gotchas:
- `run_latent_training.py` skips training when a checkpoint already exists in the output
  directory and only re-evaluates. Use a fresh `--output-dir` to actually retrain.
- Restart Streamlit after replacing a Python module — Python caches imports, so a running
  server keeps serving old code.

---

## Suggested next steps

1. Hyperparameter sweep, to close the last "maybe a better architecture" objection.
2. G8 frozen evaluation on the reserved untouched dates.
3. Extend the bhavcopy fetch beyond five dates — the fetcher generalizes, but the sealed
   contract only admits the five frozen date ids, so `frozen.py` gates it deliberately.
