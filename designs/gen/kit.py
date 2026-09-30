"""Shared kit for the 20 design canvases.

Every board: a fixed-size root with class "dh t-dark|t-light" (theme from the `dark` tweak,
flipped by the Liquid Glass switch in Play), colours as CSS custom properties defined per
design for both themes, the switch at the same top-right spot, and the magnet rail on one
edge with prototype links to the other boards.

Charts are drawn to scale from site_data.json (real NSE files, verified research outputs,
the project's pricer) and painted with style="…var(--token)…" so they follow the theme.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "site_data.json").read_text()) if (HERE / "site_data.json").exists() else {}

PAGES = [  # (file stem, nav label, short description)
    ("Main", "Home", "the question and the answer"),
    ("Market", "Market", "real NSE prices"),
    ("Model", "The model", "price an option"),
    ("Maths", "How it works", "the equations"),
    ("Finding", "The finding", "why a fit isn't an answer"),
    ("About", "About", "video, method, limits"),
    ("Team", "Team", "who built it"),
    ("References", "References", "papers and data"),
]
PAGE_LABEL = {s: l for s, l, _ in PAGES}

TOKEN_KEYS = ["bg", "surf", "raised", "line", "grid", "ink", "body", "muted", "acc", "on_acc", "up", "down",
              "track_off", "ferro", "ferro_hi"]


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def theme_css(light: dict, dark: dict) -> str:
    def block(sel, tok):
        return sel + "{" + ";".join(f"--{k.replace('_', '-')}:{v}" for k, v in tok.items()) + "}"
    return block(".dh.t-light", light) + block(".dh.t-dark", dark)


# ------------------------------------------------------------------ number formats ------

def inr(v, dp=2):
    neg = v < 0
    s = f"{abs(v):.{dp}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    return ("-" if neg else "") + whole + ("." + frac if frac else "")


def arrow(p):
    return ("▲", "up") if p >= 0 else ("▼", "dn")


# ------------------------------------------------------------------ the switch -----------

SWITCH_CSS = """
.gsw-wrap{position:absolute;top:8px;right:20px;z-index:30;display:flex;align-items:center;gap:10px;height:32px;
  font-size:14px;font-weight:500;color:var(--muted)}
.gsw{position:relative;width:52px;height:32px;padding:0;border:0;border-radius:16px;cursor:pointer;
  background:var(--track-off);transition:background-color .2s ease}
.gsw:focus-visible{outline:3px solid #0A84FF;outline-offset:3px}
.t-dark .gsw{background:#30D158}.t-light .gsw[aria-checked=true]{background:#34C759}
.gsw .knob{position:absolute;top:2px;left:2px;width:28px;height:28px;border-radius:14px;background:#FFFFFF;
  box-shadow:0 3px 8px rgba(0,0,0,.18),0 1px 1px rgba(0,0,0,.12);transition:transform .32s cubic-bezier(.3,1.4,.5,1),width .18s ease}
.t-dark .gsw .knob{transform:translateX(20px)}
.gsw:active .knob{width:38px;background:rgba(255,255,255,.42);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.75),inset 0 -6px 10px rgba(255,255,255,.35),0 6px 16px rgba(0,0,0,.22);
  backdrop-filter:blur(1px) saturate(1.15) brightness(1.08);-webkit-backdrop-filter:blur(1px) saturate(1.15) brightness(1.08)}
.t-dark .gsw:active .knob{transform:translateX(10px)}
@media (prefers-reduced-motion: reduce){.gsw .knob{transition:transform .2s linear}.gsw:active .knob{width:28px}}
"""


def switch():
    return ('<div class="gsw-wrap"><span>Dark mode</span>'
            '<button type="button" class="gsw" role="switch" aria-checked="{{dark}}" aria-label="Dark mode" '
            'onClick="{{toggle}}"><span class="knob"></span></button></div>')


# ------------------------------------------------------------------ the magnet rail ------

RAIL_CSS = """
.mag{position:absolute;top:260px;z-index:25;width:84px;height:360px}
.mag.l{left:0}.mag.r{right:0}
.mag .mag-bar{position:absolute;top:40px;width:7px;height:280px;border-radius:4px;
  background:linear-gradient(90deg,#3A3B3E,#8C8F95 45%,#2A2B2E);box-shadow:0 0 0 1px rgba(0,0,0,.25)}
.mag.l .mag-bar{left:8px}.mag.r .mag-bar{right:8px}
.mag .mag-bead{position:absolute;width:13px;height:13px;border-radius:7px;background:radial-gradient(circle at 35% 30%,var(--ferro-hi) 0 18%,var(--ferro) 45%);
  box-shadow:0 2px 4px rgba(0,0,0,.35)}
.mag.l .mag-bead{left:5px}.mag.r .mag-bead{right:5px}
.mag .mag-fluid{position:absolute;top:0;width:84px;height:360px;opacity:0;transform:scaleX(.2);transition:opacity .22s ease,transform .32s cubic-bezier(.2,1.2,.4,1)}
.mag.l .mag-fluid{left:0;transform-origin:0 50%}.mag.r .mag-fluid{right:0;transform-origin:100% 50%}
.mag .mag-links{position:absolute;top:44px;display:flex;flex-direction:column;gap:2px;opacity:0;pointer-events:none;
  transition:opacity .2s ease .06s;padding:10px 12px;border-radius:14px;background:var(--surf);box-shadow:0 10px 30px rgba(0,0,0,.25);
  border:1px solid var(--line);min-width:180px}
.mag.l .mag-links{left:92px}.mag.r .mag-links{right:92px}
.mag .mag-links a{display:block;padding:7px 10px;border-radius:9px;font-size:15px;font-weight:500;color:var(--ink);white-space:nowrap}
.mag .mag-links a[aria-current]{background:var(--raised);color:var(--acc)}
.mag:hover .mag-fluid,.mag:focus-within .mag-fluid{opacity:1;transform:scaleX(1)}
.mag:hover .mag-links,.mag:focus-within .mag-links{opacity:1;pointer-events:auto}
.t-dark .mag-fluid{filter:drop-shadow(0 0 4px rgba(242,244,248,.28)) drop-shadow(0 0 12px rgba(242,244,248,.10))}
@media (prefers-reduced-motion: reduce){.mag .mag-fluid{transform:none;transition:opacity .2s}}
"""


def ferro_svg(side="l", strength=1.0, w=84, h=360, uid="f"):
    """Glossy ferrofluid welling out of the rail with spikes leaning outward (toward a cursor).
    strength 0..1 sets spike length; drawn once, static (the live version animates in JS)."""
    import math as _m
    rail_x = 12
    n = 8
    top, bot = 58, 302
    # the mound of fluid hugging the rail: thickest where the cursor is (the middle)
    def body(y):
        t = (y - top) / (bot - top)
        return 5 + 13 * strength * _m.sin(_m.pi * min(max(t, 0), 1)) ** 0.8
    spikes = []
    for i in range(n):
        yc = top + 18 + i * ((bot - top - 36) / (n - 1))
        dcen = abs(i - (n - 1) / 2) / ((n - 1) / 2)
        length = (10 + 46 * (1 - dcen ** 1.5)) * strength     # closer to the cursor = taller spike
        half = 11 - 3.5 * dcen
        lean = (yc - (top + bot) / 2) * -0.06 * strength       # tips lean toward the cursor's height
        spikes.append((yc, length, half, lean))
    pts = [f"M{rail_x},{top - 14}", f"Q{rail_x + 4},{top} {rail_x + body(top + 8):.1f},{top + 8}"]
    for yc, length, half, lean in spikes:
        x0 = rail_x + body(yc)
        tip_x, tip_y = x0 + length, yc + lean
        pts.append(f"L{rail_x + body(yc - half):.1f},{yc - half:.1f}")
        # concave flanks, like real ferrofluid peaks
        pts.append(f"C{x0 + length * 0.18:.1f},{yc - half * 0.35:.1f} {x0 + length * 0.62:.1f},{tip_y - 1.4:.1f} {tip_x:.1f},{tip_y:.1f}")
        pts.append(f"C{x0 + length * 0.62:.1f},{tip_y + 1.4:.1f} {x0 + length * 0.18:.1f},{yc + half * 0.35:.1f} {rail_x + body(yc + half):.1f},{yc + half:.1f}")
    pts.append(f"L{rail_x + body(bot - 8):.1f},{bot - 8} Q{rail_x + 4},{bot} {rail_x},{bot + 14} Z")
    d_path = " ".join(pts)
    shine = []
    for yc, length, half, lean in spikes:
        x0 = rail_x + body(yc)
        shine.append(f'<path d="M{x0 - 2:.1f},{yc - half * 0.6:.1f} C{x0 + length * 0.2:.1f},{yc - half * 0.3:.1f} '
                     f'{x0 + length * 0.55:.1f},{yc + lean - 1.8:.1f} {x0 + length * 0.86:.1f},{yc + lean - 0.6:.1f}" '
                     f'style="fill:none;stroke:var(--ferro-hi);stroke-width:1.8;stroke-linecap:round;opacity:.9"></path>')
    flip = f' transform="translate({w},0) scale(-1,1)"' if side == "r" else ""
    return (f'<svg class="mag-fluid" width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true">'
            f'<defs><linearGradient id="{uid}g" x1="0" y1="0" x2="1" y2="0.3">'
            f'<stop offset="0" style="stop-color:var(--ferro)"></stop><stop offset=".55" style="stop-color:var(--ferro)"></stop>'
            f'<stop offset="1" style="stop-color:var(--ferro-hi);stop-opacity:.35"></stop></linearGradient></defs>'
            f'<g{flip}><path d="{d_path}" style="fill:url(#{uid}g);stroke:var(--ferro-hi);stroke-width:1;stroke-opacity:.45"></path>'
            f'{"".join(shine)}<ellipse cx="{rail_x + 6}" cy="{(top + bot) / 2 - 30:.0f}" rx="3" ry="16" '
            f'style="fill:var(--ferro-hi);opacity:.5"></ellipse></g></svg>')


def rail(current: str, side="l"):
    stems = [s for s, _, _ in PAGES]
    idx = stems.index(current) if current in stems else 0
    bead_top = 44 + idx * (272 / (len(PAGES) - 1))
    links = "".join(
        f'<a href="{s}.dc.html"{" aria-current=page" if s == current else ""}>{l}</a>' for s, l, _ in PAGES)
    return (f'<nav class="mag {side}" aria-label="Pages"><span class="mag-bar"></span>{ferro_svg(side, uid="r" + current)}'
            f'<span class="mag-bead" style="top:{bead_top:.0f}px"></span><div class="mag-links">{links}</div></nav>')


# ------------------------------------------------------------------ squircle icons -------

SQ = "M50,0 C88,0 100,12 100,50 C100,88 88,100 50,100 C12,100 0,88 0,50 C0,12 12,0 50,0 Z"


def glyph(kind, ink):
    s = f"stroke:{ink}"
    f = f"fill:{ink}"
    if kind == "market":
        return (f'<path d="M30,20 L30,80 M50,14 L50,70 M70,30 L70,84" style="{s};stroke-width:4;opacity:.55"></path>'
                f'<rect x="22" y="32" width="16" height="30" rx="2" style="fill:var(--up)"></rect>'
                f'<rect x="42" y="24" width="16" height="26" rx="2" style="fill:var(--down)"></rect>'
                f'<rect x="62" y="42" width="16" height="30" rx="2" style="fill:var(--up)"></rect>')
    if kind == "model":
        return (f'<path d="M20,18 L20,80 L84,80" style="fill:none;{s};stroke-width:5;opacity:.45;stroke-linecap:round;stroke-linejoin:round"></path>'
                f'<path d="M31,27 C40,52 55,63 79,66" style="fill:none;{s};stroke-width:9;stroke-linecap:round"></path>'
                f'<circle cx="31" cy="27" r="7.5" style="{f}"></circle>')
    if kind == "maths":
        return (f'<path d="M26,30 L74,30 M26,50 L60,50 M26,70 L74,70" style="{s};stroke-width:0"></path>'
                f'<text x="50" y="66" text-anchor="middle" style="{f};font-size:46px;font-weight:700;font-family:Georgia,serif;font-style:italic">∫</text>')
    if kind == "finding":
        return "".join(f'<circle cx="{x}" cy="{y}" r="7.5" style="{f}"></circle>'
                       for x, y in ((28, 34), (64, 26), (46, 54), (74, 64), (28, 74)))
    if kind == "about":
        return (f'<circle cx="50" cy="27" r="8" style="{f}"></circle>'
                f'<path d="M50,45 L50,76" style="{s};stroke-width:11;stroke-linecap:round"></path>')
    if kind == "team":
        return (f'<circle cx="36" cy="38" r="11" style="{f}"></circle><circle cx="66" cy="38" r="11" style="{f};opacity:.7"></circle>'
                f'<path d="M16,78 C18,58 54,58 56,78 Z" style="{f}"></path><path d="M46,78 C48,60 84,60 86,78 Z" style="{f};opacity:.7"></path>')
    if kind == "refs":
        return (f'<path d="M28,22 L28,80 M28,22 L64,22 L72,30 L72,80 L28,80" style="fill:none;{s};stroke-width:6;stroke-linejoin:round"></path>'
                f'<path d="M38,44 L62,44 M38,56 L62,56 M38,68 L54,68" style="{s};stroke-width:5;stroke-linecap:round"></path>')
    if kind == "home":
        return (f'<path d="M22,50 L50,26 L78,50 M31,43 L31,76 L69,76 L69,43" style="fill:none;{s};stroke-width:8;'
                f'stroke-linejoin:round;stroke-linecap:round"></path>')
    if kind == "slow":
        return f'<path d="M12,60 C30,24 56,24 70,50 C77,62 82,63 90,56" style="fill:none;{s};stroke-width:8;stroke-linecap:round"></path>'
    if kind == "fast":
        return (f'<path d="M10,52 L20,34 L30,66 L40,36 L50,64 L60,38 L70,62 L80,40 L90,52" style="fill:none;{s};'
                f'stroke-width:7;stroke-linecap:round;stroke-linejoin:round"></path>')
    if kind == "play":
        return f'<path d="M38,28 L74,50 L38,72 Z" style="{f}"></path>'
    raise ValueError(kind)


ICON_FOR = {"Main": "home", "Market": "market", "Model": "model", "Maths": "maths", "Finding": "finding",
            "About": "about", "Team": "team", "References": "refs"}


def squircle(kind, size=48, fill="var(--raised)", ink="var(--ink)", ring=True):
    ring_el = '<path d="M50,1 C87.5,1 99,12.5 99,50 C99,87.5 87.5,99 50,99 C12.5,99 1,87.5 1,50 C1,12.5 12.5,1 50,1 Z" style="fill:none;stroke:var(--line);stroke-width:1.5"></path>' if ring else ""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" aria-hidden="true" style="flex-shrink:0;display:block">'
            f'<path d="{SQ}" style="fill:{fill}"></path>{ring_el}{glyph(kind, ink)}</svg>')


# ------------------------------------------------------------------ charts ---------------

class Scale:
    def __init__(self, d0, d1, r0, r1, log=False):
        self.d0, self.d1, self.r0, self.r1, self.log = d0, d1, r0, r1, log

    def __call__(self, v):
        if self.log:
            a, b, v = math.log(self.d0), math.log(self.d1), math.log(v)
        else:
            a, b = self.d0, self.d1
        return self.r0 + (v - a) / (b - a) * (self.r1 - self.r0)


def nice_step(span, target):
    raw = span / max(target, 1)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def ticks(lo, hi, target=5):
    step = nice_step(hi - lo, target)
    v = math.ceil(lo / step) * step
    out = []
    while v <= hi + 1e-9:
        out.append(round(v, 10))
        v += step
    return out


class Ink:
    """Chart styling for one design: token names, font, sizes, stroke weights."""

    def __init__(self, font="inherit", size=13, line_w=3, grid="var(--grid)", axis="var(--line)", text="var(--muted)",
                 strong="var(--ink)", model="var(--acc)", ref="var(--muted)", bar_radius=2, dot=None):
        self.font, self.size, self.line_w = font, size, line_w
        self.grid, self.axis, self.text, self.strong = grid, axis, text, strong
        self.model, self.ref, self.bar_radius, self.dot = model, ref, bar_radius, dot


def T(x, y, s, ink: Ink, fill=None, anchor="start", weight=400, size=None, italic=False):
    st = f"fill:{fill or ink.text};font-family:{ink.font};font-size:{size or ink.size}px;font-weight:{weight}"
    if italic:
        st += ";font-style:italic"
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" style="{st}">{esc(s)}</text>'


def L(x1, y1, x2, y2, stroke, w=1, dash=None):
    d = f";stroke-dasharray:{dash}" if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" style="stroke:{stroke};stroke-width:{w}{d}"></line>'


def P(pts, stroke, w=2, dash=None, fill="none"):
    d = f";stroke-dasharray:{dash}" if dash else ""
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return (f'<polyline points="{p}" style="fill:{fill};stroke:{stroke};stroke-width:{w};stroke-linejoin:round;'
            f'stroke-linecap:round{d}"></polyline>')


def R(x, y, w, h, fill, rx=0, opacity=None):
    o = f";opacity:{opacity}" if opacity is not None else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" rx="{rx}" style="fill:{fill}{o}"></rect>'


def C(x, y, r, fill, stroke=None, sw=2):
    st = f"fill:{fill}" + (f";stroke:{stroke};stroke-width:{sw}" if stroke else "")
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" style="{st}"></circle>'


def svg(w, h, label, body):
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}" '
            f'style="display:block;max-width:100%;height:auto;overflow:visible">{body}</svg>')


def candles(w, h, rows, prev_close, ink: Ink, axis_w=84, label_every=10, vol_frac=0.2, show_last=True):
    """Daily candles. rows: [date, o, h, l, c, vol]. Green up, red down, price axis right."""
    n = len(rows)
    pw = w - axis_w
    top, time_h = 10, 24
    vol_h = (h - top - time_h) * vol_frac
    pb = h - time_h - vol_h - 12
    lo = min(r[3] for r in rows)
    hi = max(r[2] for r in rows)
    pad = (hi - lo) * 0.06
    lo, hi = lo - pad, hi + pad
    y = Scale(lo, hi, pb, top)
    sw = pw / (n + 2)
    bw = max(2.0, sw * 0.64)
    last = rows[-1][4]
    yl = y(last)
    out = []
    for tv in ticks(lo, hi, 5):
        out.append(L(0, y(tv), pw, y(tv), ink.grid))
        if abs(y(tv) - yl) > 20:
            out.append(T(pw + 10, y(tv) + 4, inr(tv, 0), ink))
    vmax = max(r[5] for r in rows)
    for i, (dt, o, hh, ll, c, v) in enumerate(rows):
        cx = sw * (i + 0.5)
        col = "var(--up)" if c >= o else "var(--down)"
        out.append(L(cx, y(hh), cx, y(ll), col, 1.3))
        yt, yb = y(max(o, c)), y(min(o, c))
        out.append(R(cx - bw / 2, yt, bw, max(1.4, yb - yt), col))
        vh = v / vmax * vol_h
        out.append(R(cx - bw / 2, h - time_h - vh, bw, vh, col, opacity=0.4))
        if i % label_every == 0:
            out.append(T(cx, h - 6, dt, ink, anchor="middle"))
    out.append(L(0, h - time_h, pw, h - time_h, ink.axis))
    out.append(T(pw + 10, h - time_h - vol_h + 10, "Volume", ink, size=ink.size - 2))
    if show_last:
        col = "var(--up)" if last >= prev_close else "var(--down)"
        out.append(L(0, yl, pw, yl, col, 1, "4 3"))
        out.append(R(pw + 2, yl - 11, axis_w - 2, 22, col, rx=3))
        out.append(T(pw + 8, yl + 4.5, inr(last), ink, fill="var(--on-up)", weight=700))
    return "".join(out)


def line_chart(w, h, series, ink: Ink, x_dom, y_dom, x_ticks, y_ticks, x_fmt=str, y_fmt=str, left=48, bottom=30,
               top=16, right=10, refs=(), log_x=False, labels=(), dots=()):
    """series: [{pts, color, w, dash}], refs: [(y, label, color)], labels: [(x, y, text, color, anchor, weight)]."""
    xs = Scale(x_dom[0], x_dom[1], left, w - right, log=log_x)
    ys = Scale(y_dom[0], y_dom[1], h - bottom, top)
    out = []
    for v in y_ticks:
        out.append(L(left, ys(v), w - right, ys(v), ink.grid))
        out.append(T(left - 10, ys(v) + 4, y_fmt(v), ink, anchor="end"))
    out.append(L(left, h - bottom, w - right, h - bottom, ink.axis))
    for v in x_ticks:
        out.append(T(xs(v), h - bottom + 20, x_fmt(v), ink, anchor="middle"))
    for yv, lab, col in refs:
        out.append(L(left, ys(yv), w - right, ys(yv), col, 1.5, "6 6"))
        if lab:
            out.append(T(w - right, ys(yv) - 8, lab, ink, anchor="end"))
    for s in series:
        out.append(P([(xs(a), ys(b)) for a, b in s["pts"]], s.get("color", ink.model), s.get("w", ink.line_w), s.get("dash")))
    for (a, b, r, fill, stroke) in dots:
        out.append(C(xs(a), ys(b), r, fill, stroke))
    for (a, b, text, col, anchor, weight) in labels:
        out.append(T(xs(a), ys(b), text, ink, fill=col, anchor=anchor, weight=weight))
    return "".join(out), xs, ys


def histogram(w, h, edges, counts, median, rand_median, ink: Ink, left=10, bottom=28):
    xs = Scale(edges[0], edges[-1], left, w - 10)
    ys = Scale(0, max(counts) * 1.14, h - bottom, 34)
    out = []
    bw = xs(edges[1]) - xs(edges[0])
    for i, c in enumerate(counts):
        if c:
            out.append(R(xs(edges[i]) + 1, ys(c), bw - 2, (h - bottom) - ys(c), ink.model, rx=ink.bar_radius, opacity=0.9))
    out.append(L(left, h - bottom, w - 10, h - bottom, ink.axis))
    for v in range(0, int(edges[-1]) + 1):
        out.append(T(xs(v), h - bottom + 19, f"{v}", ink, anchor="middle"))
    xr = xs(rand_median)
    out.append(L(xr, 12, xr, h - bottom, ink.strong, 1.5, "4 4"))
    out.append(T(xr + 7, 12 + ink.size, "Two random parameter sets", ink, fill=ink.strong, weight=700))
    out.append(T(xr + 7, 14 + 2 * ink.size, f"median {rand_median:.2f}", ink))
    xm = xs(median)
    out.append(L(xm, 12, xm, h - bottom, ink.model, 2.5))
    out.append(T(xm + 8, 12 + ink.size, "Equally good fits", ink, fill=ink.strong, weight=700))
    out.append(T(xm + 8, 14 + 2 * ink.size, f"median {median:.2f}", ink))
    return "".join(out)


PLAIN = {
    "kappa_s": ("Speed back to normal", "slow", "κ"), "kappa_f": ("Speed back to normal", "fast", "κ"),
    "sigma_s": ("Volatility of volatility", "slow", "ξ"), "sigma_f": ("Volatility of volatility", "fast", "ξ"),
    "rho_s": ("Price–volatility link", "slow", "ρ"), "rho_f": ("Price–volatility link", "fast", "ρ"),
    "theta_s": ("Long-run level", "slow", "θ"), "theta_f": ("Long-run level", "fast", "θ"),
    "v0_s": ("Today's level", "slow", "v₀"), "v0_f": ("Today's level", "fast", "v₀"),
}


def param_bars(w, rows, ink: Ink, row_h=34, label_w=260, only=None, legend=True, compact=False):
    rows = sorted(rows, key=lambda r: -r["fits"])
    if only:
        rows = [r for r in rows if r["name"] in only]
    top = 40 if legend else 6
    h = top + row_h * len(rows) + (22 if compact else 46)
    xs = Scale(0, 6, label_w, w - 46)
    out = []
    if legend:
        out.append(R(label_w, 6, 22, 11, ink.model, rx=2))
        out.append(T(label_w + 30, 16, "Equally good fits", ink))
        out.append(L(label_w + 192, 3, label_w + 192, 20, ink.strong, 2.5))
        out.append(T(label_w + 202, 16, "Two random parameter sets", ink))
    for v in range(0, 7):
        out.append(L(xs(v), top - 4, xs(v), top + row_h * len(rows), ink.grid if v else ink.axis))
        out.append(T(xs(v), top + row_h * len(rows) + 18, f"{v}", ink, anchor="middle"))
    for i, r in enumerate(rows):
        name, factor, sym = PLAIN[r["name"]]
        yc = top + row_h * i + row_h / 2
        if compact:
            out.append(T(0, yc + 4, f"{name}, {factor}", ink, fill=ink.strong, weight=500))
        else:
            out.append(T(0, yc + 5, name, ink, fill=ink.strong, weight=500))
            out.append(T(label_w - 14, yc + 5, f"{sym} {factor}", ink, anchor="end"))
        bh = row_h * 0.46
        out.append(R(xs(0), yc - bh / 2, xs(r["fits"]) - xs(0), bh, ink.model, rx=ink.bar_radius))
        xr = xs(r["random"])
        out.append(L(xr, yc - row_h * 0.38, xr, yc + row_h * 0.38, ink.strong, 2.5))
        out.append(T(max(xs(r["fits"]), xr) + 8, yc + 5, f"{r['fits']:.2f}", ink, fill=ink.strong, weight=700))
    if not compact:
        out.append(T(xs(0), h - 2, "Median distance between fits, in spreads of the training data", ink, size=ink.size - 1))
    return h, "".join(out)


def stock_panel(w, rows, rand_median, ink: Ink):
    n = len(rows)
    top_h, gap, bot_h = 190, 58, 160
    h = top_h + gap + bot_h + 28
    left, rm = 48, 196
    xs = Scale(0, n - 1, left, w - rm)
    emax = max(max(r[1], r[2]) for r in rows) * 100 * 1.1
    ye = Scale(0, emax, top_h, 20)
    out = [T(left, 12, "Price error each day, as a share of the stock price", ink, fill=ink.strong)]
    for v in ticks(0, emax, 3):
        out.append(L(left, ye(v), w - rm, ye(v), ink.grid if v else ink.axis))
        out.append(T(left - 8, ye(v) + 4, f"{v:.2g}%", ink, anchor="end"))
    out.append(P([(xs(i), ye(r[2] * 100)) for i, r in enumerate(rows)], ink.ref, 1.8, "5 4"))
    out.append(P([(xs(i), ye(r[1] * 100)) for i, r in enumerate(rows)], ink.model, 2.6))
    yf, yd_ = ye(rows[-1][2] * 100), ye(rows[-1][1] * 100)
    if abs(yf - yd_) < 34:
        m = (yf + yd_) / 2
        yf, yd_ = (m - 17, m + 17) if yf < yd_ else (m + 17, m - 17)
    out.append(T(w - rm + 14, yf + 4, "Flat volatility", ink))
    out.append(T(w - rm + 14, yd_ + 4, "Double Heston, best fit", ink, fill=ink.strong, weight=700))
    y0 = top_h + gap
    yd = Scale(0, 9, y0 + bot_h, y0 + 10)
    out.append(T(left, y0 - 12, "How far apart the equally good fits landed that day", ink, fill=ink.strong))
    for v in (0, 3, 6, 9):
        out.append(L(left, yd(v), w - rm, yd(v), ink.grid if v else ink.axis))
        out.append(T(left - 8, yd(v) + 4, f"{v}", ink, anchor="end"))
    bw = (w - rm - left) / n * 0.62
    for i, r in enumerate(rows):
        out.append(R(xs(i) - bw / 2, yd(r[3]), bw, yd(0) - yd(r[3]), ink.model, rx=1, opacity=0.9))
    yr = yd(rand_median)
    out.append(L(left, yr, w - rm, yr, ink.strong, 1.5, "4 4"))
    out.append(T(w - rm + 14, yr, "Two random", ink, fill=ink.strong, weight=700))
    out.append(T(w - rm + 14, yr + 16, f"parameter sets, {rand_median:.2f}", ink))
    seen = {}
    for i, r in enumerate(rows):
        seen.setdefault(r[0][:7], i)
    for m, i in seen.items():
        out.append(T(xs(i), h - 4, {"07": "Jul", "08": "Aug", "09": "Sep"}.get(m[5:], m), ink))
    return h, "".join(out)


def sparkline(w, h, closes, stroke=None):
    lo, hi = min(closes), max(closes)
    span = (hi - lo) or 1
    pts = [(i / (len(closes) - 1) * w, 2 + (hi - v) / span * (h - 4)) for i, v in enumerate(closes)]
    col = stroke or ("var(--up)" if closes[-1] >= closes[0] else "var(--down)")
    return svg(w, h, "Price over the period", P(pts, col, 1.7))


# ------------------------------------------------------------------ board wrapper ----------

def board(design, stem, body, height, title, extra_css=""):
    """One artboard file: fixed root, theme classes, fonts, switch + rail, dark tweak + Play toggle."""
    d = design
    css = (f"body{{margin:0;background:{d.dark['bg']}}}a{{color:inherit;text-decoration:none}}"
           f".dh{{position:relative;box-sizing:border-box;background:var(--bg);color:var(--ink);font-family:{d.body_font};"
           f"overflow:hidden;transition:background-color .2s ease,color .2s ease}}"
           f".up{{color:var(--up)}}.dn{{color:var(--down)}}.mu{{color:var(--muted)}}.bo{{color:var(--body)}}"
           f".b-tick-in{{-webkit-mask-image:linear-gradient(90deg,#000 88%,transparent);mask-image:linear-gradient(90deg,#000 88%,transparent)}}"
           + theme_css(d.light, d.dark) + SWITCH_CSS + RAIL_CSS + d.css + extra_css)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="{d.fonts_url}">
<style>{css}</style>
</helmet>
<div class="dh {{{{theme}}}}" style="width: 1440px; height: {height}px;">
{switch()}
{rail(stem, d.rail_side)}
{body}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"dark":{{"editor":"boolean","default":{str(d.default_dark).lower()}}},"$preview":{{"width":1440,"height":{height}}}}}'>
class Component extends DCLogic {{
renderVals() {{
const s = this.state || {{}};
const dark = s.dark !== undefined ? s.dark : (this.props.dark ?? {str(d.default_dark).lower()});
return {{ theme: dark ? 't-dark' : 't-light', dark: dark, toggle: () => this.setState({{ dark: !dark }}) }};
}}
}}
</script>
</body>
</html>
"""


def preview(dc_html: str, theme: str) -> str:
    """Plain HTML render of a board for local screenshots (holes filled, handlers dropped)."""
    import re
    head_css = re.search(r"<helmet>(.*?)</helmet>", dc_html, re.S).group(1)
    body = re.search(r"<x-dc>.*?</helmet>(.*)</x-dc>", dc_html, re.S).group(1)
    body = body.replace("{{theme}}", theme).replace("{{dark}}", "true" if theme == "t-dark" else "false")
    body = re.sub(r'\sonClick="\{\{[^}]+\}\}"', "", body)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">{head_css}</head><body>{body}'
            f'<script>document.fonts.ready.then(()=>document.body.setAttribute("data-ready","1"))</script></body></html>')
