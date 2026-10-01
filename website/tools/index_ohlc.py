"""Daily candles for NIFTY 50 and NIFTY BANK, so the Market page can chart them like a stock.

The NSE bhavcopies behind site.json carry stock OHLC (CM) and option/futures data (FO), but not the
indices' own open, high and low: site.json only had each index's closing level (index_close, from the
FO file's underlying price). NSE publishes those in its daily index file, ind_close_all_DDMMYYYY.csv.
This script fetches that file for every trading day in site.json (kept next to the bhavcopies in
market_data_audit/stage_a/raw/nse/<date>/), checks every close against index_close, and writes the
rows into site.json's equity table in the stocks' layout: [date, open, high, low, close, volume, prev close].
Index volume is NSE's figure: shares traded across the index's stocks.

    python3 website/tools/index_ohlc.py    (then python3 website/tools/export.py)
"""
import csv
import io
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parent
SITE = HERE / "assets" / "data" / "site.json"
RAW = ROOT / "market_data_audit" / "stage_a" / "raw" / "nse"
URL = "https://nsearchives.nseindia.com/content/indices/ind_close_all_{}.csv"
WHICH = {"NIFTY": ("Nifty 50", "NIFTY 50"), "BANKNIFTY": ("Nifty Bank", "NIFTY BANK")}  # index_close key: (NSE name, site symbol)


def day_file(d: str) -> str:
    y, m, dd = d.split("-")
    name = f"ind_close_all_{dd}{m}{y}.csv"
    p = RAW / d / name
    if not p.exists():
        # curl, not urllib: the python.org build ships without root certificates
        body = subprocess.run(["curl", "-sSf", "-m", "30", "-A", "Mozilla/5.0", URL.format(f"{dd}{m}{y}")], capture_output=True, check=True).stdout
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
    return p.read_text()


site = json.loads(SITE.read_text())
days = [d for d, _ in site["index_close"]["NIFTY"]]
rows = {k: [] for k in WHICH}
for d in days:
    by_name = {r["Index Name"].strip(): r for r in csv.DictReader(io.StringIO(day_file(d)))}
    for k, (nse, _) in WHICH.items():
        r = by_name[nse]
        o, h, l, c = (float(r[f"{x} Index Value"]) for x in ("Open", "High", "Low", "Closing"))
        prev = rows[k][-1][4] if rows[k] else round(c - float(r["Points Change"]), 2)
        rows[k].append([d, o, h, l, c, float(r["Volume"]), prev])

for k, (_, sym) in WHICH.items():
    ref = dict(site["index_close"][k])
    bad = [(r[0], r[4], ref[r[0]]) for r in rows[k] if abs(r[4] - ref[r[0]]) > 0.05]
    assert not bad, f"{sym}: NSE index file disagrees with index_close on {bad[:3]}"
    assert all(r[3] <= min(r[1], r[4]) and r[2] >= max(r[1], r[4]) for r in rows[k]), f"{sym}: a candle's high/low doesn't contain its open/close"
    site["equity"][sym] = rows[k]
    print(sym, len(rows[k]), "days, closes match index_close; last", rows[k][-1])

SITE.write_text(json.dumps(site))  # same layout as prep.py writes
