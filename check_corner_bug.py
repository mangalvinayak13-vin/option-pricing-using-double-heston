"""Does the flat-vol corner start actually reproduce the flat-BS fit when evaluated
through THIS script's own price_residuals function?"""
import warnings, sys, math
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
sys.path.insert(0, "src")
import numpy as np

import run_option_backtest as OB
from mentor_dh_pinn import params_v2 as P
from src.r2_representation.real import build_real_surface
from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS
from src.double_heston import price_double_heston_surface
from run_real_classical_fit import actual_strikes_for, reprice

date_id = "2026-07-22"    # the worst offender: floor 10.3% vs flat 2.6%
s = build_real_surface(date_id)
mk = np.asarray(s.mask, bool)
market = np.asarray(s.prices, float)
mats = sorted(set(s.maturities))
strikes = actual_strikes_for(date_id)
mk = mk & np.isfinite(strikes)
print(f"this script's mask: {mk.sum()} usable slots")

arrays = OB.surface_arrays(s)
print(f"OB.surface_arrays mask: {arrays['mask'].sum()} usable slots")
print(f"masks agree: {np.array_equal(mk, arrays['mask'])}")
print(f"strikes agree (where both finite): "
      f"{np.allclose(strikes[mk], arrays['strikes'][arrays['mask']])}")

sigma_flat = OB.flat_vol_fit(arrays)
flat_rel_via_OB = OB.flat_vol_error(arrays, sigma_flat)
print(f"\nsigma_flat = {sigma_flat:.4f}")
print(f"flat error via OB.flat_vol_error: {flat_rel_via_OB*100:.2f}%")

# Build the corner exactly as run_real_classical_fit.py does
corner = np.zeros(10)
corner[2] = corner[4] = math.log(sigma_flat ** 2)
corner[6] = corner[7] = -3.0
vec = np.asarray(P.to_array(P.decode(corner)), float)
print(f"\ndecoded corner parameters: {dict(zip(['ks','ts','ss','rs','v0s','kf','tf','sf','rf','v0f'], vec))}")

# price it with THIS script's reprice()
priced = reprice(corner, s.spot, mats, s.rates, s.carries, strikes)
err = priced[mk] - market[mk]
rmse = float(np.sqrt(np.mean(err**2)))
rel = rmse / float(np.mean(np.abs(market[mk])))
print(f"\ncorner priced via run_real_classical_fit.reprice(): relative error = {rel*100:.2f}%")
print(f"(compare: flat_bs reported by check_flat_vol_floor.py was 2.6%)")

# Also price DIRECTLY at the corner vector with the raw pricer, bypassing reprice()'s
# strike-matching, to see if there's a strike/slot mismatch inside reprice() itself.
print("\nsanity: does reprice() match a direct call to price_double_heston_surface?")
for rank in R2_EXPIRY_RANKS:
    idx = [i for i, k in enumerate(CANONICAL_SLOT_KEYS)
           if k.expiry_rank == rank and np.isfinite(strikes[i]) and mk[i]]
    if not idx:
        continue
    keys = [CANONICAL_SLOT_KEYS[i] for i in idx]
    direct = price_double_heston_surface(
        s.spot, np.array([strikes[i] for i in idx], float),
        np.full(len(keys), mats[rank - 1], float), s.rates[rank - 1], s.carries[rank - 1],
        [k.option_type for k in keys], vec, node_count=64,
    ) / s.spot
    via_reprice = priced[np.asarray(idx, int)]
    print(f"  rank {rank}: direct vs reprice match = {np.allclose(direct, via_reprice)}")
