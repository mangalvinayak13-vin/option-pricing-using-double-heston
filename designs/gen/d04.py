"""04 · Springboard — an iPhone home screen: widgets of mixed sizes, coloured app icons, a frosted dock."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#F2F2F7", surf="#FFFFFF", raised="#E9E9EE", line="#D8D8DE", grid="#EDEDF1", ink="#1C1C1E",
             body="#3C3C43", muted="#6C6C72", acc="#FF9500", on_acc="#1C1C1E", up="#248A3D", down="#D70015",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#000000", surf="#1C1C1E", raised="#2C2C2E", line="#38383A", grid="#2A2A2C", ink="#F5F5F7",
            body="#D1D1D6", muted="#98989F", acc="#FF9F0A", on_acc="#1C1C1E", up="#30D158", down="#FF453A",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

APP = {  # Apple system colours, one per page; white glyphs
    "Main": ("#8E8E93", "#6D6D72"), "Market": ("#3A3A3C", "#1C1C1E"), "Model": ("#FFB340", "#FF9500"),
    "Maths": ("#7A78E8", "#5856D6"), "Finding": ("#FF6961", "#FF3B30"), "About": ("#A1A1A6", "#7C7C80"),
    "Team": ("#4CC4DC", "#30B0C7"), "References": ("#3395FF", "#007AFF"),
}

CSS = """
.sb-top{height:56px;display:flex;align-items:center;gap:18px;padding:0 250px 0 64px;font-size:15px;color:var(--muted)}
.sb-top b{color:var(--ink);font-size:17px}
.page{padding:28px 150px 110px 64px;display:flex;flex-direction:column;gap:28px}
.lt{margin:0;font-size:58px;line-height:1.02;font-weight:800;letter-spacing:-.025em}
.sub{margin:0;font-size:21px;line-height:1.45;color:var(--body);max-width:820px}
.grid{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:22px}
.w{background:var(--surf);border-radius:30px;padding:22px 24px;display:flex;flex-direction:column;gap:10px;min-width:0;box-sizing:border-box;overflow:hidden}
.t-light .w{box-shadow:0 1px 2px rgba(0,0,0,.05),0 6px 20px rgba(0,0,0,.04)}
.wt{display:flex;justify-content:space-between;align-items:baseline;font-size:17px;font-weight:700}
.wt span{font-size:14px;font-weight:500;color:var(--muted)}
.hv{font-size:44px;font-weight:800;letter-spacing:-.02em;line-height:1}
.app{display:flex;flex-direction:column;align-items:center;gap:10px;font-size:15px;font-weight:500}
.dock{align-self:center;display:flex;gap:30px;padding:16px 26px;border-radius:40px;background:rgba(120,120,128,.18);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px)}
.grp{background:var(--surf);border-radius:18px;overflow:hidden}
.grp>*{border-bottom:1px solid var(--line)}.grp>*:last-child{border-bottom:0}
.row{display:flex;align-items:center;gap:14px;padding:14px 18px;font-size:17px}
.gh{font-size:15px;font-weight:600;color:var(--muted);padding:0 18px 8px}
.p{margin:0;font-size:18px;line-height:1.55;color:var(--body)}
.b-tick{height:40px;display:flex;align-items:center;padding:0 250px 0 64px;font-size:14px;white-space:nowrap;background:var(--surf)}
.b-tick-in{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}.b-ti{display:inline-flex;gap:8px;font-weight:500}.b-ti-lab{color:var(--muted)}
.b-tb{width:100%;border-collapse:collapse;font-size:17px}
.b-tb th{text-align:right;font-weight:600;font-size:14px;color:var(--muted);padding:8px 14px}
.b-tb td{text-align:right;padding:12px 14px;border-top:1px solid var(--line);white-space:nowrap}
.b-tb th:first-child,.b-tb td:first-child{text-align:left}.b-tb td b{font-size:17px;display:block}.b-tb .b-sub{font-size:14px}
.b-tb tr.sel td{background:var(--raised)}
.b-tb td.up,.b-tb td.dn{font-weight:700}
.b-sub{color:var(--muted)}.b-model{color:var(--acc);font-weight:700}
.b-lab{font-size:14px;font-weight:600;color:var(--muted)}
.b-form{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0}
.b-form label,.b-form fieldset{display:flex;flex-direction:column;gap:8px;border:0;margin:0;padding:0;min-width:0}
.b-form select,.b-form input{height:50px;border-radius:14px;border:0;background:var(--raised);color:var(--ink);font:500 17px Figtree,sans-serif;padding:0 14px}
.b-seg{display:grid;grid-template-columns:1fr 1fr;height:50px;padding:3px;border-radius:14px;background:var(--raised);box-sizing:border-box}
.b-seg span{display:flex;align-items:center;justify-content:center;border-radius:11px;font-weight:600;color:var(--muted)}
.b-seg span.on{background:var(--surf);color:var(--ink);box-shadow:0 2px 6px rgba(0,0,0,.12)}
.b-btn{height:50px;padding:0 24px;border-radius:25px;border:0;background:var(--acc);color:var(--on-acc);font:700 17px Figtree,sans-serif;display:inline-flex;align-items:center;justify-content:center;cursor:pointer}
.b-btn.sec{background:var(--raised);color:var(--ink)}
.b-sl{display:grid;grid-template-columns:36px 1fr 78px;gap:14px;align-items:center;padding:12px 18px;border-bottom:1px solid var(--line)}
.b-sl:last-child{border-bottom:0}.b-sl b{font-size:20px;color:var(--acc)}.b-sl label{display:flex;flex-direction:column;gap:6px;font-size:15px;color:var(--muted)}
.b-sl input{width:100%;accent-color:#FF9500}.b-sl output{text-align:right;font-weight:700;font-size:18px}
.b-greek{background:var(--surf);border-radius:24px;padding:18px 20px;display:flex;flex-direction:column;gap:6px}.b-greek b{font-size:34px;font-weight:800}
.b-num{background:var(--surf);border-radius:28px;padding:22px 24px;display:flex;flex-direction:column;gap:8px}
.b-num b{font-size:50px;font-weight:800;letter-spacing:-.02em;line-height:1;color:var(--acc)}.b-num span{font-size:16px;line-height:1.4;color:var(--body)}
.b-eq{background:var(--surf);border-radius:24px;padding:22px 24px;display:flex;flex-direction:column;gap:10px}
.b-eqn{font-size:28px;font-weight:600;line-height:1.35}
.b-steps{list-style:none;margin:0;padding:0;background:var(--surf);border-radius:24px;overflow:hidden}
.b-steps li{display:grid;grid-template-columns:48px 1fr;gap:12px;padding:18px 22px;border-bottom:1px solid var(--line)}.b-steps li:last-child{border-bottom:0}
.b-steps .b-n{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:17px;background:var(--acc);color:var(--on-acc);font-size:17px}
.b-steps li>span{display:flex;flex-direction:column;gap:5px}.b-steps li>span>b{font-size:18px}.b-steps li>span>span{font-size:16px;line-height:1.5;color:var(--body)}
.b-lin{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}
.b-lin li{background:var(--surf);border-radius:28px;padding:22px 24px;display:flex;flex-direction:column;gap:6px}.b-lin .b-y{font-size:46px;font-weight:800}
.b-lin li.now .b-y{color:var(--acc)}.b-lin li>span{display:flex;flex-direction:column;gap:3px}.b-lin li>span>span{color:var(--muted);font-size:16px}
.b-list{margin:0;padding:4px 0 0 22px;display:flex;flex-direction:column;gap:10px;font-size:17px;line-height:1.5;color:var(--body)}
.b-video{margin:0;background:var(--surf);border-radius:30px;overflow:hidden}.b-video button{width:100%;aspect-ratio:16/9;border:0;background:var(--raised);display:flex;align-items:center;justify-content:center;cursor:pointer}
.b-video figcaption{padding:16px 22px;font-size:15px;color:var(--muted)}
.b-person{background:var(--surf);border-radius:30px;padding:26px 22px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px}
.b-person .b-ph{margin-bottom:10px}.b-person b{font-size:20px}.b-person>span:last-child{color:var(--muted);font-size:15px}
.b-refs h2{margin:0 0 8px 18px;font-size:15px;font-weight:600;color:var(--muted)}
.b-refs ol{list-style:none;margin:0;padding:0;background:var(--surf);border-radius:18px;overflow:hidden}
.b-refs li{display:grid;grid-template-columns:48px 1fr;gap:6px;padding:14px 18px;border-bottom:1px solid var(--line);font-size:16px;line-height:1.45}.b-refs li:last-child{border-bottom:0}
.b-refs .b-rn{color:var(--acc);font-weight:700}.b-refs .b-rt{color:var(--body)}
.b-chip{display:inline-flex;height:36px;align-items:center;padding:0 16px;border-radius:18px;background:var(--raised);font-weight:600;font-size:15px}
.b-chip.on{background:var(--acc);color:var(--on-acc)}
.ft{padding:26px 150px 40px 64px;display:flex;justify-content:space-between;font-size:14px;color:var(--muted)}
"""

INK = Ink(font="Figtree,sans-serif", size=13, line_w=3.2, grid="var(--grid)", axis="var(--line)", bar_radius=5)


def app_icon(stem, size=88):
    a, b = APP[stem]
    kit._gid = getattr(kit, "_gid", 0)
    gid = f"ap{stem}{size}"
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" aria-hidden="true" style="display:block">'
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"></stop>'
            f'<stop offset="1" stop-color="{b}"></stop></linearGradient></defs><path d="{kit.SQ}" fill="url(#{gid})"></path>'
            f'<path d="M14,8 C28,1.5 72,1.5 86,8" style="fill:none;stroke:#FFFFFF;stroke-opacity:.3;stroke-width:1.6;stroke-linecap:round"></path>'
            f'{kit.glyph(kit.ICON_FOR[stem], "#FFFFFF")}</svg>')


def top(title=None):
    return (f'<header class="sb-top"><b>Double Heston</b><span>{esc(X.STATUS)}</span></header>')


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def dock():
    return '<nav class="dock" aria-label="Main pages">' + "".join(
        f'<a href="{s}.dc.html" class="app" aria-label="{kit.PAGE_LABEL[s]}">{app_icon(s, 72)}</a>' for s in ("Market", "Model", "Finding", "About")) + "</nav>"


def header(title, sub):
    return f'<div style="display:flex;flex-direction:column;gap:10px"><h1 class="lt">{esc(title)}</h1><p class="sub">{esc(sub)}</p></div>'


def home():
    n = X.w("NIFTY 50")
    a, c = arrow(n["pct"])
    K = X.K
    apps = "".join(f'<a href="{s}.dc.html" class="app">{app_icon(s)}{l}</a>' for s, l, _ in kit.PAGES if s != "Main")
    s, f = X.SLOW, X.FAST
    return f"""
{B.ticker()}
{top()}
<div class="page">
  {header('Double Heston, on today’s market', X.A_SHORT + ' ' + X.TWIST)}
  <section class="grid" style="grid-auto-rows:150px">
    <a href="Market.dc.html" class="w" style="grid-column:span 4;grid-row:span 2">
      <span class="wt">NIFTY 50<span>close, {X.LAST_DAY}</span></span>
      <span style="display:flex;align-items:baseline;gap:12px"><span class="hv">{inr(n['last'])}</span><span class="{c}" style="font-weight:700;font-size:18px">{a} {abs(n['pct']):.2f}%</span></span>
      {B.nifty_line(INK, 560, 170)}
    </a>
    <a href="Model.dc.html" class="w" style="grid-column:span 2;grid-row:span 2;gap:6px">
      <span class="wt">{esc(X.CONTRACT)}</span><span class="b-sub" style="font-size:14px">{esc(X.CONTRACT_SUB)}</span>
      <span class="b-lab" style="margin-top:14px">Double Heston</span><span class="hv" style="font-size:38px;color:var(--acc)">₹{inr(K['dh'])}</span>
      <span class="b-lab" style="margin-top:8px">Market close</span><span class="hv" style="font-size:30px">₹{inr(K['market'])}</span>
      <span class="b-sub" style="margin-top:auto;font-size:14px">The model assumes 20% volatility; the market priced {K['market_iv']:.1f}%.</span>
    </a>
    <a href="Finding.dc.html" class="w" style="grid-column:span 2;grid-row:span 2;background:var(--acc);color:var(--on-acc)">
      <span class="wt" style="color:var(--on-acc)">The finding</span>
      <span style="font-size:22px;font-weight:800;line-height:1.2">{X.SHARE * 100:.0f}% of 2,400 real surfaces fit equally well with different settings.</span>
      <span style="margin-top:auto;font-size:64px;font-weight:800;letter-spacing:-.03em;line-height:1">{X.RATIO:.1f}×</span>
      <span style="font-size:15px;font-weight:600">further apart than two random parameter sets</span>
    </a>
    <figure class="w" style="grid-column:span 5;grid-row:span 2;margin:0">
      <span class="wt">What options cost, by strike<span>30 days, starting settings</span></span>{B.smile(INK, 700, 250)}
    </figure>
    <div class="w" style="grid-column:span 3;grid-row:span 2">
      <span class="wt">Where equally good fits disagree</span>{B.bars(INK, 400, row_h=27, label_w=190, legend=False, compact=True, only=('kappa_s', 'kappa_f', 'v0_s', 'v0_f'))}
      <span class="b-sub" style="font-size:13px">Bars: equally good fits. Ticks: two random sets.</span>
    </div>
    <div class="w" style="grid-column:span 2;flex-direction:row;align-items:center;gap:14px">{squircle('slow', 56, fill='var(--raised)', ring=False)}<span><b style="font-size:17px">{s[0]}</b><br><span class="b-sub" style="font-size:14px">{s[1]}, half-life {X.HL['slow_years']:.1f} yr</span></span></div>
    <div class="w" style="grid-column:span 2;flex-direction:row;align-items:center;gap:14px">{squircle('fast', 56, fill='var(--acc)', ink='var(--on-acc)', ring=False)}<span><b style="font-size:17px">{f[0]}</b><br><span class="b-sub" style="font-size:14px">{f[1]}, half-life {X.HL['fast_days'] / 7:.0f} weeks</span></span></div>
    <div class="w" style="grid-column:span 4;justify-content:center;background:transparent;border:1.5px solid var(--line)"><b style="font-size:17px">Market closed</b><span class="b-sub" style="font-size:15px">Last close {X.LAST_DAY}, 15:30 IST. During market hours every tile shows live prices from Upstox.</span></div>
  </section>
  <section style="display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:18px;padding:22px 0 8px">{apps}</section>
  {dock()}
</div>
{ft()}
"""


def market():
    r = X.REL_LAST
    stats = "".join(f'<div style="display:flex;flex-direction:column;gap:4px"><span class="b-lab">{k}</span><b style="font-size:21px">{v}</b></div>' for k, v in B.rel_stats())
    return f"""
{top()}
<div class="page">
  {header('Market', X.MARKET_SUB)}
  <span style="display:flex;gap:8px"><span class="b-chip on">Watchlist</span><span class="b-chip">Indices</span><span class="b-chip">All 42</span></span>
  <section style="display:grid;grid-template-columns:440px 1fr;gap:22px;align-items:start">
    <div class="grp">{B.watch_table(names=True, spark=(66, 24), cols=('Symbol', '', 'Close', ''))}</div>
    <div style="display:flex;flex-direction:column;gap:22px;min-width:0">
      <div class="w" style="gap:14px">
        <span class="wt" style="font-size:20px">RELIANCE<span>Reliance Industries, NSE</span></span>
        <span style="display:flex;align-items:baseline;gap:14px"><span class="hv" style="font-size:56px">{inr(r[4])}</span><span style="font-size:19px;font-weight:700">{B.rel_change()}</span></span>
        <span style="display:flex;gap:8px"><span class="b-chip">1M</span><span class="b-chip on">3M</span><span class="b-chip">Line</span><span class="b-chip on">Candles</span></span>
        {B.rel_candles(INK, 730, 440, 10)}
      </div>
      <div class="w" style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px">{stats}</div>
      <div class="w"><span class="wt">NIFTY BANK<span>close</span></span>{B.nifty_line(INK, 730, 200, 'BANKNIFTY')}</div>
    </div>
  </section>
</div>
{ft()}
"""


def model():
    K = X.K
    return f"""
{top()}
<div class="page">
  {header('Price an option', 'Pick a listed option, price it with Double Heston, and set it against what the market paid.')}
  <div class="w" style="padding:22px">{B.pricing_form()}</div>
  <section style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px">
    <div class="b-num"><span>Market close</span><b style="color:var(--ink)">₹{inr(K['market'])}</b><span>IV {K['market_iv']:.2f}%, {esc(X.CONTRACT)}</span></div>
    <div class="b-num"><span>Double Heston</span><b>₹{inr(K['dh'])}</b><span>{esc(X.MC_LINE)}</span></div>
    <div class="b-num"><span>Gap</span><b style="color:var(--ink)">+₹{inr(X.GAP)}</b><span>The model assumes 20% volatility; the market priced {K['market_iv']:.1f}%.</span></div>
  </section>
  <p class="p" style="max-width:1000px">{esc(X.MODEL_EXPLAIN)}</p>
  <section style="display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start">
    <div class="w"><span class="wt">Smile, market against model<span>{X.EXPIRY}</span></span>{B.market_smile(INK, 560, 360, 48)}</div>
    <div class="grp">{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div>
  </section>
  <section style="display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start">
    <div><div class="gh">Slow factor · <span class="dn">{esc(X.FELLER['slow'])}</span></div><div class="grp">{B.sliders('slow')}</div></div>
    <div><div class="gh">Fast factor · <span class="dn">{esc(X.FELLER['fast'])}</span></div><div class="grp">{B.sliders('fast')}</div></div>
  </section>
  <div style="display:flex;justify-content:space-between;align-items:center"><p class="b-sub" style="margin:0;font-size:16px">{esc(X.FELLER_NOTE)}</p><button class="b-btn sec" type="button">Reset to starting settings</button></div>
  <section style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:22px">{B.greeks()}</section>
  <p class="b-sub" style="margin:0;font-size:15px">{esc(X.MODEL_SOURCE)}</p>
</div>
{ft()}
"""


def maths():
    return f"""
{top()}
<div class="page">
  {header('How it works', X.MATHS_INTRO)}
  <section style="display:grid;grid-template-columns:1.25fr 1fr;gap:22px;align-items:start">
    <div style="display:flex;flex-direction:column;gap:18px">{B.equations()}</div>
    {B.steps()}
  </section>
  <section style="display:grid;grid-template-columns:1fr 1fr;gap:22px">
    <div class="w"><span class="wt">The bend<span>30 days</span></span>{B.smile(INK, 560, 330)}</div>
    <div class="w"><span class="wt">Skew by time to expiry<span>volatility points</span></span>{B.skew(INK, 560, 330)}</div>
  </section>
  {B.lineage()}
</div>
{ft()}
"""


def finding():
    return f"""
{top()}
<div class="page">
  {header('The finding', X.FIND_HEAD)}
  <section style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px">{B.nums(X.PROOF1_NUMS + X.PROOF2_NUMS)}</section>
  <section style="display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:start">
    <div class="w"><span class="wt">{esc(X.PROOF1_HEAD)}</span><p class="p">{esc(X.PROOF1)}</p><p class="b-sub" style="margin:0;font-size:15px;line-height:1.5">{esc(X.PROOF1_NET)}</p></div>
    <div class="w"><span class="wt">{esc(X.PROOF2_HEAD)}</span><p class="p">{esc(X.PROOF2)}</p></div>
  </section>
  <div class="w"><span class="wt">How far apart equally good fits landed<span>2,379 surfaces</span></span>{B.hist(INK, 1170, 300)}</div>
  <section style="display:grid;grid-template-columns:1.6fr 1fr;gap:22px;align-items:start">
    <div class="w"><span class="wt">By setting</span>{B.bars(INK, 700)}</div>
    <div class="w"><span class="wt">What it means</span><p class="p">{esc(X.PER_PARAM)}</p></div>
  </section>
  <div class="w" style="gap:14px"><span class="wt">Pick a stock</span><span style="display:flex;gap:8px;flex-wrap:wrap">{B.picks()}</span><p class="p">{esc(X.rel_line())}</p>{B.stock(INK, 1170)}</div>
  <section style="display:grid;grid-template-columns:1fr 1fr;gap:22px">
    <div class="b-num"><span>Held-out dates</span><b>{X.G8['median_network_relative'] * 100:.1f}% vs {X.G8['median_best_fit_relative'] * 100:.1f}%</b><span>{esc(X.HELDOUT)}</span></div>
    <div class="b-num"><span>Option backtest</span><b style="color:var(--ink)">0 of 210</b><span>{esc(X.BACKTEST)}</span></div>
  </section>
</div>
{ft()}
"""


def about():
    return f"""
{top()}
<div class="page">
  {header('About', X.ABOUT_HEAD)}
  <section style="display:grid;grid-template-columns:1.6fr 1fr;gap:22px;align-items:start">
    {B.video(icon_fill='#FF9500', icon_ink='#1C1C1E')}
    <div class="w"><span class="wt">Method and data</span>{''.join(f'<p class="p" style="font-size:17px">{esc(m)}</p>' for m in X.METHOD)}</div>
  </section>
  <section style="display:grid;grid-template-columns:1.2fr 1fr;gap:22px;align-items:start">
    <div class="w"><span class="wt">Limits</span>{B.bullet_list(X.LIMITS)}</div>
    <div class="w"><span class="wt">Also explored</span><p class="p">{esc(X.ALSO)}</p><span class="wt" style="margin-top:12px">Source code</span><a class="b-model" style="font-size:16px" href="https://{X.REPO}">{esc(X.REPO)}</a></div>
  </section>
  {dock()}
</div>
{ft()}
"""


def team():
    return f"""
{top()}
<div class="page">
  {header(X.TEAM_HEAD, X.TEAM_INTRO)}
  <section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:22px">{B.team_cards()}</section>
  <section style="display:grid;grid-template-columns:1fr 1.4fr;gap:22px;align-items:start">
    <div class="w"><span class="wt">Supervisor</span><b style="font-size:20px">{esc(X.SUPERVISOR[0])}</b><span class="b-sub">{esc(X.SUPERVISOR[1])}</span></div>
    <div class="w"><span class="wt">Thanks</span>{B.bullet_list(X.THANKS)}</div>
  </section>
</div>
{ft()}
"""


def references():
    return f"""
{top()}
<div class="page">
  {header('References', 'The papers behind the model and its methods, and where the data comes from.')}
  <section style="display:grid;grid-template-columns:1fr 1fr;gap:28px 22px;align-items:start">{B.refs()}</section>
</div>
{ft()}
"""


DESIGN = Design(
    num=4, slug="springboard", name="Springboard",
    concept="An iPhone home screen for the site: widgets of mixed sizes, coloured app icons, a frosted dock.",
    memorable="Each page is an app with its own Apple system colour; the home screen is a grid of live widgets.",
    layout="8-column widget grid (small, medium, large tiles), large iOS titles, grouped lists for tables and settings.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap",
    display_font="Figtree,sans-serif", body_font="Figtree,Helvetica,sans-serif",
    type_sample="Double Heston, on today’s market",
    type_note="Figtree 800 for large titles and widget numbers; 500–700 for text and lists.",
    ink=INK, css=CSS, rail_side="r", default_dark=True,
    icon_fills={"model": {"fill": "#FF9500", "ink": "#1C1C1E"}, "fast": {"fill": "#FF9500", "ink": "#1C1C1E"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
