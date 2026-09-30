"""Quick render check with headless Chrome: does each page finish rendering (body[data-ready])?

python3 website/tools/check.py [page.html ...]   (the server must be running on :8765)
"""
import re
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGES = sys.argv[1:] or ["index.html", "market.html", "model.html", "how-it-works.html", "finding.html", "about.html", "team.html", "references.html"]

for p in PAGES:
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=6000", "--dump-dom", f"http://localhost:8765/{p}"],
                         capture_output=True, text=True, timeout=90).stdout
    ready = 'data-ready="1"' in dom
    charts = len(re.findall(r'data-chart="', dom))
    svgs = len(re.findall(r'<svg viewBox=', dom))
    print(f"{p:22} ready={ready}  charts={charts}  drawn={svgs}  switch={'class=\"lgs\"' in dom}  nav={'mdash-d' in dom or 'fnav' in dom}")
