"""One PDF of every built design: cover + index, a divider per design, then each board in light and dark.

python3 pdf.py            -> designs/Double-Heston-designs.pdf (1440 px boards)
python3 pdf.py --compact  -> designs/Double-Heston-designs-compact.pdf (1080 px, smaller file for email)

Cover and dividers are printed by Chrome (vector, links stay clickable); boards come from the reviewed
screenshots in gen/shots/<slug>/ (build.py --shots), captioned and stored as JPEG. The outline
(bookmarks) has one entry per design with its boards underneath.
"""
from __future__ import annotations

import html
import importlib
import io
import re
import subprocess
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter

import kit
from build import CHROME, TITLES

HERE = Path(__file__).resolve().parent
DESIGNS = HERE.parent
TMP = HERE / "pdf_tmp"
OUT = DESIGNS / "Double-Heston-designs.pdf"
STEMS = [s for s, _, _ in kit.PAGES] + ["Components"]
LABEL = {s: l for s, l, _ in kit.PAGES} | {"Components": "Components"}
DPI = 144  # 1440 px board -> 10 in page
FONT = "/System/Library/Fonts/Helvetica.ttc"


def links() -> dict[int, str]:
    rows = re.findall(r"^\| (\d\d) \| [^|]+\| (https://claude\.ai/artifact/\w+)", (DESIGNS / "PROGRESS.md").read_text(), re.M)
    return {int(n): u for n, u in rows}


def designs():
    out = []
    for p in sorted(HERE.glob("d[0-9][0-9].py")):
        d = importlib.import_module(p.stem).DESIGN
        if (HERE / "shots" / d.slug / "Main.t-light.png").exists():
            out.append(d)
    return out


def chrome_pdf(html_text: str, name: str) -> PdfReader:
    TMP.mkdir(exist_ok=True)
    src, pdf = TMP / f"{name}.html", TMP / f"{name}.pdf"
    src.write_text(html_text)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={pdf}", src.as_uri()], capture_output=True, timeout=240)
    return PdfReader(str(pdf))


PAGE_CSS = """
@page { size: 10in 5.625in; margin: 0 }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact }
html, body { margin: 0 }
body { font-family: 'Instrument Sans', system-ui, sans-serif; color: #17181A; background: #FFFFFF }
.pg { width: 10in; height: 5.625in; padding: .55in .6in; page-break-after: always; overflow: hidden; position: relative }
a { color: inherit }
"""


def cover_html(ds, urls) -> str:
    rows = "".join(
        f"<tr><td class=n>{d.num:02d}</td><td class=nm>{html.escape(d.name)}</td>"
        f"<td class=c>{html.escape(d.concept)}</td>"
        f"<td class=l>{f'<a href={urls[d.num]}>open artifact</a>' if d.num in urls else ''}</td></tr>" for d in ds)
    half = (len(ds) + 1) // 2
    return f"""<!doctype html><meta charset=utf-8>
<link rel=stylesheet href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600;700&family=Instrument+Serif&display=swap">
<style>{PAGE_CSS}
.cover h1 {{ font: 400 64px/1.02 'Instrument Serif', Georgia, serif; margin: 0 0 18px; max-width: 7.5in; letter-spacing: -.01em }}
.cover p {{ font-size: 15px; line-height: 1.5; max-width: 6.2in; color: #3A3D42; margin: 0 0 10px }}
.cover .foot {{ position: absolute; left: .6in; right: .6in; bottom: .5in; display: flex; justify-content: space-between; font-size: 12px; color: #6A6E75 }}
.idx h2 {{ font: 400 30px/1.1 'Instrument Serif', Georgia, serif; margin: 0 0 14px }}
table {{ border-collapse: collapse; width: 100% }}
td {{ font-size: 10.5px; line-height: 1.3; padding: 5px 8px 5px 0; border-top: 1px solid #E3E4E6; vertical-align: top }}
td.n {{ font-weight: 700; width: 26px; font-variant-numeric: tabular-nums }}
td.nm {{ font-weight: 700; width: 1.3in }}
td.l {{ width: .95in; white-space: nowrap; text-align: right }}
td.l a {{ color: #1F5FBF }}
</style>
<div class="pg cover">
  <h1>Double Heston: {len(ds)} website designs</h1>
  <p>Each design is the whole site: Home, Market, The model, How it works, The finding, About, Team and References,
  plus a components board with the magnet navigation rail, the light/dark switch, icons, type and colours.
  Every board is shown in light and then dark.</p>
  <p>All prices are NSE closing data from 25 Sep 2026. All model numbers come from the project's pricer and verified
  research outputs. Candles are green for up days and red for down days in every design.</p>
  <div class=foot><span>{date.today().strftime('%-d %B %Y')}</span><span>Each design is also a Design-canvas artifact; links on the next page</span></div>
</div>
<div class="pg idx"><h2>The designs</h2><table>{rows[:0]}{''.join(rows.split('</tr>')[i] + '</tr>' for i in range(half))}</table></div>
<div class="pg idx"><h2>The designs, continued</h2><table>{''.join(rows.split('</tr>')[i] + '</tr>' for i in range(half, len(ds)))}</table></div>
"""


def thumb(d, theme) -> str:
    """Top 1440x900 of the Home board, shrunk, as a small JPEG next to the divider HTML."""
    TMP.mkdir(exist_ok=True)
    im = Image.open(HERE / "shots" / d.slug / f"Main.{theme}.png").convert("RGB").crop((0, 0, 1440, 900))
    out = TMP / f"th-{d.slug}-{theme}.jpg"
    im.resize((576, 360), Image.LANCZOS).save(out, "JPEG", quality=85)
    return out.name


def divider_html(ds, urls) -> str:
    fonts = "".join(f'<link rel=stylesheet href="{d.fonts_url}">' for d in ds)
    pages = []
    for d in ds:
        sw = "".join(
            f'<div class=sw><div class=chip style="background:{t["bg"]};border-color:{t["line"]}">'
            f'<i style="background:{t["acc"]}"></i><i style="background:{t["up"]}"></i><i style="background:{t["down"]}"></i>'
            f'<b style="color:{t["ink"]};font-family:{d.display_font}">Aa</b></div><span>{lab}</span></div>'
            for t, lab in ((d.light, "Light"), (d.dark, "Dark")))
        link = f'<a href="{urls[d.num]}">{urls[d.num]}</a>' if d.num in urls else "Artifact link pending"
        pages.append(f"""<div class="pg dv">
  <div class=num>{d.num:02d}</div>
  <h1 style="font-family:{d.display_font}">{html.escape(d.name)}</h1>
  <p class=con>{html.escape(d.concept)}</p>
  <dl><dt>Layout</dt><dd>{html.escape(d.layout)}</dd>
  <dt>The memorable thing</dt><dd>{html.escape(d.memorable)}</dd>
  <dt>Type</dt><dd>{html.escape(d.type_note)}</dd></dl>
  <div class=sws>{sw}</div>
  <div class=lk>{link}</div>
  <div class=th><figure><img src="{thumb(d, 't-light')}"><figcaption>Home, light</figcaption></figure>
  <figure><img src="{thumb(d, 't-dark')}"><figcaption>Home, dark</figcaption></figure></div>
</div>""")
    return f"""<!doctype html><meta charset=utf-8>
<link rel=stylesheet href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600;700&display=swap">{fonts}
<style>{PAGE_CSS}
.dv .num {{ font-size: 13px; font-weight: 700; color: #6A6E75; margin-bottom: 6px; font-variant-numeric: tabular-nums }}
.dv h1 {{ font-size: 46px; line-height: 1.04; margin: 0 0 10px; font-weight: 700 }}
.dv .con {{ font-size: 15px; line-height: 1.45; max-width: 6.4in; margin: 0 0 16px; color: #2A2C30 }}
dl {{ display: grid; grid-template-columns: 1.45in 1fr; gap: 6px 14px; margin: 0; max-width: 6.4in }}
dt {{ font-size: 11px; font-weight: 700; color: #6A6E75 }}
dd {{ font-size: 11px; line-height: 1.4; margin: 0; color: #2A2C30 }}
.sws {{ position: absolute; right: .6in; top: .55in; display: grid; gap: 12px }}
.sw {{ display: flex; align-items: center; gap: 10px; font-size: 11px; color: #6A6E75 }}
.chip {{ width: 1.55in; height: .72in; border: 1px solid; border-radius: 10px; display: flex; align-items: flex-end; gap: 5px; padding: 9px; position: relative }}
.chip i {{ width: 14px; height: 14px; border-radius: 4px; display: block }}
.chip b {{ position: absolute; right: 10px; top: 4px; font-size: 30px }}
.lk {{ position: absolute; left: .6in; bottom: .45in; font-size: 11px }}
.lk a {{ color: #1F5FBF }}
.th {{ position: absolute; right: .6in; bottom: .42in; display: flex; gap: 14px }}
.th figure {{ margin: 0 }}
.th img {{ width: 2.35in; display: block; border: 1px solid #DADBDE; border-radius: 4px }}
.th figcaption {{ font-size: 10px; color: #6A6E75; margin-top: 4px }}
</style>{''.join(pages)}"""


def board_page(png: Path, caption: str, right: str, scale=1.0, quality=78) -> PdfReader:
    im = Image.open(png).convert("RGB")
    if scale != 1.0:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    bar = round(56 * scale)
    page = Image.new("RGB", (im.width, im.height + bar), (255, 255, 255))
    page.paste(im, (0, bar))
    dr = ImageDraw.Draw(page)
    dr.line([(0, bar - 1), (im.width, bar - 1)], fill=(220, 221, 224), width=1)
    dr.text((28 * scale, 16 * scale), caption, font=ImageFont.truetype(FONT, round(22 * scale), index=1), fill=(23, 24, 26))
    f2 = ImageFont.truetype(FONT, round(18 * scale))
    dr.text((im.width - 28 * scale - dr.textlength(right, font=f2), 19 * scale), right, font=f2, fill=(106, 110, 117))
    buf = io.BytesIO()
    page.save(buf, "PDF", resolution=DPI * scale, quality=quality)
    buf.seek(0)
    return PdfReader(buf)


def main(compact=False):
    scale, quality, out = (0.75, 70, DESIGNS / "Double-Heston-designs-compact.pdf") if compact else (1.0, 78, OUT)
    ds, urls = designs(), links()
    w = PdfWriter()
    cover = chrome_pdf(cover_html(ds, urls), "cover")
    for p in cover.pages:
        w.add_page(p)
    w.add_outline_item("Cover and index", 0)
    div = chrome_pdf(divider_html(ds, urls), "dividers")
    for i, d in enumerate(ds):
        start = len(w.pages)
        w.add_page(div.pages[i])
        parent = w.add_outline_item(f"{d.num:02d} {d.name}", start)
        for s in STEMS:
            for theme, tname in (("t-light", "light"), ("t-dark", "dark")):
                png = HERE / "shots" / d.slug / f"{s}.{theme}.png"
                if not png.exists():
                    continue
                w.add_page(board_page(png, f"{d.num:02d} {d.name}   {LABEL[s]}", tname, scale, quality).pages[0])
                if theme == "t-light":
                    w.add_outline_item(TITLES[s].split(":")[0], len(w.pages) - 1, parent=parent)
        print(d.num, d.name, len(w.pages))
    w.add_metadata({"/Title": f"Double Heston: {len(ds)} website designs", "/Author": "Double Heston project"})
    w.compress_identical_objects()
    with open(out, "wb") as f:
        w.write(f)
    print(out, f"{out.stat().st_size / 1e6:.1f} MB", len(w.pages), "pages")


def main_home():
    """Short version (python3 pdf.py --home): per design, the Home board in light and in dark, nothing else."""
    out = DESIGNS / "Double-Heston-designs-home.pdf"
    ds, urls = designs(), links()
    w = PdfWriter()
    for d in ds:
        link = urls.get(d.num, "").replace("https://", "")
        for theme, tname in (("t-light", "Light"), ("t-dark", "Dark")):
            w.add_page(board_page(HERE / "shots" / d.slug / f"Main.{theme}.png", f"{d.num:02d} {d.name}   {tname}",
                                  link, 1.0, 80).pages[0])
            if theme == "t-light":
                w.add_outline_item(f"{d.num:02d} {d.name}", len(w.pages) - 1)
    w.add_metadata({"/Title": f"Double Heston: {len(ds)} website designs, home pages", "/Author": "Double Heston project"})
    with open(out, "wb") as f:
        w.write(f)
    print(out, f"{out.stat().st_size / 1e6:.1f} MB", len(w.pages), "pages")


if __name__ == "__main__":
    import sys
    if "--home" in sys.argv:
        main_home()
    else:
        main("--compact" in sys.argv)
