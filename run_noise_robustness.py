"""
Noise robustness of the trained inverse models.

The frozen 10,000-surface dataset is noise level zero. Real quotes are not: NSE
bhavcopy carries settlement/close prices with no bid-ask, so the effective quote
noise is material. A non-identifiability claim made only on clean data is the
weaker version of the claim; if recovery degrades sharply once quotes are
perturbed, the practical conclusion is stronger.

Perturbs the test surfaces with multiplicative noise and re-scores the already
trained models. No retraining: this measures robustness of a fixed model, which
is the quantity that matters when the model meets real quotes.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")
from mentor_dh_pinn import params_v2 as P

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
NOISE_LEVELS = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]


def build_mlp(input_dim, hidden=(256, 256, 256), output_dim=10):
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=str(PROJECT_ROOT / "outputs" / "run_v4"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)

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
    x_mu, x_sd = X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0)

    n = len(X)
    ntr, nva = int(0.7 * n), int(0.15 * n)
    _, _, te = random_split(TensorDataset(torch.zeros(n)), [ntr, nva, n - ntr - nva],
                            generator=torch.Generator().manual_seed(42))
    idx = np.asarray(te.indices)

    report = {}
    for tag, latent in [("Model_1_direct", False), ("Model_2_canonical_latent", True)]:
        ckpt = Path(args.run_dir) / f"{tag}_checkpoint.pt"
        if not ckpt.exists():
            print(f"skip {tag}: no checkpoint at {ckpt}")
            continue

        target = z if latent else params
        t_mu, t_sd = target.mean(0), np.where(target.std(0) > 0, target.std(0), 1.0)

        model = build_mlp(X.shape[1])
        model.load_state_dict(torch.load(ckpt, map_location="cpu"))
        model.eval()

        rows = []
        for level in NOISE_LEVELS:
            noisy = prices[idx].copy()
            if level > 0:
                noisy = noisy * (1.0 + rng.normal(0.0, level, noisy.shape))
            feats = np.concatenate([noisy, cond[idx]], axis=1)
            with torch.no_grad():
                out = model(torch.tensor((feats - x_mu) / x_sd,
                                         dtype=torch.float32)).numpy()
            out = out * t_sd + t_mu
            if latent:
                out = np.stack([P.to_array(P.decode(r)) for r in out])

            truth = params[idx]
            skills = []
            for i in range(10):
                rmse = np.sqrt(np.mean((out[:, i] - truth[:, i]) ** 2))
                sd = np.std(truth[:, i])
                skills.append(rmse / sd if sd > 0 else np.nan)
            rows.append({"noise": level, "mean_skill": float(np.mean(skills))})
            print(f"  {tag}  noise {level*100:>4.1f}%  mean skill {np.mean(skills):.4f}")

        report[tag] = rows
        print()

    out = PROJECT_ROOT / "outputs" / "noise_robustness.json"
    out.write_text(json.dumps({
        "note": "Multiplicative gaussian noise on test prices; models NOT retrained.",
        "levels": NOISE_LEVELS,
        "results": report,
    }, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
