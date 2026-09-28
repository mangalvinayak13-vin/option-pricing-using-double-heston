"""
Model 2 as the project actually specifies it: constraints AND differentiable repricing.

Earlier "Model 2" enforced structural constraints but had no repricing term, so it
was only half the specified model. This adds the other half: predicted parameters are
priced back through the differentiable Torch mirror and the price residual is part of
the loss.

    loss = (1 - w) * MSE(latent z) + w * MSE(repriced prices, observed prices)

The two terms disagree on purpose. The parameter term treats all ten coordinates as
equally important. The repricing term weights each coordinate by how much it actually
moves prices, so directions the surface barely constrains receive almost no gradient.
Under practical non-identifiability that is the interesting case: the repricing term
should improve price fit while making parameter recovery no better, and possibly worse,
because it stops trying to pin down directions the data does not determine.

Puts come from put-call parity on the same call prices, since the Torch mirror prices
calls only.
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
from torch.utils.data import DataLoader, TensorDataset, random_split

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from mentor_dh_pinn import params_v2 as P
from mentor_dh_pinn.torch_pricer import price_call
from src.r2_representation.contract import CANONICAL_SLOT_KEYS

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


def slot_geometry():
    """Per-slot log-moneyness, expiry rank index, and a put indicator."""
    lm = torch.tensor([k.target_log_moneyness for k in CANONICAL_SLOT_KEYS], dtype=torch.float64)
    rank = torch.tensor([k.expiry_rank - 1 for k in CANONICAL_SLOT_KEYS], dtype=torch.long)
    is_put = torch.tensor([k.option_type == "put" for k in CANONICAL_SLOT_KEYS], dtype=torch.bool)
    return lm, rank, is_put


def reprice_batch(params, cond, lm, rank, is_put, node_count):
    """Spot-normalized prices for the 20 canonical slots. Differentiable in params.

    params : (B, 10) canonical order
    cond   : (B, 4) = maturity rank1, maturity rank2, rate, carry
    """
    B = params.shape[0]
    strikes = SPOT * torch.exp(lm).to(params.dtype)             # (20,)
    strikes = strikes.unsqueeze(0).expand(B, -1)                # (B, 20)

    mats = torch.stack([cond[:, 0], cond[:, 1]], dim=1)         # (B, 2)
    tau = mats.gather(1, rank.unsqueeze(0).expand(B, -1))       # (B, 20)
    rate = cond[:, 2:3].expand(-1, 20)
    carry = cond[:, 3:4].expand(-1, 20)

    calls = price_call(params, SPOT, strikes, tau, rate, carry, node_count=node_count)

    # Put-call parity: P = C - S e^{-q tau} + K e^{-r tau}
    puts = calls - SPOT * torch.exp(-carry * tau) + strikes * torch.exp(-rate * tau)
    prices = torch.where(is_put.unsqueeze(0).expand(B, -1), puts, calls)
    return prices / SPOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price-weight", type=float, default=0.5,
                    help="w in (1-w)*param_loss + w*price_loss")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--nodes", type=int, default=32, help="Quadrature nodes during training")
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "repricing"))
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device("cpu")          # the Torch pricer runs in float64/complex128

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
    z_mu, z_sd = z.mean(0), np.where(z.std(0) > 0, z.std(0), 1.0)
    Xs, Zs = (X - x_mu) / x_sd, (z - z_mu) / z_sd

    ds = TensorDataset(
        torch.tensor(Xs, dtype=torch.float64),
        torch.tensor(Zs, dtype=torch.float64),
        torch.tensor(prices, dtype=torch.float64),
        torch.tensor(cond, dtype=torch.float64),
        torch.tensor(params, dtype=torch.float64),
    )
    n = len(ds)
    ntr, nva = int(0.7 * n), int(0.15 * n)
    tr, va, te = random_split(ds, [ntr, nva, n - ntr - nva],
                              generator=torch.Generator().manual_seed(42))
    tr_l = DataLoader(tr, batch_size=args.batch_size, shuffle=True)

    lm, rank, is_put = slot_geometry()
    z_mu_t = torch.tensor(z_mu); z_sd_t = torch.tensor(z_sd)

    model = build_mlp(Xs.shape[1]).to(torch.float64).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    w = args.price_weight

    print(f"price weight {w}, {args.nodes} nodes, {args.epochs} epochs")
    best, best_state = float("inf"), None

    for ep in range(args.epochs):
        model.train()
        agg_p = agg_pr = 0.0
        seen = 0
        for xb, zb, pb, cb, _ in tr_l:
            opt.zero_grad()
            out = model(xb)
            param_loss = ((out - zb) ** 2).mean()

            vec = torch.stack(P.decode(out * z_sd_t + z_mu_t), dim=-1)
            repriced = reprice_batch(vec, cb, lm, rank, is_put, args.nodes)
            good = torch.isfinite(repriced).all(dim=1)
            price_loss = (((repriced[good] - pb[good]) ** 2).mean()
                          if good.any() else torch.zeros((), dtype=torch.float64))

            # Price residuals are ~1e-2 while standardized z residuals are ~1, so the
            # price term is scaled up to contribute comparably rather than vanish.
            loss = (1 - w) * param_loss + w * price_loss * 1e3
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()

            agg_p += param_loss.item() * len(xb)
            agg_pr += price_loss.item() * len(xb)
            seen += len(xb)

        sched.step()
        if agg_p / seen < best:
            best = agg_p / seen
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        if (ep + 1) % 10 == 0:
            print(f"  epoch {ep+1}/{args.epochs}  param {agg_p/seen:.5f}  price {agg_pr/seen:.3e}")

    model.load_state_dict(best_state)

    # --- evaluate: parameter recovery AND price fit on the held-out split -------
    model.eval()
    idx = np.asarray(te.indices)
    with torch.no_grad():
        out = model(torch.tensor(Xs[idx], dtype=torch.float64))
        vec = torch.stack(P.decode(out * z_sd_t + z_mu_t), dim=-1)
        repriced = reprice_batch(vec, torch.tensor(cond[idx], dtype=torch.float64),
                                 lm, rank, is_put, 64).numpy()
    pred = vec.numpy()
    truth = params[idx]

    skill = {}
    for i, name in enumerate(SHORT):
        rmse = float(np.sqrt(np.mean((pred[:, i] - truth[:, i]) ** 2)))
        sd = float(np.std(truth[:, i]))
        skill[name] = rmse / sd if sd > 0 else float("nan")

    ok = np.isfinite(repriced).all(axis=1)
    price_rmse = float(np.sqrt(np.mean((repriced[ok] - prices[idx][ok]) ** 2)))

    metrics = {
        "price_weight": w,
        "mean_skill": float(np.mean(list(skill.values()))),
        "param_skill": skill,
        "test_price_rmse": price_rmse,
        "test_samples": int(ok.sum()),
    }
    (out_dir / f"repricing_w{w}_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(f"\nprice weight {w}:  mean skill {metrics['mean_skill']:.4f}   "
          f"test price RMSE {price_rmse:.3e}   (n={int(ok.sum())})")


if __name__ == "__main__":
    main()
