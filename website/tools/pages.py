"""Write the eight page shells (index.html, market.html, ...). Each is the same small HTML file with:
- an inline boot script that sets data-theme / data-mode on <html> before any CSS loads (no flash of the
  wrong theme): URL ?theme=&mode= first, then the visitor's saved choice, then the system setting;
- every theme's stylesheet (so a theme change needs no reload), then the app module.

python3 website/tools/pages.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
THEMES = ["springboard", "glass", "ferro", "amber", "instrument", "trading"]
DEFAULT_THEME = "ferro"  # first-time visitors: the theme the presentation opens with (see MORNING_REPORT.md)
PAGES = json.loads((HERE / "assets" / "data" / "content.json").read_text())["PAGES"]
DESC = {
    "home": "Does letting volatility move price options better? A B.Tech physics project on Double Heston, NSE options and an honest answer.",
    "market": "NSE closing prices, candlesticks and the stocks the research covers.",
    "model": "Price a NIFTY option with Double Heston and set it against the market's close.",
    "maths": "How Double Heston works: two variance factors, one integral, a Monte Carlo check.",
    "finding": "Why a perfect price fit doesn't tell you the model's ten settings.",
    "about": "Method, data, limits and the explainer video.",
    "team": "Who built the Double Heston project.",
    "references": "The papers and data behind the project.",
}

BOOT = """(function(){var T=%s,D=%s,d=document.documentElement,q,s={},t,m;
try{q=new URLSearchParams(location.search)}catch(e){q={get:function(){return null}}}
try{s.t=localStorage.getItem('dh.theme');s.m=localStorage.getItem('dh.mode')}catch(e){}
t=q.get('theme');m=q.get('mode');if(T.indexOf(t)<0)t=null;if(m!=='light'&&m!=='dark')m=null;
try{if(t)localStorage.setItem('dh.theme',t);if(m)localStorage.setItem('dh.mode',m)}catch(e){}
t=t||(T.indexOf(s.t)>=0?s.t:D);m=m||(s.m==='light'||s.m==='dark'?s.m:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
d.setAttribute('data-theme',t);d.setAttribute('data-mode',m);d.style.colorScheme=m;})();""" % (json.dumps(THEMES), json.dumps(DEFAULT_THEME))

TEMPLATE = """<!doctype html>
<html lang="en" data-page="{id}" data-default-theme="{default}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
<script>{boot}</script>
<link rel="stylesheet" href="assets/css/fonts.css">
<link rel="stylesheet" href="assets/css/base.css">
{themes}
<link rel="modulepreload" href="assets/js/app.js">
<script type="module" src="assets/js/app.js"></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div id="app"></div>
<noscript><div class="noscript">This site draws its charts and runs the model with JavaScript. Please turn it on.</div></noscript>
</body>
</html>
"""


def main():
    themes = "\n".join(f'<link rel="stylesheet" href="assets/css/themes/{t}.css">' for t in THEMES)
    for pid, file, label, _ in PAGES:
        title = "Double Heston" if pid == "home" else f"{label} | Double Heston"
        (HERE / file).write_text(TEMPLATE.format(id=pid, default=DEFAULT_THEME, title=title, desc=DESC[pid], boot=BOOT, themes=themes))
        print("wrote", file)


if __name__ == "__main__":
    main()
