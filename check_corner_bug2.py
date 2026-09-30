import warnings, sys, math
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
sys.path.insert(0, "src")
import numpy as np

import run_option_backtest as OB
from mentor_dh_pinn import params_v2 as P
from src.r2_representation.real import build_real_surface
from src.r2_representation.contract import CANONICAL_SLOT_KEYS
from run_real_classical_fit import actual_strikes_for, reprice

date_id = "2026-07-22"
s = build_real_surface(date_id)
mk = np.asarray(s.mask, bool)
market = np.asarray(s.prices, float)
mats = sorted(set(s.maturities))
strikes = actual_strikes_for(date_id)
mk = mk & np.isfinite(strikes)

arrays = OB.surface_arrays(s)
sigma_flat = OB.flat_vol_fit(arrays)

# flat-BS priced values, via OB's own black_scholes
flat_priced = np.full(20, np.nan)
idx = np.flatnonzero(mk)
for i in idx:
    flat_priced[i] = OB.black_scholes(s.spot, strikes[i], arrays["T"][i], arrays["r"][i],
                                      arrays["q"][i], sigma_flat, arrays["is_call"][i]) / s.spot

corner = np.zeros(10)
corner[2] = corner[4] = math.log(sigma_flat ** 2)
corner[6] = corner[7] = -3.0
dh_priced = reprice(corner, s.spot, mats, s.rates, s.carries, strikes)

print(f"spot={s.spot}  sigma_flat={sigma_flat:.4f}  mats={mats}  rates={s.rates[:1]}  carries={s.carries[:1]}")
print(f"{'slot':4s} {'rank':4s} {'strike':>9s} {'market':>10s} {'flat_BS':>10s} {'DH_corner':>10s} {'flat_err':>9s} {'DH_err':>9s}")
for i in idx:
    k = CANONICAL_SLOT_KEYS[i]
    print(f"{i:4d} {k.expiry_rank:4d} {strikes[i]:9.1f} {market[i]:10.6f} {flat_priced[i]:10.6f} "
          f"{dh_priced[i]:10.6f} {(flat_priced[i]-market[i]):+9.5f} {(dh_priced[i]-market[i]):+9.5f}")
