"""
Boundary-challenge and out-of-distribution evaluation.

The models were trained only on the interior distribution. This measures what
happens outside it, using the project's own reviewed sampler for both cohorts.

Both cohorts are evaluation-only by contract: `ood_test.evaluation_only` is true
and neither `ood_test` nor `boundary_challenge` is `train_validation_eligible`.
Nothing here trains on them; they are scored against the already frozen models.

The two cohorts ask different questions. Boundary-challenge parameters are valid
but sit near a structural edge -- a Feller gap close to zero, correlations near the
disk, weak slow/fast separation -- so they test whether recovery survives where the
model is still legitimate. OOD parameters sit outside the reviewed training ranges
entirely, so they test extrapolation.

Surfaces are priced with the unchanged production pricer on the same conditioning
lattice as the frozen dataset, so the only thing that differs from the training
distribution is the parameters.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import torch
from torch import nn

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from mentor_dh_pinn import params_v2 as P
from src.audit_reviewed_sampling import sample_distribution
from src.double_heston import price_double_heston_surface
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
SPOT = 100.0


def build_mlp(input_dim, hidden=(256, 256, 256), output_dim=10):
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def price_surface(vector, maturities, rate, carry):
    out = np.zeros(len(CANONICAL_SLOT_KEYS))
    for rank in R2_EXPIRY_RANKS:
        idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS) if k.expiry_rank == rank]
        keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
        out[np.asarray(idx, int)] = price_double_heston_surface(
            SPOT, np.array([SPOT * np.exp(k.target_log_moneyness) for k in keys], float),
            np.full(len(keys), maturities[rank - 1], float), rate, carry,
            [k.option_type for k in keys], vector, node_count=64,
        )
    return out / SPOT


def training_conditioning():
    """Conditioning lattice and normalisation from the frozen training dataset."""
    prices, cond, params = [], [], []
    with open(PROJECT_ROOT / "data" / "final_r2_clean_10000" / "surfaces.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            if len(rec["prices"]) != 20:
                continue
            mats = sorted(set(rec["maturities"]))
            prices.append(rec["prices"])
            cond.append([mats[0], mats[1], rec["rates"][0], rec["carries"][0]])
            p = rec["metadata"]["parameters_canonical_order"]
            params.append([p[n] for n in P.CANONICAL])
    prices, cond, params = np.array(prices), np.array(cond), np.array(params)
    z = np.stack([P.encode(r) for r in params])
    X = np.concatenate([prices, cond], axis=1)
    return (cond, X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0),
            z.mean(0), np.where(z.std(0) > 0, z.std(0), 1.0), X.shape[1], params)


def evaluate_cohort(name, count, seed, model, cond_pool, x_mu, x_sd, t_mu, t_sd,
                    latent, rng):
    logger.info("sampling %s (%d requested)", name, count)
    frame = sample_distribution(name, count=count, seed=seed)
    accepted = frame.loc[frame["accepted"]] if "accepted" in frame.columns else frame
    logger.info("  %d/%d accepted by the sampler", len(accepted), len(frame))
    if not len(accepted):
        return None

    vectors, prices, conds = [], [], []
    failures = 0
    for row in accepted.itertuples():
        vec = np.array([getattr(row, n) for n in P.CANONICAL], float)
        c = cond_pool[rng.integers(len(cond_pool))]
        try:
            p = price_surface(vec, (c[0], c[1]), c[2], c[3])
        except Exception:
            failures += 1
            continue
        if not np.isfinite(p).all():
            failures += 1
            continue
        vectors.append(vec)
        prices.append(p)
        conds.append(c)

    if not vectors:
        logger.warning("  every %s surface failed to price", name)
        return None
    logger.info("  %d surfaces priced, %d pricing failures", len(vectors), failures)

    vectors, prices, conds = np.array(vectors), np.array(prices), np.array(conds)
    feats = (np.concatenate([prices, conds], axis=1) - x_mu) / x_sd
    with torch.no_grad():
        out = model(torch.tensor(feats, dtype=torch.float32)).numpy() * t_sd + t_mu
    pred = np.stack([P.to_array(P.decode(r)) for r in out]) if latent else out

    skill = {}
    for i, nm in enumerate(SHORT):
        sd = float(np.std(vectors[:, i]))
        rmse = float(np.sqrt(np.mean((pred[:, i] - vectors[:, i]) ** 2)))
        skill[nm] = rmse / sd if sd > 0 else float("nan")

    return {
        "cohort": name,
        "surfaces": int(len(vectors)),
        "pricing_failures": failures,
        "mean_skill": float(np.nanmean(list(skill.values()))),
        "param_skill": skill,
        "evaluation_only": True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=800)
    ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--checkpoint", default=str(
        PROJECT_ROOT / "outputs" / "run_v4" / "Model_2_canonical_latent_checkpoint.pt"))
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "ood"))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    cond_pool, x_mu, x_sd, t_mu, t_sd, in_dim, train_params = training_conditioning()
    model = build_mlp(in_dim)
    model.load_state_dict(torch.load(args.checkpoint, map_location="cpu"))
    model.eval()
    logger.info("loaded %s", Path(args.checkpoint).name)

    results = []
    for cohort in ("boundary_challenge", "ood_test"):
        r = evaluate_cohort(cohort, args.count, args.seed, model, cond_pool,
                            x_mu, x_sd, t_mu, t_sd, True, rng)
        if r:
            results.append(r)
            logger.info("  %s mean skill %.3f", cohort, r["mean_skill"])

    report = {
        "checkpoint": Path(args.checkpoint).name,
        "interior_reference_skill": 0.801,
        "cohorts": results,
        "note": ("Both cohorts are evaluation-only by the reviewed sampling contract. "
                 "Surfaces use the unchanged production pricer on the frozen dataset's "
                 "own conditioning lattice, so only the parameters differ from training."),
    }
    (out_dir / "ood_evaluation.json").write_text(json.dumps(report, indent=2))

    logger.info("")
    logger.info("OUT-OF-DISTRIBUTION EVALUATION")
    logger.info("  interior (training distribution) : 0.801")
    for r in results:
        logger.info("  %-20s : %.3f  (%d surfaces)",
                    r["cohort"], r["mean_skill"], r["surfaces"])


if __name__ == "__main__":
    main()
