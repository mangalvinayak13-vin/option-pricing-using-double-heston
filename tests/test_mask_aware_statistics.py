"""
Pin the mask-aware model's normalisation statistics.

The trained checkpoint does not store them; they are rebuilt from the frozen dataset and a
seeded random mask draw. If the draw order, the coverage list, or the dataset changes,
the rebuilt statistics change, the checkpoint is fed inputs on the wrong scale, and every
downstream number is silently wrong -- no exception, no warning.

The fingerprint below was taken from the statistics that produced the reported G8 and
market-wide results. If this test fails, do not update the constant to make it pass:
either restore whatever changed, or retrain the model and re-derive the fingerprint
deliberately.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from src import mask_aware

FINGERPRINT = "5ddeedb03a2e020b618f89bddbbb4636e2adfe84a252ca1dea46b0da0a880fe9"


def _fingerprint(stats) -> str:
    return hashlib.sha256(
        b"".join(np.ascontiguousarray(a, dtype=np.float64).tobytes() for a in stats[:4])
    ).hexdigest()


def test_statistics_match_the_ones_the_checkpoint_was_trained_under():
    assert _fingerprint(mask_aware.training_statistics()) == FINGERPRINT


def test_input_width_is_prices_plus_mask_plus_conditioning():
    assert mask_aware.training_statistics()[4] == 44


def test_statistics_are_deterministic_for_a_given_seed():
    a, b = mask_aware.training_statistics(seed=0), mask_aware.training_statistics(seed=0)
    assert all(np.array_equal(x, y) for x, y in zip(a[:4], b[:4]))


def test_a_different_seed_changes_them():
    """Guards against the seed being ignored, which would make the pin meaningless."""
    a, b = mask_aware.training_statistics(seed=0), mask_aware.training_statistics(seed=1)
    assert not np.array_equal(a[0], b[0])
