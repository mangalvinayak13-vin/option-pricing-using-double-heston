"""
Mask-aware inverse models, and the first real-market evaluation in this project.

Why a separate script. Real R2 surfaces are incomplete: the five frozen NTPC
dates populate 11-19 of the 20 nominal slots, and the R2 contract forbids
filling a missing real quote with a model price. The earlier models take all 20
prices and have no way to express "this slot is absent", so they structurally
cannot consume a real surface. R2 is specified with explicit mask semantics, so
the fix is to feed the mask: 20 prices (absent -> 0) + 20 mask flags + 4
conditioning = 44 inputs. That is not imputation; it tells the network which
slots exist.

What can and cannot be measured on real data. NTPC's true Double Heston
parameters are unknown, so parameter recovery is undefined there. The only
available real-market measure is REPRICING: predict parameters, reprice through
the frozen production pricer, compare against the market prices on unmasked
slots. The project's central finding is precisely that good repricing does not
imply good recovery, so a good repricing number here must not be read as
successful calibration.

Repricing uses the target-moneyness grid the representation is defined on.
Real quotes are assigned to targets under a 0.05 log-moneyness gate, so strike
mismatch up to that gate is folded into the reported error.
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
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
for p in (str(SRC_ROOT), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from mentor_dh_pinn import params_v2 as P
from src.double_heston import price_double_heston_surface
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS
from src.rank_conditioning import rate_and_carry_for_rank

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]

# Slot counts actually observed on the five frozen NTPC dates.
REAL_COVERAGE = [11, 12, 18, 18, 19]


def build_mlp(input_dim: int, hidden=(384, 384, 384), output_dim=10) -> nn.Module:
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def load_synthetic(data_dir: Path):
    prices, cond, params = [], [], []
    with open(data_dir / "surfaces.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            if len(rec["prices"]) != 20:
                continue
            mats = sorted(set(rec["maturities"]))
            prices.append(rec["prices"])
            cond.append([mats[0], mats[1], rec["rates"][0], rec["carries"][0]])
            p = rec["metadata"]["parameters_canonical_order"]
            params.append([p[n] for n in P.CANONICAL])
    return (np.asarray(prices, float), np.asarray(cond, float), np.asarray(params, float))


def sample_masks(n: int, rng: np.random.Generator) -> np.ndarray:
    """Half complete surfaces, half at real-world coverage, so the model handles both."""
    masks = np.ones((n, 20), dtype=bool)
    incomplete = rng.random(n) < 0.5
    for i in np.flatnonzero(incomplete):
        keep = rng.choice(REAL_COVERAGE)
        drop = rng.choice(20, size=20 - keep, replace=False)
        masks[i, drop] = False
    return masks


def reprice_surface(vector: np.ndarray, spot: float, maturities, rates, carries,
                    actual_strikes: np.ndarray, node_count: int = 64) -> np.ndarray:
    """Spot-normalized prices on each slot's ACTUAL traded strike.

    Pricing at the nominal moneyness target instead would charge the model for the
    target-to-quote strike mismatch, which reaches 0.04 in log-moneyness and inflated
    an earlier version of this measurement by roughly a factor of three.
    """
    out = np.full(len(CANONICAL_SLOT_KEYS), np.nan, dtype=np.float64)
    for rank in R2_EXPIRY_RANKS:
        idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS)
               if k.expiry_rank == rank and np.isfinite(actual_strikes[i])]
        if not idx:
            continue
        keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
        strikes = np.array([actual_strikes[i] for i in idx], float)
        mats = np.full(len(keys), maturities[rank - 1], float)
        rate, carry = rate_and_carry_for_rank(rank, rates, carries)
        out[np.asarray(idx, int)] = price_double_heston_surface(
            spot, strikes, mats, rate, carry,
            [k.option_type for k in keys], vector, node_count=node_count,
        )
    return out / spot


def actual_strikes_for(date_id: str) -> np.ndarray:
    """Per-slot traded strike from the sealed audit, NaN where the slot is unusable."""
    from src.g2_r2r3 import market
    table = market.audit_date(date_id)["slot_table"]
    by_key = {
        (int(r.expiry_rank), round(float(r.target_log_moneyness), 6), str(r.option_type)):
            float(r.strike)
        for r in table.itertuples() if bool(r.usable)
    }
    return np.array([
        by_key.get((k.expiry_rank, round(k.target_log_moneyness, 6), k.option_type), np.nan)
        for k in CANONICAL_SLOT_KEYS
    ], float)


def train(model, tr, va, epochs, lr, device):
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    lossf = nn.MSELoss()
    best, best_state, best_ep = float("inf"), None, -1
    hist = {"train_loss": [], "val_loss": []}

    for ep in range(epochs):
        model.train()
        tot = 0.0
        for xb, yb in tr:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = lossf(model(xb), yb)
            loss.backward()
            opt.step()
            tot += loss.item() * len(xb)
        trl = tot / len(tr.dataset)

        model.eval()
        tot = 0.0
        with torch.no_grad():
            for xb, yb in va:
                xb, yb = xb.to(device), yb.to(device)
                tot += lossf(model(xb), yb).item() * len(xb)
        val = tot / len(va.dataset)

        sched.step()
        hist["train_loss"].append(trl)
        hist["val_loss"].append(val)
        if val < best:
            best, best_ep = val, ep + 1
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        if (ep + 1) % 50 == 0:
            logger.info("  epoch %d/%d train %.5f val %.5f", ep + 1, epochs, trl, val)

    model.load_state_dict(best_state)
    hist["best_val"], hist["best_epoch"] = best, best_ep
    logger.info("  best epoch %d (val %.5f)", best_ep, best)
    return hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=int, choices=[1, 2], required=True)
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "real_eval"))
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    latent = args.model == 2
    tag = f"MaskAware_Model_{args.model}_" + ("canonical_latent" if latent else "direct")

    prices, cond, params = load_synthetic(PROJECT_ROOT / "data" / "final_r2_clean_10000")
    z = np.stack([P.encode(r) for r in params])
    masks = sample_masks(len(prices), rng)

    X = np.concatenate([prices * masks, masks.astype(float), cond], axis=1)   # 44
    target = z if latent else params

    x_mu, x_sd = X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0)
    t_mu, t_sd = target.mean(0), np.where(target.std(0) > 0, target.std(0), 1.0)
    Xs, Ys = (X - x_mu) / x_sd, (target - t_mu) / t_sd

    ds = TensorDataset(torch.tensor(Xs, dtype=torch.float32),
                       torch.tensor(Ys, dtype=torch.float32))
    n = len(ds)
    ntr, nva = int(0.7 * n), int(0.15 * n)
    tr, va, te = random_split(ds, [ntr, nva, n - ntr - nva],
                              generator=torch.Generator().manual_seed(42))
    tr_l = DataLoader(tr, batch_size=args.batch_size, shuffle=True)
    va_l = DataLoader(va, batch_size=args.batch_size)

    logger.info("%s: %d inputs (20 prices + 20 mask + 4 conditioning)", tag, Xs.shape[1])
    model = build_mlp(Xs.shape[1])
    hist = train(model, tr_l, va_l, args.epochs, args.lr, device)

    # --- synthetic test: parameter recovery -------------------------------------
    model.eval()
    te_idx = np.asarray(te.indices)
    with torch.no_grad():
        pred = model(torch.tensor(Xs[te_idx], dtype=torch.float32).to(device)).cpu().numpy()
    pred = pred * t_sd + t_mu
    if latent:
        pred = np.stack([P.to_array(P.decode(r)) for r in pred])
    truth = params[te_idx]

    skill = {}
    for i, name in enumerate(SHORT):
        rmse = float(np.sqrt(np.mean((pred[:, i] - truth[:, i]) ** 2)))
        sd = float(np.std(truth[:, i]))
        skill[name] = rmse / sd if sd > 0 else float("nan")
    mean_skill = float(np.mean(list(skill.values())))
    logger.info("%s synthetic mean skill %.3f", tag, mean_skill)

    # --- real market: repricing only (no ground-truth parameters exist) ----------
    from src.g2_r2r3 import frozen
    from src.r2_representation.real import build_real_surface

    real_results = []
    for date_id in frozen.MARKET_DATES:
        s = build_real_surface(date_id)
        mk = np.asarray(s.mask, bool)
        mats = sorted(set(s.maturities))
        strikes = actual_strikes_for(date_id)
        feat = np.concatenate([
            np.asarray(s.prices, float) * mk,
            mk.astype(float),
            [mats[0], mats[1], s.rates[0], s.carries[0]],
        ])
        with torch.no_grad():
            raw = model(torch.tensor((feat - x_mu) / x_sd,
                                     dtype=torch.float32).unsqueeze(0).to(device)).cpu().numpy()[0]
        vec = raw * t_sd + t_mu
        if latent:
            vec = np.asarray(P.to_array(P.decode(vec)), float)

        try:
            repriced = reprice_surface(vec, s.spot, mats, s.rates, s.carries, strikes)
            market = np.asarray(s.prices, float)
            cmp_mask = mk & np.isfinite(strikes)     # need the traded strike to compare
            err = repriced[cmp_mask] - market[cmp_mask]
            mk = cmp_mask
            rmse = float(np.sqrt(np.mean(err ** 2)))
            # Relative to the mean observed price, so it is readable as a percentage.
            rel = rmse / float(np.mean(np.abs(market[mk])))
            priced_ok = True
        except Exception as exc:
            logger.warning("%s repricing failed: %s", date_id, exc)
            rmse, rel, priced_ok = float("nan"), float("nan"), False

        from src.constraints import validate_parameters
        real_results.append({
            "date_id": date_id,
            "usable_slots": int(mk.sum()),
            "repricing_rmse_normalized": rmse,
            "repricing_rmse_relative": rel,
            "priced": priced_ok,
            "parameters_valid": bool(validate_parameters(vec)["is_valid"]),
            "parameters": {n: float(v) for n, v in zip(SHORT, vec)},
        })
        logger.info("  %s  slots %2d/20  repricing RMSE %.6f (%.1f%% of mean price)  valid=%s",
                    date_id, int(mk.sum()), rmse, rel * 100,
                    real_results[-1]["parameters_valid"])

    metrics = {
        "tag": tag,
        "inputs": int(Xs.shape[1]),
        "synthetic_mean_skill": mean_skill,
        "synthetic_param_skill": skill,
        "synthetic_test_samples": int(len(truth)),
        "real_market": real_results,
        "real_market_caveat": (
            "Repricing only. NTPC's true parameters are unknown, so parameter recovery "
            "is undefined on real data. Good repricing does not imply recovery."
        ),
    }
    (out_dir / f"{tag}_metrics.json").write_text(json.dumps(metrics, indent=2))
    (out_dir / f"{tag}_history.json").write_text(json.dumps(hist, indent=2))
    torch.save(model.state_dict(), out_dir / f"{tag}_checkpoint.pt")
    logger.info("wrote %s", out_dir / f"{tag}_metrics.json")


if __name__ == "__main__":
    main()
