"""
Noise cohort: train at several quote-noise levels, test at several.

The earlier noise work perturbed test prices against models trained on clean data,
which answers "is a clean-trained model fragile" but not "does training on noise
help". The project specifies a noise cohort as a dataset, so this trains a separate
model per training-noise level and evaluates each across the full test-noise grid.

The interesting cell is the diagonal: if training on 1% noise makes a model robust
at 1% test noise, noise is a nuisance to be engineered around. If the diagonal
degrades anyway, the information genuinely is not there once quotes are imprecise,
which is the stronger reading.

Noise is multiplicative on prices, resampled every epoch so the model sees the
noise distribution rather than one fixed perturbation it could memorise.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TRAIN_NOISE = [0.0, 0.005, 0.01, 0.02, 0.05]
TEST_NOISE = [0.0, 0.005, 0.01, 0.02, 0.05]


def build_mlp(input_dim, hidden=(256, 256, 256), output_dim=10):
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def load():
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
    return np.array(prices), np.array(cond), np.array(params)


def skill_of(pred, truth):
    out = []
    for i in range(10):
        sd = np.std(truth[:, i])
        out.append(np.sqrt(np.mean((pred[:, i] - truth[:, i]) ** 2)) / sd if sd > 0 else np.nan)
    return float(np.mean(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "noise_cohort"))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")

    prices, cond, params = load()
    z = np.stack([P.encode(r) for r in params])

    n = len(prices)
    g = torch.Generator().manual_seed(42)
    perm = torch.randperm(n, generator=g).numpy()
    ntr, nva = int(0.7 * n), int(0.15 * n)
    tr_i, va_i, te_i = perm[:ntr], perm[ntr:ntr + nva], perm[ntr + nva:]

    # Normalisation is fixed on the clean training split so that changing the noise
    # level changes the data the model sees, not the scale it is measured on.
    X_clean = np.concatenate([prices, cond], axis=1)
    x_mu, x_sd = X_clean[tr_i].mean(0), np.where(X_clean[tr_i].std(0) > 0,
                                                 X_clean[tr_i].std(0), 1.0)
    t_mu, t_sd = z[tr_i].mean(0), np.where(z[tr_i].std(0) > 0, z[tr_i].std(0), 1.0)
    Ys = (z - t_mu) / t_sd

    def features(idx, noise, rng):
        p = prices[idx]
        if noise > 0:
            p = p * (1.0 + rng.normal(0.0, noise, p.shape))
        return (np.concatenate([p, cond[idx]], axis=1) - x_mu) / x_sd

    grid = {}
    for train_noise in TRAIN_NOISE:
        torch.manual_seed(args.seed)
        rng = np.random.default_rng(args.seed)

        model = build_mlp(X_clean.shape[1]).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
        lossf = nn.MSELoss()
        y_tr = torch.tensor(Ys[tr_i], dtype=torch.float32)
        y_va = torch.tensor(Ys[va_i], dtype=torch.float32)

        best, best_state = float("inf"), None
        for _ in range(args.epochs):
            # Resample noise each epoch so the model learns the distribution,
            # not one fixed draw.
            xb_all = torch.tensor(features(tr_i, train_noise, rng), dtype=torch.float32)
            model.train()
            order = torch.randperm(len(tr_i))
            for s in range(0, len(order), args.batch_size):
                sel = order[s:s + args.batch_size]
                opt.zero_grad()
                lossf(model(xb_all[sel]), y_tr[sel]).backward()
                opt.step()

            model.eval()
            with torch.no_grad():
                xv = torch.tensor(features(va_i, train_noise, rng), dtype=torch.float32)
                val = lossf(model(xv), y_va).item()
            sched.step()
            if val < best:
                best = val
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

        model.load_state_dict(best_state)
        model.eval()

        row = {}
        for test_noise in TEST_NOISE:
            eval_rng = np.random.default_rng(1234)      # same perturbation for every model
            with torch.no_grad():
                xt = torch.tensor(features(te_i, test_noise, eval_rng), dtype=torch.float32)
                out = model(xt).numpy() * t_sd + t_mu
            pred = np.stack([P.to_array(P.decode(r)) for r in out])
            row[f"{test_noise}"] = skill_of(pred, params[te_i])

        grid[f"{train_noise}"] = row
        # Build the whole line first: the joined cells contain literal '%' which
        # logging would otherwise try to read as format specifiers.
        cells = "  ".join(f"test {float(k) * 100:.1f}%: {v:.3f}" for k, v in row.items())
        logger.info("train noise %.1f%% -> %s", train_noise * 100, cells)

    diagonal = {f"{lv}": grid[f"{lv}"][f"{lv}"] for lv in TRAIN_NOISE}
    report = {
        "train_noise_levels": TRAIN_NOISE,
        "test_noise_levels": TEST_NOISE,
        "grid": grid,
        "matched_diagonal": diagonal,
        "note": ("Multiplicative price noise resampled per epoch during training. "
                 "Normalisation fixed on the clean training split. The diagonal is "
                 "the fair 'trained for this noise level' comparison."),
    }
    (out_dir / "noise_cohort.json").write_text(json.dumps(report, indent=2))

    logger.info("")
    logger.info("MATCHED DIAGONAL (trained and tested at the same noise level)")
    for lv in TRAIN_NOISE:
        logger.info("  %4.1f%% noise -> skill %.3f", lv * 100, diagonal[f"{lv}"])


if __name__ == "__main__":
    main()
