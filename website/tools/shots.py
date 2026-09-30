"""Screenshot pages for review (server on :8765). Output: website/.shots/<theme>/<page>.<mode>.png

python3 website/tools/shots.py springboard                 all pages, light + dark, 1440 wide, full height
python3 website/tools/shots.py springboard model dark      one page, one mode
python3 website/tools/shots.py springboard home light 720  first screen at 1280 x 720 (projector)
"""
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path(__file__).resolve().parents[1] / ".shots"
FILES = {"home": "index.html", "market": "market.html", "model": "model.html", "maths": "how-it-works.html",
         "finding": "finding.html", "about": "about.html", "team": "team.html", "references": "references.html"}
BASE = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--virtual-time-budget=9000", "--force-prefers-reduced-motion"]


def height(url):
    dom = subprocess.run(BASE + ["--window-size=1440,1000", "--dump-dom", url], capture_output=True, text=True, timeout=120).stdout
    m = re.search(r'data-h="(\d+)"', dom)
    return int(m.group(1)) if m else 3000


def main():
    theme = sys.argv[1]
    pages = [sys.argv[2]] if len(sys.argv) > 2 and sys.argv[2] != "all" else list(FILES)
    modes = [sys.argv[3]] if len(sys.argv) > 3 else ["light", "dark"]
    proj = len(sys.argv) > 4 and sys.argv[4] == "720"
    (OUT / theme).mkdir(parents=True, exist_ok=True)
    for p in pages:
        for m in modes:
            url = f"http://localhost:8765/{FILES[p]}?theme={theme}&mode={m}"
            w, h = (1280, 720) if proj else (1440, height(url))
            png = OUT / theme / f"{p}.{m}{'.720' if proj else ''}.png"
            subprocess.run(BASE + [f"--window-size={w},{h}", f"--screenshot={png}", url], capture_output=True, timeout=120)
            print(png.relative_to(OUT.parent), h)


if __name__ == "__main__":
    main()
