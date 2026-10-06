"""Write assets/data/content.json from content.py: every constant the themes print.

python3 website/tools/export.py

site.json and ferro_pair.json are snapshots from designs/gen (prep.py, ferro_pair.py, ferro_curves.py):
re-run those generators and copy the two files into website/assets/data to refresh the numbers.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content as X  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "assets" / "data" / "content.json"
SKIP = {"D", "DATA", "PAIR", "CB", "G8", "NET", "AMB", "WATCH", "REL", "REL_ROWS", "REL_STOCK", "PER", "PA", "PB",
        "K", "HL"}


def main():
    out = {}
    for name in dir(X):
        if not name.isupper() or name in SKIP or name.startswith("_"):
            continue
        v = getattr(X, name)
        try:
            json.dumps(v)
        except TypeError:
            continue
        out[name] = v
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(OUT.name, len(out), "keys")


if __name__ == "__main__":
    main()
