"""Contact sheet of a design's boards (one theme) for quick review, plus optional crops.

python3 sheet.py amber-instrument t-dark
python3 sheet.py amber-instrument t-dark Model 0 1200     -> crop of one board, y range
"""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
slug, theme = sys.argv[1], sys.argv[2]
src = HERE / "shots" / slug
if len(sys.argv) > 3:
    name, y0, y1 = sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    Image.open(src / f"{name}.{theme}.png").crop((0, y0, 1440, y1)).save(src / f"_crop_{name}_{y0}.png")
    sys.exit()
order = ["Main", "Market", "Model", "Maths", "Finding", "About", "Team", "References", "Components"]
ims = [Image.open(src / f"{n}.{theme}.png") for n in order]
scale = 0.2
w = int(1440 * scale)
H = max(int(i.height * scale) for i in ims)
sheet = Image.new("RGB", (w * len(ims) + 10 * (len(ims) - 1), H), (128, 128, 128))
for k, im in enumerate(ims):
    sheet.paste(im.resize((w, int(im.height * scale))), (k * (w + 10), 0))
sheet.save(src / f"_sheet_{theme}.png")
print(sheet.size)
