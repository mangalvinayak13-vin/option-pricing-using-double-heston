"""
Shared pieces of the mask-aware inverse model.

run_real_market_eval.py trains it; run_g8_eval.py and run_market_wide.py apply it to real
surfaces. The last two each carried their own copy of the network definition and of the
normalisation statistics, and the statistics are not stored with the checkpoint -- they
are rebuilt from the frozen dataset and a seeded random mask draw. Two copies of code
that must match to the last bit, in scripts run months apart, is how a model ends up
silently mis-normalised, so there is now exactly one.

The normalisation contract, which the trained checkpoint depends on:
  * input vector = 20 prices (masked slots zeroed) + 20 mask flags + 4 conditioning = 44
  * about half of training surfaces are masked to a real-world coverage of 11-19 slots,
    drawn with numpy default_rng(seed), one uniform draw per surface, then one
    choice/choice pair per masked surface, in dataset order
  * targets are the canonical latent z from mentor_dh_pinn.params_v2

Changing the draw order, the coverage list, or the dataset changes these statistics and
invalidates the checkpoint without any error. tests/ pins them.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from torch import nn

from mentor_dh_pinn import params_v2 as P

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Slot counts actually observed on the five frozen NTPC development dates.
REAL_COVERAGE = [11, 12, 18, 18, 19]


def build_mlp(input_dim: int, hidden=(384, 384, 384), output_dim: int = 10) -> nn.Module:
    layers, prev = [], input_dim
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(0.1)]
        prev = h
    layers.append(nn.Linear(prev, output_dim))
    return nn.Sequential(*layers)


def training_statistics(seed: int = 0):
    """Normalisation the mask-aware checkpoint was trained under.

    Returns (x_mean, x_std, latent_mean, latent_std, input_dim).
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
    return (X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0),
            z.mean(0), np.where(z.std(0) > 0, z.std(0), 1.0), X.shape[1])
