"""Does trf actually converge, or exhaust max_nfev on every start? Times it too."""
import warnings, sys, time
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
sys.path.insert(0, "src")
import numpy as np
from scipy.optimize import least_squares

from mentor_dh_pinn import params_v2 as P
from src.plausible_bounds import training_parameter_stats, penalty_residuals
from src.g8_evaluation import register_g8_dates, build_g8_surface, G8_CANDIDATE_DATES
from src.g2_r2r3 import market
from run_market_ambiguity import reprice, NUMERIC_BOX

register_g8_dates()
market.TICKER = "RELIANCE"
report = market.audit_date("2026-07-02")
s = build_g8_surface("2026-07-02", report)
strikes = np.array([v if v is not None else np.nan
                    for v in s.metadata["provenance"]["actual_strikes"]], float)
mask = np.asarray(s.mask, bool) & np.isfinite(strikes)
observed = np.asarray(s.prices, float)
mats = sorted(set(s.maturities))

spread, phys_lo, phys_hi = training_parameter_stats(margin=2.0)
box_lo, box_hi = np.full(10, -NUMERIC_BOX), np.full(10, NUMERIC_BOX)


def price_residuals(z):
    try:
        got = reprice(np.asarray(P.to_array(P.decode(z)), float), s.spot, mats,
                      s.rates, s.carries, strikes)
        out = got[mask] - observed[mask]
        return out if np.isfinite(out).all() else np.full(int(mask.sum()), 1e3)
    except Exception:
        return np.full(int(mask.sum()), 1e3)


def residuals(z):
    vector = np.asarray(P.to_array(P.decode(z)), float)
    penalty = penalty_residuals(vector, phys_lo, phys_hi, spread)
    return np.concatenate([price_residuals(z), penalty])


rng = np.random.default_rng(0)
print("status codes: 0=max_nfev hit (no convergence), 1-4=genuine convergence")
print()
for i in range(8):
    z0 = rng.uniform(np.clip(phys_lo, box_lo, box_hi), np.clip(phys_hi, box_lo, box_hi))
    t0 = time.time()
    sol = least_squares(residuals, z0, bounds=(box_lo, box_hi), method="trf", max_nfev=1200)
    dt = time.time() - t0
    print(f"  start {i}: status={sol.status}  nfev={sol.nfev:5d}  "
          f"cost={sol.cost:.3e}  time={dt:.2f}s")
