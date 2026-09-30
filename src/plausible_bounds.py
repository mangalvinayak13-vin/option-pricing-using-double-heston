"""
Physical-parameter bounds for optimisers working in the canonical latent space.

Why this exists. Bounding the LATENT coordinate z independently, one axis at a time, does
not bound the PHYSICAL parameters it decodes to, because several are coupled products or
shares of more than one z coordinate. kappa_fast = kappa_slow * (1 + exp(z1)): bounding z0
and z1 each to +/-8 independently still permits kappa_fast up to 8.9 million, against a
training maximum of 10. On clean synthetic surfaces (full 20 slots, no noise, strong price
curvature) an optimiser rarely wanders that far and this goes unnoticed. On real surfaces --
partial, noisy, with genuinely flatter directions -- it does not go unnoticed: the optimiser
runs a poorly-constrained direction straight to the box edge, and every downstream number
inherits a physically meaningless value in that coordinate.

This was found by checking three already-computed real-market results against a trivial
baseline: a single fitted Black-Scholes volatility beat the reported "best possible Double
Heston fit" on 10 of 13 real NTPC dates. Double Heston nests Black-Scholes (both
vol-of-variance terms to zero recovers it exactly), so a true optimum can never lose to the
nested case. Its optimiser was not finding the optimum -- it was finding a box corner.

The fix bounds the DECODED physical parameters directly, with a soft penalty rather than a
hard constraint, so an optimiser under real, noisy, partial data can still explore the
plausible region freely but pays an increasing cost for leaving it. The bound itself is
derived from the training set's own observed range, not chosen by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mentor_dh_pinn import params_v2 as P

PARAM_NAMES = ["kappa_s", "theta_s", "sigma_s", "rho_s", "v0_s",
               "kappa_f", "theta_f", "sigma_f", "rho_f", "v0_f"]


def training_parameter_stats(margin: float = 2.0):
    """(spread, phys_lo, phys_hi) from the 10,000 training parameter vectors.

    `margin` widens the observed [min, max] by that multiple of its own width on each
    side. margin=2.0 (the default) means a parameter observed in [a, b] is allowed out
    to [a - 2(b-a), b + 2(b-a)] before the penalty engages -- generous enough that a
    real surface with a genuinely different volatility regime is not falsely penalised,
    while still keeping kappa_fast, say, under about 30 instead of unbounded.
    """
    vals = []
    with open(PROJECT_ROOT / "data" / "final_r2_clean_10000" / "surfaces.jsonl") as f:
        for line in f:
            p = json.loads(line)["metadata"]["parameters_canonical_order"]
            vals.append([p[n] for n in P.CANONICAL])
    arr = np.asarray(vals, float)
    lo, hi = arr.min(axis=0), arr.max(axis=0)
    pad = (hi - lo) * margin
    return arr.std(axis=0), lo - pad, hi + pad


def near_bound_parameters(vector: np.ndarray, phys_lo: np.ndarray, phys_hi: np.ndarray,
                          rel_tol: float = 0.03) -> list[str]:
    """Which parameters, if any, sit within `rel_tol` of their physical bound.

    A fit landing here is not a fit that failed; it is telling you something. If the
    optimiser pushes a coordinate to the edge of the plausible region and the penalty
    is the only thing stopping it, the price data alone has no preference for any
    finite value there -- a genuinely unconstrained direction, not an artefact of a
    badly drawn box (the bound itself came from the training set, not a guess) and not
    a solver failure. Reported explicitly so it is never averaged away into a distance
    number a reader would have no way to interpret.
    """
    width = phys_hi - phys_lo
    near_lo = (vector - phys_lo) < rel_tol * width
    near_hi = (phys_hi - vector) < rel_tol * width
    return [n for n, lo, hi in zip(PARAM_NAMES, near_lo, near_hi) if lo or hi]


def penalty_residuals(vector: np.ndarray, phys_lo: np.ndarray, phys_hi: np.ndarray,
                      spread: np.ndarray, weight: float = 3.0) -> np.ndarray:
    """Extra residual entries penalising physical parameters outside [phys_lo, phys_hi].

    Zero when every parameter is inside its bound; grows linearly, scaled by that
    parameter's own training spread so no single coordinate dominates by unit choice
    alone, past it. Append to a price-residual vector before calling least_squares:
    the optimiser then pays an increasing cost for leaving the plausible region instead
    of being hard-stopped at an arbitrary box edge, so it still finds the best fit it
    can within the region rather than freezing on its boundary.
    """
    below = np.clip((phys_lo - vector) / spread, 0, None)
    above = np.clip((vector - phys_hi) / spread, 0, None)
    return weight * (below + above)
