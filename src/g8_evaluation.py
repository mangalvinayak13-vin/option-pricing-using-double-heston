"""
G8: frozen real-market evaluation on dates never used in development.

The five dates in ``frozen.MARKET_DATES`` are development dates -- their own
metadata carries ``development_date_excluded_from_g8: True``. Evaluating on them
is not a held-out test. G8 is the separately controlled milestone that supplies
untouched dates.

This module deliberately does NOT extend the sealed development contract. It
registers its own raw root, reuses the sealed audit and quote-selection logic
unchanged (``g2_r2r3.market.audit_date``), and builds surfaces labelled as G8 so
they can never be confused with development ones.

Candidate dates are Wednesdays after the July development window. Wednesday
matches the development cadence, and any date that is a holiday, lacks NTPC
futures support, or fails the R2 construction contract is dropped with its reason
recorded rather than patched.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.g2_r2r3 import frozen, market
from src.r2_representation.contract import CANONICAL_SLOT_KEYS
from src.r2_representation.surface import R2Surface

logger = logging.getLogger(__name__)

G8_RAW_ROOT = "market_data_audit/g8/raw/nse"
SOURCE_G8 = "REAL_NSE_G8_HELD_OUT"

# Wednesdays after the last development date (2026-07-29), through mid-September.
# Kept well clear of the development window so there is no overlap to argue about.
G8_CANDIDATE_DATES: tuple[str, ...] = (
    "2026-08-05", "2026-08-12", "2026-08-19", "2026-08-26",
    "2026-09-02", "2026-09-09", "2026-09-16", "2026-09-23",
)


def register_g8_dates(dates: tuple[str, ...] = G8_CANDIDATE_DATES) -> str:
    """Point the sealed audit at the G8 raw root and a rate observation.

    ``market.audit_date`` looks two things up by date: the raw root, and the
    risk-free rate observation. ``frozen.MARKET_DATES`` -- the development list --
    is deliberately left alone.

    On the rate. Only two hash-sealed RBI observations exist (2026-07-01 and
    2026-07-15), both inside the development window, and an RBI yield must not be
    invented. The sealed contract anticipates this: it permits a new date to carry
    forward an observation dated on or before the valuation date, and flags the
    result via ``rate_carry_forward``. So G8 dates carry forward the latest
    available observation, and each surface records that it did.

    Why the approximation is small here rather than merely convenient: the forward
    is futures-implied, and ``market`` derives carry as
    ``rate - log(forward/spot)/maturity``. Any assumed rate is therefore absorbed
    by carry, leaving the forward pinned by the futures market. The rate survives
    only in the discount factor, where being wrong by 50bp over a 0.1-year maturity
    shifts prices by about 0.05% -- two orders of magnitude below the repricing
    errors being measured. Returns the observation date used.
    """
    latest = max(frozen.RATE_OBSERVATIONS)
    for date_id in dates:
        if date_id in frozen.MARKET_DATES:
            raise ValueError(f"{date_id} is a development date; it cannot be used for G8")
        if date.fromisoformat(latest) > date.fromisoformat(date_id):
            raise ValueError(
                f"no rate observation on or before {date_id}; latest is {latest}"
            )
        frozen.MARKET_RAW_ROOTS[date_id] = G8_RAW_ROOT
        frozen.RATE_SOURCE_BY_VALUATION[date_id] = latest
    return latest


def build_g8_surface(date_id: str, report: dict[str, Any] | None = None) -> R2Surface:
    """Build one masked G8 surface using the sealed quote-selection contract.

    Mirrors ``r2_representation.real.build_real_surface`` but without its
    development-date gate, and labels the result as held-out.
    """
    report = report if report is not None else market.audit_date(date_id)
    if not report.get("constructible", False):
        raise ValueError(
            f"{date_id} is not R2-constructible: {report.get('hard_failure', 'no R2 support')}"
        )

    details = sorted(report["expiry_details"], key=lambda item: item["rank"])
    if len(details) < 2:
        raise ValueError(f"{date_id} has {len(details)} eligible expiry ranks, needs 2")
    selected = details[:2]
    listed_ranks = [int(item["rank"]) for item in selected]
    rank_map = {rep: listed for rep, listed in enumerate(listed_ranks, start=1)}

    spot = float(report["spot"])
    maturities = tuple(float(i["dte"]) / 365.0 for i in selected)
    rates = tuple(float(i["rate"]) for i in selected)
    carries = tuple(float(i["carry"]) for i in selected)

    rows = {
        (int(r.expiry_rank), float(r.target_log_moneyness), str(r.option_type)): r
        for r in report["slot_table"].itertuples()
    }

    prices, mask, strikes, raw_prices, reasons = [], [], [], [], []
    for key in CANONICAL_SLOT_KEYS:
        row = rows.get((rank_map[key.expiry_rank], key.target_log_moneyness, key.option_type))
        if row is None:
            raise ValueError(f"{date_id}: audit table lacks canonical slot {key}")
        if bool(row.usable):
            raw = float(row.observed_price)
            prices.append(raw / spot)
            mask.append(True)
            strikes.append(float(row.strike))
            raw_prices.append(raw)
            reasons.append("")
        else:
            # Never impute a missing real quote; the mask carries the absence.
            prices.append(0.0)
            mask.append(False)
            strikes.append(None)
            raw_prices.append(None)
            reasons.append(str(row.failure_reason))

    return R2Surface(
        prices=tuple(prices),
        mask=tuple(mask),
        maturities=tuple(maturities[k.expiry_rank - 1] for k in CANONICAL_SLOT_KEYS),
        rates=tuple(rates[k.expiry_rank - 1] for k in CANONICAL_SLOT_KEYS),
        carries=tuple(carries[k.expiry_rank - 1] for k in CANONICAL_SLOT_KEYS),
        spot=spot,
        surface_id=f"{market.TICKER}_{date_id}_R2_G8",
        source=SOURCE_G8,
        metadata={
            "synthetic": False,
            "ticker": market.TICKER,
            "date_id": date_id,
            "valuation_date": date_id,
            "g8_held_out": True,
            "development_date_excluded_from_g8": False,
            "listed_expiry_ranks_used": listed_ranks,
            "expiry_dates": [str(i["expiry_date"]) for i in selected],
            "dte": [int(i["dte"]) for i in selected],
            "quote_selection_contract": "official_nse_udiff_hungarian_0.05_gate_as_sealed_g2_audit",
            "imputation": "NONE_MASKED_EXPLICITLY",
            "usable_slot_count": int(sum(mask)),
            "provenance": {
                "actual_strikes": strikes,
                "observed_raw_prices": raw_prices,
                "failure_reasons": reasons,
            },
        },
    )


def fetch_and_audit(dates: tuple[str, ...] = G8_CANDIDATE_DATES) -> dict[str, Any]:
    """Download each candidate and report whether it yields a usable G8 surface."""
    from src.nse_bhavcopy_fetch import fetch_date

    register_g8_dates(dates)
    usable, rejected = [], {}

    for date_id in dates:
        try:
            fetch_date(date_id)
        except Exception as exc:
            rejected[date_id] = f"download failed: {exc}"
            logger.warning("%s rejected: download failed (%s)", date_id, exc)
            continue
        try:
            surface = build_g8_surface(date_id)
        except Exception as exc:
            rejected[date_id] = str(exc)
            logger.warning("%s rejected: %s", date_id, exc)
            continue
        usable.append(date_id)
        logger.info("%s usable: %d/20 slots, spot %.2f",
                    date_id, sum(surface.mask), surface.spot)

    return {"usable": usable, "rejected": rejected}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dates", nargs="*", default=None)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    dates = tuple(args.dates) if args.dates else G8_CANDIDATE_DATES
    result = fetch_and_audit(dates)

    print(f"\nG8 candidates: {len(dates)}")
    print(f"  usable   : {len(result['usable'])} -> {result['usable']}")
    print(f"  rejected : {len(result['rejected'])}")
    for date_id, reason in result["rejected"].items():
        print(f"      {date_id}: {reason[:90]}")

    out = REPOSITORY_ROOT / "outputs" / "g8" / "g8_date_selection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out}")
    return 0 if result["usable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
