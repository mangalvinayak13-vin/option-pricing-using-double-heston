# Read the version 1.0 headline numbers straight from the research outputs, so the comparison cites files, not memory.
import json
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1] / "dh2" if False else Path(__file__).resolve().parents[0].parents[0]  # placeholder, replaced below
ROOT = Path(__file__).resolve().parents[1]   # wild/.shots/dh2 = the 2.0 branch checkout, which contains the tracked research outputs
for rel in ["outputs/ambiguity/ambiguity_summary.json", "outputs/real_markets/nifty_comparison/nifty_selection.json",
            "outputs/real_markets/nifty_comparison/nifty_comparison_summary.json", "outputs/g8_fixed/g8_evaluation.json",
            "outputs/consolidated_results.json", "outputs/unified_v6/finetune_real_summary.json"]:
    p = ROOT / rel
    print("\n##", rel, "exists" if p.exists() else "MISSING")
    if p.exists():
        d = json.loads(p.read_text())
        s = json.dumps(d)
        print(s[:1800] + (" ..." if len(s) > 1800 else ""))
b = pd.read_csv(ROOT / "outputs/option_backtest/option_backtest_pairs.csv")
print("\n## option_backtest_pairs.csv", len(b), "pairs;",
      {c: round(float(b[c].median()), 4) for c in ["err_stale_dh", "err_fresh_dh", "err_stale_bs", "err_bs_same_day"]},
      "stale DH beats stale BS on", round(float((b.err_stale_dh < b.err_stale_bs).mean()), 4),
      "; fresh DH beats same-day BS on", round(float((b.err_fresh_dh < b.err_bs_same_day).mean()), 4))
a = pd.read_csv(ROOT / "outputs/ambiguity/ambiguity_vs_flat.csv")
print("## ambiguity_vs_flat.csv", len(a), "surfaces; DH/flat rmse ratio median", round(float(a.dh_over_flat.median()), 3), "max", round(float(a.dh_over_flat.max()), 3))
