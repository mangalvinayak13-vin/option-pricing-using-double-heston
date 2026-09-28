"""
Download official NSE UDiFF bhavcopies into the layout the sealed Stage A /
G2 market contract expects.

Replaces the abandoned Upstox path: Upstox's REST API serves live and recent
quotes, not dated historical option chains. NSE publishes the same UDiFF CSVs
that `src/g2_r2r3/market.py` already parses, so this fetches those instead and
writes them exactly where `frozen.MARKET_RAW_ROOTS` says to look.

Nothing here parses or interprets the data: the existing sealed contract does
that. This module only puts the official files on disk.
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
import zipfile
from pathlib import Path

import requests

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.g2_r2r3 import frozen

logger = logging.getLogger(__name__)

ARCHIVE = "https://nsearchives.nseindia.com/content"

# NSE rejects non-browser clients outright.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/",
}

SEGMENTS = {"CM": "cm", "FO": "fo"}


def _url(segment: str, stamp: str) -> str:
    return f"{ARCHIVE}/{SEGMENTS[segment]}/BhavCopy_NSE_{segment}_0_0_0_{stamp}_F_0000.csv.zip"


def fetch_date(date_id: str, *, force: bool = False) -> dict[str, Path]:
    """Download the CM and FO bhavcopy for one frozen date. Returns {segment: path}."""
    if date_id not in frozen.MARKET_RAW_ROOTS:
        raise ValueError(
            f"{date_id} is not one of the frozen market dates "
            f"{list(frozen.MARKET_RAW_ROOTS)}; G8 dates are a separate milestone"
        )

    stamp = date_id.replace("-", "")
    target_dir = REPOSITORY_ROOT / frozen.MARKET_RAW_ROOTS[date_id] / date_id
    target_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for segment in SEGMENTS:
        name = f"BhavCopy_NSE_{segment}_0_0_0_{stamp}_F_0000.csv"
        destination = target_dir / name

        if destination.exists() and not force:
            logger.info("%s %s already present (%d bytes)", date_id, segment,
                        destination.stat().st_size)
            written[segment] = destination
            continue

        url = _url(segment, stamp)
        response = requests.get(url, headers=HEADERS, timeout=60)
        response.raise_for_status()

        # A blocked or missing file comes back as an HTML error page with HTTP 200,
        # so check the payload really is a zip rather than trusting the status.
        if not response.content[:2] == b"PK":
            raise RuntimeError(
                f"{url} did not return a zip archive "
                f"(first bytes {response.content[:16]!r}); NSE may be refusing the request"
            )

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            members = archive.namelist()
            if name not in members:
                raise RuntimeError(f"{url} contains {members}, expected {name!r}")
            destination.write_bytes(archive.read(name))

        logger.info("%s %s -> %s (%d bytes)", date_id, segment, destination,
                    destination.stat().st_size)
        written[segment] = destination

    return written


def fetch_all(dates: tuple[str, ...] | None = None, *, force: bool = False) -> dict[str, dict[str, Path]]:
    targets = dates or frozen.MARKET_DATES
    out: dict[str, dict[str, Path]] = {}
    failures: dict[str, str] = {}
    for date_id in targets:
        try:
            out[date_id] = fetch_date(date_id, force=force)
        except Exception as exc:                      # keep going; report at the end
            failures[date_id] = str(exc)
            logger.error("%s failed: %s", date_id, exc)
    if failures:
        logger.warning("%d/%d dates failed: %s", len(failures), len(targets), list(failures))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dates", nargs="*", default=None,
                        help="Frozen date ids; default is all five")
    parser.add_argument("--force", action="store_true", help="Re-download present files")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = fetch_all(tuple(args.dates) if args.dates else None, force=args.force)

    print(f"\n{len(result)}/{len(args.dates or frozen.MARKET_DATES)} dates on disk")
    for date_id, files in sorted(result.items()):
        for segment, path in sorted(files.items()):
            print(f"  {date_id} {segment}: {path.stat().st_size:>9,} bytes")
    return 0 if len(result) == len(args.dates or frozen.MARKET_DATES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
