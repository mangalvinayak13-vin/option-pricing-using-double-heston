"""
Live progress bar for the real-market ambiguity run.

    python3 ambiguity_progress.py          # refreshes until the run finishes, Ctrl+C to quit
    python3 ambiguity_progress.py --once   # print once and exit

Two things worth knowing about what this shows.

The run writes its results file once per DATE, not once per surface, so the count of
completed surfaces moves in 14 steps. The bar is drawn from that count, which is real.
The "current date" figure in between steps is an estimate from elapsed time, and is
labelled as one; it is not read from the run.

The run is a separate process. This script only reads its output file and asks the
operating system how long it has been alive, so it cannot slow the run down and
closing it does not affect the run.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "outputs" / "ambiguity" / "ambiguity_surfaces.csv"
SUMMARY = ROOT / "outputs" / "ambiguity" / "ambiguity_summary.json"
PROCESS_NAME = "run_market_ambiguity.py"


def _etime_to_seconds(text: str) -> int:
    """Parse ps's [[dd-]hh:]mm:ss elapsed-time format."""
    text = text.strip()
    days = 0
    if "-" in text:
        d, text = text.split("-", 1)
        days = int(d)
    parts = [int(p) for p in text.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return days * 86400 + h * 3600 + m * 60 + s


def run_age_seconds() -> int | None:
    """How long the ambiguity run has been alive, or None if it is not running."""
    try:
        pids = subprocess.run(["pgrep", "-f", PROCESS_NAME], capture_output=True,
                              text=True).stdout.split()
    except Exception:
        return None
    ages = []
    for pid in pids:
        if int(pid) == os.getpid():
            continue
        out = subprocess.run(["ps", "-o", "etime=", "-p", pid], capture_output=True,
                             text=True).stdout
        if out.strip():
            ages.append(_etime_to_seconds(out))
    return max(ages) if ages else None


def read_results():
    if not RESULTS.is_file():
        return [], set()
    with open(RESULTS, newline="") as fh:
        rows = list(csv.DictReader(fh))
    return rows, {r["date_id"] for r in rows}


def fmt_duration(seconds: float) -> str:
    seconds = int(max(seconds, 0))
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    return f"{h}h{m:02d}m" if h else f"{m}m"


def bar(fraction: float, width: int = 44) -> str:
    fraction = min(max(fraction, 0.0), 1.0)
    fill = int(round(fraction * width))
    return "[" + "#" * fill + "-" * (width - fill) + f"] {fraction * 100:5.1f}%"


def render(total_dates: int) -> tuple[str, bool]:
    finished = SUMMARY.is_file()
    rows, dates = read_results()
    done_dates = len(dates)
    age = run_age_seconds()
    now = time.time()

    lines = ["", "  Ambiguity test  --  real NSE surfaces, 16 starts each", ""]

    if finished:
        lines += [f"  {bar(1.0)}", f"  COMPLETE: {len(rows)} surfaces across {done_dates} dates", ""]
    elif not rows:
        lines += ["  waiting for the first date to finish...", ""]
    else:
        per_date_surfaces = len(rows) / max(done_dates, 1)
        expected = per_date_surfaces * total_dates

        raw_frac, eta, running_long = 0.0, None, False
        in_date_time = None
        if age is not None:
            started_at = now - age
            last_write = RESULTS.stat().st_mtime
            per_date_time = max(last_write - started_at, 1) / max(done_dates, 1)
            in_date_time = now - last_write
            raw_frac = in_date_time / per_date_time
            running_long = raw_frac > 1.0
            # Dates do not take equal time -- one finished minutes after the previous,
            # another can run for an hour -- so the average is a rough guide only.
            eta = (total_dates - done_dates - min(raw_frac, 0.99)) * per_date_time

        est_frac_in_date = min(raw_frac, 0.99)
        overall = (done_dates + est_frac_in_date) / total_dates
        lines += [
            f"  {bar(done_dates / total_dates)}   confirmed",
            f"  {bar(overall)}   with in-progress estimate",
            "",
            f"  dates complete   {done_dates} of {total_dates}",
            f"  surfaces so far  {len(rows)} of ~{expected:.0f}",
        ]
        if age is not None:
            lines.append(f"  running for      {fmt_duration(age)}")
            if running_long:
                lines.append(f"  current date     running {fmt_duration(in_date_time)}, longer than "
                             f"the average date -- still working, just slow")
            else:
                lines.append(f"  current date     ~{est_frac_in_date * 100:.0f}% "
                             f"(estimated from elapsed time)")
            lines.append(f"  time left        roughly {fmt_duration(eta)} at the average pace "
                         f"(uneven -- treat as a guide)")
        else:
            lines.append("  run NOT detected -- it has finished or stopped")
        lines.append("")

        multi = sum(1 for r in rows if int(float(r["price_equivalent_count"])) >= 2)
        disp = [float(r["median_pairwise_dispersion"]) for r in rows
                if int(float(r["price_equivalent_count"])) >= 2]
        lines.append(f"  more than one equally-good fit   {multi / len(rows) * 100:.0f}% of surfaces")
        if disp:
            lines.append(f"  median parameter gap             {statistics.median(disp):.2f} "
                         f"training-spreads")
        lines.append("")

    lines.append("  (Ctrl+C to close this; the run is unaffected)")
    return "\n".join(lines), finished


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dates", type=int, default=14, help="Total dates in the run")
    ap.add_argument("--interval", type=float, default=2.0)
    args = ap.parse_args()

    if args.once:
        print(render(args.dates)[0])
        return 0

    try:
        while True:
            text, finished = render(args.dates)
            sys.stdout.write("\033[H\033[J" + text + "\n")
            sys.stdout.flush()
            if finished:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
