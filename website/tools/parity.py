"""Content parity across themes: every theme must show exactly the same information and links.

For each page, renders every theme (headless Chrome, server on :8765) and compares, against the first
theme: the section keys in order, every number shown, and every link target. Theme chrome (ticker,
switch, side nav) is excluded; the ticker is shared code and identical by construction.

python3 website/tools/parity.py [page ...]
"""
import html
import re
import subprocess
import sys
from collections import Counter

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
THEMES = ["springboard", "glass", "ferro", "amber", "instrument", "trading"]
FILES = {"home": "index.html", "market": "market.html", "model": "model.html", "maths": "how-it-works.html",
         "finding": "finding.html", "about": "about.html", "team": "team.html", "references": "references.html"}


def grab(file, theme):
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=7000", "--force-prefers-reduced-motion",
                          "--dump-dom", f"http://localhost:8765/{file}?theme={theme}&mode=light"], capture_output=True, text=True, timeout=120).stdout
    m = re.search(r'<main id="main".*?</main>', dom, re.S)
    main = m.group(0) if m else ""
    main = re.sub(r'<div class="tick b-tick".*?</div></div></div></div>', "", main, flags=re.S)       # shared ticker
    main = re.sub(r'<svg class="spark".*?</svg>', "", main, flags=re.S)
    keys = re.findall(r'data-sec="([^"]+)"', main)
    keys = [k for k in keys if k != "apps"]
    links = Counter(h for h in re.findall(r'href="([^"#]+)', main))
    text = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(svg|math)\b.*?</\1>", " ", main, flags=re.S)))
    nums = Counter(re.findall(r"\d[\d,]*(?:\.\d+)?", text))
    charts = re.findall(r'data-chart="([^"]+)"', main)
    return keys, nums, set(links), charts


def main():
    pages = sys.argv[1:] or list(FILES)
    bad = 0
    for p in pages:
        base = None
        for t in THEMES:
            keys, nums, links, charts = grab(FILES[p], t)
            if base is None:
                base = (t, keys, nums, links, charts)
                print(f"{p:10} {t:12} {len(keys)} sections, {sum(nums.values())} numbers, {len(links)} link targets, {len(charts)} charts")
                continue
            bt, bk, bn, bl, bc = base
            issues = []
            if keys != bk:
                issues.append(f"sections differ: missing {sorted(set(bk) - set(keys))} extra {sorted(set(keys) - set(bk))}" + (" (order)" if set(keys) == set(bk) else ""))
            if nums != bn:
                issues.append(f"numbers differ: only in {bt} {sorted((bn - nums).elements())[:12]}, only here {sorted((nums - bn).elements())[:12]}")
            if links != bl:
                issues.append(f"links differ: missing {sorted(bl - links)} extra {sorted(links - bl)}")
            if charts != bc:
                issues.append(f"charts differ: {bc} vs {charts}")
            bad += bool(issues)
            print(f"{p:10} {t:12} {'same' if not issues else 'DIFFERENT'}")
            for i in issues:
                print("   ", i)
    print("parity:", "OK" if not bad else f"{bad} differences")


if __name__ == "__main__":
    main()
