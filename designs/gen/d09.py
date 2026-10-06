"""09 · Oscilloscope — a lab instrument: scope screens with division grids, phosphor traces, rotary knobs."""
from __future__ import annotations

import math

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

DARK = dict(bg="#0F1419", surf="#151C23", raised="#1B242D", line="#27323D", grid="#1E2934", ink="#E4E9EE",
            body="#B6C0C9", muted="#8D99A5", acc="#7FB2E5", on_acc="#0F1419", up="#3DDC97", down="#FF6B6B",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")
LIGHT = dict(bg="#EEF2F6", surf="#FFFFFF", raised="#E3E9EF", line="#C6D0DA", grid="#DCE3EA", ink="#0F1419",
             body="#2D3945", muted="#4F5D6A", acc="#1F6FB8", on_acc="#FFFFFF", up="#1A7F4B", down="#C62F2F",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")

MONO = "'IBM Plex Mono',monospace"
CSS = f"""
.t-dark{{--scr:#081016;--div:rgba(127,178,229,.14);--divs:rgba(127,178,229,.07)}}
.t-light{{--scr:#F7FAFC;--div:rgba(31,111,184,.16);--divs:rgba(31,111,184,.07)}}
.bezel{{height:58px;display:flex;align-items:center;gap:24px;padding:0 250px 0 72px;background:var(--surf);border-bottom:1px solid var(--line);font-family:{MONO};font-size:14px;color:var(--muted)}}
.bezel b{{font-family:'IBM Plex Sans',sans-serif;font-size:19px;font-weight:700;color:var(--ink)}}
.led{{width:9px;height:9px;border-radius:5px;background:var(--muted);display:inline-block;margin-right:8px}}
.wrap{{padding:40px 150px 90px 72px;display:flex;flex-direction:column;gap:36px}}
.h1{{margin:0;font-size:50px;font-weight:700;letter-spacing:-.02em;line-height:1.05}}
.lede{{margin:0;font-size:19px;line-height:1.55;color:var(--body);max-width:880px}}
.p{{margin:0;font-size:17px;line-height:1.6;color:var(--body)}}
.panel{{background:var(--surf);border:1px solid var(--line);border-radius:10px;padding:18px;display:flex;flex-direction:column;gap:12px;min-width:0}}
.ch{{display:flex;justify-content:space-between;align-items:center;font-family:{MONO};font-size:13.5px;color:var(--muted)}}
.ch b{{color:var(--acc);font-weight:600}}
.scr{{background-color:var(--scr);background-image:linear-gradient(var(--div) 1px,transparent 1px),linear-gradient(90deg,var(--div) 1px,transparent 1px),linear-gradient(var(--divs) 1px,transparent 1px),linear-gradient(90deg,var(--divs) 1px,transparent 1px);
  background-size:80px 80px,80px 80px,16px 16px,16px 16px;border-radius:6px;padding:14px;box-shadow:inset 0 0 0 1px var(--line),inset 0 0 40px rgba(0,0,0,.25)}}
.t-dark .scr polyline{{filter:drop-shadow(0 0 3px rgba(127,178,229,.9))}}
.meas{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);border-radius:8px;overflow:hidden}}
.meas div{{background:var(--raised);padding:10px 12px;display:flex;flex-direction:column;gap:2px;font-family:{MONO}}}
.meas span{{font-size:12.5px;color:var(--muted)}}.meas b{{font-size:21px;font-weight:600;color:var(--ink)}}
.knobs{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px}}
.knob{{display:flex;flex-direction:column;align-items:center;gap:6px;font-family:{MONO};font-size:12.5px;color:var(--muted);text-align:center}}
.knob b{{font-size:16px;color:var(--ink);font-weight:600}}
.sr{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}
.b-tick{{height:34px;display:flex;align-items:center;padding:0 250px 0 72px;font-family:{MONO};font-size:13px;white-space:nowrap;background:var(--scr);border-bottom:1px solid var(--line)}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-family:{MONO};font-size:14.5px}}
.b-tb th{{text-align:right;font-weight:500;font-size:12.5px;color:var(--muted);padding:8px 10px;border-bottom:1px solid var(--line)}}
.b-tb td{{text-align:right;padding:8px 10px;border-bottom:1px solid var(--grid);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb td b{{font-family:'IBM Plex Sans',sans-serif}}.b-tb tr.sel td{{background:var(--raised);color:var(--acc)}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc)}}.b-lab{{font-family:{MONO};font-size:12.5px;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0}}.b-form label:nth-child(1),.b-form label:nth-child(2){{grid-column:1/-1}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:5px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:40px;border-radius:6px;border:1px solid var(--line);background:var(--scr);color:var(--ink);font:500 15px {MONO};padding:0 10px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:40px;border-radius:6px;overflow:hidden;border:1px solid var(--line)}}.b-seg span{{display:flex;align-items:center;justify-content:center;font-family:{MONO};color:var(--muted)}}.b-seg span.on{{background:var(--acc);color:var(--on-acc)}}
.b-btn{{grid-column:1/-1;height:44px;border-radius:22px;border:0;background:var(--acc);color:var(--on-acc);font:700 16px 'IBM Plex Sans',sans-serif;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;padding:0 22px}}
.b-btn.sec{{background:transparent;color:var(--acc);border:1.5px solid var(--acc)}}
.b-greek{{background:var(--raised);padding:12px 14px;display:flex;flex-direction:column;gap:2px;font-family:{MONO}}}.b-greek b{{font-size:24px}}.b-greek .b-sub{{font-family:'IBM Plex Sans',sans-serif;font-size:13px}}
.b-num{{background:var(--raised);padding:14px 16px;display:flex;flex-direction:column;gap:4px;border-radius:8px}}.b-num b{{font-family:{MONO};font-size:34px;font-weight:600;color:var(--acc)}}.b-num span{{font-size:14px;line-height:1.4;color:var(--muted)}}
.b-eq{{display:flex;flex-direction:column;gap:6px;padding:14px 0;border-bottom:1px solid var(--grid)}}.b-eqn{{font-family:{MONO};font-size:20px;line-height:1.5;color:var(--acc)}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:14px}}.b-steps li{{display:grid;grid-template-columns:44px 1fr;gap:10px}}
.b-steps .b-n{{font-family:{MONO};font-size:15px;color:var(--acc);padding-top:2px}}.b-steps li>span{{display:flex;flex-direction:column;gap:4px}}.b-steps li>span>b{{font-size:17px}}.b-steps li>span>span{{font-size:15.5px;line-height:1.55;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.b-lin li{{background:var(--raised);border-radius:8px;padding:14px;display:flex;flex-direction:column;gap:4px}}
.b-lin .b-y{{font-family:{MONO};font-size:30px}}.b-lin li.now .b-y{{color:var(--acc)}}.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{color:var(--muted);font-size:14.5px}}
.b-list{{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:8px;font-size:16px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;border-radius:6px;display:flex;align-items:center;justify-content:center;cursor:pointer;background-color:var(--scr);background-image:linear-gradient(var(--div) 1px,transparent 1px),linear-gradient(90deg,var(--div) 1px,transparent 1px);background-size:80px 80px}}
.b-video figcaption{{margin-top:10px;font-size:14.5px;color:var(--muted)}}
.b-person{{background:var(--surf);border:1px solid var(--line);border-radius:10px;padding:16px;display:flex;flex-direction:column;gap:4px}}.b-person .b-ph{{height:130px;border-radius:6px;background:var(--scr);display:flex;align-items:center;justify-content:center;margin-bottom:8px}}
.b-person b{{font-size:18px}}.b-person>span:last-child{{font-family:{MONO};color:var(--muted);font-size:13px}}
.b-refs{{background:var(--surf);border:1px solid var(--line);border-radius:10px;padding:16px 18px}}.b-refs h2{{margin:0 0 8px;font-family:{MONO};font-size:14px;font-weight:600;color:var(--acc)}}
.b-refs ol{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}}.b-refs li{{display:grid;grid-template-columns:44px 1fr;font-size:15px;line-height:1.5}}.b-refs .b-rn{{font-family:{MONO};color:var(--acc)}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{font-family:{MONO};font-size:12.5px;padding:4px 9px;border-radius:5px;border:1px solid var(--line);color:var(--muted)}}.b-chip.on{{border-color:var(--acc);color:var(--acc)}}
.b-links{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px}}.b-links a{{display:flex;flex-direction:column;align-items:center;gap:8px;padding:14px 8px;border:1px solid var(--line);border-radius:10px;background:var(--surf);text-align:center}}
.b-links a>span{{display:flex;flex-direction:column;gap:2px}}.b-links b{{font-size:15px}}.b-links a>span>span{{color:var(--muted);font-size:12.5px;font-family:{MONO}}}
.ft{{padding:20px 150px 32px 72px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-family:{MONO};font-size:13px;color:var(--muted)}}
"""

INK = Ink(font=MONO, size=12, line_w=2.4, grid="transparent", axis="var(--div)", bar_radius=1)


def knob(sym, name, factor, val, lo, hi, size=76):
    t = (val - lo) / (hi - lo)
    a0, a1 = -225, 45
    ang = a0 + t * (a1 - a0)
    cx = cy = size / 2
    r = size / 2 - 7

    def pt(a, rr):
        return cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a))

    x0, y0 = pt(a0, r)
    x1, y1 = pt(ang, r)
    xe, ye = pt(a1, r)
    large = 1 if (ang - a0) > 180 else 0
    ix, iy = pt(ang, r - 12)
    fmt = f"{val:.4f}" if sym in ("v₀", "θ") else f"{val:.2f}"
    svg = (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" aria-hidden="true">'
           f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 1 1 {xe:.1f},{ye:.1f}" style="fill:none;stroke:var(--grid);stroke-width:5;stroke-linecap:round"></path>'
           f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f}" style="fill:none;stroke:var(--acc);stroke-width:5;stroke-linecap:round"></path>'
           f'<circle cx="{cx}" cy="{cy}" r="{r - 9}" style="fill:var(--raised);stroke:var(--line);stroke-width:1.5"></circle>'
           f'<line x1="{cx}" y1="{cy}" x2="{ix:.1f}" y2="{iy:.1f}" style="stroke:var(--ink);stroke-width:3;stroke-linecap:round"></line></svg>')
    return (f'<label class="knob">{svg}<b>{sym} {fmt}</b><span>{esc(name)}</span>'
            f'<input class="sr" type="range" min="{lo}" max="{hi}" step="0.001" value="{val}" aria-label="{factor} factor {esc(name)}"></label>')


def knobs(factor):
    return '<div class="knobs">' + "".join(knob(sym, name, f, v, lo, hi) for f, sym, name, v, lo, hi in X.SLIDERS if f == factor) + "</div>"


def bezel():
    return f'<header class="bezel"><b>DH-2009 volatility analyser</b><span><span class="led"></span>{esc(X.STATUS)}</span></header>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def screen(ch, title, chart, right=""):
    return f'<div class="panel"><div class="ch"><span><b>{ch}</b>  {esc(title)}</span><span>{right}</span></div><div class="scr">{chart}</div></div>'


def meas(items):
    return '<div class="meas">' + "".join(f"<div><span>{esc(k)}</span><b>{esc(v)}</b></div>" for k, v in items) + "</div>"


def title(h, p):
    return f'<div style="display:flex;flex-direction:column;gap:12px"><h1 class="h1">{esc(h)}</h1><p class="lede">{esc(p)}</p></div>'


def home():
    pts = X.D["smile_30d"]
    return f"""
{B.ticker()}
{bezel()}
<div class="wrap">
  {title(X.Q, X.A_SHORT + ' ' + X.A_LONG + ' ' + X.TWIST)}
  <div style="display:grid;grid-template-columns:1.5fr 1fr;gap:20px;align-items:start">
    <div style="display:flex;flex-direction:column;gap:12px">{screen('CH1', 'implied volatility by strike, 30 days', B.smile(INK, 720, 380), 'starting settings')}
      {meas([('peak, strike 80', f'{pts[0][1]:.2f}%'), ('at the money', f'{pts[4][1]:.2f}%'), ('strike 120', f'{pts[-1][1]:.2f}%'), ('flat reference', '20.00%')])}</div>
    <div style="display:flex;flex-direction:column;gap:20px">
      {screen('CH2', 'skew by time to expiry', B.skew(INK, 440, 250), 'vol points')}
      <div class="panel"><div class="ch"><span><b>FACTORS</b>  two clocks</span></div><p class="p" style="font-size:15.5px">{esc(X.TWO_CLOCKS)}</p>{meas([('slow κ', '0.50'), ('half-life', f'{X.HL["slow_years"]:.1f} y'), ('fast κ', '5.00'), ('half-life', f'{X.HL["fast_days"]:.0f} d')])}</div>
    </div>
  </div>
  <div class="panel" style="gap:16px"><div class="ch"><span><b>RESULT</b>  the finding</span><a class="b-model" href="Finding.dc.html">{X.CTA['finding']}</a></div>
    <div style="display:grid;grid-template-columns:1fr 1.25fr;gap:24px;align-items:center"><p class="p" style="font-size:19px;color:var(--ink)">{esc(X.FINDING_LINE)} {esc(X.FINDING_SUB)}</p><div class="scr">{B.bars(INK, 640, row_h=28, label_w=220, legend=False, compact=True, only=('kappa_s', 'kappa_f', 'sigma_s', 'rho_s', 'theta_s', 'v0_s', 'v0_f'))}</div></div>
    {meas([('recovery skill, simulated', '1.80'), ('surfaces with several fits', f'{X.SHARE * 100:.0f}%'), ('distance vs random', f'{X.RATIO:.1f}×'), ('vs one flat volatility', f'−{X.FLAT_BETTER * 100:.0f}% error')])}</div>
  {B.page_links('Main', 40)}
</div>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{bezel()}
<div class="wrap">
  {title('Market', X.MARKET_SUB)}
  <div style="display:grid;grid-template-columns:1.6fr 1fr;gap:20px;align-items:start">
    <div style="display:flex;flex-direction:column;gap:12px">{screen('CH1', 'RELIANCE, daily', B.rel_candles(INK, 740, 440, 10), '<span class="b-chip">1M</span> <span class="b-chip on">3M</span>')}
      {meas([(k, v) for k, v in B.rel_stats()[:4]])}{meas([('Prev close', B.rel_stats()[4][1]), ('Volume', B.rel_stats()[5][1]), ('Days', '62'), ('Source', 'NSE')])}</div>
    <div class="panel" style="padding:10px 6px"><div class="ch" style="padding:6px 10px"><span><b>LIST</b>  watchlist</span><span>close {X.LAST_DAY}</span></div>{B.watch_table(spark=(60, 20))}</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">{screen('CH2', 'NIFTY 50 close', B.nifty_line(INK, 540, 220))}{screen('CH3', 'NIFTY BANK close', B.nifty_line(INK, 540, 220, 'BANKNIFTY'))}</div>
</div>
{ft()}
"""


def model():
    K = X.K
    return f"""
{bezel()}
<div class="wrap">
  {title('The model', 'Price a listed option with Double Heston and set it against the market. ' + X.MODEL_EXPLAIN)}
  <div style="display:grid;grid-template-columns:360px 1fr;gap:20px;align-items:start">
    <div class="panel"><div class="ch"><span><b>INPUT</b>  contract</span></div>{B.pricing_form()}</div>
    <div style="display:flex;flex-direction:column;gap:12px">
      {meas([('market close', f'₹{inr(K["market"])}'), ('market IV', f'{K["market_iv"]:.2f}%'), ('Double Heston', f'₹{inr(K["dh"])}'), ('model IV', f'{K["dh_iv"]:.2f}%')])}
      {meas([('gap', f'+₹{inr(X.GAP)}'), ('Monte Carlo', f'₹{inr(K["mc"])}'), ('± standard error', f'{K["mc_se"]:.2f}'), ('days to expiry', str(K['dte']))])}
      {screen('CH1', 'smile, market (rings) against model (trace)', B.market_smile(INK, 820, 330, 50), X.EXPIRY)}
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div class="panel"><div class="ch"><span><b>SLOW</b>  factor 1</span><span class="dn">Feller fails</span></div>{knobs('slow')}</div>
    <div class="panel"><div class="ch"><span><b>FAST</b>  factor 2</span><span class="dn">Feller fails</span></div>{knobs('fast')}</div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center"><span class="b-sub" style="font-size:15px">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div>
  <div style="display:grid;grid-template-columns:1.3fr 1fr;gap:20px;align-items:start">
    <div class="panel" style="padding:10px 6px"><div class="ch" style="padding:6px 10px"><span><b>CHAIN</b>  around the money</span><span>NSE close</span></div>{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div>
    <div class="panel"><div class="ch"><span><b>GREEKS</b></span></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);border-radius:8px;overflow:hidden">{B.greeks()}</div><span class="b-sub" style="font-size:13.5px">{esc(X.MODEL_SOURCE)}</span></div>
  </div>
</div>
{ft()}
"""


def maths():
    return f"""
{bezel()}
<div class="wrap">
  {title('How it works', X.MATHS_INTRO)}
  <div style="display:grid;grid-template-columns:1.2fr 1fr;gap:20px;align-items:start">
    <div class="panel"><div class="ch"><span><b>EQN</b>  the model</span></div>{B.equations()}</div>
    <div class="panel"><div class="ch"><span><b>PROC</b>  step by step</span></div>{B.steps()}</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">{screen('CH1', 'the bend, 30 days', B.smile(INK, 540, 300))}{screen('CH2', 'skew by time to expiry', B.skew(INK, 540, 300))}</div>
  {B.lineage()}
</div>
{ft()}
"""


def finding():
    return f"""
{bezel()}
<div class="wrap">
  {title('The finding', X.FIND_HEAD + ' ' + X.FINDING_SUB)}
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start">
    <div class="panel"><div class="ch"><span><b>TEST 1</b>  {esc(X.PROOF1_HEAD.lower())}</span></div><p class="p">{esc(X.PROOF1)}</p>{meas([(c, n) for n, c in X.PROOF1_NUMS] + [('network, RMSE skill', f'{X.NET["mean_skill"]:.2f}')])}<span class="b-sub" style="font-size:14px;line-height:1.5">{esc(X.PROOF1_NET)}</span></div>
    <div class="panel"><div class="ch"><span><b>TEST 2</b>  {esc(X.PROOF2_HEAD.lower())}</span></div><p class="p">{esc(X.PROOF2)}</p>{meas([(c, n) for n, c in X.PROOF2_NUMS] + [('median fits per surface', '10 of 16')])}</div>
  </div>
  {screen('CH1', 'distance between equally good fits, 2,379 surfaces', B.hist(INK, 1170, 280))}
  <div style="display:grid;grid-template-columns:1.5fr 1fr;gap:20px;align-items:start">{screen('CH2', 'by setting', B.bars(INK, 700, label_w=230))}<div class="panel"><div class="ch"><span><b>NOTE</b></span></div><p class="p">{esc(X.PER_PARAM)}</p></div></div>
  <div class="panel"><div class="ch"><span><b>CH3</b>  one stock, day by day</span><span style="display:flex;gap:6px">{B.picks()}</span></div><p class="p">{esc(X.rel_line())}</p><div class="scr">{B.stock(INK, 1150)}</div></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div class="panel"><div class="ch"><span><b>TEST 3</b>  held-out dates</span></div>{meas([('network error', f'{X.G8["median_network_relative"] * 100:.1f}%'), ('best possible', f'{X.G8["median_best_fit_relative"] * 100:.1f}%'), ('gap', f'{X.G8["median_gap_pp"]:.1f} pts'), ('dates', '8')])}<p class="p" style="font-size:15.5px">{esc(X.HELDOUT)}</p></div>
    <div class="panel"><div class="ch"><span><b>TEST 4</b>  option backtest</span></div>{meas([('stocks', '210'), ('days', '60'), ('network wins', '0'), ('flat wins', '210')])}<p class="p" style="font-size:15.5px">{esc(X.BACKTEST)}</p></div>
  </div>
</div>
{ft()}
"""


def about():
    return f"""
{bezel()}
<div class="wrap">
  {title('About', X.ABOUT_HEAD)}
  <div style="display:grid;grid-template-columns:1.6fr 1fr;gap:20px;align-items:start">
    <div class="panel"><div class="ch"><span><b>VIDEO</b>  explainer</span></div>{B.video()}</div>
    <div class="panel"><div class="ch"><span><b>METHOD</b>  and data</span></div>{''.join(f'<p class="p" style="font-size:15.5px">{esc(m)}</p>' for m in X.METHOD)}</div>
  </div>
  <div style="display:grid;grid-template-columns:1.3fr 1fr;gap:20px;align-items:start">
    <div class="panel"><div class="ch"><span><b>LIMITS</b></span></div>{B.bullet_list(X.LIMITS)}</div>
    <div class="panel"><div class="ch"><span><b>ALSO</b>  explored</span></div><p class="p">{esc(X.ALSO)}</p><a class="b-model" style="font-family:'IBM Plex Mono',monospace;font-size:13.5px" href="https://{X.REPO}">{esc(X.REPO)}</a></div>
  </div>
</div>
{ft()}
"""


def team():
    return f"""
{bezel()}
<div class="wrap">
  {title(X.TEAM_HEAD, X.TEAM_INTRO)}
  <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px">{B.team_cards()}</div>
  <div style="display:grid;grid-template-columns:1fr 1.3fr;gap:20px;align-items:start">
    <div class="panel"><div class="ch"><span><b>SUPERVISOR</b></span></div><b style="font-size:19px">{esc(X.SUPERVISOR[0])}</b><span class="b-sub">{esc(X.SUPERVISOR[1])}</span></div>
    <div class="panel"><div class="ch"><span><b>THANKS</b></span></div>{B.bullet_list(X.THANKS)}</div>
  </div>
</div>
{ft()}
"""


def references():
    return f"""
{bezel()}
<div class="wrap">
  {title('References', 'The papers behind the model and its methods, and where the data comes from.')}
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start">{B.refs()}</div>
</div>
{ft()}
"""


DESIGN = Design(
    num=9, slug="oscilloscope", name="Oscilloscope",
    concept="A lab instrument: scope screens with division grids and phosphor traces, rotary knobs for the ten settings.",
    memorable="The ten settings as rotary knobs, and every chart on a glowing scope screen with channel labels.",
    layout="Instrument panels in a grid: scope screens left, controls and measurement strips right; mono readouts.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;700&display=swap",
    display_font="'IBM Plex Sans',sans-serif", body_font="'IBM Plex Sans',Helvetica,sans-serif",
    type_sample="CH1  σ(K) = 26.21% @ 80",
    type_note="IBM Plex Sans 400–700 for text and titles; IBM Plex Mono for channel labels, readouts and chart axes.",
    ink=INK, css=CSS, rail_side="r", default_dark=True,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
