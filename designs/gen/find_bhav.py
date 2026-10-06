"""List every NSE bhavcopy day in the repo (one CM + one FO file per trading day)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
found = {}
for p in ROOT.rglob("BhavCopy_NSE_*_0_0_0_*_F_0000.csv"):
    if ".claude" in p.relative_to(ROOT).parts:
        continue
    m = re.search(r"BhavCopy_NSE_(CM|FO)_0_0_0_(\d{8})_F_0000\.csv", p.name)
    d = f"{m[2][:4]}-{m[2][4:6]}-{m[2][6:]}"
    found.setdefault(d, {}).setdefault(m[1], str(p.relative_to(ROOT)))
print("dates found:", len(found), "with CM:", sum("CM" in v for v in found.values()),
      "with FO:", sum("FO" in v for v in found.values()))
for d in list(sorted(found))[:3] + list(sorted(found))[-3:]:
    print(d, found[d])
days = {d: v for d, v in sorted(found.items()) if "CM" in v and "FO" in v}
(Path(__file__).parent / "bhav_index.json").write_text(json.dumps(days, indent=1))
print(len(days), "complete days:", min(days), "to", max(days))
print("folders:", sorted({str(Path(v["CM"]).parent.parent) for v in days.values()}))
