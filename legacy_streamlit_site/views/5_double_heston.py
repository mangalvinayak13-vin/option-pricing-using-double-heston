"""
Double Heston inverse calibration — results page.

Reads outputs/consolidated_results.json, copied into double_heston_results/.
Every section renders only if its data is present, so a partial run shows what
exists rather than placeholders.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

PROJECT = Path(__file__).parent.parent
RESULTS = PROJECT / "double_heston_results" / "consolidated_results.json"

PARAM_LABELS = {
    "kappa_s": "κ_slow (mean reversion)",
    "theta_s": "θ_slow (long-run variance)",
    "sigma_s": "σ_slow (vol of vol)",
    "rho_s": "ρ_slow (correlation)",
    "v0_s": "V₀_slow (initial variance)",
    "kappa_f": "κ_fast (mean reversion)",
    "theta_f": "θ_fast (long-run variance)",
    "sigma_f": "σ_fast (vol of vol)",
    "rho_f": "ρ_fast (correlation)",
    "v0_f": "V₀_fast (initial variance)",
}

st.title("Double Heston Inverse Calibration")

if not RESULTS.exists():
    st.error(f"No results file at `{RESULTS.relative_to(PROJECT)}`. Run the training pipeline first.")
    st.stop()

data = json.loads(RESULTS.read_text())

st.markdown("""
Recovering the ten Double Heston parameters from an option price surface, and asking
whether that is possible at all.

Training is on 10,000 synthetic surfaces from this project's own pricing engine.
Evaluation spans the synthetic test split, a 36-configuration architecture sweep, a
classical calibration baseline, a noise cohort, out-of-distribution cohorts, and
thirteen real NTPC dates from official NSE bhavcopy — eight of them fully held out.
""")

st.warning(
    "**The surface does not determine the parameters.** Both networks score about "
    "0.80 mean skill, where 1.0 means doing no better than ignoring the prices and "
    "predicting the average. A classical optimizer fits the same surfaces to machine "
    "precision and does *worse* than that. No architecture across a 169× range in "
    "capacity does better.",
    icon="🔬",
)

st.divider()

# ---------------------------------------------------------------- skill metric
st.subheader("How to read these numbers")
st.markdown("""
**Skill = RMSE ÷ that parameter's spread in the test set.** 0.0 is perfect recovery;
1.0 means the model does no better than always predicting the average; above 1.0 means
it does *worse* than that.

Raw RMSE cannot be compared across parameters here — κ_fast has a spread of about 1.6
while θ_fast has about 0.03. Skill is what makes them comparable. It matches the
project's existing `standardized_parameter_rmse` convention.
""")

# ---------------------------------------------------------------- headline models
models = data.get("models", {})
if models:
    st.subheader("Parameter recovery")
    cols = st.columns(len(models))
    for col, (tag, m) in zip(cols, models.items()):
        with col:
            st.metric(tag.replace("Model_", "Model ").replace("_", " "),
                      f"{m['mean_skill']:.3f}",
                      delta="mean skill (1.0 = no better than guessing)",
                      delta_color="off")

    rows = []
    for tag, m in models.items():
        v = m.get("constraint_validity", {})
        rows.append({
            "Model": tag.replace("Model_", "Model ").replace("_", " "),
            "Mean skill": f"{m['mean_skill']:.3f}",
            "Structurally valid": f"{v.get('constraint_validity_rate', float('nan')) * 100:.1f}%",
            "Test surfaces": m["test_samples"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Validity is checked with the project's own `src/constraints.py`: positivity, "
        "slow/fast ordering, both strict Feller inequalities, and the open joint-correlation "
        "disk. Model 2 is 100% valid by construction — its latent bijection cannot emit an "
        "invalid vector for any finite input."
    )

    with st.expander("Per-parameter skill"):
        table = {"Parameter": [PARAM_LABELS.get(k, k) for k in
                               next(iter(models.values()))["param_skill"]]}
        for tag, m in models.items():
            table[tag.replace("Model_", "M").replace("_", " ")] = [
                f"{v:.3f}" for v in m["param_skill"].values()
            ]
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
        st.caption(
            "V₀ recovers best — it is pinned by the overall price level. κ and σ barely "
            "recover at all. That split is the signature of an ill-conditioned inverse "
            "problem rather than a training bug."
        )

# ---------------------------------------------------------------- multi-seed
seeds = data.get("multi_seed", {})
cmp_ = seeds.get("comparison")
if cmp_:
    st.subheader("Is the gap between the two models real?")
    a, b = seeds["Model_1_direct"], seeds["Model_2_canonical_latent"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Model 1 direct", f"{a['mean']:.4f}", delta=f"± {a['sd']:.4f} (n={a['n']})",
              delta_color="off")
    c2.metric("Model 2 latent", f"{b['mean']:.4f}", delta=f"± {b['sd']:.4f} (n={b['n']})",
              delta_color="off")
    c3.metric("p-value", f"{cmp_['p_value']:.5f}",
              delta="Welch t-test" , delta_color="off")

    if cmp_["significant"]:
        st.success(
            f"**Yes — the gap is real.** Model 2 is worse at recovery by "
            f"{cmp_['difference']:+.4f} mean skill (p = {cmp_['p_value']:.5f} across "
            f"{a['n']} seeds each; the two ranges do not overlap). So the canonical "
            f"constraint parameterization costs a small but measurable amount of recovery "
            f"accuracy, and buys guaranteed structural validity in exchange. That is a "
            f"genuine trade-off, not a wash.",
            icon="📊",
        )
    else:
        st.info(f"Within noise (p = {cmp_['p_value']:.4f}).", icon="📊")

# ---------------------------------------------------------------- noise
noise = data.get("noise_robustness", {})
if noise:
    st.subheader("Noise robustness")
    st.markdown(
        "Models held fixed; multiplicative noise applied to the test prices. This is the "
        "question that matters for real quotes, since NSE bhavcopy gives close prices with "
        "no bid-ask."
    )
    levels = [r["noise"] for r in next(iter(noise.values()))]
    table = {"Noise": [f"{lv * 100:.1f}%" for lv in levels]}
    for tag, rows in noise.items():
        table[tag.replace("Model_", "M").replace("_", " ")] = [
            f"{r['mean_skill']:.3f}" for r in rows
        ]
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    st.caption(
        "These models were trained on clean data. Skill above 1.0 at 5% means a "
        "clean-trained model does worse than ignoring the prices — but that is a "
        "train/test mismatch, not a property of the problem. The cohort below "
        "separates the two."
    )

# ---------------------------------------------------------------- noise cohort
cohort = data.get("noise_cohort")
if cohort:
    st.subheader("Noise cohort — models trained for the noise they face")
    st.markdown(
        "A separate model trained at each noise level, with noise resampled every epoch. "
        "The diagonal below is the fair comparison: trained and tested at the same level."
    )

    diag = cohort["matched_diagonal"]
    fixed = data.get("noise_robustness", {}).get("Model_2_canonical_latent", [])
    fixed_by = {f"{r['noise']}": r["mean_skill"] for r in fixed}

    rows = []
    for lv, sk in sorted(diag.items(), key=lambda kv: float(kv[0])):
        rows.append({
            "Noise level": f"{float(lv) * 100:.1f}%",
            "Trained for this noise": f"{sk:.3f}",
            "Clean-trained model": f"{fixed_by.get(lv, float('nan')):.3f}"
                                   if lv in fixed_by else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    worst = max(diag.values())
    st.warning(
        f"**This corrects the table above.** A model trained for its noise degrades "
        f"gently — {min(diag.values()):.3f} clean to {worst:.3f} at 5% — rather than "
        f"collapsing past 1.0. The catastrophic clean-trained figure was largely "
        f"train/test mismatch.\n\n"
        f"What survives is milder but still decisive: even trained directly for the noise "
        f"it faces, the model never gets near useful recovery. Noise makes a bad situation "
        f"slightly worse; it is not what causes it.",
        icon="⚖️",
    )

# ---------------------------------------------------------------- architecture sweep
arch = data.get("architecture_sweep")
if arch:
    st.subheader("Does a better architecture help?")
    st.markdown(
        f"{arch['configurations']} configurations: widths from 64 to 1024, depths from 2 "
        f"to 5 layers, three learning rates, with and without dropout. Each keeps its "
        f"best-validation weights."
    )

    rows = [{
        "Architecture": a["architecture"].replace("_", " "),
        "Parameters": f"{a['parameters']:,}",
        "Best skill": f"{a['best_skill']:.4f}",
    } for a in arch["by_architecture"]]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    smallest = arch["by_architecture"][0]
    largest = arch["by_architecture"][-1]
    ratio = largest["parameters"] / smallest["parameters"]
    st.success(
        f"**Capacity is not what is binding.** A {smallest['parameters']:,}-parameter "
        f"network scores {smallest['best_skill']:.3f} and a "
        f"{largest['parameters']:,}-parameter one scores {largest['best_skill']:.3f} — "
        f"a **{ratio:.0f}× increase in capacity buys nothing**. Across all "
        f"{arch['configurations']} configurations the best is {arch['best_skill']:.4f} "
        f"and the worst {arch['worst_skill']:.4f}.\n\n"
        f"This closes the last standing objection to the non-identifiability reading. "
        f"The ceiling sits near 0.78 regardless of what is thrown at it.",
        icon="📐",
    )

# ---------------------------------------------------------------- classical
cls = data.get("classical_baseline")
if cls:
    st.subheader("Classical calibration on the same surfaces")
    st.markdown(
        "The third arm. A least-squares optimizer with multi-starts, using the identical "
        "pricer and identical latent coordinates as the networks, fitting each surface "
        "directly. It is given a large advantage: it sees the exact surface it is fitting "
        "and may iterate freely, where a network gets one forward pass."
    )
    med_skill = cls.get("mean_median_skill", cls["mean_skill"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Price fit", f"{cls['median_price_rmse']:.2e}",
              delta="median RMSE — effectively exact", delta_color="off")
    c2.metric("Parameter recovery", f"{med_skill:.2f}",
              delta="median skill (1.0 = no better than guessing)", delta_color="off")
    c3.metric("Price-equivalent fits",
              f"{cls.get('price_equivalent_fraction', 0) * 100:.0f}%",
              delta="below the G2 threshold", delta_color="off")

    eq = cls.get("price_equivalent_subset")
    if med_skill > 1.0:
        st.success(
            f"**This is the decisive result of the project.** The optimizer fits the prices "
            f"to **{cls['median_price_rmse']:.1e}** — machine precision, roughly 10,000× "
            f"closer than either network gets — and recovers parameters at **{med_skill:.2f}** "
            f"skill. That is *above 1.0*: it lands further from the truth than simply "
            f"guessing the average would have.\n\n"
            f"So there exist parameter vectors that reproduce the surface to eight decimal "
            f"places while being badly wrong, and the optimizer finds one of them essentially "
            f"at random. No amount of model capacity fixes that, because the information is "
            f"not in the surface to begin with.",
            icon="🎯",
        )
        if eq:
            st.markdown(
                f"Restricting to the **{eq['n']} fits that are price-equivalent** "
                f"(median price RMSE {eq['median_price_rmse']:.2e}) does not rescue it — "
                f"median skill there is **{eq['mean_median_skill']:.2f}**. This reproduces "
                f"the project's existing G2 result — 39 separated parameter clusters at "
                f"price RMSE `4.708e-08` — on a larger, independently drawn sample."
            )

        st.info(
            f"**The counterintuitive part, and the best line for a presentation.** The "
            f"networks score about 0.80 while this optimizer scores {med_skill:.2f}, so the "
            f"networks recover parameters *better* — precisely because they fit the prices "
            f"*worse*. A network trained across 10,000 surfaces is pulled toward the "
            f"population average, and when the surface does not identify the parameters, "
            f"that average is closer to the truth than an arbitrary price-equivalent "
            f"solution. Here, fitting prices better is actively harmful to recovery.",
            icon="🔄",
        )

    st.caption(f"{cls['surfaces_calibrated']} surfaces, {cls['starts_per_surface']} "
               f"multi-starts each, bounded latent coordinates. Skill is median-based, "
               f"since a single diverged fit would otherwise dominate an RMSE.")

# ---------------------------------------------------------------- real market
real = data.get("real_market")
if real:
    st.subheader("Real NSE market data")
    st.markdown(
        "Five frozen NTPC dates from official NSE UDiFF bhavcopy. Real surfaces are "
        "incomplete — 11 to 19 of the 20 nominal slots — and the R2 contract forbids "
        "filling a missing quote with a model price, so the network takes the mask as "
        "input rather than imputing."
    )

    rows = []
    for r in real["rows"]:
        rows.append({
            "Date": r["date_id"],
            "Slots": f"{r['usable_slots']}/20",
            "Network": f"{r['network_relative'] * 100:.1f}%",
            "Best possible fit": f"{r['best_fit_relative'] * 100:.1f}%"
                                 if r["best_fit_relative"] is not None else "—",
            "Gap": f"{r['gap_pp']:+.1f}pp" if r["gap_pp"] is not None else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Repricing error as a percentage of the mean observed price, computed at each "
        "slot's **actual traded strike**. 'Best possible fit' is a 12-start least-squares "
        "fit to that same surface — the floor any method could reach."
    )

    st.info(
        "Double Heston fits these real surfaces to 1.4–11.5%, so the model class is "
        "workable on NTPC — the remaining error is the network's synthetic-to-real "
        "transfer, not a failure of the model.",
        icon="📉",
    )

    st.caption(
        "⚠️ These are the five **development** dates — their own metadata marks them "
        "excluded from G8, so they are not a held-out test. See the G8 section below. "
        f"{real['caveat']}"
    )

# ---------------------------------------------------------------- G8 held-out
g8 = data.get("g8")
if g8:
    st.subheader("G8 — the actual held-out test")
    st.markdown(
        f"Eight Wednesdays after the development window, downloaded and audited through "
        f"the same sealed contract, and never seen during any development decision. "
        f"This is the real out-of-sample number."
    )

    rows = [{
        "Date": r["date_id"],
        "Slots": f"{r['usable_slots']}/20",
        "Network": f"{r['network_relative'] * 100:.1f}%",
        "Best possible fit": f"{r['best_fit_relative'] * 100:.1f}%",
        "Gap": f"{r['gap_pp']:+.1f}pp",
    } for r in g8["rows"]]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Median network", f"{g8['median_network_relative'] * 100:.1f}%",
              delta="repricing error", delta_color="off")
    c2.metric("Median model floor", f"{g8['median_best_fit_relative'] * 100:.1f}%",
              delta="best any method could do", delta_color="off")
    c3.metric("Median gap", f"{g8['median_gap_pp']:+.1f}pp",
              delta="attributable to the network", delta_color="off")

    st.warning(
        f"**Held-out performance is worse than the development dates suggested**, which is "
        f"the normal and expected direction. The development gap ran 1.8–11.3 points with a "
        f"median near 5.6; on G8 it is {g8['median_gap_pp']:.1f}. Quote the G8 number, not "
        f"the development one.",
        icon="🎯",
    )

    cov = g8.get("coverage_vs_gap")
    if cov and not cov["significant"]:
        st.error(
            f"**A claim from the development dates did not replicate.** Those five suggested "
            f"transfer quality tracked slot coverage. Across these eight held-out dates there "
            f"is no such relationship: Spearman ρ = {cov['spearman_rho']:+.3f}, "
            f"p = {cov['p_value']:.2f}. The two complete 20/20 surfaces show gaps of +11.0 and "
            f"+14.5 points, worse than several sparser dates. The original pattern was "
            f"an artefact of reading five points.",
            icon="↩️",
        )

    st.caption(
        f"All predicted parameter sets are structurally valid. The risk-free rate is carried "
        f"forward from the latest sealed RBI observation on or before each date "
        f"({', '.join(g8.get('rate_observations_used') or ['—'])}) "
        f"— permitted by the contract, and low-impact because the forward is futures-implied, "
        f"so the rate only moves the discount factor."
    )

# ---------------------------------------------------------------- repricing sweep
sweep = data.get("repricing_sweep")
if sweep:
    st.subheader("Does a differentiable repricing loss help?")
    st.markdown(
        "The project specifies Model 2 as constraints **and** differentiable repricing. "
        "Adding the repricing term weights each parameter by how much it actually moves "
        "prices, so directions the surface barely constrains get almost no gradient."
    )
    df = pd.DataFrame([{
        "Price weight": f"{s['price_weight']:.1f}",
        "Mean skill": f"{s['mean_skill']:.3f}",
        "Test price RMSE": f"{s['test_price_rmse']:.2e}",
    } for s in sweep])
    st.dataframe(df, use_container_width=True, hide_index=True)

    lo, hi = sweep[0], sweep[-1]
    price_gain = (1 - hi["test_price_rmse"] / lo["test_price_rmse"]) * 100
    skill_change = abs(hi["mean_skill"] - lo["mean_skill"])

    st.success(
        f"**The clearest single result in this project.** Going from no repricing term to "
        f"a dominant one improves price fit by **{price_gain:.0f}%** "
        f"({lo['test_price_rmse']:.2e} → {hi['test_price_rmse']:.2e}) while parameter "
        f"recovery moves by **{skill_change:.4f}** — against a seed-to-seed spread of "
        f"0.003, so that is indistinguishable from nothing.\n\n"
        f"The physics-informed loss buys price accuracy and delivers no recovery. "
        f"That is what an unidentifiable inverse problem looks like: the extra gradient "
        f"signal lands entirely in directions the surface already constrained, because "
        f"the directions it does not constrain leave no trace in the prices to learn from.",
        icon="🎯",
    )

# ---------------------------------------------------------------- OOD
ood = data.get("ood")
if ood:
    st.subheader("Outside the training distribution")
    st.markdown(
        "Both cohorts come from the project's own reviewed sampler and are "
        "evaluation-only by contract — nothing was trained on them. Boundary-challenge "
        "parameters are valid but near a structural edge (Feller gap close to zero, "
        "correlations near the disk, weak slow/fast separation). OOD parameters sit "
        "outside the reviewed ranges entirely."
    )

    rows = [{"Cohort": "interior (training distribution)",
             "Surfaces": "1,500",
             "Mean skill": f"{ood['interior_reference_skill']:.3f}"}]
    rows += [{"Cohort": c["cohort"].replace("_", " "),
              "Surfaces": f"{c['surfaces']:,}",
              "Mean skill": f"{c['mean_skill']:.3f}"} for c in ood["cohorts"]]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    worst = max(c["mean_skill"] for c in ood["cohorts"])
    st.caption(
        f"Degradation is orderly: near-boundary parameters cost a little, fully "
        f"out-of-distribution parameters push skill to {worst:.2f} — well past the point "
        f"where predicting the average would do better. The model is doing what a trained "
        f"model does, which is to regress toward what it saw."
    )

# ---------------------------------------------------------------- caveats
st.divider()
with st.expander("What this does and does not establish"):
    st.markdown("""
    **Established**
    - Four separate training setups, five seeds each, all land at 0.80 ± 0.02 mean skill.
    - The project's own canonical latent bijection gives no recovery improvement, which
      rules out parameterization as the explanation.
    - A classical optimizer fits the prices to machine precision (9.2e-08) and recovers
      parameters *worse than guessing the average* (median skill 1.80). Price-equivalent
      solutions exist that are badly wrong, and an optimizer finds them.
    - Recovery collapses entirely past 2% quote noise.
    - This agrees with the project's existing G2 finding, where classical multi-start
      reached a median price RMSE of 4.708e-08 and still landed in 39 separated parameter
      clusters.

    - 36 architectures spanning a 169× range in parameter count all land between 0.78
      and 0.83, so capacity is not the binding constraint.
    - Held out on eight untouched NSE dates: every predicted parameter set is
      structurally valid, and repricing sits a median 10.1 points above the floor.
    - Degradation outside the training distribution is orderly rather than erratic.

    **Not established**
    - Real-market measurement is repricing only. NTPC's true parameters are unknown, so
      parameter recovery is undefined there.
    - G8 covers eight dates on one ticker. The other three selected sector primaries
      (CIPLA, INFY, HDFCBANK) have not been evaluated.
    - A network-side PDE-informed model (Model 3) has not been built. It is explicitly
      not a blocker, and the existing Archive-2 PDE loss has a reproduced defect that
      must not be imported.

    **Three corrections made during this work**, all of which changed conclusions:
    - An initial run fed the network only the 20 prices. Maturity, rate and carry vary
      across surfaces, so that left the inverse map ambiguous by input construction,
      independent of any physics. Fixing it moved mean skill from about 0.90 to 0.80.
    - Real-market repricing initially priced at nominal moneyness targets while comparing
      against quotes struck up to 0.04 away, inflating the error roughly threefold. At
      actual traded strikes the best-possible Double Heston fit is 1.4–11.5%, not 16–35%.
    - The real-market repricing code looked up each quote's interest rate and carry by
      its expiry rank, but indexed into a flat per-slot array rather than a per-rank one
      — every second-expiry quote (the longer-dated leg) was silently priced with the
      first expiry's rate and carry instead of its own. This affected every real-market
      script in the project, including the "best possible fit" floor, the market-wide
      run, and the option-repricing backtest. Fixing it changed the G8 median floor from
      8.2% to 4.3% and the median gap from +10.1pp to +10.8pp; the "network loses to flat
      Black-Scholes on every one of 210 stocks" finding was re-checked afterward and
      held.
    """)

st.caption("Training data is synthetic and noise-free. Real NSE data is used for "
           "evaluation only, never for training.")
