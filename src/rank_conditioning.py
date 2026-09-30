"""
Correct per-rank rate/carry/maturity lookup from an R2 surface's flat per-slot arrays.

R2Surface stores maturities, rates and carries as 20-element arrays, one entry per
CANONICAL_SLOT_KEYS slot, constant within a rank and replicated across every slot of
that rank. CANONICAL_SLOT_KEYS is laid out in five-slot blocks by rank: indices 0-4 are
rank 1 calls, 5-9 are rank 2 calls, 10-14 rank 1 puts, 15-19 rank 2 puts.

Every reprice() in this project's real-market scripts (run_market_wide.py,
run_g8_eval.py, run_market_ambiguity.py, run_real_classical_fit.py) indexed these
per-slot arrays as `rates[rank - 1]`, `carries[rank - 1]` -- treating them as if they
were already a 2-element per-rank array. They are not. `rates[0]` happens to land on a
rank-1 slot (correct by coincidence), but `rates[1]` for rank=2 lands on slot index 1,
which is STILL a rank-1 slot (moneyness -0.05, still rank 1) -- so every rank-2 price
in this project's real-market repricing was computed with the RANK-1 rate and carry.

This was found by a sanity check that should be mechanically guaranteed: a Double
Heston parameter vector at the point where it degenerates to flat Black-Scholes
(v0 = theta, vol-of-variance ~ 0, correlation = 0) must reprice a real surface
identically to a fitted flat Black-Scholes volatility, at every maturity. It matched
exactly at the short (rank 1) maturity and was off by several points at the longer
(rank 2) one -- the fingerprint of a wrong conditioning input at rank 2 specifically,
not a modelling limitation.

`maturities` was NOT affected: callers already deduplicate it correctly via
`sorted(set(surface.maturities))`, and rank 2's maturity is always the larger value,
so that ordering happens to match rank order. rates and carries were passed as the raw
undeduplicated per-slot arrays with no such deduplication.
"""

from __future__ import annotations

import numpy as np

from src.r2_representation.contract import CANONICAL_SLOT_KEYS, R2_EXPIRY_RANKS

# The first slot index belonging to each rank, computed once from the canonical layout
# rather than hard-coded, so a change to the slot ordering cannot silently reintroduce
# this bug.
_FIRST_SLOT_OF_RANK = {
    rank: next(i for i, k in enumerate(CANONICAL_SLOT_KEYS) if k.expiry_rank == rank)
    for rank in R2_EXPIRY_RANKS
}


def rate_and_carry_for_rank(rank: int, rates, carries) -> tuple[float, float]:
    """The correct (rate, carry) for `rank` from a surface's per-slot rates/carries."""
    i = _FIRST_SLOT_OF_RANK[rank]
    return float(rates[i]), float(carries[i])
