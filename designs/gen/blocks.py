"""Content blocks with neutral class names (b-*). Every design styles them its own way.

The words and numbers come from content.py; charts from kit.py with the design's Ink.
"""
from __future__ import annotations

import content as X
import kit
from kit import arrow, esc, inr, squircle, svg


# ------------------------------------------------------------------ market ---------------

def ticker(label=True, syms=None):
    items = []
    for s in syms or X.FEATURED:
        v = X.w(s)
        a, c = arrow(v["pct"])
        items.append(f'<span class="b-ti"><b>{s}</b><span>{inr(v["last"])}</span><span class="{c}">{a} {abs(v["pct"]):.2f}%</span></span>')
    lab = f'<span class="b-ti-lab">Close {X.LAST_DAY}</span>' if label else ""
    return f'<div class="b-tick" aria-label="Closing prices, scrolling"><div class="b-tick-in">{lab}{"".join(items)}</div></div>'


def watch_table(syms=None, spark=(84, 26), sel="RELIANCE", names=False, cols=("Symbol", "62 days", "Close", "Day")):
    rows = []
    for s in syms or (X.FEATURED + ["BHARTIARTL", "KOTAKBANK", "BAJFINANCE", "MARUTI"]):
        v = X.w(s)
        a, c = arrow(v["pct"])
        nm = f'<span class="b-sub">{esc(X.NAMES.get(s, ""))}</span>' if names else ""
        rows.append(f'<tr{" class=sel" if s == sel else ""}><td><b>{s}</b>{nm}</td><td>{kit.sparkline(spark[0], spark[1], v["closes"])}</td>'
                    f'<td>{inr(v["last"])}</td><td class="{c}">{a} {abs(v["pct"]):.2f}%</td></tr>')
    head = "".join(f"<th>{h}</th>" for h in cols)
    return f'<table class="b-tb"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def rel_stats():
    r = X.REL_LAST
    return [("Open", inr(r[1])), ("High", inr(r[2])), ("Low", inr(r[3])), ("Close", inr(r[4])),
            ("Prev close", inr(r[6])), ("Volume", f"{r[5] / 1e5:.1f} lakh")]


def rel_change():
    r = X.REL_LAST
    chg = r[4] - r[6]
    a, c = arrow(chg)
    return f'<span class="{c}">{a} {inr(abs(chg))} ({abs(chg / r[6] * 100):.2f}%) on {X.LAST_DAY}</span>'


def rel_candles(ink, w=800, h=460, label_every=10):
    return svg(w, h, "RELIANCE daily candlesticks, 1 Jul to 25 Sep 2026, NSE closing data; green closed higher, red lower",
               kit.candles(w, h, X.REL_ROWS, X.REL_LAST[6], ink, label_every=label_every))


def nifty_line(ink, w=1180, h=240, which="NIFTY", color=None):
    data = X.D["index_close"][which]
    lo, hi = min(x[1] for x in data), max(x[1] for x in data)
    pad = (hi - lo) * 0.12
    body, _, _ = kit.line_chart(w, h, [{"pts": [(i, x[1]) for i, x in enumerate(data)], "w": 2.5, "color": color or ink.model}], ink,
                                (0, len(data) - 1), (lo - pad, hi + pad), [0, 21, 42, len(data) - 1],
                                kit.ticks(lo - pad, hi + pad, 4), x_fmt=lambda i: X.short_date(data[int(i)][0]),
                                y_fmt=lambda v: inr(v, 0), left=66)
    name = "NIFTY 50" if which == "NIFTY" else "NIFTY BANK"
    return svg(w, h, f"{name} closing level over 62 trading days", body)


# ------------------------------------------------------------------ model ----------------

def pricing_form(cls="b-form"):
    K = X.K
    return f"""<form class="{cls}" onsubmit="return false">
<label><span class="b-lab">Underlying</span><select><option>NIFTY 50, {inr(X.SPOT)}</option></select></label>
<label><span class="b-lab">Expiry</span><select><option>{X.EXPIRY}, {K['dte']} days</option></select></label>
<label><span class="b-lab">Strike</span><input value="{inr(K['strike'], 0)}"></label>
<fieldset><legend class="b-lab">Type</legend><span class="b-seg"><span class="on">Call</span><span>Put</span></span></fieldset>
<button class="b-btn pri" type="submit">Price option</button>
</form>"""


def chain_table(cols=("Strike", "Call", "Call IV", "Model call", "Put", "Put IV")):
    K = X.K
    rows = []
    for r in X.CHAIN:
        rows.append(f'<tr{" class=sel" if r["strike"] == K["strike"] else ""}><td>{inr(r["strike"], 0)}</td><td>{inr(r["call"])}</td>'
                    f'<td class="b-sub">{r["call_iv"]:.1f}%</td><td class="b-model">{inr(r["dh_call"])}</td><td>{inr(r["put"])}</td>'
                    f'<td class="b-sub">{r["put_iv"]:.1f}%</td></tr>')
    return f'<table class="b-tb"><thead><tr>{"".join(f"<th>{c}</th>" for c in cols)}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def sliders(factor, step="0.001"):
    out = []
    for f, sym, name, val, lo, hi in X.SLIDERS:
        if f != factor:
            continue
        fmt = f"{val:.4f}" if sym in ("v₀", "θ") else f"{val:.2f}"
        out.append(f'<div class="b-sl"><b>{sym}</b><label>{name}<input type="range" min="{lo}" max="{hi}" step="{step}" value="{val}" '
                   f'aria-label="{factor} factor {name}"></label><output>{fmt}</output></div>')
    return "".join(out)


def greeks(cls="b-greek"):
    return "".join(f'<div class="{cls}"><span class="b-lab">{n}</span><b>{v}</b><span class="b-sub">{u}</span></div>' for n, v, u in X.GREEKS)


def market_smile(ink, w=620, h=360, left=52):
    K = X.K
    mk = [(r["strike"], r["mkt_iv"]) for r in X.D["chain"] if r.get("mkt_iv")]
    dh = [(r["strike"], r["dh_iv"]) for r in X.D["chain"]]
    lo_k, hi_k = X.D["chain"][0]["strike"], X.D["chain"][-1]["strike"]
    body, xs, ys = kit.line_chart(
        w, h, [{"pts": dh}], ink, (lo_k, hi_k), (9, 22), [lo_k, K["strike"], hi_k], [10, 14, 18, 22],
        x_fmt=lambda v: inr(v, 0), y_fmt=lambda v: f"{v:g}%", left=left,
        dots=[(a, b, 4.5, "var(--bg)", ink.strong) for a, b in mk],
        labels=[(lo_k, dh[0][1] + 0.7, "Double Heston, starting settings", ink.model, "start", 700),
                (lo_k, mk[0][1] + 1.1, "Market, from NSE closing prices", ink.strong, "start", 700)])
    body += kit.L(xs(K["spot"]), 16, xs(K["spot"]), h - 30, ink.axis, 1, "2 4") + kit.T(xs(K["spot"]) + 6, h - 38, "spot", ink)
    return svg(w, h, "Implied volatility by strike: market (NSE closing prices, 25 Sep 2026) against Double Heston at its starting settings", body)


# ------------------------------------------------------------------ research charts ------

def smile(ink, w=720, h=400, x_fmt=lambda v: f"{v:.0f}%", flat_label="One fixed volatility, 20%", spot=True):
    pts = X.D["smile_30d"]
    body, xs, ys = kit.line_chart(
        w, h, [{"pts": pts}], ink, (80, 120), (14, 27.5), [80, 90, 100, 110, 120], [16, 20, 24],
        x_fmt=x_fmt, y_fmt=lambda v: f"{v:g}%", refs=[(20, flat_label, ink.ref)],
        labels=[(80, pts[0][1] + 0.9, f"Double Heston, {pts[0][1]:.1f}%", ink.strong, "start", 700),
                (120, pts[-1][1] - 1.4, f"{pts[-1][1]:.1f}%", ink.strong, "end", 700)],
        dots=[(80, pts[0][1], 5, ink.model, None), (120, pts[-1][1], 5, ink.model, None)])
    if spot:
        body += kit.L(xs(100), 16, xs(100), h - 30, ink.axis, 1, "2 4") + kit.T(xs(100) + 6, h - 38, "today's price", ink)
    return svg(w, h, "Implied volatility by strike at 30 days: flat 20% for one fixed volatility; Double Heston falls from "
               f"{pts[0][1]:.1f}% at strike 80 to {pts[-1][1]:.1f}% at strike 120", body)


def skew(ink, w=560, h=260, left=34):
    rows = X.D["skew_by_T"]
    body, _, _ = kit.line_chart(
        w, h, [{"pts": [(r[0], r[1]) for r in rows]}], ink, (7, 730), (0, 4), [7, 30, 90, 365, 730], [0, 1, 2, 3, 4],
        x_fmt=lambda v: {7: "1 wk", 30: "1 mo", 90: "3 mo", 365: "1 yr", 730: "2 yr"}[v], y_fmt=lambda v: f"{v:g}",
        log_x=True, left=left,
        labels=[(7, rows[0][1] + 0.35, f"{rows[0][1]:.1f} points at 1 week", ink.strong, "start", 700),
                (730, rows[-1][1] - 0.55, f"{rows[-1][1]:.1f} at 2 years", ink.strong, "end", 700)],
        dots=[(r[0], r[1], 3.5, ink.model, None) for r in rows])
    return svg(w, h, "Skew by time to expiry, falling from 3.4 volatility points at one week to 1.2 at two years", body)


def hist(ink, w=1100, h=300):
    return svg(w, h, f"Histogram: how far apart equally good fits landed on {X.D['hist']['n']:,} real surfaces",
               kit.histogram(w, h, X.D["hist"]["edges"], X.D["hist"]["counts"], X.D["hist"]["median"], X.RAND, ink))


def bars(ink, w=1000, **kw):
    h, body = kit.param_bars(w, X.PER, ink, **kw)
    return svg(w, h, "How far apart equally good fits land for each setting, against two random parameter sets", body)


def stock(ink, w=1180):
    h, body = kit.stock_panel(w, X.REL_STOCK, X.RAND, ink)
    return svg(w, h, "RELIANCE, 60 trading days: price error and dispersion by day", body)


def picks(sel="RELIANCE", cls="b-chip"):
    return "".join(f'<span class="{cls}{" on" if t == sel else ""}">{t}</span>'
                   for t in ["RELIANCE", "HDFCBANK", "INFY", "TCS", "SBIN", "ICICIBANK", "ITC", "LT"])


# ------------------------------------------------------------------ text blocks ----------

def nums(items, cls="b-num"):
    return "".join(f'<div class="{cls}"><b>{n}</b><span>{esc(c)}</span></div>' for n, c in items)


def equations(cls="b-eq"):
    rows = [("The price moves with two variances", X.EQ_PRICE), ("Each variance pulls back to its own level", X.EQ_VAR),
            ("Independent factors multiply", X.EQ_CF), ("The price is one integral (Gil-Pelaez)", X.EQ_CALL),
            ("A factor never touches zero when", X.EQ_FELLER)]
    return "".join(f'<div class="{cls}"><span class="b-lab">{esc(l)}</span><div class="b-eqn">{esc(e)}</div></div>' for l, e in rows)


def steps(cls="b-steps", numbered=True):
    li = "".join(f'<li>{f"<b class=b-n>{i}</b>" if numbered else ""}<span><b>{esc(h)}</b><span>{esc(t)}</span></span></li>'
                 for i, (h, t) in enumerate(X.MATHS_STEPS, 1))
    return f'<ol class="{cls}">{li}</ol>'


def lineage(cls="b-lin"):
    li = "".join(f'<li{" class=now" if y == "2009" else ""}><b class="b-y">{y}</b><span><b>{n}</b><span>{d}</span></span></li>' for y, n, d in X.LINEAGE)
    return f'<ol class="{cls}">{li}</ol>'


def bullet_list(items, cls="b-list"):
    return f'<ul class="{cls}">{"".join(f"<li>{esc(i)}</li>" for i in items)}</ul>'


def video(icon_fill="var(--acc)", icon_ink="var(--on-acc)", cls="b-video"):
    return (f'<figure class="{cls}"><button type="button" aria-label="Play the project video">'
            f'{squircle("play", 96, fill=icon_fill, ink=icon_ink, ring=False)}</button>'
            f'<figcaption>{esc(X.VIDEO_CAPTION)} The video loads only when played.</figcaption></figure>')


def team_cards(cls="b-person", icon=True):
    return "".join(f'<div class="{cls}">{"<span class=b-ph>" + squircle("team", 64, ring=False) + "</span>" if icon else ""}'
                   f'<b>{esc(n)}</b><span>{esc(r)}</span></div>' for n, r in X.TEAM)


def refs(cls="b-refs", numbered=True):
    n = 0
    out = []
    for g, items in X.REFS:
        lis = []
        for a, t, s in items:
            n += 1
            num = f'<span class="b-rn">[{n}]</span>' if numbered else ""
            lis.append(f'<li>{num}<span><b>{esc(a)}</b> <span class="b-rt">{esc(t)}</span> <span class="b-sub">{esc(s)}</span></span></li>')
        out.append(f'<section class="{cls}"><h2>{esc(g)}</h2><ol>{"".join(lis)}</ol></section>')
    return "".join(out)


def page_links(current, size=44, fill="var(--raised)", ink="var(--ink)", acc_for="Model", cls="b-links"):
    cells = []
    for s, l, d in kit.PAGES:
        if s == current:
            continue
        f, i = ("var(--acc)", "var(--on-acc)") if s == acc_for else (fill, ink)
        cells.append(f'<a href="{s}.dc.html">{squircle(kit.ICON_FOR[s], size, fill=f, ink=i)}<span><b>{l}</b><span>{d}</span></span></a>')
    return f'<nav class="{cls}" aria-label="All pages">{"".join(cells)}</nav>'


FOOT = ("Not trading advice. Prices are NSE closing prices; live Upstox prices replace them during market hours.", X.REPO)
