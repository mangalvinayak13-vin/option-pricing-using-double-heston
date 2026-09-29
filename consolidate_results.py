"""
Gather every experiment into one JSON the web page reads.

Each block is written only if its source file exists, so the page degrades to
whatever has actually been run rather than inventing placeholders.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "consolidated_results.json"


def load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def main():
    report: dict = {"generated_at": datetime.now().isoformat()}

    # --- headline single-run models -------------------------------------------
    models = {}
    for tag in ("Model_1_direct", "Model_2_canonical_latent"):
        m = load(ROOT / "outputs" / "run_v4" / f"{tag}_metrics.json")
        if m:
            models[tag] = {
                "mean_skill": m["mean_skill"],
                "param_skill": m["param_skill"],
                "constraint_validity": m.get("constraint_validity", {}),
                "test_samples": m["test_samples"],
            }
    report["models"] = models

    # --- multi-seed ------------------------------------------------------------
    seeds: dict = {}
    for tag in ("Model_1_direct", "Model_2_canonical_latent"):
        vals = []
        for s in range(10):
            m = load(ROOT / "outputs" / "seeds" / f"seed_{s}" / f"{tag}_metrics.json")
            if m:
                vals.append(m["mean_skill"])
        if vals:
            a = np.array(vals)
            seeds[tag] = {
                "n": len(vals),
                "mean": float(a.mean()),
                "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
                "values": [float(v) for v in a],
            }
    if len(seeds) == 2:
        from scipy import stats
        a = np.array(seeds["Model_1_direct"]["values"])
        b = np.array(seeds["Model_2_canonical_latent"]["values"])
        t, p = stats.ttest_ind(a, b, equal_var=False)
        seeds["comparison"] = {
            "difference": float(b.mean() - a.mean()),
            "welch_t": float(t),
            "p_value": float(p),
            "significant": bool(p < 0.05),
        }
    report["multi_seed"] = seeds

    # --- noise ------------------------------------------------------------------
    noise = load(ROOT / "outputs" / "noise_robustness.json")
    if noise:
        report["noise_robustness"] = noise["results"]

    # --- classical baseline on the synthetic split -------------------------------
    cls = load(ROOT / "outputs" / "classical" / "classical_baseline_metrics.json")
    if cls:
        report["classical_baseline"] = cls

    # --- real market --------------------------------------------------------------
    net = load(ROOT / "outputs" / "real_eval" /
               "MaskAware_Model_2_canonical_latent_metrics.json")
    fit = load(ROOT / "outputs" / "real_eval" / "real_classical_fit.json")
    if net and fit:
        floor = {r["date_id"]: r for r in fit["results"]}
        rows = []
        for r in net["real_market"]:
            f = floor.get(r["date_id"], {})
            rows.append({
                "date_id": r["date_id"],
                "usable_slots": r["usable_slots"],
                "network_relative": r["repricing_rmse_relative"],
                "best_fit_relative": f.get("best_fit_repricing_relative"),
                "gap_pp": (r["repricing_rmse_relative"] - f["best_fit_repricing_relative"]) * 100
                          if "best_fit_repricing_relative" in f else None,
                "parameters_valid": r["parameters_valid"],
            })
        report["real_market"] = {
            "rows": rows,
            "mask_aware_synthetic_skill": net["synthetic_mean_skill"],
            "caveat": net["real_market_caveat"],
        }

    # --- repricing-loss sweep --------------------------------------------------------
    sweep = []
    for w in ("0.0", "0.5", "0.9"):
        m = load(ROOT / "outputs" / "repricing" / f"repricing_w{w}_metrics.json")
        if m:
            sweep.append({
                "price_weight": float(w),
                "mean_skill": m["mean_skill"],
                "test_price_rmse": m["test_price_rmse"],
            })
    if sweep:
        report["repricing_sweep"] = sweep

    # --- architecture sweep ------------------------------------------------------------
    arch = load(ROOT / "outputs" / "sweep" / "sweep_results.json")
    if arch and "results" in arch:
        by_arch = {}
        for r in arch["results"]:
            name = r["architecture"]
            if name not in by_arch or r["mean_skill"] < by_arch[name]["mean_skill"]:
                by_arch[name] = r
        report["architecture_sweep"] = {
            "configurations": arch.get("configurations", len(arch["results"])),
            "best_skill": arch.get("best_skill"),
            "median_skill": arch.get("median_skill"),
            "worst_skill": arch.get("worst_skill"),
            "best_config": arch.get("best_config"),
            "by_architecture": [
                {"architecture": k, "parameters": v["parameters"],
                 "best_skill": v["mean_skill"]}
                for k, v in sorted(by_arch.items(), key=lambda kv: kv[1]["parameters"])
            ],
        }

    # --- G8 held-out real market --------------------------------------------------------
    g8 = load(ROOT / "outputs" / "g8" / "g8_evaluation.json")
    if g8:
        rows = g8["rows"]
        slots = np.array([r["usable_slots"] for r in rows], float)
        gaps = np.array([r["gap_pp"] for r in rows], float)
        coverage = None
        if len(rows) >= 4:
            from scipy import stats
            rho, p = stats.spearmanr(slots, gaps)
            coverage = {"spearman_rho": float(rho), "p_value": float(p),
                        "significant": bool(p < 0.05)}
        report["g8"] = {
            "dates_evaluated": g8["dates_evaluated"],
            "median_network_relative": g8["median_network_relative"],
            "median_best_fit_relative": g8["median_best_fit_relative"],
            "median_gap_pp": g8["median_gap_pp"],
            "all_parameters_valid": g8["all_parameters_valid"],
            "rate_observations_used": g8.get("rate_observations_used"),
            "coverage_vs_gap": coverage,
            "rows": rows,
        }

    # --- noise cohort ---------------------------------------------------------------------
    cohort = load(ROOT / "outputs" / "noise_cohort" / "noise_cohort.json")
    if cohort:
        report["noise_cohort"] = {
            "matched_diagonal": cohort["matched_diagonal"],
            "grid": cohort["grid"],
        }

    # --- boundary / OOD ---------------------------------------------------------------------
    ood = load(ROOT / "outputs" / "ood" / "ood_evaluation.json")
    if ood:
        report["ood"] = {
            "interior_reference_skill": ood["interior_reference_skill"],
            "cohorts": [{"cohort": c["cohort"], "surfaces": c["surfaces"],
                         "mean_skill": c["mean_skill"]} for c in ood["cohorts"]],
        }

    OUT.write_text(json.dumps(report, indent=2))
    print(f"wrote {OUT}")
    for key in report:
        if key != "generated_at":
            print(f"  included: {key}")


if __name__ == "__main__":
    main()
