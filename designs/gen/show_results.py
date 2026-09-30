"""Print the verified headline numbers the Finding pages quote."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
c = json.loads((ROOT / "outputs" / "consolidated_results.json").read_text())


def short(x, depth=0):
    if isinstance(x, dict):
        return {k: short(v, depth + 1) for k, v in list(x.items())[:14]} if depth < 3 else "{…}"
    if isinstance(x, list):
        return f"[list {len(x)}]"
    return x


for k in ("classical_baseline", "g8", "real_market", "models"):
    print("==", k)
    print(json.dumps(short(c[k]), indent=1)[:2500])
bt = ROOT / "outputs" / "option_backtest"
print([p.name for p in bt.iterdir()])
