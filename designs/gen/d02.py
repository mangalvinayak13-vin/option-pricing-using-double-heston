"""02 · Front Panel — chart-led editorial. Every page opens on one large numbered figure; no boxes."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, esc, inr, squircle

LIGHT = dict(bg="#F4F5F0", surf="#FFFFFF", raised="#E6E9E1", line="#C9CEC3", grid="#E0E3DA", ink="#111311",
             body="#3A3F3A", muted="#5B625B", acc="#1B6B50", on_acc="#FFFFFF", up="#13804E", down="#C52F3E",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#0F1311", surf="#151A17", raised="#1C2320", line="#2A332E", grid="#1C2420", ink="#E9EEEA",
            body="#B7C0BA", muted="#8E9892", acc="#4FD1A5", on_acc="#06140E", up="#2EBD85", down="#F6465D",
            on_up="#04120C", track_off="#39393D", ferro="#050505", ferro_hi="#EEF3F0")

DISP = "'Bricolage Grotesque',sans-serif"
CSS = f"""
.hd{{height:64px;display:flex;align-items:center;gap:26px;padding:0 260px 0 72px;font-size:15px;color:var(--muted)}}
.hd .brand{{font-family:{DISP};font-weight:800;font-size:20px;color:var(--ink);letter-spacing:-.02em}}
.hd .dot{{width:8px;height:8px;border-radius:4px;background:var(--muted);display:inline-block;margin-right:8px}}
.b-tick{{height:44px;display:flex;align-items:center;padding:0 250px 0 72px;border-bottom:1px solid var(--line);font-size:15px;white-space:nowrap}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:30px;overflow:hidden;align-items:center}}
.b-ti{{display:inline-flex;gap:9px}}.b-ti-lab{{color:var(--muted)}}
.wrap{{padding:56px 150px 120px 72px;display:flex;flex-direction:column;gap:120px}}
.g{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:28px;row-gap:24px}}
.k{{font-size:15px;font-weight:600;color:var(--acc)}}
.d1{{margin:0;font-family:{DISP};font-weight:800;font-size:68px;line-height:.98;letter-spacing:-.035em}}
.d2{{margin:0;font-family:{DISP};font-weight:800;font-size:42px;line-height:1.02;letter-spacing:-.03em}}
.lede{{margin:0;font-size:21px;line-height:1.55;color:var(--body)}}
.p{{margin:0;font-size:18px;line-height:1.62;color:var(--body)}}
figure{{margin:0;display:flex;flex-direction:column;gap:14px}}
figcaption{{font-size:15px;line-height:1.5;color:var(--muted);max-width:760px}}
figcaption b{{color:var(--ink);font-weight:600}}
.b-btn{{display:inline-flex;align-items:center;height:52px;padding:0 24px;border-radius:26px;border:1.5px solid var(--ink);font-size:17px;font-weight:600;color:var(--ink);background:transparent;font-family:inherit}}
.b-btn.pri{{background:var(--acc);border-color:var(--acc);color:var(--on-acc)}}
.b-lab{{font-size:14px;font-weight:600;color:var(--muted)}}
.b-sub{{color:var(--muted);font-size:14px}}
.b-num{{display:flex;flex-direction:column;gap:8px}}.b-num b{{font-family:{DISP};font-weight:800;font-size:58px;line-height:.95;letter-spacing:-.03em;color:var(--acc)}}
.b-num span{{font-size:16px;line-height:1.45;color:var(--body)}}
.b-tb{{width:100%;border-collapse:collapse;font-size:16px}}
.b-tb th{{text-align:right;font-size:14px;font-weight:600;color:var(--muted);padding:10px 10px;border-bottom:1.5px solid var(--ink)}}
.b-tb td{{text-align:right;padding:11px 10px;border-bottom:1px solid var(--line)}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}
.b-tb tr.sel td{{background:var(--raised);font-weight:700}}.b-model{{color:var(--acc);font-weight:600}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:18px;align-items:end;margin:0;padding:24px 0;border-top:1.5px solid var(--ink);border-bottom:1px solid var(--line)}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:8px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:50px;border-radius:12px;border:1.5px solid var(--line);background:var(--surf);color:var(--ink);font:500 17px/1 inherit;padding:0 14px}}
.b-seg{{display:inline-flex;height:50px;border-radius:12px;border:1.5px solid var(--line);overflow:hidden}}
.b-seg span{{display:flex;align-items:center;padding:0 18px;font-weight:600;color:var(--muted)}}.b-seg span.on{{background:var(--ink);color:var(--bg)}}
.b-sl{{display:grid;grid-template-columns:34px 1fr 78px;gap:14px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}}
.b-sl b{{font-family:{DISP};font-size:22px;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:6px;font-size:15px;color:var(--muted)}}
.b-sl input{{width:100%;accent-color:#1B6B50}}.b-sl output{{text-align:right;font-weight:700;font-size:18px}}
.b-greek{{display:flex;flex-direction:column;gap:6px}}.b-greek b{{font-family:{DISP};font-size:38px;font-weight:800;letter-spacing:-.02em}}
.b-eq{{display:flex;flex-direction:column;gap:10px;padding:0 0 26px;border-bottom:1px solid var(--line)}}
.b-eqn{{font-family:{DISP};font-size:30px;font-weight:600;line-height:1.35;letter-spacing:-.01em}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:26px}}
.b-steps li{{display:grid;grid-template-columns:54px 1fr;gap:16px}}.b-steps .b-n{{font-family:{DISP};font-size:40px;font-weight:800;color:var(--acc);line-height:1}}
.b-steps li>span{{display:flex;flex-direction:column;gap:6px}}.b-steps li>span>b{{font-size:20px}}.b-steps li>span>span{{font-size:17px;line-height:1.55;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px}}
.b-lin li{{display:flex;flex-direction:column;gap:6px;padding-top:18px;border-top:1.5px solid var(--line)}}.b-lin li.now{{border-top-color:var(--acc)}}
.b-lin .b-y{{font-family:{DISP};font-size:56px;font-weight:800;letter-spacing:-.03em}}.b-lin li.now .b-y{{color:var(--acc)}}
.b-lin li>span{{display:flex;flex-direction:column;gap:3px}}.b-lin li>span>b{{font-size:20px}}.b-lin li>span>span{{color:var(--muted);font-size:16px}}
.b-list{{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:10px;font-size:18px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;border-radius:24px;background:var(--raised);display:flex;align-items:center;justify-content:center;cursor:pointer}}
.b-video figcaption{{margin-top:12px}}
.b-person{{display:flex;flex-direction:column;gap:8px}}.b-person .b-ph{{aspect-ratio:4/5;border-radius:24px;background:var(--raised);display:flex;align-items:center;justify-content:center;margin-bottom:10px}}
.b-person b{{font-family:{DISP};font-size:24px;font-weight:800}}.b-person>span:last-child{{color:var(--muted);font-size:16px}}
.b-refs h2{{margin:0 0 12px;font-family:{DISP};font-size:28px;font-weight:800}}
.b-refs ol{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}}
.b-refs li{{display:grid;grid-template-columns:52px 1fr;gap:10px;padding:14px 0;border-bottom:1px solid var(--line);font-size:17px;line-height:1.5}}
.b-refs .b-rn{{color:var(--acc);font-weight:700}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{display:inline-flex;height:38px;align-items:center;padding:0 16px;border-radius:19px;border:1.5px solid var(--line);font-weight:600;font-size:15px}}
.b-chip.on{{background:var(--ink);color:var(--bg);border-color:var(--ink)}}
.b-links{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:34px 28px}}
.b-links a{{display:flex;align-items:center;gap:14px}}.b-links a>span{{display:flex;flex-direction:column;gap:2px}}.b-links b{{font-size:18px}}.b-links a>span>span{{color:var(--muted);font-size:15px}}
.ft{{padding:30px 150px 44px 72px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-size:15px;color:var(--muted)}}
.lnk{{font-weight:600;color:var(--acc);font-size:17px;text-decoration:underline;text-underline-offset:5px}}
"""

INK = Ink(font="Geist,sans-serif", size=14, line_w=4, grid="transparent", axis="var(--ink)", bar_radius=3)


def hd():
    return (f'<header class="hd"><a class="brand" href="Main.dc.html">Double Heston</a>'
            f'<span><span class="dot"></span>{esc(X.STATUS)}</span></header>')


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def fig(n, chart, cap):
    return f'<figure>{chart}<figcaption><b>Figure {n}.</b> {esc(cap)}</figcaption></figure>'


def title(kicker, head, lede=None, span=9):
    l = f'<p class="lede" style="grid-column:1/span 8">{esc(lede)}</p>' if lede else ""
    return (f'<section class="g" style="row-gap:22px"><span class="k" style="grid-column:1/span 12">{kicker}</span>'
            f'<h1 class="d1" style="grid-column:1/span {span}">{esc(head)}</h1>{l}</section>')


def home():
    s, f = X.SLOW, X.FAST
    return f"""
{B.ticker()}
{hd()}
<div class="wrap">
  <section class="g" style="align-items:end">
    <div style="grid-column:1/span 4;display:flex;flex-direction:column;gap:24px;padding-bottom:40px">
      <h1 class="d1" style="font-size:60px">{esc(X.Q)}</h1>
      <p class="lede"><b style="color:var(--ink)">{esc(X.A_SHORT)}</b> {esc(X.A_LONG)}</p>
      <div style="display:flex;gap:12px;flex-wrap:wrap"><a class="b-btn pri" href="Model.dc.html">{X.CTA['model']}</a><a class="b-btn" href="Finding.dc.html">{X.CTA['finding']}</a></div>
    </div>
    <div style="grid-column:5/span 8">{fig(1, B.smile(INK, 790, 500), X.SMILE_CAPTION)}</div>
  </section>
  <section class="g" style="align-items:center">
    <div style="grid-column:1/span 5;display:flex;flex-direction:column;gap:22px">
      <h2 class="d2">Two clocks shape the curve.</h2><p class="p">{esc(X.TWO_CLOCKS)}</p>
      <div style="display:flex;align-items:center;gap:16px">{squircle('slow', 58)}<span><b style="font-size:19px">{s[0]}, {s[1]}</b><br><span class="b-sub" style="font-size:16px">{s[2]}</span></span></div>
      <div style="display:flex;align-items:center;gap:16px">{squircle('fast', 58, fill='var(--acc)', ink='var(--on-acc)')}<span><b style="font-size:19px">{f[0]}, {f[1]}</b><br><span class="b-sub" style="font-size:16px">{f[2]}</span></span></div>
    </div>
    <div style="grid-column:7/span 6">{fig(2, B.skew(INK, 580, 300), 'How steep the skew is, by time to expiry: implied volatility at 95% of the price minus at 105%, in volatility points.')}</div>
  </section>
  <section class="g" style="align-items:end">
    <div style="grid-column:1/span 12;display:flex;align-items:baseline;justify-content:space-between"><h2 class="d2">NIFTY 50, the last 62 trading days</h2><a class="lnk" href="Market.dc.html">{X.CTA['market']}</a></div>
    <div style="grid-column:1/span 12">{fig(3, B.nifty_line(INK, 1210, 260), f'Closing level from the official NSE files, {X.FIRST_DAY} to {X.LAST_DAY}. Last close {inr(X.SPOT)}.')}</div>
  </section>
  <section class="g" style="row-gap:40px">
    <p class="d2" style="grid-column:1/span 10;font-size:50px;line-height:1.08">{esc(X.FINDING_LINE)}</p>
    <div style="grid-column:1/span 8">{fig(4, B.bars(INK, 800), 'Median distance between equally good fits for each setting, against two parameter sets picked at random. Speeds are the least pinned down; today’s level the most.')}</div>
    <div style="grid-column:9/span 4;display:flex;flex-direction:column;gap:30px">{B.nums([('1.80', 'recovery skill on simulated data, where 1.00 is guessing'), (f'{X.RATIO:.1f}×', 'further apart than two random parameter sets')])}<a class="lnk" href="Finding.dc.html">{X.CTA['finding']}</a></div>
  </section>
  {B.page_links('Main', 52)}
</div>
{ft()}
"""


def market():
    stats = "".join(f'<span style="display:flex;flex-direction:column;gap:4px"><span class="b-lab">{k}</span><b style="font-size:21px">{v}</b></span>' for k, v in B.rel_stats())
    return f"""
{hd()}
<div class="wrap">
  {title('Market', 'Market', X.MARKET_SUB)}
  <section style="display:flex;flex-direction:column;gap:18px">
    <div style="display:flex;align-items:baseline;justify-content:space-between">
      <span style="display:flex;align-items:baseline;gap:18px"><b class="d2">RELIANCE</b><span class="d2" style="font-weight:600">{inr(X.REL_LAST[4])}</span><span style="font-size:19px;font-weight:600">{B.rel_change()}</span></span>
      <span style="display:flex;gap:10px"><span class="b-chip">Line</span><span class="b-chip on">Candles</span><span class="b-chip">1M</span><span class="b-chip on">3M</span></span>
    </div>
    {fig(1, B.rel_candles(INK, 1218, 520, 8), 'Daily candlesticks from the official NSE files: green when the day closed higher, red when it closed lower. Volume below.')}
    <div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:20px;padding-top:6px">{stats}</div>
  </section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 7;display:flex;flex-direction:column;gap:16px"><h2 class="d2">Watchlist</h2>{B.watch_table(names=True)}</div>
    <div style="grid-column:8/span 5;display:flex;flex-direction:column;gap:40px">
      {fig(2, B.nifty_line(INK, 500, 220), 'NIFTY 50 closing level. Index levels are published as closes, so this is a line, not candles.')}
      {fig(3, B.nifty_line(INK, 500, 220, 'BANKNIFTY'), 'NIFTY BANK closing level over the same 62 days.')}
      <p class="p">{esc(X.UNIVERSE)}</p>
    </div>
  </section>
</div>
{ft()}
"""


def model():
    K = X.K
    return f"""
{hd()}
<div class="wrap" style="gap:88px">
  {title('The model', 'Price an option', 'Pick a listed option, price it with Double Heston, and set it against what the market paid.')}
  {B.pricing_form()}
  <section class="g" style="align-items:end">
    <div style="grid-column:1/span 3" class="b-num"><b style="color:var(--ink)">₹{inr(K['market'])}</b><span>Market close, {esc(X.CONTRACT)}. Implied volatility {K['market_iv']:.2f}%.</span></div>
    <div style="grid-column:4/span 3" class="b-num"><b>₹{inr(K['dh'])}</b><span>Double Heston at its starting settings. {esc(X.MC_LINE)}.</span></div>
    <div style="grid-column:7/span 2" class="b-num"><b style="color:var(--ink)">+₹{inr(X.GAP, 0)}</b><span>model minus market</span></div>
    <p class="p" style="grid-column:9/span 4">{esc(X.MODEL_EXPLAIN)}</p>
  </section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 7">{fig(1, B.market_smile(INK, 700, 400), 'Implied volatility by strike, expiry ' + X.EXPIRY + '. Circles: the market, from NSE closing prices. Line: Double Heston at its starting settings.')}</div>
    <div style="grid-column:8/span 5;display:flex;flex-direction:column;gap:12px"><b style="font-size:19px">Option chain around the money</b>{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div>
  </section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 6;display:flex;flex-direction:column;gap:6px"><h2 class="d2" style="font-size:32px">Slow factor</h2><span class="b-sub" style="color:var(--down)">{esc(X.FELLER['slow'])}</span>{B.sliders('slow')}</div>
    <div style="grid-column:7/span 6;display:flex;flex-direction:column;gap:6px"><h2 class="d2" style="font-size:32px">Fast factor</h2><span class="b-sub" style="color:var(--down)">{esc(X.FELLER['fast'])}</span>{B.sliders('fast')}</div>
    <div style="grid-column:1/span 12;display:flex;justify-content:space-between;align-items:center"><p class="b-sub" style="margin:0;font-size:16px">{esc(X.FELLER_NOTE)}</p><button class="b-btn" type="button">Reset to starting settings</button></div>
  </section>
  <section style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:28px;padding-top:24px;border-top:1.5px solid var(--ink)">{B.greeks()}</section>
  <p class="b-sub" style="margin:0;font-size:15px">{esc(X.MODEL_SOURCE)}</p>
</div>
{ft()}
"""


def maths():
    return f"""
{hd()}
<div class="wrap" style="gap:96px">
  {title('How it works', 'Two variances, one integral', X.MATHS_INTRO)}
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 7;display:flex;flex-direction:column;gap:26px">{B.equations()}</div>
    <div style="grid-column:9/span 4">{B.steps()}</div>
  </section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 7">{fig(1, B.smile(INK, 700, 400), 'The bend the model produces at its starting settings, against one fixed volatility.')}</div>
    <div style="grid-column:8/span 5">{fig(2, B.skew(INK, 500, 320), f'The fast factor (half-life about {X.HL["fast_days"] / 7:.0f} weeks) shapes short-dated options; the slow one ({X.HL["slow_years"]:.1f} years) holds up the long end.')}</div>
  </section>
  <section style="display:flex;flex-direction:column;gap:26px"><h2 class="d2">Where it comes from</h2>{B.lineage()}</section>
</div>
{ft()}
"""


def finding():
    return f"""
{hd()}
<div class="wrap" style="gap:104px">
  {title('The finding', X.FIND_HEAD, None, 10)}
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 6;display:flex;flex-direction:column;gap:18px"><h2 class="d2" style="font-size:34px">{esc(X.PROOF1_HEAD)}</h2><p class="p">{esc(X.PROOF1)}</p><p class="b-sub" style="margin:0;font-size:16px;line-height:1.55">{esc(X.PROOF1_NET)}</p></div>
    <div style="grid-column:8/span 5;display:grid;grid-template-columns:1fr 1fr;gap:34px 24px">{B.nums(X.PROOF1_NUMS)}</div>
  </section>
  <section class="g" style="align-items:start;row-gap:40px">
    <div style="grid-column:1/span 6;display:flex;flex-direction:column;gap:18px"><h2 class="d2" style="font-size:34px">{esc(X.PROOF2_HEAD)}</h2><p class="p">{esc(X.PROOF2)}</p></div>
    <div style="grid-column:8/span 5;display:grid;grid-template-columns:1fr 1fr;gap:34px 24px">{B.nums(X.PROOF2_NUMS)}</div>
    <div style="grid-column:1/span 12">{fig(1, B.hist(INK, 1210, 320), 'How far apart the equally good fits landed on each of the 2,379 surfaces that had more than one, in spreads of the training data.')}</div>
  </section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 8">{fig(2, B.bars(INK, 800), 'The same distance, setting by setting.')}</div>
    <p class="p" style="grid-column:9/span 4">{esc(X.PER_PARAM)}</p>
  </section>
  <section style="display:flex;flex-direction:column;gap:22px">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap"><h2 class="d2">Pick a stock</h2><span style="display:flex;gap:8px;flex-wrap:wrap">{B.picks()}</span></div>
    <p class="p" style="max-width:900px">{esc(X.rel_line())}</p>
    {fig(3, B.stock(INK, 1210), 'RELIANCE, 60 trading days. Top: price error of the best Double Heston fit and of one flat volatility. Bottom: how far apart the equally good fits landed.')}
  </section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 6" class="b-num"><b>{X.G8['median_network_relative'] * 100:.1f}% vs {X.G8['median_best_fit_relative'] * 100:.1f}%</b><span>{esc(X.HELDOUT)}</span></div>
    <div style="grid-column:7/span 6" class="b-num"><b style="color:var(--ink)">0 of 210</b><span>{esc(X.BACKTEST)}</span></div>
  </section>
</div>
{ft()}
"""


def about():
    return f"""
{hd()}
<div class="wrap" style="gap:96px">
  {title('About', X.ABOUT_HEAD, None, 10)}
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 8">{B.video()}</div>
    <div style="grid-column:9/span 4;display:flex;flex-direction:column;gap:16px"><h2 class="d2" style="font-size:30px">Method and data</h2>{''.join(f'<p class="p" style="font-size:17px">{esc(m)}</p>' for m in X.METHOD)}</div>
  </section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 7;display:flex;flex-direction:column;gap:16px"><h2 class="d2" style="font-size:30px">Limits</h2>{B.bullet_list(X.LIMITS)}</div>
    <div style="grid-column:9/span 4;display:flex;flex-direction:column;gap:16px"><h2 class="d2" style="font-size:30px">Also explored</h2><p class="p">{esc(X.ALSO)}</p></div>
  </section>
  <p class="p" style="font-size:20px">Source code: <a class="lnk" style="font-size:20px" href="https://{X.REPO}">{esc(X.REPO)}</a></p>
</div>
{ft()}
"""


def team():
    return f"""
{hd()}
<div class="wrap" style="gap:88px">
  {title('Team', X.TEAM_HEAD, X.TEAM_INTRO)}
  <section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:28px">{B.team_cards()}</section>
  <section class="g" style="align-items:start">
    <div style="grid-column:1/span 5;display:flex;flex-direction:column;gap:8px"><span class="k">Supervisor</span><b class="d2" style="font-size:30px">{esc(X.SUPERVISOR[0])}</b><span class="b-sub" style="font-size:17px">{esc(X.SUPERVISOR[1])}</span></div>
    <div style="grid-column:7/span 6;display:flex;flex-direction:column;gap:14px"><span class="k">Thanks</span>{B.bullet_list(X.THANKS)}</div>
  </section>
</div>
{ft()}
"""


def references():
    return f"""
{hd()}
<div class="wrap" style="gap:72px">
  {title('References', 'References', 'The papers behind the model and its methods, and where the data comes from.')}
  <section style="display:grid;grid-template-columns:1fr 1fr;gap:56px 48px;align-items:start">{B.refs()}</section>
</div>
{ft()}
"""


DESIGN = Design(
    num=2, slug="front-panel", name="Front Panel",
    concept="Chart-led editorial: every page opens on one large numbered figure, with the words set around it.",
    memorable="Figure 1 on every page: the chart is the headline, captions carry the argument.",
    layout="12-column editorial grid, no boxes; question left, a large figure right; generous vertical rhythm.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Geist:wght@400;500;600;700&display=swap",
    display_font=DISP, body_font="Geist,Helvetica,sans-serif",
    type_sample="Two clocks shape the curve.",
    type_note="Bricolage Grotesque 800 for headlines and figures' numbers; Geist 400–700 for text, tables and charts.",
    ink=INK, css=CSS, rail_side="r", default_dark=False,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}, "fast": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
