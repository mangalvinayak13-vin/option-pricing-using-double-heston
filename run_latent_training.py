"""
Inverse-calibration training in the canonical latent coordinates.

Model 1 (baseline)  : network predicts the ten parameters directly.
Model 2 (canonical) : network predicts the unconstrained latent z of
                      src/mentor_dh_pinn/params_v2.py and decodes through the
                      project's bijection, so every output satisfies positivity,
                      slow/fast ordering, both strict Feller inequalities and the
                      open joint-correlation disk by construction.

Why latent coordinates matter here: kappa_fast has a spread of ~1.6 in the
dataset while theta_fast has ~0.03, so a plain MSE on raw parameters is
dominated by the kappa coordinate. params_v2 puts speeds in log coordinates and
splits totals through a bounded share, which equalizes the scales. That file's
own comments record the same failure ("the model barely beat a constant
predictor") from the softplus-gap parameterization.

Both models are scored in PARAMETER space so the numbers are comparable, using
skill = RMSE / (parameter spread in the test set); 1.0 means no better than
always predicting the mean.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mentor_dh_pinn import params_v2 as P

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]


def build_mlp(input_dim: int, hidden=(256, 256, 256), output_dim=10) -> nn.Module:
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def load_dataset(data_path: Path):
    """Returns (X, params, z) where X is 24 inputs, params the canonical ten, z the latent."""
    X, params = [], []
    with open(data_path / "surfaces.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            prices = rec["prices"]
            if len(prices) != 20:
                continue
            mats = sorted(set(rec["maturities"]))
            X.append(list(prices) + [mats[0], mats[1], rec["rates"][0], rec["carries"][0]])
            p = rec["metadata"]["parameters_canonical_order"]
            params.append([p[n] for n in P.CANONICAL])

    X = np.asarray(X, dtype=np.float64)
    params = np.asarray(params, dtype=np.float64)
    z = np.stack([P.encode(row) for row in params])

    # The bijection must reproduce the truth, otherwise latent targets are wrong.
    back = np.stack([P.to_array(P.decode(row)) for row in z])
    err = np.abs(back - params).max()
    if err > 1e-8:
        raise RuntimeError(f"encode/decode round-trip error {err:.3e} exceeds 1e-8")
    logger.info("loaded %d surfaces; bijection round-trip max err %.2e", len(X), err)

    return X, params, z


def standardize(a: np.ndarray):
    mu, sd = a.mean(0), a.std(0)
    sd = np.where(sd > 0, sd, 1.0)
    return (a - mu) / sd, mu, sd


def train(model, train_loader, val_loader, epochs, lr, device):
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    lossf = nn.MSELoss()
    history = {"train_loss": [], "val_loss": []}

    # Validation loss bottoms out early (~epoch 35-45) and then climbs for hundreds of
    # epochs while train loss keeps falling, so the final-epoch weights are strictly worse
    # than the best ones. Keep the best-validation state and restore it at the end.
    best_val = float("inf")
    best_state = None
    best_epoch = -1

    for ep in range(epochs):
        model.train()
        tot = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = lossf(model(xb), yb)
            loss.backward()
            opt.step()
            tot += loss.item() * len(xb)
        tr = tot / len(train_loader.dataset)

        model.eval()
        tot = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                tot += lossf(model(xb), yb).item() * len(xb)
        va = tot / len(val_loader.dataset)

        sched.step()
        history["train_loss"].append(tr)
        history["val_loss"].append(va)

        if va < best_val:
            best_val = va
            best_epoch = ep + 1
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

        if (ep + 1) % 25 == 0:
            logger.info("epoch %d/%d train %.6f val %.6f", ep + 1, epochs, tr, va)

    if best_state is not None:
        model.load_state_dict(best_state)
    history["best_val"] = best_val
    history["best_epoch"] = best_epoch
    logger.info("restored best-validation weights from epoch %d (val %.6f); "
                "final-epoch val was %.6f", best_epoch, best_val, history["val_loss"][-1])

    return history


def evaluate(model, loader, target_mu, target_sd, latent: bool, device):
    """Score in parameter space regardless of what the network predicts."""
    model.eval()
    preds, truths = [], []
    with torch.no_grad():
        for xb, _, pb in loader:
            out = model(xb.to(device)).cpu().numpy()
            out = out * target_sd + target_mu          # undo standardization
            if latent:
                out = np.stack([P.to_array(P.decode(r)) for r in out])
            preds.append(out)
            truths.append(pb.numpy())

    preds = np.concatenate(preds)
    truths = np.concatenate(truths)

    rmse = {}
    skill = {}
    for i, name in enumerate(SHORT):
        rmse[name] = float(np.sqrt(np.mean((preds[:, i] - truths[:, i]) ** 2)))
        spread = float(np.std(truths[:, i]))
        skill[name] = rmse[name] / spread if spread > 0 else float("nan")

    # Structural validity against the project's own canonical checker. Model 2 should be
    # 100% valid by construction; Model 1 has nothing stopping it emitting invalid physics.
    # src/constraints.py uses relative imports, so it must be loaded as src.constraints
    # rather than as a top-level module.
    from src.constraints import validate_parameters
    diags = [validate_parameters(row) for row in preds]
    validity = {
        "constraint_validity_rate": float(np.mean([d["is_valid"] for d in diags])),
        "positivity_violation_rate": float(1.0 - np.mean([d["positive_valid"] for d in diags])),
        "ordering_violation_rate": float(1.0 - np.mean([d["ordering_valid"] for d in diags])),
        "slow_feller_violation_rate": float(np.mean([d["slow_feller_gap"] <= 0.0 for d in diags])),
        "fast_feller_violation_rate": float(np.mean([d["fast_feller_gap"] <= 0.0 for d in diags])),
        "correlation_disk_violation_rate": float(np.mean([d["correlation_disk_value"] >= 1.0 for d in diags])),
    }

    return {
        "param_rmse": rmse,
        "param_skill": skill,
        "mean_skill": float(np.mean(list(skill.values()))),
        "standardized_parameter_rmse": float(
            np.sqrt(np.mean([s ** 2 for s in skill.values()]))
        ),
        "constraint_validity": validity,
        "rmse": float(np.sqrt(np.mean((preds - truths) ** 2))),
        "mae": float(np.mean(np.abs(preds - truths))),
        "test_samples": int(len(truths)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=int, choices=[1, 2], required=True)
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data-dir", default=str(PROJECT_ROOT / "data" / "final_r2_clean_10000"))
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "run_v3"))
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    X, params, z = load_dataset(Path(args.data_dir))

    latent = args.model == 2
    target = z if latent else params
    Xs, _, _ = standardize(X)
    Ys, t_mu, t_sd = standardize(target)

    ds = TensorDataset(
        torch.tensor(Xs, dtype=torch.float32),
        torch.tensor(Ys, dtype=torch.float32),
        torch.tensor(params, dtype=torch.float64),
    )
    n = len(ds)
    n_tr, n_va = int(0.7 * n), int(0.15 * n)
    tr, va, te = random_split(ds, [n_tr, n_va, n - n_tr - n_va],
                              generator=torch.Generator().manual_seed(42))

    # train/val loaders yield (x, y); the params column is only needed at test time
    def xy(batch):
        xs, ys, _ = zip(*batch)
        return torch.stack(xs), torch.stack(ys)

    tr_loader = DataLoader(tr, batch_size=args.batch_size, shuffle=True, collate_fn=xy)
    va_loader = DataLoader(va, batch_size=args.batch_size, collate_fn=xy)
    te_loader = DataLoader(te, batch_size=args.batch_size)

    tag = "Model_1_direct" if args.model == 1 else "Model_2_canonical_latent"
    logger.info("%s: predicting %s, %d inputs, %d epochs",
                tag, "latent z" if latent else "raw parameters", Xs.shape[1], args.epochs)

    model = build_mlp(Xs.shape[1])
    history = train(model, tr_loader, va_loader, args.epochs, args.lr, device)
    metrics = evaluate(model, te_loader, t_mu, t_sd, latent, device)

    torch.save(model.state_dict(), out_dir / f"{tag}_checkpoint.pt")
    (out_dir / f"{tag}_history.json").write_text(json.dumps(history, indent=2))
    (out_dir / f"{tag}_metrics.json").write_text(json.dumps(metrics, indent=2))

    logger.info("%s mean skill %.3f (1.0 = no better than the mean)", tag, metrics["mean_skill"])
    for k in SHORT:
        logger.info("   %-9s skill %.3f  rmse %.5f", k, metrics["param_skill"][k], metrics["param_rmse"][k])


if __name__ == "__main__":
    main()
