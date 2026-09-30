"""
Regression tests for the rank-2 rate/carry bug and the physical-bound penalty.

R2Surface stores rates and carries per SLOT (20 entries, constant within an expiry
rank). Every real-market reprice() once looked them up as rates[rank - 1], which for
rank 2 lands on slot 1 -- still a rank-1 slot -- so every longer-dated leg was priced
with the shorter expiry's rate and carry. These tests fail on that old lookup: they
move one rank's rates and check that only that rank's prices move.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from mentor_dh_pinn import params_v2 as P
from src.plausible_bounds import penalty_residuals
from src.r2_representation.contract import CANONICAL_SLOT_KEYS
from src.rank_conditioning import _FIRST_SLOT_OF_RANK, rate_and_carry_for_rank

RANK = np.array([k.expiry_rank for k in CANONICAL_SLOT_KEYS])


def test_first_slot_of_each_rank_belongs_to_that_rank():
    for rank, i in _FIRST_SLOT_OF_RANK.items():
        assert CANONICAL_SLOT_KEYS[i].expiry_rank == rank
        assert i == int(np.flatnonzero(RANK == rank)[0])


def test_helper_returns_each_ranks_own_rate_and_carry():
    rates = np.where(RANK == 1, 0.05, 0.09)
    carries = np.where(RANK == 1, 0.01, -0.03)
    assert rate_and_carry_for_rank(1, rates, carries) == (0.05, 0.01)
    assert rate_and_carry_for_rank(2, rates, carries) == (0.09, -0.03)


def _repricer(name):
    if name == "run_market_wide":
        import run_market_wide as m
        return m.reprice
    if name == "run_g8_eval":
        import run_g8_eval as m
        return m.reprice
    if name == "run_market_ambiguity":
        import run_market_ambiguity as m
        return m.reprice
    if name == "run_real_market_eval":
        import run_real_market_eval as m
        return m.reprice_surface
    if name == "run_real_classical_fit":
        import run_real_classical_fit as m
        return lambda vec, *rest: m.reprice(P.encode(vec), *rest)  # takes latent z
    raise ValueError(name)


@pytest.mark.parametrize("name", ["run_market_wide", "run_g8_eval", "run_market_ambiguity",
                                  "run_real_market_eval", "run_real_classical_fit"])
def test_each_rank_is_priced_with_its_own_rate_and_carry(name):
    reprice = _repricer(name)
    spot = 100.0
    strikes = spot * np.exp([k.target_log_moneyness for k in CANONICAL_SLOT_KEYS])
    mats = [30 / 365, 90 / 365]
    vector = np.asarray(P.to_array(P.decode(np.zeros(10))), float)
    base_r, base_q = np.full(20, 0.05), np.zeros(20)
    p0 = reprice(vector, spot, mats, base_r, base_q, strikes)

    for field in ("rate", "carry"):
        for moved in (1, 2):
            r = np.where(RANK == moved, 0.10, 0.05) if field == "rate" else base_r
            q = np.where(RANK == moved, 0.04, 0.0) if field == "carry" else base_q
            p = reprice(vector, spot, mats, r, q, strikes)
            still = RANK != moved
            np.testing.assert_allclose(
                p[still], p0[still], rtol=0, atol=1e-12,
                err_msg=f"{name}: changing rank-{moved} {field} moved the other rank's prices")
            assert not np.allclose(p[~still], p0[~still]), \
                f"{name}: changing rank-{moved} {field} did not move rank-{moved} prices"


def test_penalty_is_zero_inside_bounds_and_linear_outside():
    lo, hi, spread = np.zeros(10), np.ones(10), np.full(10, 0.5)
    assert np.all(penalty_residuals(np.full(10, 0.5), lo, hi, spread) == 0)
    vec = np.full(10, 0.5)
    vec[0], vec[3] = 2.0, -1.0
    out = penalty_residuals(vec, lo, hi, spread, weight=3.0)
    assert out[0] == pytest.approx(3.0 * (2.0 - 1.0) / 0.5)
    assert out[3] == pytest.approx(3.0 * (0.0 - -1.0) / 0.5)
    assert np.all(np.delete(out, [0, 3]) == 0)
