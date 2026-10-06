"""01 · Amber Instrument — the look the user chose: a precision instrument in amber on near-black."""
from __future__ import annotations

import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle, svg

LIGHT = dict(bg="#F3F2EE", surf="#FFFFFF", raised="#ECEAE3", line="#D6D3C9", grid="#E6E3DB", ink="#16170F",
             body="#3E3D36", muted="#67665E", acc="#9E6108", on_acc="#FFFFFF", up="#14804F", down="#C9303F",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0B0B0C", ferro_hi="#A7ADB5")
DARK = dict(bg="#0F100E", surf="#151612", raised="#1C1D19", line="#2C2D28", grid="#1F201C", ink="#EDEAE1",
            body="#BDBAB1", muted="#95928A", acc="#F0B24A", on_acc="#17140C", up="#2EBD85", down="#F6465D",
            on_up="#06120C", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

CSS = """
.bar{height:48px;display:flex;align-items:center;gap:28px;padding:0 250px 0 128px;border-bottom:1px solid var(--line);font-size:14px;color:var(--muted)}
.brand{font-weight:700;color:var(--ink);font-size:16px;letter-spacing:-.01em}
.chip{display:inline-flex;align-items:center;gap:8px}.chip i{width:9px;height:9px;border:1.6px solid var(--muted);box-sizing:border-box;display:inline-block}
.tick{height:48px;display:flex;align-items:center;padding:0 250px 0 128px;background:var(--surf);border-bottom:1px solid var(--line);font-size:15px;white-space:nowrap}
.tick-in{flex:1;min-width:0;display:flex;align-items:center;gap:34px;overflow:hidden;mask-image:linear-gradient(90deg,#000 88%,transparent);-webkit-mask-image:linear-gradient(90deg,#000 88%,transparent)}
.tick b{font-weight:700}.tick span{display:inline-flex;gap:9px}
.pg{padding:64px 80px 104px 128px;display:flex;flex-direction:column;gap:72px}
.g{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:24px}
.lbl{font-size:14px;font-weight:700;color:var(--muted)}
.panel{border:1px solid var(--line);background:var(--surf);min-width:0}
.ph{display:flex;justify-content:space-between;align-items:baseline;gap:16px;padding:14px 20px;border-bottom:1px solid var(--line)}
.pb{padding:22px}
.t1{margin:0;font-size:60px;line-height:1.02;font-weight:700;letter-spacing:-.035em}
.t2{margin:0;font-size:34px;line-height:1.1;font-weight:700;letter-spacing:-.025em}
.lead{margin:0;font-size:20px;line-height:1.55;color:var(--body);max-width:760px}
.p{margin:0;font-size:18px;line-height:1.6;color:var(--body)}
.btn{display:inline-flex;align-items:center;height:50px;padding:0 20px;border:1.5px solid var(--line);font-size:17px;font-weight:700;color:var(--ink);background:transparent;font-family:inherit}
.btn.pri{background:var(--acc);border-color:var(--acc);color:var(--on-acc)}
.big{font-weight:900;letter-spacing:-.04em;line-height:.95}
.prompt{color:var(--acc)}
.tb{width:100%;border-collapse:collapse;font-size:16px}
.tb th{font-size:13px;font-weight:700;color:var(--muted);text-align:right;padding:10px 12px;border-bottom:1px solid var(--line)}
.tb td{text-align:right;padding:10px 12px;border-bottom:1px solid var(--grid)}
.tb th:first-child,.tb td:first-child{text-align:left}
.tb tr.sel td{background:var(--raised);font-weight:700}
.seg{display:inline-flex;border:1.5px solid var(--line)}.seg span{padding:7px 14px;font-size:14px;font-weight:700;color:var(--muted)}
.seg span.on{background:var(--raised);color:var(--acc)}
.sl{display:grid;grid-template-columns:34px 1fr 76px;align-items:center;gap:14px;padding:10px 0;border-bottom:1px solid var(--grid)}
.sl b{font-size:18px;color:var(--acc)}.sl label{display:flex;flex-direction:column;gap:6px;font-size:14px;color:var(--muted)}
.sl input{width:100%;accent-color:#F0B24A}.sl output{text-align:right;font-size:17px;font-weight:700}
.eq{font-size:26px;line-height:1.5;font-family:'Schibsted Grotesk',sans-serif;color:var(--ink);padding:22px 26px;border-left:3px solid var(--acc);background:var(--raised)}
.ft{border-top:1px solid var(--line);padding:26px 80px 40px 128px;display:flex;justify-content:space-between;font-size:15px;color:var(--muted)}
.lnk{font-weight:700;color:var(--acc);font-size:17px}
.idx{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-top:1px solid var(--line);border-left:1px solid var(--line)}
.idx a{display:flex;align-items:center;gap:14px;padding:18px 20px;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.idx b{font-size:17px}.idx span{font-size:14px;color:var(--muted)}
"""

INK = Ink(font="'Schibsted Grotesk',sans-serif", size=13, line_w=3.5)


def bar():
    return (f'<div class="bar"><a href="Main.dc.html" class="brand">rw/ws instrument</a>'
            f'<span class="chip"><i></i>{esc(X.STATUS)}</span></div>')


def footer():
    return ('<footer class="ft"><span>Not trading advice. Prices are NSE closing prices; live Upstox prices replace them during market hours.</span>'
            f'<span>{esc(X.REPO)}</span></footer>')


def ticker():
    items = []
    for s in X.FEATURED:
        v = X.w(s)
        a, c = arrow(v["pct"])
        items.append(f'<span><b>{s}</b>{inr(v["last"])}<span class="{c}">{a} {abs(v["pct"]):.2f}%</span></span>')
    return (f'<div class="tick" aria-label="Closing prices, scrolling"><div class="tick-in"><span class="mu">Close {X.LAST_DAY}</span>'
            f'{"".join(items)}</div></div>')


def smile_chart(w=720, h=400):
    pts = X.D["smile_30d"]
    body, xs, ys = kit.line_chart(
        w, h, [{"pts": pts}], INK, (80, 120), (14, 27.5), [80, 90, 100, 110, 120], [16, 20, 24],
        x_fmt=lambda v: f"{v:.0f}%", y_fmt=lambda v: f"{v:g}%", refs=[(20, "One fixed volatility, 20%", "var(--muted)")],
        labels=[(80, pts[0][1] + 0.9, f"Double Heston, {pts[0][1]:.1f}%", "var(--ink)", "start", 700),
                (120, pts[-1][1] - 1.4, f"{pts[-1][1]:.1f}%", "var(--ink)", "end", 700)],
        dots=[(80, pts[0][1], 5, "var(--acc)", None), (120, pts[-1][1], 5, "var(--acc)", None)])
    body += kit.L(xs(100), 16, xs(100), h - 30, "var(--line)", 1, "2 4") + kit.T(xs(100) + 6, h - 38, "today's price", INK)
    return svg(w, h, "Implied volatility by strike at 30 days: flat 20% for one fixed volatility; Double Heston falls from "
               f"{pts[0][1]:.1f}% at strike 80 to {pts[-1][1]:.1f}% at strike 120", body)


def skew_chart(w=560, h=260):
    rows = X.D["skew_by_T"]
    body, xs, ys = kit.line_chart(
        w, h, [{"pts": [(r[0], r[1]) for r in rows]}], INK, (7, 730), (0, 4), [7, 30, 90, 365, 730], [0, 1, 2, 3, 4],
        x_fmt=lambda v: {7: "1 wk", 30: "1 mo", 90: "3 mo", 365: "1 yr", 730: "2 yr"}[v], y_fmt=lambda v: f"{v:g}",
        log_x=True, left=34,
        labels=[(7, rows[0][1] + 0.35, f"{rows[0][1]:.1f} points at 1 week", "var(--ink)", "start", 700),
                (730, rows[-1][1] - 0.55, f"{rows[-1][1]:.1f} at 2 years", "var(--ink)", "end", 700)],
        dots=[(r[0], r[1], 3.5, "var(--acc)", None) for r in rows])
    return svg(w, h, "Skew by time to expiry, falling from 3.4 volatility points at one week to 1.2 at two years", body)


def page_index(current):
    cells = "".join(
        f'<a href="{s}.dc.html">{squircle(kit.ICON_FOR[s], 44, fill="var(--acc)" if s == "Model" else "var(--raised)", ink="var(--on-acc)" if s == "Model" else "var(--ink)")}'
        f'<span style="display:flex;flex-direction:column;gap:2px"><b>{l}</b><span>{d}</span></span></a>'
        for s, l, d in kit.PAGES if s != current)
    return f'<nav class="idx" aria-label="All pages">{cells}</nav>'


# ------------------------------------------------------------------ pages -----------------

def home():
    slow, fast = X.SLOW, X.FAST
    return f"""
{ticker()}
<div class="pg">
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 5;display:flex;flex-direction:column;gap:26px;padding-top:12px">
      <span class="lbl">Query</span>
      <h1 class="t1"><span class="prompt">$</span> does letting volatility move price options better?</h1>
      <div style="display:flex;flex-direction:column;gap:14px;padding-left:18px;border-left:3px solid var(--acc)">
        <b style="font-size:24px">{esc(X.A_SHORT)}</b>
        <p class="p">{esc(X.A_LONG)}</p>
        <p class="p">{esc(X.TWIST)}</p>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn pri" href="Model.dc.html">{X.CTA['model']}</a><a class="btn" href="Finding.dc.html">{X.CTA['finding']}</a><a class="lnk" style="align-self:center;margin-left:8px" href="Market.dc.html">{X.CTA['market']}</a></div>
    </div>
    <figure class="panel" style="grid-column:6/span 7;margin:0">
      <div class="ph"><span class="lbl">Readout: implied volatility by strike</span><span class="mu" style="font-size:14px">30 days, starting settings</span></div>
      <div class="pb">{smile_chart(740, 420)}</div>
      <figcaption class="mu" style="padding:0 22px 18px;font-size:14px">{esc(X.SMILE_CAPTION)}</figcaption>
    </figure>
  </section>

  <section class="g">
    <div class="panel" style="grid-column:1/span 7">
      <div class="ph"><span class="lbl">Two factors</span><span class="mu" style="font-size:14px">ten settings in all</span></div>
      <div class="pb" style="display:grid;grid-template-columns:1fr 1.25fr;gap:28px;align-items:center">
        <div style="display:flex;flex-direction:column;gap:22px">
          <p class="p" style="font-size:17px">{esc(X.TWO_CLOCKS)}</p>
          <div style="display:flex;align-items:center;gap:14px">{squircle('slow', 52)}<span style="display:flex;flex-direction:column;gap:3px"><b style="font-size:18px">{slow[0]}, {slow[1]}</b><span class="mu" style="font-size:15px">{slow[2]}</span></span></div>
          <div style="display:flex;align-items:center;gap:14px">{squircle('fast', 52, fill='var(--acc)', ink='var(--on-acc)')}<span style="display:flex;flex-direction:column;gap:3px"><b style="font-size:18px">{fast[0]}, {fast[1]}</b><span class="mu" style="font-size:15px">{fast[2]}</span></span></div>
        </div>
        <figure style="margin:0;display:flex;flex-direction:column;gap:6px"><span class="lbl">Skew by time to expiry, volatility points</span>{skew_chart(430, 250)}</figure>
      </div>
    </div>
    <div class="panel" style="grid-column:8/span 5">
      <div class="ph"><span class="lbl">Lineage</span><span class="mu" style="font-size:14px">shown for context</span></div>
      <ol style="list-style:none;margin:0;padding:8px 22px 18px">
        {''.join(f'<li style="display:grid;grid-template-columns:86px 1fr;gap:12px;padding:16px 0;border-bottom:1px solid var(--grid)"><b class="big" style="font-size:30px;{"color:var(--acc)" if y == "2009" else ""}">{y}</b><span style="display:flex;flex-direction:column;gap:3px"><b style="font-size:18px">{n}</b><span class="mu" style="font-size:15px">{d}</span></span></li>' for y, n, d in X.LINEAGE)}
      </ol>
    </div>
  </section>

  <section class="panel">
    <div class="ph"><span class="lbl">Finding, verified</span><a class="lnk" href="Finding.dc.html">{X.CTA['finding']}</a></div>
    <div class="pb g" style="align-items:end;padding:30px 22px">
      <div style="grid-column:1/span 6;display:flex;flex-direction:column;gap:14px">
        <span style="font-size:30px;font-weight:700;letter-spacing:-.02em;line-height:1.25">fit(prices) ≈ exact<br><span class="prompt">recover(settings) = no</span></span>
        <p class="p" style="font-size:17px">{esc(X.FINDING_LINE)} {esc(X.FINDING_SUB)}</p>
      </div>
      {''.join(f'<div style="grid-column:span 2;display:flex;flex-direction:column;gap:8px;padding-left:18px;border-left:1px solid var(--line)"><span class="big" style="font-size:52px;color:var(--acc)">{n}</span><span class="mu" style="font-size:14px;line-height:1.4">{c}</span></div>' for n, c in (("1.80", "recovery skill on simulated data; 1.00 is guessing"), (f"{X.SHARE * 100:.0f}%", "of 2,400 real surfaces had several equally good fits"), (f"{X.RATIO:.1f}×", "further apart than two random parameter sets")))}
    </div>
  </section>

  {page_index('Main')}
</div>
{footer()}
"""


def market():
    rows = []
    for s in X.FEATURED + ["BHARTIARTL", "KOTAKBANK", "BAJFINANCE", "MARUTI"]:
        v = X.w(s)
        a, c = arrow(v["pct"])
        sel = ' class="sel"' if s == "RELIANCE" else ""
        rows.append(f'<tr{sel}><td><b>{s}</b></td><td>{kit.sparkline(84, 26, v["closes"])}</td><td>{inr(v["last"])}</td>'
                    f'<td class="{c}">{a} {abs(v["pct"]):.2f}%</td></tr>')
    r = X.REL_LAST
    chg = r[4] - r[6]
    a, c = arrow(chg)
    cw, ch = 800, 460
    cand = svg(cw, ch, "RELIANCE daily candlesticks, 1 Jul to 25 Sep 2026, NSE closing data",
               kit.candles(cw, ch, X.REL_ROWS, r[6], INK, label_every=10))
    nifty = X.D["index_close"]["NIFTY"]
    nw, nh = 1232, 240
    lo, hi = min(x[1] for x in nifty), max(x[1] for x in nifty)
    nb, nxs, nys = kit.line_chart(nw, nh, [{"pts": [(i, x[1]) for i, x in enumerate(nifty)], "w": 2.5}], INK,
                                  (0, len(nifty) - 1), (lo - 80, hi + 80), [0, 20, 40, len(nifty) - 1],
                                  kit.ticks(lo - 80, hi + 80, 4), x_fmt=lambda i: X.short_date(nifty[int(i)][0]),
                                  y_fmt=lambda v: inr(v, 0), left=64)
    stats = [("Open", r[1]), ("High", r[2]), ("Low", r[3]), ("Close", r[4]), ("Prev close", r[6])]
    return f"""
{bar()}
<div class="pg">
  <div class="g" style="align-items:end">
    <div style="grid-column:1/span 8;display:flex;flex-direction:column;gap:14px"><span class="lbl">Page 2 of 8</span><h1 class="t1">Market</h1><p class="lead">{esc(X.MARKET_SUB)}</p></div>
    <p class="mu" style="grid-column:9/span 4;margin:0;font-size:15px;line-height:1.5">{esc(X.UNIVERSE)}</p>
  </div>
  <section class="g" style="align-items:start">
    <div class="panel" style="grid-column:1/span 4">
      <div class="ph"><span class="lbl">Watchlist</span><span class="mu" style="font-size:14px">close, {X.LAST_DAY}</span></div>
      <table class="tb"><thead><tr><th>Symbol</th><th>62 days</th><th>Close</th><th>Day</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
      <div style="padding:14px 20px"><a class="lnk" href="#">Show all 42</a></div>
    </div>
    <div class="panel" style="grid-column:5/span 8">
      <div class="ph" style="align-items:center">
        <span style="display:flex;align-items:baseline;gap:16px"><b style="font-size:22px">RELIANCE</b><span class="mu" style="font-size:15px">Reliance Industries, NSE</span></span>
        <span style="display:flex;gap:10px"><span class="seg"><span>Line</span><span class="on">Candles</span></span><span class="seg"><span>1M</span><span class="on">3M</span></span></span>
      </div>
      <div class="pb" style="display:flex;flex-direction:column;gap:18px">
        <span style="display:flex;align-items:baseline;gap:16px"><span class="big" style="font-size:56px">{inr(r[4])}</span><span class="{c}" style="font-size:20px;font-weight:700">{a} {inr(abs(chg))} ({abs(chg / r[6] * 100):.2f}%) on {X.LAST_DAY}</span></span>
        {cand}
        <div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));border-top:1px solid var(--line)">
          {''.join(f'<div style="padding:14px 14px 0 0;display:flex;flex-direction:column;gap:5px"><span class="lbl">{k}</span><b style="font-size:19px">{inr(v)}</b></div>' for k, v in stats)}
          <div style="padding:14px 0 0;display:flex;flex-direction:column;gap:5px"><span class="lbl">Volume</span><b style="font-size:19px">{r[5] / 1e5:.1f} lakh</b></div>
        </div>
      </div>
    </div>
  </section>
  <section class="panel">
    <div class="ph"><span class="lbl">NIFTY 50, closing level</span><span class="mu" style="font-size:14px">index levels are published as closes in the F&amp;O file, so this is a line, not candles</span></div>
    <div class="pb">{svg(nw - 46, nh, "NIFTY 50 closing level, 62 trading days", nb)}</div>
  </section>
  <p class="mu" style="margin:0;font-size:15px">Want options on these? <a class="lnk" href="Model.dc.html">Price one on the model page</a></p>
</div>
{footer()}
"""


def model():
    K = X.K
    chain_rows = []
    for r in X.CHAIN:
        sel = ' class="sel"' if r["strike"] == K["strike"] else ""
        chain_rows.append(f'<tr{sel}><td>{inr(r["strike"], 0)}</td><td>{inr(r["call"])}</td><td class="mu">{r["call_iv"]:.1f}%</td>'
                          f'<td style="color:var(--acc)">{inr(r["dh_call"])}</td><td>{inr(r["put"])}</td><td class="mu">{r["put_iv"]:.1f}%</td></tr>')
    mk = [(r["strike"], r["mkt_iv"]) for r in X.D["chain"] if r.get("mkt_iv")]
    dh = [(r["strike"], r["dh_iv"]) for r in X.D["chain"]]
    lo_k, hi_k = X.D["chain"][0]["strike"], X.D["chain"][-1]["strike"]
    body, xs, ys = kit.line_chart(
        620, 360, [{"pts": dh}], INK, (lo_k, hi_k), (9, 22), [lo_k, K["strike"], hi_k], [10, 14, 18, 22],
        x_fmt=lambda v: inr(v, 0), y_fmt=lambda v: f"{v:g}%", left=52,
        dots=[(a, b, 4.5, "var(--bg)", "var(--ink)") for a, b in mk],
        labels=[(lo_k, dh[0][1] + 0.7, "Double Heston, starting settings", "var(--acc)", "start", 700),
                (lo_k, mk[0][1] + 1.1, "Market, from NSE closing prices", "var(--ink)", "start", 700)])
    body += kit.L(xs(K["spot"]), 16, xs(K["spot"]), 330, "var(--line)", 1, "2 4") + kit.T(xs(K["spot"]) + 6, 322, "spot", INK)
    smile = svg(620, 360, "Implied volatility by strike: market (NSE closing prices, 25 Sep 2026) against Double Heston at its starting settings", body)

    def sliders(factor):
        out = []
        for f, sym, name, val, lo, hi in X.SLIDERS:
            if f != factor:
                continue
            fmt = f"{val:.4f}" if sym in ("v₀", "θ") else f"{val:.2f}"
            out.append(f'<div class="sl"><b>{sym}</b><label>{name}<input type="range" min="{lo}" max="{hi}" step="0.001" value="{val}" aria-label="{factor} {name}"></label><output>{fmt}</output></div>')
        return "".join(out)

    greeks = "".join(f'<div style="display:flex;flex-direction:column;gap:6px;padding:18px 20px;border-right:1px solid var(--line)"><span class="lbl">{n}</span>'
                     f'<b class="big" style="font-size:30px">{v}</b><span class="mu" style="font-size:14px">{u}</span></div>' for n, v, u in X.GREEKS)
    return f"""
{bar()}
<div class="pg">
  <div style="display:flex;flex-direction:column;gap:14px"><span class="lbl">Page 3 of 8</span><h1 class="t1">The model</h1><p class="lead">Price any listed option with Double Heston and set it against what the market paid.</p></div>
  <form class="panel" style="display:grid;grid-template-columns:1.2fr 1.2fr .9fr .9fr auto;align-items:end;gap:18px;padding:20px 22px" onsubmit="return false">
    <label style="display:flex;flex-direction:column;gap:8px"><span class="lbl">Underlying</span><select class="btn" style="font-weight:500"><option>NIFTY 50 · {inr(X.SPOT)}</option></select></label>
    <label style="display:flex;flex-direction:column;gap:8px"><span class="lbl">Expiry</span><select class="btn" style="font-weight:500"><option>{X.EXPIRY}, {K['dte']} days</option></select></label>
    <label style="display:flex;flex-direction:column;gap:8px"><span class="lbl">Strike</span><input class="btn" style="font-weight:500;width:100%;box-sizing:border-box" value="{inr(K['strike'], 0)}"></label>
    <span style="display:flex;flex-direction:column;gap:8px"><span class="lbl">Type</span><span class="seg" style="height:47px;align-items:center"><span class="on">Call</span><span>Put</span></span></span>
    <button class="btn pri" type="submit">Price option</button>
  </form>
  <section class="g">
    <div class="panel" style="grid-column:1/span 4;display:flex;flex-direction:column">
      <div class="ph"><span class="lbl">Market close</span><span class="mu" style="font-size:14px">IV {K['market_iv']:.2f}%</span></div>
      <div class="pb"><span class="big" style="font-size:60px">₹{inr(K['market'])}</span><p class="mu" style="margin:12px 0 0;font-size:15px">{esc(X.CONTRACT)}, {esc(X.CONTRACT_SUB[0].lower() + X.CONTRACT_SUB[1:])}. Open interest {K['oi'] / 1e5:.1f} lakh.</p></div>
    </div>
    <div class="panel" style="grid-column:5/span 4">
      <div class="ph"><span class="lbl">Double Heston, starting settings</span><span class="mu" style="font-size:14px">IV {K['dh_iv']:.2f}%</span></div>
      <div class="pb"><span class="big" style="font-size:60px;color:var(--acc)">₹{inr(K['dh'])}</span><p class="mu" style="margin:12px 0 0;font-size:15px">{esc(X.MC_LINE)}</p></div>
    </div>
    <div class="panel" style="grid-column:9/span 4">
      <div class="ph"><span class="lbl">Gap, model minus market</span></div>
      <div class="pb"><span class="big" style="font-size:60px">+₹{inr(X.GAP)}</span><p class="mu" style="margin:12px 0 0;font-size:15px">The model assumes 20% volatility; the market priced {K['market_iv']:.1f}%.</p></div>
    </div>
  </section>
  <p class="lead" style="max-width:980px">{esc(X.MODEL_EXPLAIN)}</p>
  <section class="g" style="align-items:start">
    <figure class="panel" style="grid-column:1/span 6;margin:0"><div class="ph"><span class="lbl">Smile: market against model</span><span class="mu" style="font-size:14px">{X.EXPIRY}</span></div><div class="pb">{smile}</div></figure>
    <div class="panel" style="grid-column:7/span 6">
      <div class="ph"><span class="lbl">Option chain around the money</span><span class="mu" style="font-size:14px">NSE close, {X.LAST_DAY}</span></div>
      <table class="tb"><thead><tr><th>Strike</th><th>Call</th><th>Call IV</th><th>Model call</th><th>Put</th><th>Put IV</th></tr></thead><tbody>{''.join(chain_rows)}</tbody></table>
    </div>
  </section>
  <section class="g" style="align-items:start">
    <div class="panel" style="grid-column:1/span 6"><div class="ph"><span class="lbl">Slow factor</span><span class="dn" style="font-size:14px">{esc(X.FELLER['slow'])}</span></div><div class="pb" style="padding-top:6px">{sliders('slow')}</div></div>
    <div class="panel" style="grid-column:7/span 6"><div class="ph"><span class="lbl">Fast factor</span><span class="dn" style="font-size:14px">{esc(X.FELLER['fast'])}</span></div><div class="pb" style="padding-top:6px">{sliders('fast')}</div></div>
    <div style="grid-column:1/span 12;display:flex;justify-content:space-between;align-items:center"><p class="mu" style="margin:0;font-size:15px">{esc(X.FELLER_NOTE)}</p><button class="btn" type="button">Reset to starting settings</button></div>
  </section>
  <section class="panel"><div class="ph"><span class="lbl">Greeks of the model price</span><span class="mu" style="font-size:14px">vega uses Black–Scholes at the model's implied volatility</span></div>
    <div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr))">{greeks}</div></section>
  <p class="mu" style="margin:0;font-size:14px;line-height:1.5">{esc(X.MODEL_SOURCE)}</p>
</div>
{footer()}
"""


def maths():
    steps = "".join(f'<li style="display:grid;grid-template-columns:64px 1fr;gap:18px;padding:22px 0;border-bottom:1px solid var(--grid)">'
                    f'<b class="big" style="font-size:34px;color:var(--acc)">{i}</b><span style="display:flex;flex-direction:column;gap:8px">'
                    f'<b style="font-size:21px">{esc(h)}</b><span class="p">{esc(t)}</span></span></li>' for i, (h, t) in enumerate(X.MATHS_STEPS, 1))
    return f"""
{bar()}
<div class="pg">
  <div style="display:flex;flex-direction:column;gap:14px"><span class="lbl">Page 4 of 8</span><h1 class="t1">How it works</h1><p class="lead">{esc(X.MATHS_INTRO)}</p></div>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 7;display:flex;flex-direction:column;gap:18px">
      <span class="lbl">The price moves with two variances</span><div class="eq">{esc(X.EQ_PRICE)}</div>
      <span class="lbl">Each variance pulls back to its own level</span><div class="eq">{esc(X.EQ_VAR)}</div>
      <span class="lbl">Independent factors multiply</span><div class="eq">{esc(X.EQ_CF)}</div>
      <span class="lbl">The price is one integral (Gil-Pelaez)</span><div class="eq" style="font-size:21px">{esc(X.EQ_CALL)}</div>
      <span class="lbl">A factor never touches zero when</span><div class="eq">{esc(X.EQ_FELLER)}</div>
    </div>
    <ol style="grid-column:8/span 5;list-style:none;margin:0;padding:0">{steps}</ol>
  </section>
  <section class="g">
    <figure class="panel" style="grid-column:1/span 7;margin:0"><div class="ph"><span class="lbl">What the bend looks like</span><span class="mu" style="font-size:14px">30 days, starting settings</span></div><div class="pb">{smile_chart(700, 360)}</div></figure>
    <figure class="panel" style="grid-column:8/span 5;margin:0"><div class="ph"><span class="lbl">Why two clocks</span><span class="mu" style="font-size:14px">skew, volatility points</span></div><div class="pb">{skew_chart(440, 300)}<p class="mu" style="margin:14px 0 0;font-size:15px;line-height:1.5">The fast factor (half-life about {X.HL['fast_days'] / 7:.0f} weeks) shapes short-dated options; the slow one (half-life {X.HL['slow_years']:.1f} years) holds up the long end.</p></div></figure>
  </section>
  <section class="panel"><div class="ph"><span class="lbl">Lineage</span></div>
    <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr))">{''.join(f'<div style="padding:22px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:8px"><b class="big" style="font-size:44px;{"color:var(--acc)" if y == "2009" else ""}">{y}</b><b style="font-size:20px">{n}</b><span class="mu" style="font-size:16px">{d}</span></div>' for y, n, d in X.LINEAGE)}</div></section>
</div>
{footer()}
"""


def finding():
    hist = svg(1100, 300, f"Histogram: how far apart equally good fits landed on {X.D['hist']['n']:,} real surfaces",
               kit.histogram(1100, 300, X.D["hist"]["edges"], X.D["hist"]["counts"], X.D["hist"]["median"], X.RAND, INK))
    pb_h, pb = kit.param_bars(1000, X.PER, INK)
    bars = svg(1000, pb_h, "Per-setting distance between equally good fits, against two random parameter sets", pb)
    sp_h, sp = kit.stock_panel(1180, X.REL_STOCK, X.RAND, INK)
    stock = svg(1180, sp_h, "RELIANCE, 60 trading days: price error and dispersion by day", sp)
    picks = "".join(f'<span class="seg" style="border-color:{"var(--acc)" if t == "RELIANCE" else "var(--line)"}"><span class="{"on" if t == "RELIANCE" else ""}">{t}</span></span>'
                    for t in ["RELIANCE", "HDFCBANK", "INFY", "TCS", "SBIN", "ICICIBANK", "ITC", "LT"])

    def nums(items):
        return "".join(f'<div style="display:flex;flex-direction:column;gap:8px;padding:0 18px;border-left:1px solid var(--line)"><span class="big" style="font-size:46px;color:var(--acc)">{n}</span><span class="mu" style="font-size:15px;line-height:1.4">{esc(c)}</span></div>' for n, c in items)

    return f"""
{bar()}
<div class="pg">
  <div style="display:flex;flex-direction:column;gap:18px"><span class="lbl">Page 5 of 8</span>
    <h1 class="t1" style="max-width:1100px">fit(prices) ≈ exact<br><span class="prompt">recover(settings) = no</span></h1><p class="lead">{esc(X.FIND_HEAD)}</p></div>
  <section class="panel"><div class="ph"><span class="lbl">Proof one: {esc(X.PROOF1_HEAD.lower())}</span></div>
    <div class="pb g" style="align-items:start"><p class="p" style="grid-column:1/span 6">{esc(X.PROOF1)}</p><div style="grid-column:7/span 6;display:grid;grid-template-columns:repeat(3,minmax(0,1fr))">{nums(X.PROOF1_NUMS)}</div>
    <p class="mu" style="grid-column:1/span 12;margin:6px 0 0;font-size:16px;line-height:1.55">{esc(X.PROOF1_NET)}</p></div></section>
  <section class="panel"><div class="ph"><span class="lbl">Proof two: {esc(X.PROOF2_HEAD.lower())}</span></div>
    <div class="pb g" style="align-items:start"><p class="p" style="grid-column:1/span 6">{esc(X.PROOF2)}</p><div style="grid-column:7/span 6;display:grid;grid-template-columns:repeat(3,minmax(0,1fr))">{nums(X.PROOF2_NUMS)}</div>
    <figure style="grid-column:1/span 12;margin:18px 0 0">{hist}</figure></div></section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 8">{bars}</div>
    <p class="p" style="grid-column:9/span 4">{esc(X.PER_PARAM)}</p>
  </section>
  <section class="panel"><div class="ph" style="align-items:center"><span class="lbl">Pick a stock</span><span style="display:flex;gap:8px;flex-wrap:wrap">{picks}</span></div>
    <div class="pb" style="display:flex;flex-direction:column;gap:18px"><p class="p">{esc(X.rel_line())}</p>{stock}</div></section>
  <section class="g">
    <div class="panel" style="grid-column:1/span 6"><div class="ph"><span class="lbl">Held-out dates</span></div><div class="pb" style="display:flex;gap:28px;align-items:center"><span class="big" style="font-size:52px">{X.G8['median_network_relative'] * 100:.1f}%</span><span class="mu" style="font-size:22px">vs</span><span class="big" style="font-size:52px;color:var(--acc)">{X.G8['median_best_fit_relative'] * 100:.1f}%</span></div><p class="p" style="padding:0 22px 22px">{esc(X.HELDOUT)}</p></div>
    <div class="panel" style="grid-column:7/span 6"><div class="ph"><span class="lbl">Option backtest</span></div><div class="pb"><span class="big" style="font-size:52px">0 of 210</span><p class="p" style="margin-top:14px">{esc(X.BACKTEST)}</p></div></div>
  </section>
</div>
{footer()}
"""


def about():
    return f"""
{bar()}
<div class="pg">
  <div style="display:flex;flex-direction:column;gap:14px"><span class="lbl">Page 6 of 8</span><h1 class="t1" style="max-width:1000px">{esc(X.ABOUT_HEAD)}</h1></div>
  <section class="g" style="align-items:start">
    <figure class="panel" style="grid-column:1/span 8;margin:0">
      <button type="button" aria-label="Play the project video" style="width:100%;aspect-ratio:16/9;display:flex;align-items:center;justify-content:center;background:var(--raised);border:0;cursor:pointer">{squircle('play', 96, fill='var(--acc)', ink='var(--on-acc)', ring=False)}</button>
      <figcaption class="mu" style="padding:16px 20px;font-size:15px">{esc(X.VIDEO_CAPTION)} The video loads only when played.</figcaption>
    </figure>
    <div style="grid-column:9/span 4;display:flex;flex-direction:column;gap:18px"><span class="lbl">Method and data</span>{''.join(f'<p class="p" style="font-size:17px">{esc(m)}</p>' for m in X.METHOD)}</div>
  </section>
  <section class="g" style="align-items:start">
    <div class="panel" style="grid-column:1/span 7"><div class="ph"><span class="lbl">Limits</span></div><ul style="margin:0;padding:18px 22px 22px 42px;display:flex;flex-direction:column;gap:10px">{''.join(f'<li class="p">{esc(l)}</li>' for l in X.LIMITS)}</ul></div>
    <div class="panel" style="grid-column:8/span 5"><div class="ph"><span class="lbl">Also explored</span></div><p class="p" style="padding:22px">{esc(X.ALSO)}</p></div>
  </section>
  <section class="panel"><div class="ph"><span class="lbl">Source code</span></div><div class="pb"><a class="lnk" style="font-size:22px" href="https://{X.REPO}">{esc(X.REPO)}</a></div></section>
</div>
{footer()}
"""


def team():
    cards = "".join(f'<div class="panel" style="display:flex;flex-direction:column"><div style="aspect-ratio:1/1;background:var(--raised);display:flex;align-items:center;justify-content:center">{squircle("team", 72, ring=False)}</div>'
                    f'<div class="pb" style="display:flex;flex-direction:column;gap:6px"><b style="font-size:21px">{esc(n)}</b><span class="mu" style="font-size:15px">{esc(r)}</span></div></div>' for n, r in X.TEAM)
    return f"""
{bar()}
<div class="pg">
  <div style="display:flex;flex-direction:column;gap:14px"><span class="lbl">Page 7 of 8</span><h1 class="t1">{esc(X.TEAM_HEAD)}</h1><p class="lead">{esc(X.TEAM_INTRO)}</p></div>
  <section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px">{cards}</section>
  <section class="g" style="align-items:start">
    <div class="panel" style="grid-column:1/span 5"><div class="ph"><span class="lbl">Supervisor</span></div><div class="pb" style="display:flex;flex-direction:column;gap:6px"><b style="font-size:21px">{esc(X.SUPERVISOR[0])}</b><span class="mu" style="font-size:15px">{esc(X.SUPERVISOR[1])}</span></div></div>
    <div class="panel" style="grid-column:6/span 7"><div class="ph"><span class="lbl">Thanks</span></div><ul style="margin:0;padding:18px 22px 22px 42px;display:flex;flex-direction:column;gap:8px">{''.join(f'<li class="p">{esc(t)}</li>' for t in X.THANKS)}</ul></div>
  </section>
</div>
{footer()}
"""


def references():
    n = 0
    groups = []
    for g, items in X.REFS:
        lis = []
        for a, t, s in items:
            n += 1
            lis.append(f'<li style="display:grid;grid-template-columns:52px 1fr;gap:14px;padding:16px 0;border-bottom:1px solid var(--grid)"><span class="lbl" style="color:var(--acc);font-size:16px">[{n}]</span>'
                       f'<span style="display:flex;flex-direction:column;gap:4px"><b style="font-size:18px">{esc(a)}</b><span class="p" style="font-size:17px">{esc(t)} <span class="mu">{esc(s)}</span></span></span></li>')
        groups.append(f'<section class="panel"><div class="ph"><span class="lbl">{esc(g)}</span></div><ol style="list-style:none;margin:0;padding:4px 22px 10px">{"".join(lis)}</ol></section>')
    return f"""
{bar()}
<div class="pg">
  <div style="display:flex;flex-direction:column;gap:14px"><span class="lbl">Page 8 of 8</span><h1 class="t1">References</h1><p class="lead">The papers behind the model and the methods, and where the data comes from.</p></div>
  {''.join(groups)}
</div>
{footer()}
"""


DESIGN = Design(
    num=1, slug="amber-instrument", name="Amber Instrument",
    concept="A precision instrument: bracketed readouts, a $ query hero and hairline panels, in amber on near-black.",
    memorable="The $ query headline and the fit(prices) ≈ exact / recover(settings) = no readout.",
    layout="12-column grid of hairline panels with labelled headers; left-aligned; one amber accent for the model.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;700;900&display=swap",
    display_font="'Schibsted Grotesk',sans-serif", body_font="'Schibsted Grotesk',Helvetica,sans-serif",
    type_sample="$ does volatility move? 23,140.50",
    type_note="Schibsted Grotesk throughout: 700 for headlines, 900 for readout numbers, 400/500 for text.",
    ink=INK, css=CSS, rail_side="l", default_dark=True,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}, "fast": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
