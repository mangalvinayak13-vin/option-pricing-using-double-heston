"""Contact sheet: one page in several themes side by side, scaled down, for quick review.

python3 website/tools/sheet.py home light [height]   -> website/.shots/sheet-home-light.png
(uses the existing screenshots in website/.shots/<theme>/<page>.<mode>.png; run shots.py first)
"""
import sys
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[1] / ".shots"
THEMES = ["springboard", "glass", "ferro", "amber", "instrument", "trading"]
page, mode = sys.argv[1], sys.argv[2]
cut = int(sys.argv[3]) if len(sys.argv) > 3 else 3600
ims = []
for t in THEMES:
    p = OUT / t / f"{page}.{mode}.png"
    if p.exists():
        im = Image.open(p).convert("RGB")
        ims.append(im.crop((0, 0, im.width, min(im.height, cut))))
sc = 0.25
w = int(sum(i.width for i in ims) * sc) + 8 * len(ims)
h = int(max(i.height for i in ims) * sc)
sheet = Image.new("RGB", (w, h), (128, 128, 128))
x = 0
for im in ims:
    s = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    sheet.paste(s, (x, 0))
    x += s.width + 8
dst = OUT / f"sheet-{page}-{mode}.png"
sheet.save(dst)
print(dst)
