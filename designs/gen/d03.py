"""03 · Trading Desk — a broker terminal: dense panes on 1-px seams, condensed numerals, an option ticket."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

DARK = dict(bg="#0B0E11", surf="#12161B", raised="#1A2027", line="#262D36", grid="#1C222A", ink="#EAECEF",
            body="#B7BDC6", muted="#8A94A2", acc="#9B87FF", on_acc="#0B0E11", up="#0ECB81", down="#F6465D",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#EEF1F6")
LIGHT = dict(bg="#E6E9ED", surf="#FFFFFF", raised="#F3F5F7", line="#D5DAE0", grid="#ECEFF2", ink="#14171A",
             body="#3B424A", muted="#59616D", acc="#5A3FE6", on_acc="#FFFFFF", up="#0B8A58", down="#D1283F",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")

COND = "'Barlow Condensed',sans-serif"
CSS = f"""
.top{{height:52px;display:flex;align-items:center;gap:22px;padding:0 250px 0 112px;background:var(--surf);border-bottom:1px solid var(--line);font-size:15px}}
.top .brand{{font-family:{COND};font-weight:700;font-size:24px;letter-spacing:.01em}}
.top .brand span{{color:var(--acc)}}
.srch{{display:flex;align-items:center;gap:8px;height:34px;width:260px;padding:0 12px;border-radius:6px;background:var(--raised);color:var(--muted);font-size:14px}}
.ix{{display:flex;gap:18px;font-size:14px;color:var(--muted)}}.ix b{{color:var(--ink);font-weight:600}}
.st{{margin-left:auto;font-size:14px;color:var(--muted);display:flex;align-items:center;gap:8px}}.st i{{width:8px;height:8px;border-radius:4px;background:var(--muted)}}
.desk{{display:grid;gap:1px;background:var(--line);padding:1px;margin-left:96px}}
.pane{{background:var(--surf);min-width:0;display:flex;flex-direction:column}}
.ph{{height:40px;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:0 16px;border-bottom:1px solid var(--line);font-size:14px;color:var(--muted)}}
.ph b{{color:var(--ink);font-weight:600;font-size:15px}}
.tabs{{display:flex;gap:2px}}.tabs span{{padding:5px 10px;border-radius:5px;font-size:13px;font-weight:600;color:var(--muted)}}.tabs span.on{{background:var(--raised);color:var(--ink)}}
.pb{{padding:16px}}
.big{{font-family:{COND};font-weight:600;letter-spacing:-.01em;line-height:1}}
.pgt{{padding:26px 20px 22px 112px;display:flex;align-items:flex-end;justify-content:space-between;gap:24px;background:var(--bg)}}
.pgt h1{{margin:0;font-family:{COND};font-weight:700;font-size:56px;line-height:1}}
.pgt p{{margin:0;font-size:18px;line-height:1.5;color:var(--body);max-width:720px}}
.p{{margin:0;font-size:17px;line-height:1.58;color:var(--body)}}
.b-tick{{height:36px;display:flex;align-items:center;padding:0 250px 0 112px;background:var(--bg);border-bottom:1px solid var(--line);font-size:14px;white-space:nowrap}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-size:15px}}
.b-tb th{{text-align:right;font-weight:500;font-size:13px;color:var(--muted);padding:8px 12px;border-bottom:1px solid var(--line)}}
.b-tb td{{white-space:nowrap;text-align:right;padding:7px 12px;border-bottom:1px solid var(--grid);font-family:{COND};font-size:17px;font-weight:500}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb td b{{font-family:'Barlow',sans-serif;font-size:15px}}
.b-tb tr.sel td{{background:var(--raised)}}.b-tb tr.sel td:first-child{{box-shadow:inset 3px 0 0 var(--acc)}}
.b-model{{color:var(--acc)}}.b-sub{{color:var(--muted)}}
.b-lab{{font-size:13px;font-weight:500;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:40px;border-radius:6px;border:1px solid var(--line);background:var(--raised);color:var(--ink);font:500 16px 'Barlow',sans-serif;padding:0 10px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:40px;border-radius:6px;overflow:hidden;border:1px solid var(--line)}}
.b-seg span{{display:flex;align-items:center;justify-content:center;font-weight:600;color:var(--muted)}}.b-seg span.on{{background:var(--up);color:var(--on-up)}}
.b-btn{{height:44px;border-radius:6px;border:0;background:var(--acc);color:var(--on-acc);font:700 17px 'Barlow',sans-serif;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;padding:0 18px}}
.b-btn.sec{{background:var(--raised);color:var(--ink);border:1px solid var(--line)}}
.b-form .b-btn{{grid-column:1/-1}}.b-form label:nth-child(1),.b-form label:nth-child(2){{grid-column:1/-1}}
.b-sl{{display:grid;grid-template-columns:28px 1fr 70px;gap:12px;align-items:center;padding:8px 0;border-bottom:1px solid var(--grid)}}
.b-sl b{{font-family:{COND};font-size:20px;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:4px;font-size:13px;color:var(--muted)}}
.b-sl input{{width:100%;accent-color:#9B87FF}}.b-sl output{{text-align:right;font-family:{COND};font-size:19px;font-weight:600}}
.b-greek{{display:flex;flex-direction:column;gap:4px;padding:14px 16px;background:var(--surf)}}.b-greek b{{font-family:{COND};font-size:32px;font-weight:600}}
.b-num{{display:flex;flex-direction:column;gap:6px;padding:16px;background:var(--surf)}}.b-num b{{font-family:{COND};font-size:48px;font-weight:600;line-height:1;color:var(--acc)}}
.b-num span{{font-size:14px;line-height:1.4;color:var(--muted)}}
.b-eq{{display:flex;flex-direction:column;gap:8px;padding:16px;border-bottom:1px solid var(--grid)}}
.b-eqn{{font-family:'Barlow',sans-serif;font-size:24px;font-weight:500;line-height:1.4}}
.b-steps{{list-style:none;margin:0;padding:0}}.b-steps li{{display:grid;grid-template-columns:44px 1fr;gap:12px;padding:14px 16px;border-bottom:1px solid var(--grid)}}
.b-steps .b-n{{font-family:{COND};font-size:30px;color:var(--acc);line-height:1}}.b-steps li>span{{display:flex;flex-direction:column;gap:5px}}
.b-steps li>span>b{{font-size:17px}}.b-steps li>span>span{{font-size:15px;line-height:1.5;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--line)}}
.b-lin li{{background:var(--surf);padding:16px;display:flex;flex-direction:column;gap:6px}}.b-lin .b-y{{font-family:{COND};font-size:44px;font-weight:600}}
.b-lin li.now .b-y{{color:var(--acc)}}.b-lin li>span{{display:flex;flex-direction:column;gap:2px}}.b-lin li>span>span{{color:var(--muted);font-size:15px}}
.b-list{{margin:0;padding:6px 16px 16px 34px;display:flex;flex-direction:column;gap:8px;font-size:16px;line-height:1.5;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;background:var(--raised);display:flex;align-items:center;justify-content:center;cursor:pointer}}
.b-video figcaption{{padding:12px 16px;font-size:14px;color:var(--muted)}}
.b-person{{display:flex;flex-direction:column;gap:6px;padding:16px;background:var(--surf)}}.b-person .b-ph{{height:160px;background:var(--raised);display:flex;align-items:center;justify-content:center;margin-bottom:8px}}
.b-person b{{font-size:19px}}.b-person>span:last-child{{color:var(--muted);font-size:15px}}
.b-refs{{background:var(--surf)}}.b-refs h2{{margin:0;height:40px;display:flex;align-items:center;padding:0 16px;border-bottom:1px solid var(--line);font-size:15px;font-weight:600}}
.b-refs ol{{list-style:none;margin:0;padding:0}}.b-refs li{{display:grid;grid-template-columns:48px 1fr;gap:8px;padding:11px 16px;border-bottom:1px solid var(--grid);font-size:15px;line-height:1.45}}
.b-refs .b-rn{{font-family:{COND};font-size:17px;color:var(--acc)}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{padding:5px 10px;border-radius:5px;font-size:13px;font-weight:600;color:var(--muted);border:1px solid var(--line)}}.b-chip.on{{background:var(--acc);color:var(--on-acc);border-color:var(--acc)}}
.b-links{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:1px;background:var(--line)}}
.b-links a{{display:flex;align-items:center;gap:10px;padding:14px;background:var(--surf)}}.b-links a>span{{display:flex;flex-direction:column;gap:1px}}
.b-links b{{font-size:15px}}.b-links a>span>span{{color:var(--muted);font-size:13px}}
.ft{{padding:16px 20px 22px 112px;display:flex;justify-content:space-between;font-size:14px;color:var(--muted);background:var(--bg)}}
"""

INK = Ink(font="'Barlow',sans-serif", size=13, line_w=2.4, bar_radius=1)


def top():
    nifty, bank = X.w("NIFTY 50"), X.w("NIFTY BANK")
    ix = "".join(f'<span>{n} <b>{inr(v["last"])}</b> <span class="{arrow(v["pct"])[1]}">{arrow(v["pct"])[0]} {abs(v["pct"]):.2f}%</span></span>'
                 for n, v in (("NIFTY", nifty), ("BANK", bank)))
    return (f'<header class="top"><a class="brand" href="Main.dc.html">DH<span>/</span>desk</a>'
            f'<label class="srch"><svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5.2" style="fill:none;stroke:var(--muted);stroke-width:1.8"></circle>'
            f'<path d="M11,11 L15,15" style="stroke:var(--muted);stroke-width:1.8;stroke-linecap:round"></path></svg>Search 42 stocks</label>'
            f'<span class="ix">{ix}</span><span class="st"><i></i>Closed, last close {X.LAST_DAY}</span></header>')


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def pane(title, body, right="", pad=True, style=""):
    return (f'<section class="pane" style="{style}"><div class="ph"><b>{title}</b>{right}</div>'
            f'{"<div class=pb>" + body + "</div>" if pad else body}</section>')


def pgt(h, p):
    return f'<div class="pgt"><h1>{esc(h)}</h1><p>{esc(p)}</p></div>'


def ticket():
    K = X.K
    return pane("Option ticket", f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">{squircle('model', 40, fill='var(--acc)', ink='var(--on-acc)', ring=False)}
<span><b style="font-size:17px">{esc(X.CONTRACT)}</b><br><span class="b-sub" style="font-size:14px">{esc(X.CONTRACT_SUB)}</span></span></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);margin-bottom:14px">
  <div style="background:var(--surf);padding:12px 0"><span class="b-lab">Market close</span><div class="big" style="font-size:40px">₹{inr(K['market'])}</div><span class="b-sub" style="font-size:13px">IV {K['market_iv']:.2f}%</span></div>
  <div style="background:var(--surf);padding:12px 0 12px 14px"><span class="b-lab">Double Heston</span><div class="big" style="font-size:40px;color:var(--acc)">₹{inr(K['dh'])}</div><span class="b-sub" style="font-size:13px">IV {K['dh_iv']:.2f}%</span></div>
</div>
<p class="p" style="font-size:15px;margin-bottom:14px">Gap <b style="color:var(--ink)">+₹{inr(X.GAP)}</b>. {esc(X.MC_LINE)}.</p>
{B.pricing_form()}""", '<span class="tabs"><span class="on">Call</span><span>Put</span></span>')


def home():
    r = X.REL_LAST
    return f"""
{B.ticker()}
{top()}
<div class="desk" style="grid-template-columns:330px 1fr 370px">
  {pane('Watchlist', B.watch_table(spark=(64, 22)), '<span class="tabs"><span class="on">Top</span><span>All 42</span></span>', pad=False)}
  {pane('RELIANCE', f'<div style="display:flex;align-items:baseline;gap:14px;margin-bottom:10px"><span class="big" style="font-size:52px">{inr(r[4])}</span><span style="font-size:18px;font-weight:600">{B.rel_change()}</span></div>{B.rel_candles(INK, 640, 470, 10)}<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--line);margin-top:16px">' + ''.join(f'<div class="b-num" style="padding:12px 14px"><span>{k}</span><b style="font-size:26px;color:var(--ink)">{v}</b></div>' for k, v in B.rel_stats()) + '</div>', '<span class="tabs"><span>1D</span><span>1M</span><span class="on">3M</span><span>Line</span><span class="on">Candles</span></span>')}
  {ticket()}
</div>
<div class="desk" style="grid-template-columns:1.15fr 1fr 1fr">
  {pane('Does moving volatility price options better?', f'<p class="p" style="font-size:19px;color:var(--ink);margin-bottom:10px"><b>{esc(X.A_SHORT)}</b></p><p class="p">{esc(X.A_LONG)} {esc(X.TWIST)}</p>{B.smile(INK, 520, 300)}')}
  {pane('Two clocks', f'<p class="p" style="margin-bottom:12px">{esc(X.TWO_CLOCKS)}</p><div style="display:flex;gap:18px;margin-bottom:12px">' + ''.join(f'<span style="display:flex;align-items:center;gap:10px">{squircle(k, 40, fill=fl, ink=ik, ring=False)}<span><b>{a}, {b}</b><br><span class="b-sub" style="font-size:13px">{c}</span></span></span>' for k, fl, ik, (a, b, c) in (("slow", "var(--raised)", "var(--ink)", X.SLOW), ("fast", "var(--acc)", "var(--on-acc)", X.FAST))) + f'</div>{B.skew(INK, 440, 250)}')}
  {pane('The finding', f'<p class="p" style="font-size:18px;color:var(--ink);margin-bottom:12px">{esc(X.FINDING_LINE)}</p>' + B.bars(INK, 430, row_h=26, label_w=180, legend=False, compact=True, only=('kappa_s', 'kappa_f', 'sigma_s', 'v0_s', 'v0_f')) + f'<p class="b-sub" style="font-size:13px;margin:6px 0 12px">Bars: equally good fits. Ticks: two random parameter sets.</p><a class="b-btn" href="Finding.dc.html">{X.CTA["finding"]}</a>', '<span class="b-model" style="font-weight:700">3.9× random</span>')}
</div>
{B.page_links('Main', 36)}
{ft()}
"""


def market():
    stats = "".join(f'<div class="b-num" style="padding:12px 16px"><span>{k}</span><b style="font-size:28px;color:var(--ink)">{v}</b></div>' for k, v in B.rel_stats())
    return f"""
{top()}
{pgt('Market', X.MARKET_SUB)}
<div class="desk" style="grid-template-columns:420px 1fr">
  {pane('Watchlist', B.watch_table(names=True, spark=(70, 24)), f'<span class="b-sub">close {X.LAST_DAY}</span>', pad=False)}
  <div style="display:grid;gap:1px;min-width:0">
    {pane('RELIANCE, Reliance Industries', f'<div style="display:flex;align-items:baseline;gap:14px;margin-bottom:10px"><span class="big" style="font-size:60px">{inr(X.REL_LAST[4])}</span><span style="font-size:19px;font-weight:600">{B.rel_change()}</span></div>{B.rel_candles(INK, 840, 520, 8)}', '<span class="tabs"><span>1M</span><span class="on">3M</span><span>Line</span><span class="on">Candles</span></span>')}
    <div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:1px">{stats}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px">
      {pane('NIFTY 50, close', B.nifty_line(INK, 420, 200))}
      {pane('NIFTY BANK, close', B.nifty_line(INK, 420, 200, 'BANKNIFTY'))}
    </div>
  </div>
</div>
{ft()}
"""


def model():
    return f"""
{top()}
{pgt('The model', 'Price a listed option with Double Heston and set it against the market. ' + X.MODEL_EXPLAIN)}
<div class="desk" style="grid-template-columns:370px 1fr 1fr">
  {ticket()}
  {pane('Smile, market against model', B.market_smile(INK, 460, 360, 46), f'<span class="b-sub">{X.EXPIRY}</span>')}
  {pane('Option chain', B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV')), f'<span class="b-sub">NSE close</span>', pad=False)}
</div>
<div class="desk" style="grid-template-columns:1fr 1fr">
  {pane('Slow factor', B.sliders('slow'), f'<span class="dn" style="font-size:13px">{esc(X.FELLER["slow"])}</span>')}
  {pane('Fast factor', B.sliders('fast'), f'<span class="dn" style="font-size:13px">{esc(X.FELLER["fast"])}</span>')}
</div>
<div class="desk" style="grid-template-columns:repeat(5,minmax(0,1fr)) 1.4fr">{B.greeks()}
  <div class="b-greek" style="justify-content:center;gap:10px"><span class="b-sub" style="font-size:14px">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div></div>
<p class="b-sub" style="margin:0;padding:14px 20px 0 112px;font-size:14px">{esc(X.MODEL_SOURCE)}</p>
{ft()}
"""


def maths():
    return f"""
{top()}
{pgt('How it works', X.MATHS_INTRO)}
<div class="desk" style="grid-template-columns:1.3fr 1fr">
  {pane('Equations', B.equations(), '<span class="b-sub">ten settings, two factors</span>', pad=False)}
  {pane('Step by step', B.steps(), pad=False)}
</div>
<div class="desk" style="grid-template-columns:1fr 1fr">
  {pane('The bend at the starting settings', B.smile(INK, 600, 360))}
  {pane('Skew by time to expiry', B.skew(INK, 600, 360) + f'<p class="p" style="margin-top:10px;font-size:15px">Fast factor half-life about {X.HL["fast_days"] / 7:.0f} weeks; slow factor {X.HL["slow_years"]:.1f} years.</p>')}
</div>
<div class="desk" style="grid-template-columns:1fr">{pane('Lineage', B.lineage(), pad=False)}</div>
{ft()}
"""


def finding():
    return f"""
{top()}
{pgt('The finding', X.FIND_HEAD + ' ' + X.FINDING_SUB)}
<div class="desk" style="grid-template-columns:repeat(6,minmax(0,1fr))">{B.nums(X.PROOF1_NUMS + X.PROOF2_NUMS)}</div>
<div class="desk" style="grid-template-columns:1fr 1fr">
  {pane(X.PROOF1_HEAD, f'<p class="p">{esc(X.PROOF1)}</p><p class="b-sub" style="margin:12px 0 0;font-size:15px;line-height:1.5">{esc(X.PROOF1_NET)}</p>')}
  {pane(X.PROOF2_HEAD, f'<p class="p">{esc(X.PROOF2)}</p>')}
</div>
<div class="desk" style="grid-template-columns:1fr">{pane('How far apart equally good fits landed, 2,379 surfaces', B.hist(INK, 1290, 300))}</div>
<div class="desk" style="grid-template-columns:1.5fr 1fr">
  {pane('By setting', B.bars(INK, 740))}
  {pane('What it means', f'<p class="p">{esc(X.PER_PARAM)}</p>')}
</div>
<div class="desk" style="grid-template-columns:1fr">{pane('Pick a stock', f'<p class="p" style="margin-bottom:12px">{esc(X.rel_line())}</p>{B.stock(INK, 1290)}', f'<span style="display:flex;gap:6px">{B.picks()}</span>')}</div>
<div class="desk" style="grid-template-columns:1fr 1fr">
  {pane('Held-out dates', f'<div class="big" style="font-size:56px">{X.G8["median_network_relative"] * 100:.1f}% <span class="b-sub" style="font-size:24px">vs</span> <span style="color:var(--acc)">{X.G8["median_best_fit_relative"] * 100:.1f}%</span></div><p class="p" style="margin-top:10px">{esc(X.HELDOUT)}</p>')}
  {pane('Option backtest', f'<div class="big" style="font-size:56px">0 of 210</div><p class="p" style="margin-top:10px">{esc(X.BACKTEST)}</p>')}
</div>
{ft()}
"""


def about():
    return f"""
{top()}
{pgt('About', X.ABOUT_HEAD)}
<div class="desk" style="grid-template-columns:1.6fr 1fr">
  {pane('The video', B.video(), pad=False)}
  {pane('Method and data', ''.join(f'<p class="p" style="margin-bottom:12px">{esc(m)}</p>' for m in X.METHOD))}
</div>
<div class="desk" style="grid-template-columns:1.3fr 1fr 1fr">
  {pane('Limits', B.bullet_list(X.LIMITS), pad=False)}
  {pane('Also explored', f'<p class="p">{esc(X.ALSO)}</p>')}
  {pane('Source code', f'<a class="b-model" style="font-size:17px;font-weight:600;word-break:break-all" href="https://{X.REPO}">{esc(X.REPO)}</a>')}
</div>
{ft()}
"""


def team():
    return f"""
{top()}
{pgt(X.TEAM_HEAD, X.TEAM_INTRO)}
<div class="desk" style="grid-template-columns:repeat(4,minmax(0,1fr))">{B.team_cards()}</div>
<div class="desk" style="grid-template-columns:1fr 1.4fr">
  {pane('Supervisor', f'<b style="font-size:20px">{esc(X.SUPERVISOR[0])}</b><p class="b-sub" style="margin:4px 0 0;font-size:15px">{esc(X.SUPERVISOR[1])}</p>')}
  {pane('Thanks', B.bullet_list(X.THANKS), pad=False)}
</div>
{ft()}
"""


def references():
    return f"""
{top()}
{pgt('References', 'The papers behind the model and its methods, and where the data comes from.')}
<div class="desk" style="grid-template-columns:1fr 1fr;align-items:start">{B.refs()}</div>
{ft()}
"""


DESIGN = Design(
    num=3, slug="trading-desk", name="Trading Desk",
    concept="A broker terminal: dense panes on 1-px seams, condensed numerals, the option as an order ticket.",
    memorable="The option ticket beside the candles: market close against the model price, one tap to price.",
    layout="Full-bleed pane grid (watchlist, chart, ticket) with tabbed pane headers; compact rows; nothing floats.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700&display=swap",
    display_font=COND, body_font="'Barlow',Helvetica,sans-serif",
    type_sample="NIFTY 23,140.50  ₹600.40",
    type_note="Barlow Condensed 600 for prices and headings (numbers fit dense panes); Barlow 400–700 for text.",
    ink=INK, css=CSS, rail_side="l", default_dark=True,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
