"""12 · Two Clocks — the slow and fast factors as two dials; the finding: the market can't read the clocks."""
from __future__ import annotations

import blocks as B
import charts2 as C2
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

DARK = dict(bg="#0B1024", surf="#121A36", raised="#1A2346", line="#28335C", grid="#18213F", ink="#E8ECFA",
            body="#C0C8E4", muted="#8F99BE", acc="#FF6B6B", on_acc="#0B1024", up="#3DDC97", down="#FF4D6D",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")
LIGHT = dict(bg="#EDEFF7", surf="#FFFFFF", raised="#E1E5F2", line="#C5CCE2", grid="#DDE2F0", ink="#141B34",
             body="#34405E", muted="#55607D", acc="#D1343F", on_acc="#FFFFFF", up="#1B7F4D", down="#B0123A",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")

U = "Unbounded,sans-serif"
K = "Karla,Helvetica,sans-serif"
CSS = f"""
.top{{height:62px;display:flex;align-items:center;gap:22px;padding:0 250px 0 120px;font-size:15px;color:var(--muted)}}
.top b{{font-family:{U};font-weight:700;font-size:17px;color:var(--ink)}}
.pg{{padding:40px 90px 110px 120px;display:flex;flex-direction:column;gap:90px}}
.h1{{margin:0;font-family:{U};font-weight:700;font-size:58px;line-height:1.06;letter-spacing:-.02em}}
.h2{{margin:0;font-family:{U};font-weight:600;font-size:34px;line-height:1.12;letter-spacing:-.01em}}
.kick{{font-family:{U};font-size:14px;font-weight:500;color:var(--acc);letter-spacing:.02em}}
.lede{{margin:0;font-size:21px;line-height:1.55;color:var(--body);max-width:820px}}
.p{{margin:0;font-size:18px;line-height:1.6;color:var(--body)}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:start}}
.dials{{display:grid;grid-template-columns:1fr 1fr;gap:36px}}
.dial{{display:flex;flex-direction:column;align-items:center;gap:12px;text-align:center}}
.dial b{{font-family:{U};font-size:22px}}.dial span{{color:var(--muted);font-size:16px}}
.card{{background:var(--surf);border-radius:22px;padding:28px;display:flex;flex-direction:column;gap:16px;min-width:0}}
.big{{font-family:{U};font-weight:700;font-size:64px;letter-spacing:-.03em;line-height:1}}
.b-tick{{height:36px;display:flex;align-items:center;padding:0 250px 0 120px;font-size:14px;white-space:nowrap;background:var(--surf)}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-size:16px}}
.b-tb th{{text-align:right;font-weight:700;font-size:13.5px;color:var(--muted);padding:10px 12px;border-bottom:1px solid var(--line)}}
.b-tb td{{text-align:right;padding:10px 12px;border-bottom:1px solid var(--grid);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb tr.sel td{{background:var(--raised);font-weight:700}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc);font-weight:700}}.b-lab{{font-size:13.5px;font-weight:700;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:50px;border-radius:25px;border:1.5px solid var(--line);background:var(--surf);color:var(--ink);font:500 17px {K};padding:0 18px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:50px;border-radius:25px;border:1.5px solid var(--line);overflow:hidden}}.b-seg span{{display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--muted)}}.b-seg span.on{{background:var(--acc);color:var(--on-acc)}}
.b-btn{{height:50px;padding:0 26px;border-radius:25px;border:0;background:var(--acc);color:var(--on-acc);font:700 17px {K};cursor:pointer;display:inline-flex;align-items:center}}.b-btn.sec{{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}}
.b-sl{{display:grid;grid-template-columns:34px 1fr 78px;gap:14px;align-items:center;padding:11px 0;border-bottom:1px solid var(--grid)}}
.b-sl b{{font-family:{U};font-size:18px;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:5px;font-size:15px;color:var(--muted)}}.b-sl input{{width:100%;accent-color:#FF6B6B}}.b-sl output{{text-align:right;font-weight:700;font-size:17px}}
.b-greek{{background:var(--surf);border-radius:18px;padding:18px;display:flex;flex-direction:column;gap:4px}}.b-greek b{{font-family:{U};font-size:28px}}
.b-num{{display:flex;flex-direction:column;gap:8px}}.b-num b{{font-family:{U};font-size:48px;font-weight:700;color:var(--acc);letter-spacing:-.02em;line-height:1}}.b-num span{{font-size:16px;line-height:1.45;color:var(--body)}}
.b-eq{{display:flex;flex-direction:column;gap:8px;padding:18px 0;border-bottom:1px solid var(--grid)}}.b-eqn{{font-family:{U};font-size:22px;font-weight:500;line-height:1.5}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:20px}}.b-steps li{{display:grid;grid-template-columns:56px 1fr;gap:12px}}
.b-steps .b-n{{width:44px;height:44px;border-radius:22px;border:2px solid var(--acc);color:var(--acc);display:flex;align-items:center;justify-content:center;font-family:{U};font-size:17px}}
.b-steps li>span{{display:flex;flex-direction:column;gap:5px}}.b-steps li>span>b{{font-size:18px}}.b-steps li>span>span{{font-size:16.5px;line-height:1.55;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}}.b-lin li{{display:flex;flex-direction:column;gap:6px;padding-top:16px;border-top:3px solid var(--line)}}.b-lin li.now{{border-top-color:var(--acc)}}
.b-lin .b-y{{font-family:{U};font-size:44px}}.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{color:var(--muted)}}
.b-list{{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:10px;font-size:17.5px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;border-radius:22px;background:var(--surf);display:flex;align-items:center;justify-content:center;cursor:pointer}}.b-video figcaption{{margin-top:12px;font-size:15px;color:var(--muted)}}
.b-person{{background:var(--surf);border-radius:22px;padding:24px;display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center}}.b-person .b-ph{{width:120px;height:120px;border-radius:60px;background:var(--raised);display:flex;align-items:center;justify-content:center;margin-bottom:8px}}
.b-person b{{font-family:{U};font-size:18px}}.b-person>span:last-child{{color:var(--muted);font-size:15px}}
.b-refs h2{{margin:0 0 10px;font-family:{U};font-size:22px}}.b-refs ol{{list-style:none;margin:0 0 30px;padding:0}}.b-refs li{{display:grid;grid-template-columns:48px 1fr;padding:12px 0;border-bottom:1px solid var(--grid);font-size:16.5px;line-height:1.5}}
.b-refs .b-rn{{font-family:{U};font-size:14px;color:var(--acc);padding-top:3px}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{font-size:14px;font-weight:700;padding:7px 14px;border-radius:17px;border:1.5px solid var(--line)}}.b-chip.on{{background:var(--acc);border-color:var(--acc);color:var(--on-acc)}}
.b-links{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px}}.b-links a{{display:flex;align-items:center;gap:14px;background:var(--surf);border-radius:18px;padding:16px}}.b-links a>span{{display:flex;flex-direction:column}}.b-links b{{font-size:17px}}.b-links a>span>span{{color:var(--muted);font-size:14px}}
.ft{{padding:24px 90px 36px 120px;display:flex;justify-content:space-between;font-size:14px;color:var(--muted);border-top:1px solid var(--line)}}
"""

INK = Ink(font=K, size=13.5, line_w=3.4, grid="var(--grid)", axis="var(--line)", bar_radius=4)


def top():
    return f'<header class="top"><b>two clocks</b><span>{esc(X.STATUS)}</span></header>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def head(kick, h, lede=None):
    l = f'<p class="lede">{esc(lede)}</p>' if lede else ""
    return f'<section style="display:flex;flex-direction:column;gap:18px"><span class="kick">{esc(kick)}</span><h1 class="h1">{esc(h)}</h1>{l}</section>'


def dials(size=300):
    return (f'<div class="dials"><div class="dial">{C2.clock(INK, size, X.HL["slow_years"], "Slow factor", "var(--ink)")}'
            f'<b>Slow, κ 0.5</b><span>half a shock gone in {X.HL["slow_years"]:.1f} years</span></div>'
            f'<div class="dial">{C2.clock(INK, size, X.HL["fast_days"] / 365, "Fast factor", "var(--acc)")}'
            f'<b>Fast, κ 5.0</b><span>half a shock gone in {X.HL["fast_days"]:.0f} days</span></div></div>')


def home():
    return f"""
{B.ticker()}
{top()}
<div class="pg">
  <section class="two" style="align-items:center">
    <div style="display:flex;flex-direction:column;gap:22px"><span class="kick">Double Heston</span><h1 class="h1">Two clocks run inside every option price.</h1><p class="lede">{esc(X.A_SHORT)} {esc(X.A_LONG)}</p>
      <span style="display:flex;gap:12px"><a class="b-btn" href="Model.dc.html">{X.CTA['model']}</a><a class="b-btn sec" href="Finding.dc.html">{X.CTA['finding']}</a></span></div>
    {dials(280)}
  </section>
  <section style="display:flex;flex-direction:column;gap:18px"><h2 class="h2">How fast each clock forgets a shock</h2><p class="p" style="max-width:820px">{esc(X.TWO_CLOCKS)} Each dial runs for two years; its hand points at the factor's half-life.</p>{C2.decay(INK, 1200, 360)}</section>
  <section class="two"><div class="card"><h2 class="h2">The bend they make</h2>{B.smile(INK, 560, 330)}<span class="b-sub">{esc(X.SMILE_CAPTION)}</span></div>
    <div class="card"><h2 class="h2">The market can’t read the clocks</h2><p class="p">{esc(X.FINDING_LINE)} The settings the prices pin down least are exactly the two clock speeds.</p>{B.bars(INK, 560, row_h=27, label_w=210, legend=False, compact=True, only=('kappa_s', 'kappa_f', 'v0_s', 'v0_f'))}<span class="b-sub" style="font-size:14px">Bars: equally good fits. Ticks: two random parameter sets.</span><a class="b-model" href="Finding.dc.html">{X.CTA['finding']}</a></div></section>
  {B.page_links('Main', 44, fill='var(--raised)')}
</div>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{top()}
<div class="pg">
  {head('Market', 'Sixty-two days of real prices', X.MARKET_SUB)}
  <section class="card"><div style="display:flex;justify-content:space-between;align-items:baseline"><span style="display:flex;align-items:baseline;gap:16px"><b class="h2">RELIANCE</b><span class="big" style="font-size:48px">{inr(r[4])}</span><span style="font-weight:700;font-size:18px">{B.rel_change()}</span></span><span style="display:flex;gap:8px"><span class="b-chip">1M</span><span class="b-chip on">3M</span><span class="b-chip">Line</span><span class="b-chip on">Candles</span></span></div>
    {B.rel_candles(INK, 1170, 470, 8)}<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:16px">{''.join(f'<div class="b-num"><span>{k}</span><b style="font-size:22px;color:var(--ink)">{v}</b></div>' for k, v in B.rel_stats())}</div></section>
  <section class="two"><div class="card"><h2 class="h2">Watchlist</h2>{B.watch_table(spark=(72, 24))}</div><div class="card"><h2 class="h2">NIFTY 50</h2>{B.nifty_line(INK, 560, 260)}<p class="p">{esc(X.UNIVERSE)}</p></div></section>
</div>
{ft()}
"""


def model():
    K_ = X.K
    return f"""
{top()}
<div class="pg">
  {head('The model', 'Set the two clocks, price the option', 'Pick a listed option and price it with Double Heston, then compare it with what the market paid.')}
  <section class="card">{B.pricing_form()}</section>
  <section style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px">{B.nums([(f'₹{inr(K_["market"])}', f'market close, {X.CONTRACT}, IV {K_["market_iv"]:.2f}%'), (f'₹{inr(K_["dh"])}', f'Double Heston, IV {K_["dh_iv"]:.2f}%. {X.MC_LINE}'), (f'+₹{inr(X.GAP)}', 'model minus market')])}</section>
  <p class="lede">{esc(X.MODEL_EXPLAIN)}</p>
  <section class="two">
    <div class="card"><div style="display:flex;align-items:center;gap:18px">{C2.clock(INK, 110, X.HL["slow_years"], "Slow factor", "var(--ink)")}<span><h2 class="h2" style="font-size:26px">Slow clock</h2><span class="dn" style="font-size:14.5px">{esc(X.FELLER['slow'])}</span></span></div>{B.sliders('slow')}</div>
    <div class="card"><div style="display:flex;align-items:center;gap:18px">{C2.clock(INK, 110, X.HL["fast_days"] / 365, "Fast factor", "var(--acc)")}<span><h2 class="h2" style="font-size:26px">Fast clock</h2><span class="dn" style="font-size:14.5px">{esc(X.FELLER['fast'])}</span></span></div>{B.sliders('fast')}</div>
  </section>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:-50px"><span class="b-sub">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div>
  <section class="two"><div class="card"><h2 class="h2">Smile, market against model</h2>{B.market_smile(INK, 560, 340, 50)}</div><div class="card"><h2 class="h2">Option chain</h2>{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div></section>
  <section style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:18px">{B.greeks()}</section>
  <span class="b-sub" style="font-size:14px">{esc(X.MODEL_SOURCE)}</span>
</div>
{ft()}
"""


def maths():
    return f"""
{top()}
<div class="pg">
  {head('How it works', 'Where the clocks live in the equations', X.MATHS_INTRO)}
  <section class="two"><div>{B.equations()}</div><div class="card"><h2 class="h2">Half-life</h2><div class="b-eqn" style="font-family:Unbounded,sans-serif;font-size:30px">t½ = ln 2 / κ</div><p class="p">κ is the clock speed in the variance equation. A shock to a factor decays like e^(−κt), so half of it is gone after ln 2 / κ years: {X.HL['slow_years']:.2f} years for κ 0.5 and {X.HL['fast_days']:.0f} days for κ 5.0.</p>{dials(200)}</div></section>
  <section style="display:flex;flex-direction:column;gap:18px"><h2 class="h2">Shock remaining over time</h2>{C2.decay(INK, 1200, 330)}</section>
  <section class="two">{B.steps()}<div class="card"><h2 class="h2">Skew by time to expiry</h2>{B.skew(INK, 560, 300)}<span class="b-sub">The fast clock shapes short-dated options; the slow one holds up the long end.</span></div></section>
  {B.lineage()}
</div>
{ft()}
"""


def finding():
    return f"""
{top()}
<div class="pg">
  {head('The finding', 'The prices can’t read the clocks', X.FIND_HEAD)}
  <section class="two"><div style="display:flex;flex-direction:column;gap:16px"><h2 class="h2">{esc(X.PROOF1_HEAD)}</h2><p class="p">{esc(X.PROOF1)}</p><p class="b-sub" style="margin:0;font-size:15.5px;line-height:1.55">{esc(X.PROOF1_NET)}</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:28px">{B.nums(X.PROOF1_NUMS)}</div></section>
  <section class="two"><div style="display:flex;flex-direction:column;gap:16px"><h2 class="h2">{esc(X.PROOF2_HEAD)}</h2><p class="p">{esc(X.PROOF2)}</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:28px">{B.nums(X.PROOF2_NUMS)}</div></section>
  <section class="card">{B.hist(INK, 1170, 290)}</section>
  <section class="two"><div class="card"><h2 class="h2">By setting</h2>{B.bars(INK, 560, label_w=200)}</div><div style="display:flex;flex-direction:column;gap:18px;justify-content:center"><p class="p" style="font-size:20px;color:var(--ink)">The two longest bars are the clock speeds.</p><p class="p">{esc(X.PER_PARAM)}</p></div></section>
  <section class="card"><div style="display:flex;justify-content:space-between;align-items:center"><h2 class="h2">One stock, day by day</h2><span style="display:flex;gap:6px">{B.picks()}</span></div><p class="p">{esc(X.rel_line())}</p>{B.stock(INK, 1170)}</section>
  <section class="two">{B.nums([(f'{X.G8["median_network_relative"] * 100:.1f}%', X.HELDOUT), ('0 of 210', X.BACKTEST)])}</section>
</div>
{ft()}
"""


def about():
    return f"""
{top()}
<div class="pg">
  {head('About', X.ABOUT_HEAD)}
  <section class="two">{B.video()}<div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Method and data</h2>{''.join(f'<p class="p">{esc(m)}</p>' for m in X.METHOD)}</div></section>
  <section class="two"><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Limits</h2>{B.bullet_list(X.LIMITS)}</div><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Also explored</h2><p class="p">{esc(X.ALSO)}</p><a class="b-model" href="https://{X.REPO}">{esc(X.REPO)}</a></div></section>
</div>
{ft()}
"""


def team():
    return f"""
{top()}
<div class="pg">
  {head('Team', X.TEAM_HEAD, X.TEAM_INTRO)}
  <section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:22px">{B.team_cards()}</section>
  <section class="two"><div class="card"><span class="kick">Supervisor</span><h2 class="h2">{esc(X.SUPERVISOR[0])}</h2><span class="b-sub">{esc(X.SUPERVISOR[1])}</span></div><div class="card"><span class="kick">Thanks</span>{B.bullet_list(X.THANKS)}</div></section>
</div>
{ft()}
"""


def references():
    return f"""
{top()}
<div class="pg">
  {head('References', 'Sources', 'The papers behind the model and its methods, and where the data comes from.')}
  <section class="two">{B.refs()}</section>
</div>
{ft()}
"""


DESIGN = Design(
    num=12, slug="two-clocks", name="Two Clocks",
    concept="The slow and fast factors as two dials; the finding told as 'the market can’t read the clocks'.",
    memorable="Two dials, each a two-year clock with its hand on the factor's half-life (1.4 years, 51 days).",
    layout="Two-column spreads around dials and a shock-decay chart; rounded panels; Unbounded headlines.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Unbounded:wght@400;500;600;700&family=Karla:wght@400;500;700&display=swap",
    display_font=U, body_font=K,
    type_sample="t½ = ln 2 / κ",
    type_note="Unbounded 500–700 for headlines, numbers and dial labels; Karla 400–700 for text, tables and charts.",
    ink=INK, css=CSS, rail_side="l", default_dark=True,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}, "fast": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
