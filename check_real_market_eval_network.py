"""
Re-check MaskAware_Model_2_canonical_latent_metrics.json's real_market section.

run_real_market_eval.py bundles training (300 epochs) with a final real-market
repricing evaluation. Its reprice_surface() was fixed for the rank-2 rate/carry
bug (src/rank_conditioning.py, imported at the top of that file), but the metrics
file on disk is dated 2026-09-29 01:11 -- BEFORE that fix existed anywhere in this
session -- and the script was never re-run afterward. That means the "Network"
column on the site's 5-dev-date real-market table may still be pre-fix.

Retraining is unnecessary and wasteful: the bug is only in how prices are computed
FROM the network's output, not in the trained weights. This script reconstructs
the exact same normalisation statistics run_real_market_eval.py used (same data,
same seed, same mask sampling -- all deterministic), loads the EXISTING checkpoint,
and re-runs only the real-market repricing loop with the fix. If the numbers
change, it patches the metrics file in place; if they don't, it says so and
touches nothing.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import torch

import run_real_market_eval as E
from mentor_dh_pinn import params_v2 as P

SEED = 0
CHECKPOINT = ROOT / "outputs" / "real_eval" / "MaskAware_Model_2_canonical_latent_checkpoint.pt"
METRICS = ROOT / "outputs" / "real_eval" / "MaskAware_Model_2_canonical_latent_metrics.json"


def main() -> int:
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)

    prices, cond, params = E.load_synthetic(ROOT / "data" / "final_r2_clean_10000")
    z = np.stack([P.encode(r) for r in params])
    masks = E.sample_masks(len(prices), rng)

    X = np.concatenate([prices * masks, masks.astype(float), cond], axis=1)
    target = z  # Model 2 = canonical latent

    x_mu, x_sd = X.mean(0), np.where(X.std(0) > 0, X.std(0), 1.0)
    t_mu, t_sd = target.mean(0), np.where(target.std(0) > 0, target.std(0), 1.0)

    model = E.build_mlp(X.shape[1])
    model.load_state_dict(torch.load(CHECKPOINT, map_location="cpu"))
    model.eval()

    old = json.loads(METRICS.read_text())
    old_real = {r["date_id"]: r for r in old["real_market"]}

    from src.g2_r2r3 import frozen
    from src.r2_representation.real import build_real_surface
    from src.constraints import validate_parameters

    print(f"{'date':12s} {'old network%':>13s} {'new network%':>13s} {'changed?':>9s}")
    real_results = []
    any_changed = False
    for date_id in frozen.MARKET_DATES:
        s = build_real_surface(date_id)
        mk = np.asarray(s.mask, bool)
        mats = sorted(set(s.maturities))
        strikes = E.actual_strikes_for(date_id)
        feat = np.concatenate([
            np.asarray(s.prices, float) * mk,
            mk.astype(float),
            [mats[0], mats[1], s.rates[0], s.carries[0]],
        ])
        with torch.no_grad():
            raw = model(torch.tensor((feat - x_mu) / x_sd,
                                     dtype=torch.float32).unsqueeze(0)).numpy()[0]
        vec = raw * t_sd + t_mu
        vec = np.asarray(P.to_array(P.decode(vec)), float)

        repriced = E.reprice_surface(vec, s.spot, mats, s.rates, s.carries, strikes)
        market = np.asarray(s.prices, float)
        cmp_mask = mk & np.isfinite(strikes)
        err = repriced[cmp_mask] - market[cmp_mask]
        rmse = float(np.sqrt(np.mean(err ** 2)))
        rel = rmse / float(np.mean(np.abs(market[cmp_mask])))

        old_rel = old_real.get(date_id, {}).get("repricing_rmse_relative", float("nan"))
        changed = abs(old_rel - rel) > 1e-9
        any_changed = any_changed or changed
        print(f"{date_id:12s} {old_rel*100:12.2f}% {rel*100:12.2f}% {'YES' if changed else 'no':>9s}")

        real_results.append({
            "date_id": date_id,
            "usable_slots": int(cmp_mask.sum()),
            "repricing_rmse_normalized": rmse,
            "repricing_rmse_relative": rel,
            "priced": True,
            "parameters_valid": bool(validate_parameters(vec)["is_valid"]),
            "parameters": {n: float(v) for n, v in zip(E.SHORT, vec)},
        })

    print()
    if not any_changed:
        print("No change -- the pre-fix numbers already matched the corrected reprice. "
              "Metrics file left untouched.")
        return 0

    print("Numbers changed -- patching the real_market section of the metrics file.")
    old["real_market"] = real_results
    METRICS.write_text(json.dumps(old, indent=2))
    print(f"wrote {METRICS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
