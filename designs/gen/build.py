"""Build one design's canvas: 8 page boards + a components board, measured, rendered, indexed.

python3 build.py d01            -> designs/01-amber-instrument/project/*.dc.html + canvas.json
python3 build.py d01 --shots    -> also screenshot every board (dark and light) into designs/gen/shots/
"""
from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import kit
from components import components_body, COMP_CSS

HERE = Path(__file__).resolve().parent
DESIGNS = HERE.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CH = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
      "--virtual-time-budget=7000"]
STEMS = [s for s, _, _ in kit.PAGES] + ["Components"]
TITLES = {s: l for s, l, _ in kit.PAGES} | {"Components": "Components: navigation, switch, icons, charts"}


def measure(html_path: Path) -> int:
    dom = subprocess.run(CH + ["--window-size=1440,1000", "--dump-dom", html_path.as_uri()],
                         capture_output=True, text=True, timeout=180).stdout
    m = re.search(r'data-h="(\d+)"', dom)
    return int(m.group(1)) if m else 2400


def shot(html_path: Path, png: Path, h: int):
    subprocess.run(CH + [f"--window-size=1440,{h}", f"--screenshot={png}", html_path.as_uri()],
                   capture_output=True, text=True, timeout=180)


def build(mod_name: str, shots: bool):
    d = importlib.import_module(mod_name).DESIGN
    root = DESIGNS / f"{d.num:02d}-{d.slug}"
    proj = root / "project"
    proj.mkdir(parents=True, exist_ok=True)
    prev = HERE / "preview" / d.slug
    prev.mkdir(parents=True, exist_ok=True)
    bodies = {s: (components_body(d) if s == "Components" else d.pages[s]()) for s in STEMS}
    heights = {}
    for s in STEMS:
        probe = kit.board(d, s, bodies[s], "auto", f"{d.name}: {TITLES[s]}", COMP_CSS if s == "Components" else "")
        probe = probe.replace('height: autopx;', 'height: auto;')
        p = prev / f"{s}.html"
        p.write_text(kit.preview(probe, "t-dark").replace(
            'document.body.setAttribute("data-ready","1")',
            'document.body.setAttribute("data-h",document.querySelector(".dh").scrollHeight)'))
        heights[s] = max(900, measure(p))
    for s in STEMS:
        html = kit.board(d, s, bodies[s], heights[s], f"{d.name}: {TITLES[s]}", COMP_CSS if s == "Components" else "")
        (proj / f"{s}.dc.html").write_text(html)
        if shots:
            for theme in ("t-dark", "t-light"):
                p = prev / f"{s}.{theme}.html"
                p.write_text(kit.preview(html, theme))
                out = HERE / "shots" / d.slug
                out.mkdir(parents=True, exist_ok=True)
                shot(p, out / f"{s}.{theme}.png", heights[s])
    # canvas index: pages 1-4 on row one, 5-8 on row two, components at the end of row one
    boards, order = {}, []
    row1 = ["Main", "Market", "Model", "Maths", "Components"]
    row2 = ["Finding", "About", "Team", "References"]
    y2 = max(heights[s] for s in row1) + 400
    for row, y in ((row1, 0), (row2, y2)):
        for i, s in enumerate(row):
            key = f"{s}.dc.html"
            boards[key] = {"x": i * 1520, "y": y, "w": 1440, "h": heights[s], "title": TITLES[s], "is_interactive": True}
            order.append(key)
    canvas = {
        "v": 3,
        "createdOnFiles": {"v": 1, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        "title": f"DH Design {d.num:02d} — {d.name}",
        "launch": {"view": "canvas"},
        "pages": [],
        "boards": boards,
        "order": order,
        "notes": {
            "title": {"x": 0, "y": -300, "kind": "title1", "maxW": 7520, "text": f"{d.num:02d} · {d.name}: {d.concept}"},
            "row2": {"x": 0, "y": y2 - 300, "kind": "title1", "maxW": 5960, "text": "The finding, About, Team, References"},
            "plan": {"x": 0, "y": -1000, "w": 1200, "maxH": 560, "color": "yellow" if False else "orange", "text": d.plan_note()},
        },
        "designSystems": [],
    }
    (proj / "canvas.json").write_text(json.dumps(canvas, indent=2, ensure_ascii=False) + "\n")
    print(d.name, heights)
    return root


if __name__ == "__main__":
    build(sys.argv[1], "--shots" in sys.argv)
