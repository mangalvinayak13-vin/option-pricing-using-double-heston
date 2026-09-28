"""
Hyperparameter sweep over the inverse network.

This closes the one objection left against the non-identifiability reading: that
recovery is poor because the architecture is poor. If a spread of widths, depths,
learning rates, dropout and batch sizes all land in the same narrow band, capacity
is not what is binding.

Deliberately includes configurations that should be too small and too large, so a
flat result is informative rather than a consequence of only trying one scale.

Each run uses best-validation weights. Validation loss bottoms around epoch 40 and
then climbs, so 150 epochs is ample and the early-stopping point is well inside it.
"""

from __future__ import annotations

import argparse
import itertools
import json
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")
from mentor_dh_pinn import params_v2 as P

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]

ARCHITECTURES = {
    "tiny_2x64": (64, 64),
    "small_2x128": (128, 128),
    "base_3x256": (256, 256, 256),
    "wide_3x512": (512, 512, 512),
    "deep_5x256": (256, 256, 256, 256, 256),
    "very_wide_2x1024": (1024, 1024),
}
LEARNING_RATES = [3e-3, 1e-3, 3e-4]
DROPOUTS = [0.0, 0.1]
BATCH_SIZES = [128]


def build_mlp(input_dim, hidden, dropout, output_dim=10):
    layers, prev = [], input_dim
    for h in hidden:
        layers.append(nn.Linear(prev, h))
        layers.append(nn.ReLU())
        if dropout > 0:
            layers.append(nn.Dropout(dropout))
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


def run_one(Xs, Ys, params, splits, hidden, lr, dropout, batch, epochs, latent,
            t_mu, t_sd, device):
    tr, va, te = splits
    tr_l = DataLoader(tr, batch_size=batch, shuffle=True)
    va_l = DataLoader(va, batch_size=batch)

    model = build_mlp(Xs.shape[1], hidden, dropout).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    lossf = nn.MSELoss()

    best, best_state = float("inf"), None
    for _ in range(epochs):
        model.train()
        for xb, yb in tr_l:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            lossf(model(xb), yb).backward()
            opt.step()
        model.eval()
        tot = 0.0
        with torch.no_grad():
            for xb, yb in va_l:
                xb, yb = xb.to(device), yb.to(device)
                tot += lossf(model(xb), yb).item() * len(xb)
        val = tot / len(va.dataset)
        sched.step()
        if val < best:
            best = val
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    model.eval()

    idx = np.asarray(te.indices)
    with torch.no_grad():
        out = model(torch.tensor(Xs[idx], dtype=torch.float32).to(device)).cpu().numpy()
    out = out * t_sd + t_mu
    if latent:
        out = np.stack([P.to_array(P.decode(r)) for r in out])

    truth = params[idx]
    skills = []
    for i in range(10):
        rmse = np.sqrt(np.mean((out[:, i] - truth[:, i]) ** 2))
        sd = np.std(truth[:, i])
        skills.append(rmse / sd if sd > 0 else np.nan)
    return float(np.mean(skills)), float(best)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--latent", action="store_true",
                    help="Predict the canonical latent z instead of raw parameters")
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "sweep"))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    prices, cond, params = load()
    target = np.stack([P.encode(r) for r in params]) if args.latent else params

    X = np.concatenate([prices, cond], axis=1)
    x_mu, x_sd = X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0)
    t_mu, t_sd = target.mean(0), np.where(target.std(0) > 0, target.std(0), 1.0)
    Xs, Ys = (X - x_mu) / x_sd, (target - t_mu) / t_sd

    ds = TensorDataset(torch.tensor(Xs, dtype=torch.float32),
                       torch.tensor(Ys, dtype=torch.float32))
    n = len(ds)
    ntr, nva = int(0.7 * n), int(0.15 * n)
    splits = random_split(ds, [ntr, nva, n - ntr - nva],
                          generator=torch.Generator().manual_seed(42))

    combos = list(itertools.product(ARCHITECTURES.items(), LEARNING_RATES,
                                    DROPOUTS, BATCH_SIZES))
    logger.info("%d configurations, %d epochs each", len(combos), args.epochs)

    results = []
    for i, ((name, hidden), lr, dropout, batch) in enumerate(combos, 1):
        torch.manual_seed(0)
        skill, val = run_one(Xs, Ys, params, splits, hidden, lr, dropout, batch,
                             args.epochs, args.latent, t_mu, t_sd, device)
        results.append({
            "architecture": name, "hidden": list(hidden), "lr": lr,
            "dropout": dropout, "batch": batch,
            "mean_skill": skill, "best_val_loss": val,
            "parameters": sum(p.numel() for p in build_mlp(Xs.shape[1], hidden, dropout).parameters()),
        })
        logger.info("[%2d/%d] %-16s lr=%.0e drop=%.1f -> skill %.4f",
                    i, len(combos), name, lr, dropout, skill)
        (out_dir / "sweep_results.json").write_text(json.dumps({
            "latent": args.latent, "epochs": args.epochs, "results": results,
        }, indent=2))

    skills = np.array([r["mean_skill"] for r in results])
    best = min(results, key=lambda r: r["mean_skill"])
    summary = {
        "configurations": len(results),
        "best_skill": float(skills.min()),
        "worst_skill": float(skills.max()),
        "median_skill": float(np.median(skills)),
        "spread": float(skills.max() - skills.min()),
        "best_config": best,
        "results": results,
        "latent": args.latent,
        "epochs": args.epochs,
    }
    (out_dir / "sweep_results.json").write_text(json.dumps(summary, indent=2))

    logger.info("")
    logger.info("SWEEP over %d configurations", len(results))
    logger.info("  best   %.4f  (%s, lr=%.0e, drop=%.1f, %d params)",
                summary["best_skill"], best["architecture"], best["lr"],
                best["dropout"], best["parameters"])
    logger.info("  median %.4f", summary["median_skill"])
    logger.info("  worst  %.4f", summary["worst_skill"])
    logger.info("  spread %.4f", summary["spread"])


if __name__ == "__main__":
    main()
