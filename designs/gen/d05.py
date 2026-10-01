"""05 · Sidebar — a macOS app: a source-list sidebar (this page's sections + watchlist), inset grouped lists."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#FFFFFF", surf="#F5F5F7", raised="#ECECF0", line="#E0E0E6", grid="#F1F1F4", ink="#1D1D1F",
             body="#424245", muted="#6E6E73", acc="#D70F44", on_acc="#FFFFFF", up="#1E8E3E", down="#D70015",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#1E1E20", surf="#28282B", raised="#333337", line="#3B3B40", grid="#2C2C30", ink="#F5F5F7",
            body="#D1D1D6", muted="#9C9CA3", acc="#FF375F", on_acc="#1E1E20", up="#30D158", down="#FF453A",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

TINTS = ["#FF375F", "#FF9F0A", "#30B0C7", "#5E5CE6", "#34C759", "#8E8E93", "#0A84FF"]

CSS = """
.app{display:grid;grid-template-columns:290px minmax(0,1fr);min-height:100%}
.side{background:var(--surf);border-right:1px solid var(--line);padding:18px 14px 28px;display:flex;flex-direction:column;gap:22px}
.traffic{display:flex;gap:8px;padding:4px 8px 6px}.traffic i{width:12px;height:12px;border-radius:6px;display:block}
.srch{display:flex;align-items:center;gap:8px;height:34px;padding:0 10px;border-radius:9px;background:var(--raised);font-size:14px;color:var(--muted)}
.sh{font-size:12.5px;font-weight:700;color:var(--muted);padding:0 10px 6px}
.nv{display:flex;align-items:center;gap:11px;height:36px;padding:0 10px;border-radius:8px;font-size:15px;font-weight:500}
.nv.on{background:var(--raised)}
.wl{display:grid;grid-template-columns:1fr auto;gap:1px 10px;padding:8px 10px;border-radius:8px;font-size:14px}
.wl .pill{justify-self:end;font-size:12px;font-weight:700;padding:1px 7px;border-radius:5px}
.pill.up{background:rgba(52,199,89,.16)}.pill.dn{background:rgba(255,69,58,.16)}
.main{min-width:0;display:flex;flex-direction:column}
.tb{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 250px 0 44px;border-bottom:1px solid var(--line);font-size:15px;color:var(--muted)}
.tb b{color:var(--ink);font-size:17px}
.content{padding:40px 140px 90px 44px;display:flex;flex-direction:column;gap:44px}
.h1{margin:0;font-size:46px;line-height:1.06;font-weight:800;letter-spacing:-.025em;max-width:980px}
.lede{margin:0;font-size:19px;line-height:1.55;color:var(--body);max-width:820px}
.h2{margin:0 0 12px;font-size:24px;font-weight:800;letter-spacing:-.01em}
.grp{border-radius:12px;background:var(--surf);overflow:hidden}
.t-light .grp{background:var(--surf)}
.grp>.r{display:flex;align-items:center;gap:14px;padding:13px 18px;border-bottom:1px solid var(--line);font-size:16px}.grp>.r:last-child{border-bottom:0}
.p{margin:0;font-size:17px;line-height:1.6;color:var(--body)}
.b-tick{height:34px;display:flex;align-items:center;padding:0 250px 0 44px;border-bottom:1px solid var(--line);font-size:13.5px;white-space:nowrap}
.b-tick-in{flex:1;min-width:0;display:flex;gap:24px;overflow:hidden}.b-ti{display:inline-flex;gap:7px}.b-ti-lab{color:var(--muted)}
.b-tb{width:100%;border-collapse:collapse;font-size:15px}
.b-tb th{text-align:right;font-weight:600;font-size:13px;color:var(--muted);padding:9px 14px;border-bottom:1px solid var(--line)}
.b-tb td{text-align:right;padding:10px 14px;border-bottom:1px solid var(--line);white-space:nowrap}
.b-tb tr:nth-child(even) td{background:var(--grid)}
.b-tb th:first-child,.b-tb td:first-child{text-align:left}.b-tb tr.sel td{background:var(--acc);color:var(--on-acc)}.b-tb tr.sel td *{color:var(--on-acc)}
.b-sub{color:var(--muted)}.b-model{color:var(--acc);font-weight:700}.b-lab{font-size:13px;font-weight:600;color:var(--muted)}
.b-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 18px;margin:0;padding:18px;border-radius:12px;background:var(--surf)}
.b-form label,.b-form fieldset{display:grid;grid-template-columns:110px 1fr;align-items:center;gap:12px;border:0;margin:0;padding:0;min-width:0}
.b-form select,.b-form input{height:34px;border-radius:7px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:500 15px Manrope,sans-serif;padding:0 10px}
.b-seg{display:grid;grid-template-columns:1fr 1fr;height:32px;padding:2px;border-radius:8px;background:var(--raised);box-sizing:border-box}
.b-seg span{display:flex;align-items:center;justify-content:center;border-radius:6px;font-size:14px;font-weight:600;color:var(--muted)}.b-seg span.on{background:var(--bg);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.15)}
.b-btn{height:36px;padding:0 16px;border-radius:8px;border:0;background:var(--acc);color:var(--on-acc);font:700 15px Manrope,sans-serif;cursor:pointer;display:inline-flex;align-items:center;justify-content:center}
.b-btn.sec{background:var(--raised);color:var(--ink)}
.b-form .b-btn{grid-column:2;justify-self:end}
.b-sl{display:grid;grid-template-columns:30px 1fr 74px;gap:12px;align-items:center;padding:11px 18px;border-bottom:1px solid var(--line)}.b-sl:last-child{border-bottom:0}
.b-sl b{font-size:18px;color:var(--acc)}.b-sl label{display:flex;flex-direction:column;gap:5px;font-size:14px;color:var(--muted)}
.b-sl input{width:100%;accent-color:#FF375F}.b-sl output{text-align:right;font-weight:700;font-size:16px}
.b-greek{padding:14px 18px;display:flex;flex-direction:column;gap:4px;border-right:1px solid var(--line)}.b-greek:last-child{border-right:0}.b-greek b{font-size:28px;font-weight:800}
.b-num{padding:18px;border-radius:12px;background:var(--surf);display:flex;flex-direction:column;gap:6px}.b-num b{font-size:42px;font-weight:800;letter-spacing:-.02em;color:var(--acc);line-height:1}.b-num span{font-size:14.5px;line-height:1.45;color:var(--body)}
.b-eq{padding:16px 18px;border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:8px}.b-eq:last-child{border-bottom:0}
.b-eqn{font-size:24px;font-weight:600;line-height:1.4;font-family:'Manrope',sans-serif}
.b-steps{list-style:none;margin:0;padding:0}.b-steps li{display:grid;grid-template-columns:40px 1fr;gap:10px;padding:14px 18px;border-bottom:1px solid var(--line)}.b-steps li:last-child{border-bottom:0}
.b-steps .b-n{width:26px;height:26px;border-radius:7px;background:var(--acc);color:var(--on-acc);display:flex;align-items:center;justify-content:center;font-size:14px}
.b-steps li>span{display:flex;flex-direction:column;gap:4px}.b-steps li>span>b{font-size:16px}.b-steps li>span>span{font-size:15px;line-height:1.5;color:var(--body)}
.b-lin{list-style:none;margin:0;padding:0}.b-lin li{display:grid;grid-template-columns:90px 1fr;gap:12px;align-items:center;padding:14px 18px;border-bottom:1px solid var(--line)}.b-lin li:last-child{border-bottom:0}
.b-lin .b-y{font-size:30px;font-weight:800}.b-lin li.now .b-y{color:var(--acc)}.b-lin li>span{display:flex;flex-direction:column;gap:2px}.b-lin li>span>span{color:var(--muted);font-size:14.5px}
.b-list{margin:0;padding:14px 18px 16px 38px;display:flex;flex-direction:column;gap:8px;font-size:16px;line-height:1.5;color:var(--body)}
.b-video{margin:0;border-radius:12px;overflow:hidden;background:var(--surf)}.b-video button{width:100%;aspect-ratio:16/9;border:0;background:var(--raised);display:flex;align-items:center;justify-content:center;cursor:pointer}
.b-video figcaption{padding:12px 16px;font-size:14px;color:var(--muted)}
.b-person{display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px;padding:22px 16px;border-radius:12px;background:var(--surf)}.b-person .b-ph{margin-bottom:6px}.b-person b{font-size:18px}.b-person>span:last-child{color:var(--muted);font-size:14px}
.b-refs h2{margin:0 0 8px;font-size:13px;font-weight:700;color:var(--muted);padding-left:4px}.b-refs ol{list-style:none;margin:0;padding:0;border-radius:12px;background:var(--surf);overflow:hidden}
.b-refs li{display:grid;grid-template-columns:42px 1fr;gap:6px;padding:12px 18px;border-bottom:1px solid var(--line);font-size:15px;line-height:1.45}.b-refs li:last-child{border-bottom:0}
.b-refs .b-rn{color:var(--acc);font-weight:700}.b-refs .b-rt{color:var(--body)}
.b-chip{display:inline-flex;height:30px;align-items:center;padding:0 12px;border-radius:7px;background:var(--raised);font-size:14px;font-weight:600}.b-chip.on{background:var(--acc);color:var(--on-acc)}
.ft{padding:18px 140px 28px 44px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-size:13.5px;color:var(--muted)}
"""

INK = Ink(font="Manrope,sans-serif", size=13, line_w=2.8, bar_radius=3)


def sidebar(sections, active=0):
    items = "".join(
        f'<a href="#" class="nv{" on" if i == active else ""}">{squircle(ic, 24, fill=TINTS[i % len(TINTS)], ink="#FFFFFF", ring=False)}{esc(t)}</a>'
        for i, (ic, t) in enumerate(sections))
    wl = []
    for s in ["NIFTY 50", "NIFTY BANK", "RELIANCE", "HDFCBANK", "INFY", "TCS", "SBIN"]:
        v = X.w(s)
        a, c = arrow(v["pct"])
        wl.append(f'<a href="Market.dc.html" class="wl"><b>{s}</b><span>{inr(v["last"])}</span><span class="b-sub" style="font-size:12px">{esc(X.NAMES.get(s, ""))}</span>'
                  f'<span class="pill {c}">{a} {abs(v["pct"]):.2f}%</span></a>')
    return f"""<aside class="side">
<span class="traffic" aria-hidden="true"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i></span>
<label class="srch"><svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5.2" style="fill:none;stroke:var(--muted);stroke-width:1.8"></circle><path d="M11,11 L15,15" style="stroke:var(--muted);stroke-width:1.8;stroke-linecap:round"></path></svg>Search 42 stocks</label>
<nav style="display:flex;flex-direction:column;gap:1px" aria-label="On this page"><span class="sh">On this page</span>{items}</nav>
<div style="display:flex;flex-direction:column"><span class="sh">Watchlist, close {X.LAST_DAY}</span>{''.join(wl)}</div>
<span class="b-sub" style="margin-top:auto;padding:0 10px;font-size:13px;line-height:1.5">{esc(X.STATUS)}</span>
</aside>"""


def shell(title, sections, body, ticker=False, active=0):
    return f"""<div class="app">{sidebar(sections, active)}<div class="main">
{B.ticker() if ticker else ''}<div class="tb"><b>{esc(title)}</b><span>Double Heston</span></div>
<div class="content">{body}</div>
<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer></div></div>"""


def home():
    s, f = X.SLOW, X.FAST
    rows = [("slow", "var(--raised)", "var(--ink)", s), ("fast", "var(--acc)", "var(--on-acc)", f)]
    grp = "".join(f'<a href="Maths.dc.html" class="r">{squircle(k, 32, fill=fl, ink=ik, ring=False)}<b>{a}</b><span class="b-sub" style="margin-left:auto">{b}, {c.lower()}</span><span class="b-sub" aria-hidden="true">›</span></a>' for k, fl, ik, (a, b, c) in rows)
    grp += '<a href="Model.dc.html" class="r">' + squircle("model", 32, fill="#5E5CE6", ink="#FFFFFF", ring=False) + '<b>Try the ten settings yourself</b><span class="b-sub" style="margin-left:auto">on the model page</span><span class="b-sub" aria-hidden="true">›</span></a>'
    body = f"""
<div style="display:flex;flex-direction:column;gap:14px"><span class="b-sub" style="font-size:15px">Wednesday, 30 September</span><h1 class="h1">{esc(X.Q)}</h1><p class="lede">{esc(X.A_SHORT)} {esc(X.A_LONG)}</p></div>
<figure style="margin:0;display:flex;flex-direction:column;gap:8px">{B.smile(INK, 880, 400)}<figcaption class="b-sub" style="font-size:14px;padding-left:48px">{esc(X.SMILE_CAPTION)}</figcaption></figure>
<div class="grp" style="max-width:800px">{grp}</div>
<section style="display:flex;flex-direction:column;gap:14px;max-width:900px"><h2 class="h2">Then it can’t tell you why.</h2><p class="p">{esc(X.FINDING_LINE)} {esc(X.FINDING_SUB)}</p>{B.bars(INK, 820)}<a class="b-model" href="Finding.dc.html">{X.CTA['finding']}</a></section>
"""
    return shell("Overview", [("home", "The question"), ("slow", "Two factors"), ("finding", "The finding")], body, ticker=True)


def market():
    r = X.REL_LAST
    stats = "".join(f'<div class="b-greek"><span class="b-lab">{k}</span><b style="font-size:22px">{v}</b></div>' for k, v in B.rel_stats())
    body = f"""
<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">Market</h1><p class="lede">{esc(X.MARKET_SUB)}</p></div>
<section style="display:flex;flex-direction:column;gap:14px">
  <div style="display:flex;align-items:baseline;justify-content:space-between"><span style="display:flex;align-items:baseline;gap:14px"><b style="font-size:26px">RELIANCE</b><span style="font-size:40px;font-weight:800">{inr(r[4])}</span><span style="font-weight:700;font-size:17px">{B.rel_change()}</span></span>
  <span style="display:flex;gap:6px"><span class="b-chip">1M</span><span class="b-chip on">3M</span><span class="b-chip">Line</span><span class="b-chip on">Candles</span></span></div>
  {B.rel_candles(INK, 960, 460, 8)}
  <div class="grp" style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr))">{stats}</div>
</section>
<section><h2 class="h2">All stocks</h2><div class="grp">{B.watch_table(names=True, spark=(80, 24))}</div></section>
<section style="display:grid;grid-template-columns:1fr 1fr;gap:24px"><div><h2 class="h2">NIFTY 50, close</h2>{B.nifty_line(INK, 470, 210)}</div><div><h2 class="h2">NIFTY BANK, close</h2>{B.nifty_line(INK, 470, 210, 'BANKNIFTY')}</div></section>
"""
    return shell("Market", [("market", "RELIANCE"), ("refs", "All stocks"), ("home", "Indices")], body)


def model():
    K = X.K
    body = f"""
<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">Price an option</h1><p class="lede">Set the contract, price it with Double Heston, and compare it with the market close.</p></div>
{B.pricing_form()}
<section style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px">
  <div class="b-num"><span>Market close</span><b style="color:var(--ink)">₹{inr(K['market'])}</b><span>IV {K['market_iv']:.2f}%. {esc(X.CONTRACT)}, {esc(X.CONTRACT_SUB[0].lower() + X.CONTRACT_SUB[1:])}.</span></div>
  <div class="b-num"><span>Double Heston</span><b>₹{inr(K['dh'])}</b><span>{esc(X.MC_LINE)}</span></div>
  <div class="b-num"><span>Gap</span><b style="color:var(--ink)">+₹{inr(X.GAP)}</b><span>The model assumes 20% volatility; the market priced {K['market_iv']:.1f}%.</span></div>
</section>
<p class="p" style="max-width:900px">{esc(X.MODEL_EXPLAIN)}</p>
<section style="display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start">
  <div><h2 class="h2">Smile, market against model</h2>{B.market_smile(INK, 480, 330, 46)}</div>
  <div><h2 class="h2">Option chain</h2><div class="grp">{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div></div>
</section>
<section style="display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start">
  <div><h2 class="h2">Slow factor</h2><p class="b-sub" style="margin:0 0 8px;color:var(--down)">{esc(X.FELLER['slow'])}</p><div class="grp">{B.sliders('slow')}</div></div>
  <div><h2 class="h2">Fast factor</h2><p class="b-sub" style="margin:0 0 8px;color:var(--down)">{esc(X.FELLER['fast'])}</p><div class="grp">{B.sliders('fast')}</div></div>
</section>
<div style="display:flex;justify-content:space-between;align-items:center"><span class="b-sub">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div>
<section><h2 class="h2">Greeks</h2><div class="grp" style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr))">{B.greeks()}</div></section>
<p class="b-sub" style="margin:0;font-size:14px">{esc(X.MODEL_SOURCE)}</p>
"""
    return shell("The model", [("model", "Contract"), ("finding", "Market and model"), ("slow", "Settings"), ("maths", "Greeks")], body)


def maths():
    body = f"""
<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">How it works</h1><p class="lede">{esc(X.MATHS_INTRO)}</p></div>
<section><h2 class="h2">Equations</h2><div class="grp">{B.equations()}</div></section>
<section style="display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start">
  <div><h2 class="h2">Step by step</h2><div class="grp">{B.steps()}</div></div>
  <div style="display:flex;flex-direction:column;gap:24px"><div><h2 class="h2">The bend</h2>{B.smile(INK, 470, 300)}</div><div><h2 class="h2">Skew by time to expiry</h2>{B.skew(INK, 470, 260)}</div></div>
</section>
<section><h2 class="h2">Lineage</h2><div class="grp">{B.lineage()}</div></section>
"""
    return shell("How it works", [("maths", "Equations"), ("refs", "Step by step"), ("slow", "Charts"), ("home", "Lineage")], body)


def finding():
    body = f"""
<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">{esc(X.FIND_HEAD)}</h1></div>
<section style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">{esc(X.PROOF1_HEAD)}</h2><p class="p" style="max-width:900px">{esc(X.PROOF1)}</p>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px">{B.nums(X.PROOF1_NUMS)}</div><p class="b-sub" style="margin:0;font-size:15px;line-height:1.5;max-width:900px">{esc(X.PROOF1_NET)}</p></section>
<section style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">{esc(X.PROOF2_HEAD)}</h2><p class="p" style="max-width:900px">{esc(X.PROOF2)}</p>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px">{B.nums(X.PROOF2_NUMS)}</div>{B.hist(INK, 980, 290)}</section>
<section style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">By setting</h2><p class="p" style="max-width:900px">{esc(X.PER_PARAM)}</p>{B.bars(INK, 900)}</section>
<section style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Pick a stock</h2><span style="display:flex;gap:6px;flex-wrap:wrap">{B.picks()}</span><p class="p">{esc(X.rel_line())}</p>{B.stock(INK, 980)}</section>
<section class="grp"><div class="r"><b style="min-width:150px">Held-out dates</b><span class="p" style="font-size:15.5px">{esc(X.HELDOUT)}</span></div><div class="r"><b style="min-width:150px">Option backtest</b><span class="p" style="font-size:15.5px">{esc(X.BACKTEST)}</span></div></section>
"""
    return shell("The finding", [("slow", "Simulated surfaces"), ("finding", "Real surfaces"), ("refs", "By setting"), ("market", "Pick a stock"), ("maths", "Out of sample")], body)


def about():
    body = f"""
<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">{esc(X.ABOUT_HEAD)}</h1></div>
<section style="display:grid;grid-template-columns:1.5fr 1fr;gap:24px;align-items:start">{B.video(icon_fill='#FF375F', icon_ink='#FFFFFF')}
<div><h2 class="h2">Method and data</h2><div class="grp">{''.join(f'<div class="r"><span class="p" style="font-size:15.5px">{esc(m)}</span></div>' for m in X.METHOD)}</div></div></section>
<section style="display:grid;grid-template-columns:1.2fr 1fr;gap:24px;align-items:start">
<div><h2 class="h2">Limits</h2><div class="grp">{B.bullet_list(X.LIMITS)}</div></div>
<div><h2 class="h2">Also explored</h2><div class="grp"><div class="r"><span class="p" style="font-size:15.5px">{esc(X.ALSO)}</span></div><a class="r b-model" href="https://{X.REPO}" style="font-size:14.5px">{esc(X.REPO)}</a></div></div></section>
"""
    return shell("About", [("play", "Video"), ("refs", "Method and data"), ("about", "Limits")], body)


def team():
    body = f"""
<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">{esc(X.TEAM_HEAD)}</h1><p class="lede">{esc(X.TEAM_INTRO)}</p></div>
<section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px">{B.team_cards()}</section>
<section style="display:grid;grid-template-columns:1fr 1.3fr;gap:24px;align-items:start">
<div><h2 class="h2">Supervisor</h2><div class="grp"><div class="r"><b>{esc(X.SUPERVISOR[0])}</b><span class="b-sub" style="margin-left:auto">{esc(X.SUPERVISOR[1])}</span></div></div></div>
<div><h2 class="h2">Thanks</h2><div class="grp">{B.bullet_list(X.THANKS)}</div></div></section>
"""
    return shell("Team", [("team", "People"), ("about", "Thanks")], body)


def references():
    body = f"""
<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">References</h1><p class="lede">The papers behind the model and its methods, and where the data comes from.</p></div>
<section style="display:flex;flex-direction:column;gap:22px">{B.refs()}</section>
"""
    return shell("References", [("refs", "Models"), ("maths", "Numerical methods"), ("about", "History"), ("market", "Data and software")], body)


DESIGN = Design(
    num=5, slug="sidebar", name="Sidebar",
    concept="A macOS app: a source-list sidebar with this page's sections and a watchlist, inset grouped lists.",
    memorable="The sidebar: coloured squircle section icons over a live watchlist, like Finder meets Stocks.",
    layout="Two panes: a 290-px source list, and a content pane with a toolbar, inset grouped lists and charts.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap",
    display_font="Manrope,sans-serif", body_font="Manrope,Helvetica,sans-serif",
    type_sample="Then it can’t tell you why.",
    type_note="Manrope 800 for titles, 500–700 for lists and text; sizes follow macOS (13–17 px lists, 46 px titles).",
    ink=INK, css=CSS, rail_side="r", default_dark=False,
    icon_fills={"model": {"fill": "#FF375F", "ink": "#FFFFFF"}, "fast": {"fill": "#FF375F", "ink": "#FFFFFF"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
