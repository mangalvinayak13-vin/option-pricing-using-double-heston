"""
G8 evaluation: the frozen models against real dates they have never seen.

The earlier real-market run used the five development dates, whose own metadata
marks them excluded from G8. This is the actual held-out test: eight Wednesdays
after the development window, downloaded and audited through the same sealed
quote-selection contract.

For each date it reports the network's repricing error and, alongside it, the
best fit the Double Heston model class can reach on that same surface. The gap
between them is the part attributable to the network; the floor is the part
attributable to the model.

Only repricing is measurable. NTPC's true parameters are unknown on any real
date, so parameter recovery is undefined here.
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
from scipy.optimize import least_squares

PROJECT_ROOT = Path(__file__).resolve().parent
for p in (str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

warnings.filterwarnings("ignore")

from mentor_dh_pinn import params_v2 as P
from src.double_heston import price_double_heston_surface
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS
from src import g8_evaluation as G8

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SHORT = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
         "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]
LATENT_BOX = 8.0
REAL_COVERAGE = [11, 12, 18, 18, 19]


def build_mlp(input_dim, hidden=(384, 384, 384), output_dim=10):
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def training_statistics(seed: int = 0):
    """Reproduce the exact normalization the mask-aware model was trained under.

    run_real_market_eval.py derives these from the dataset and a seeded mask draw
    rather than saving them, so they are rebuilt here with the same seed. If they
    drifted, every G8 prediction would be silently wrong, so the mask draw and
    ordering below must stay identical to that script.
    """
    rng = np.random.default_rng(seed)
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

    masks = np.ones((len(prices), 20), dtype=bool)
    incomplete = rng.random(len(prices)) < 0.5
    for i in np.flatnonzero(incomplete):
        keep = rng.choice(REAL_COVERAGE)
        masks[i, rng.choice(20, size=20 - keep, replace=False)] = False

    X = np.concatenate([prices * masks, masks.astype(float), cond], axis=1)
    x_mu, x_sd = X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0)
    t_mu, t_sd = z.mean(0), np.where(z.std(0) > 0, z.std(0), 1.0)
    return x_mu, x_sd, t_mu, t_sd, X.shape[1]


def reprice(vector, spot, maturities, rates, carries, strikes):
    out = np.full(len(CANONICAL_SLOT_KEYS), np.nan)
    for rank in R2_EXPIRY_RANKS:
        idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS)
               if k.expiry_rank == rank and np.isfinite(strikes[i])]
        if not idx:
            continue
        keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
        out[np.asarray(idx, int)] = price_double_heston_surface(
            spot, np.array([strikes[i] for i in idx], float),
            np.full(len(keys), maturities[rank - 1], float),
            rates[rank - 1], carries[rank - 1],
            [k.option_type for k in keys], vector, node_count=64,
        )
    return out / spot


def best_possible_fit(market, mask, spot, maturities, rates, carries, strikes, rng,
                      starts=12):
    """Least-squares floor: the closest any Double Heston fit gets to this surface."""
    lo, hi = np.full(10, -LATENT_BOX), np.full(10, LATENT_BOX)

    def residuals(z):
        try:
            got = reprice(np.asarray(P.to_array(P.decode(z)), float),
                          spot, maturities, rates, carries, strikes)[mask] - market[mask]
            return got if np.isfinite(got).all() else np.full(int(mask.sum()), 1e3)
        except Exception:
            return np.full(int(mask.sum()), 1e3)

    best_cost, best_z = np.inf, None
    for _ in range(starts):
        z0 = np.clip(rng.normal(0, 1, 10), -LATENT_BOX + 1, LATENT_BOX - 1)
        try:
            sol = least_squares(residuals, z0, bounds=(lo, hi), method="trf", max_nfev=2000)
        except Exception:
            continue
        if sol.cost < best_cost:
            best_cost, best_z = sol.cost, sol.x

    if best_z is None:
        return np.nan
    return float(np.sqrt(np.mean(residuals(best_z) ** 2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default=str(
        PROJECT_ROOT / "outputs" / "real_eval" /
        "MaskAware_Model_2_canonical_latent_checkpoint.pt"))
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "g8"))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    x_mu, x_sd, t_mu, t_sd, in_dim = training_statistics()
    model = build_mlp(in_dim)
    model.load_state_dict(torch.load(args.checkpoint, map_location="cpu"))
    model.eval()
    logger.info("loaded %s (%d inputs)", Path(args.checkpoint).name, in_dim)

    rate_observation = G8.register_g8_dates()
    logger.info("G8 rate observation carried forward from %s", rate_observation)

    from src.constraints import validate_parameters

    rows = []
    for date_id in G8.G8_CANDIDATE_DATES:
        try:
            s = G8.build_g8_surface(date_id)
        except Exception as exc:
            logger.warning("%s skipped: %s", date_id, exc)
            continue

        mk = np.asarray(s.mask, bool)
        strikes = np.array(
            [v if v is not None else np.nan
             for v in s.metadata["provenance"]["actual_strikes"]], float)
        mk = mk & np.isfinite(strikes)
        market = np.asarray(s.prices, float)
        mats = sorted(set(s.maturities))

        feat = np.concatenate([
            np.asarray(s.prices, float) * np.asarray(s.mask, bool),
            np.asarray(s.mask, bool).astype(float),
            [mats[0], mats[1], s.rates[0], s.carries[0]],
        ])
        with torch.no_grad():
            raw = model(torch.tensor((feat - x_mu) / x_sd,
                                     dtype=torch.float32).unsqueeze(0)).numpy()[0]
        vector = np.asarray(P.to_array(P.decode(raw * t_sd + t_mu)), float)

        net = reprice(vector, s.spot, mats, s.rates, s.carries, strikes)
        net_rmse = float(np.sqrt(np.mean((net[mk] - market[mk]) ** 2)))
        scale = float(np.mean(np.abs(market[mk])))
        floor = best_possible_fit(market, mk, s.spot, mats, s.rates, s.carries,
                                  strikes, rng)

        rows.append({
            "date_id": date_id,
            "usable_slots": int(mk.sum()),
            "spot": s.spot,
            "network_rmse": net_rmse,
            "network_relative": net_rmse / scale,
            "best_fit_rmse": floor,
            "best_fit_relative": floor / scale,
            "gap_pp": (net_rmse - floor) / scale * 100,
            "parameters_valid": bool(validate_parameters(vector)["is_valid"]),
            "rate_carry_forward_from": rate_observation,
        })
        logger.info("  %s  slots %2d/20  network %5.1f%%  floor %5.1f%%  gap %+5.1fpp",
                    date_id, int(mk.sum()), rows[-1]["network_relative"] * 100,
                    rows[-1]["best_fit_relative"] * 100, rows[-1]["gap_pp"])

    net_rel = np.array([r["network_relative"] for r in rows])
    floor_rel = np.array([r["best_fit_relative"] for r in rows])

    report = {
        "milestone": "G8_FROZEN_REAL_MARKET_EVALUATION",
        "held_out": True,
        "dates_evaluated": len(rows),
        "rate_observation_carried_forward_from": rate_observation,
        "median_network_relative": float(np.median(net_rel)),
        "median_best_fit_relative": float(np.median(floor_rel)),
        "median_gap_pp": float(np.median(net_rel - floor_rel) * 100),
        "all_parameters_valid": bool(all(r["parameters_valid"] for r in rows)),
        "rows": rows,
        "caveat": (
            "Repricing only; NTPC's true parameters are unknown so recovery is "
            "undefined on real data. The rate is carried forward from the latest "
            "sealed RBI observation, which shifts only the discount factor because "
            "the forward is futures-implied."
        ),
    }
    (out_dir / "g8_evaluation.json").write_text(json.dumps(report, indent=2))

    logger.info("")
    logger.info("G8 HELD-OUT EVALUATION on %d dates", len(rows))
    logger.info("  median network repricing : %.1f%%", report["median_network_relative"] * 100)
    logger.info("  median model-class floor : %.1f%%", report["median_best_fit_relative"] * 100)
    logger.info("  median gap               : %+.1fpp", report["median_gap_pp"])
    logger.info("  all parameter sets valid : %s", report["all_parameters_valid"])


if __name__ == "__main__":
    main()
