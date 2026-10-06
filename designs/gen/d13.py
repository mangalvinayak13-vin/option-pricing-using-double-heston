"""13 · Brownian — randomness as the visual language: a full-bleed fan of real simulated paths."""
from __future__ import annotations

import blocks as B
import charts2 as C2
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#FFFFFF", surf="#F6F4F7", raised="#ECE8EE", line="#D6D0DA", grid="#EEEAF0", ink="#121212",
             body="#333036", muted="#5D5761", acc="#B8166F", on_acc="#FFFFFF", up="#15803D", down="#C81E1E",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#0D0B14", surf="#16131F", raised="#1F1B2B", line="#2E2940", grid="#1C1827", ink="#EDEBF5",
            body="#C8C4D6", muted="#9690AA", acc="#FF5CB8", on_acc="#0D0B14", up="#3DDC97", down="#FF5A5A",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

S = "Syne,sans-serif"
W = "'Work Sans',Helvetica,sans-serif"
CSS = f"""
.top{{height:60px;display:flex;align-items:center;gap:24px;padding:0 250px 0 64px;font-size:15px;color:var(--muted)}}
.top b{{font-family:{S};font-weight:800;font-size:20px;color:var(--ink)}}
.herofan{{position:relative;padding:0 110px 0 20px}}
.over{{position:absolute;left:64px;top:26px;max-width:640px;display:flex;flex-direction:column;gap:14px;padding:22px 26px;background:var(--bg);box-shadow:0 0 0 1px var(--line)}}
.pg{{padding:56px 150px 110px 64px;display:flex;flex-direction:column;gap:96px}}
.h1{{margin:0;font-family:{S};font-weight:800;font-size:64px;line-height:1;letter-spacing:-.02em}}
.h2{{margin:0;font-family:{S};font-weight:700;font-size:36px;line-height:1.08}}
.lede{{margin:0;font-size:20px;line-height:1.55;color:var(--body);max-width:820px}}
.p{{margin:0;font-size:18px;line-height:1.6;color:var(--body)}}
.sp{{display:grid;grid-template-columns:5fr 7fr;gap:56px;align-items:start}}
.sp.r{{grid-template-columns:7fr 5fr}}
.note{{font-size:15px;line-height:1.5;color:var(--muted)}}
.b-tick{{height:36px;display:flex;align-items:center;padding:0 250px 0 64px;font-size:14px;white-space:nowrap;border-bottom:1px solid var(--line)}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-size:16px}}
.b-tb th{{text-align:right;font-weight:600;font-size:13.5px;color:var(--muted);padding:10px;border-bottom:2px solid var(--ink)}}
.b-tb td{{text-align:right;padding:10px;border-bottom:1px solid var(--grid);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb tr.sel td{{color:var(--acc);font-weight:700}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc);font-weight:700}}.b-lab{{font-size:13.5px;font-weight:600;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:50px;border:0;border-bottom:2px solid var(--ink);background:transparent;color:var(--ink);font:500 18px {W};padding:0 4px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:50px;border:2px solid var(--ink)}}.b-seg span{{display:flex;align-items:center;justify-content:center;font-weight:700}}.b-seg span.on{{background:var(--acc);color:var(--on-acc)}}
.b-btn{{height:52px;padding:0 26px;border:0;background:var(--acc);color:var(--on-acc);font:700 17px {W};cursor:pointer;display:inline-flex;align-items:center}}.b-btn.sec{{background:transparent;color:var(--ink);border:2px solid var(--ink)}}
.b-sl{{display:grid;grid-template-columns:34px 1fr 78px;gap:14px;align-items:center;padding:11px 0;border-bottom:1px solid var(--grid)}}
.b-sl b{{font-family:{S};font-size:20px;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:5px;font-size:15px;color:var(--muted)}}.b-sl input{{width:100%;accent-color:#B8166F}}.b-sl output{{text-align:right;font-weight:700;font-size:17px}}
.b-greek{{display:flex;flex-direction:column;gap:4px}}.b-greek b{{font-family:{S};font-size:34px;font-weight:700}}
.b-num{{display:flex;flex-direction:column;gap:6px}}.b-num b{{font-family:{S};font-size:56px;font-weight:800;color:var(--acc);letter-spacing:-.02em;line-height:1}}.b-num span{{font-size:16px;line-height:1.45;color:var(--body)}}
.b-eq{{display:flex;flex-direction:column;gap:6px;padding:16px 0;border-bottom:1px solid var(--grid)}}.b-eqn{{font-size:24px;font-weight:500;line-height:1.45}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:22px}}.b-steps li{{display:grid;grid-template-columns:50px 1fr;gap:12px}}
.b-steps .b-n{{font-family:{S};font-size:36px;font-weight:800;color:var(--acc);line-height:1}}.b-steps li>span{{display:flex;flex-direction:column;gap:5px}}.b-steps li>span>b{{font-size:18px}}.b-steps li>span>span{{font-size:16.5px;line-height:1.55;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:30px}}.b-lin li{{display:flex;flex-direction:column;gap:6px}}.b-lin .b-y{{font-family:{S};font-size:54px;font-weight:800}}.b-lin li.now .b-y{{color:var(--acc)}}
.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{color:var(--muted)}}
.b-list{{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:10px;font-size:17.5px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;background:var(--surf);display:flex;align-items:center;justify-content:center;cursor:pointer}}.b-video figcaption{{margin-top:12px;font-size:15px;color:var(--muted)}}
.b-person{{display:flex;flex-direction:column;gap:6px}}.b-person .b-ph{{aspect-ratio:1/1;background:var(--surf);display:flex;align-items:center;justify-content:center;margin-bottom:10px}}.b-person b{{font-family:{S};font-size:22px;font-weight:700}}.b-person>span:last-child{{color:var(--muted);font-size:15px}}
.b-refs h2{{margin:0 0 10px;font-family:{S};font-size:24px;font-weight:700}}.b-refs ol{{list-style:none;margin:0 0 34px;padding:0}}.b-refs li{{display:grid;grid-template-columns:48px 1fr;padding:12px 0;border-bottom:1px solid var(--grid);font-size:16.5px;line-height:1.5}}
.b-refs .b-rn{{font-family:{S};color:var(--acc);font-weight:700}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{font-size:14px;font-weight:700;padding:6px 12px;border:1.5px solid var(--line)}}.b-chip.on{{background:var(--ink);color:var(--bg);border-color:var(--ink)}}
.b-links{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:26px}}.b-links a{{display:flex;align-items:center;gap:14px}}.b-links a>span{{display:flex;flex-direction:column}}.b-links b{{font-size:17px}}.b-links a>span>span{{color:var(--muted);font-size:14px}}
.ft{{padding:24px 150px 36px 64px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-size:14px;color:var(--muted)}}
"""

INK = Ink(font=W, size=13.5, line_w=3, grid="var(--grid)", axis="var(--ink)", bar_radius=0)


def top():
    return f'<header class="top"><b>brownian</b><span>Double Heston. {esc(X.STATUS)}</span></header>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def head(h, lede=None):
    l = f'<p class="lede">{esc(lede)}</p>' if lede else ""
    return f'<section style="display:flex;flex-direction:column;gap:18px"><h1 class="h1">{esc(h)}</h1>{l}</section>'


FAN_NOTE = ("Every grey line is one possible year for a stock priced at 100 today, simulated by the project’s Monte Carlo "
            "engine at the model’s starting settings. The band holds the middle 50% and 90% of 400 paths.")


def home():
    return f"""
{B.ticker()}
{top()}
<div class="herofan">{C2.fan(INK, 1310, 600, 60)}<div class="over"><h1 class="h1" style="font-size:54px">Volatility is a random walk too.</h1><p class="p">{esc(X.A_SHORT)} {esc(X.A_LONG)}</p>
  <span style="display:flex;gap:12px"><a class="b-btn" href="Model.dc.html">{X.CTA['model']}</a><a class="b-btn sec" href="Finding.dc.html">{X.CTA['finding']}</a></span></div></div>
<div class="pg">
  <p class="note" style="margin:-60px 0 0;max-width:900px">{esc(FAN_NOTE)}</p>
  <section class="sp"><div style="display:flex;flex-direction:column;gap:18px"><h2 class="h2">Two random volatilities, not one</h2><p class="p">{esc(X.TWO_CLOCKS)}</p>
    <div style="display:flex;gap:28px">{B.nums([(f'{X.HL["slow_years"]:.1f} yr', 'half-life of the slow factor, κ 0.5'), (f'{X.HL["fast_days"]:.0f} d', 'half-life of the fast factor, κ 5.0')])}</div></div>
    <figure style="margin:0;display:flex;flex-direction:column;gap:8px">{B.smile(INK, 720, 380)}<figcaption class="note">{esc(X.SMILE_CAPTION)}</figcaption></figure></section>
  <section class="sp r"><figure style="margin:0">{B.hist(INK, 720, 300)}</figure><div style="display:flex;flex-direction:column;gap:18px"><h2 class="h2">The settings are random too, in a way</h2><p class="p">{esc(X.FINDING_LINE)} {esc(X.FINDING_SUB)}</p><a class="b-model" href="Finding.dc.html">{X.CTA['finding']}</a></div></section>
  {B.page_links('Main', 44, fill='var(--surf)')}
</div>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{top()}
<div class="pg">
  {head('Market: one path that actually happened', X.MARKET_SUB)}
  <section style="display:flex;flex-direction:column;gap:16px"><div style="display:flex;align-items:baseline;justify-content:space-between"><span style="display:flex;align-items:baseline;gap:16px"><b class="h2">RELIANCE</b><span class="h1" style="font-size:52px">{inr(r[4])}</span><span style="font-weight:700;font-size:18px">{B.rel_change()}</span></span><span style="display:flex;gap:6px"><span class="b-chip">1M</span><span class="b-chip on">3M</span><span class="b-chip">Line</span><span class="b-chip on">Candles</span></span></div>
  {B.rel_candles(INK, 1226, 480, 8)}<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:20px">{''.join(f'<div class="b-num"><span>{k}</span><b style="font-size:24px;color:var(--ink)">{v}</b></div>' for k, v in B.rel_stats())}</div></section>
  <section class="sp r"><div>{B.watch_table(names=True, spark=(80, 24))}</div><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">NIFTY 50</h2>{B.nifty_line(INK, 480, 240)}<p class="p">{esc(X.UNIVERSE)}</p></div></section>
</div>
{ft()}
"""


def model():
    K_ = X.K
    return f"""
{top()}
<div class="pg">
  {head('Price an option by averaging 20,000 futures', 'Pick a listed option. Double Heston prices it by formula; the simulator checks it by averaging the payoff over 20,000 simulated paths.')}
  {B.pricing_form()}
  <section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:26px">{B.nums([(f'₹{inr(K_["market"], 0)}', f'market close, IV {K_["market_iv"]:.2f}%'), (f'₹{inr(K_["dh"], 0)}', f'Double Heston formula, IV {K_["dh_iv"]:.2f}%'), (f'₹{inr(K_["mc"], 0)}', f'mean of 20,000 paths, ± {K_["mc_se"]:.2f}'), (f'+₹{inr(X.GAP, 0)}', 'model minus market')])}</section>
  <p class="lede">{esc(X.MODEL_EXPLAIN)}</p>
  <section class="sp r"><figure style="margin:0">{B.market_smile(INK, 720, 380, 52)}</figure><div>{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div></section>
  <section class="sp" style="grid-template-columns:1fr 1fr"><div><h2 class="h2" style="font-size:28px">Slow factor</h2><p class="dn" style="margin:6px 0 0">{esc(X.FELLER['slow'])}</p>{B.sliders('slow')}</div><div><h2 class="h2" style="font-size:28px">Fast factor</h2><p class="dn" style="margin:6px 0 0">{esc(X.FELLER['fast'])}</p>{B.sliders('fast')}</div></section>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:-60px"><span class="b-sub">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div>
  <section style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:24px">{B.greeks()}</section>
  <span class="note">{esc(X.MODEL_SOURCE)}</span>
</div>
{ft()}
"""


def maths():
    return f"""
{top()}
<div class="pg">
  {head('How it works', X.MATHS_INTRO)}
  <section class="sp"><div>{B.equations()}</div><div>{B.steps()}</div></section>
  <section style="display:flex;flex-direction:column;gap:12px"><h2 class="h2">What the equations produce: paths</h2>{C2.fan(INK, 1226, 460, 40)}<p class="note">{esc(FAN_NOTE)}</p></section>
  <section class="sp"><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">And averaged over paths: the skew</h2><p class="p">How steep the smile is, by time to expiry, at the starting settings.</p></div>{B.skew(INK, 720, 300)}</section>
  {B.lineage()}
</div>
{ft()}
"""


def finding():
    return f"""
{top()}
<div class="pg">
  {head(X.FIND_HEAD)}
  <section class="sp"><div style="display:flex;flex-direction:column;gap:16px"><h2 class="h2">{esc(X.PROOF1_HEAD)}</h2><p class="p">{esc(X.PROOF1)}</p><p class="note">{esc(X.PROOF1_NET)}</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:30px">{B.nums(X.PROOF1_NUMS)}</div></section>
  <section class="sp"><div style="display:flex;flex-direction:column;gap:16px"><h2 class="h2">{esc(X.PROOF2_HEAD)}</h2><p class="p">{esc(X.PROOF2)}</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:30px">{B.nums(X.PROOF2_NUMS)}</div></section>
  {B.hist(INK, 1226, 300)}
  <section class="sp r">{B.bars(INK, 720, label_w=240)}<p class="p">{esc(X.PER_PARAM)}</p></section>
  <section style="display:flex;flex-direction:column;gap:14px"><div style="display:flex;justify-content:space-between;align-items:center"><h2 class="h2">One stock, day by day</h2><span style="display:flex;gap:6px">{B.picks()}</span></div><p class="p">{esc(X.rel_line())}</p>{B.stock(INK, 1226)}</section>
  <section class="sp" style="grid-template-columns:1fr 1fr">{B.nums([(f'{X.G8["median_network_relative"] * 100:.1f}%', X.HELDOUT), ('0 of 210', X.BACKTEST)])}</section>
</div>
{ft()}
"""


def about():
    return f"""
{top()}
<div class="pg">
  {head(X.ABOUT_HEAD)}
  <section class="sp r">{B.video()}<div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Method and data</h2>{''.join(f'<p class="p">{esc(m)}</p>' for m in X.METHOD)}</div></section>
  <section class="sp"><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Limits</h2>{B.bullet_list(X.LIMITS)}</div><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Also explored</h2><p class="p">{esc(X.ALSO)}</p><a class="b-model" href="https://{X.REPO}">{esc(X.REPO)}</a></div></section>
</div>
{ft()}
"""


def team():
    return f"""
{top()}
<div class="pg">
  {head(X.TEAM_HEAD, X.TEAM_INTRO)}
  <section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:26px">{B.team_cards()}</section>
  <section class="sp"><div><span class="b-lab">Supervisor</span><h2 class="h2">{esc(X.SUPERVISOR[0])}</h2><p class="p">{esc(X.SUPERVISOR[1])}</p></div><div><span class="b-lab">Thanks</span>{B.bullet_list(X.THANKS)}</div></section>
</div>
{ft()}
"""


def references():
    return f"""
{top()}
<div class="pg">
  {head('References', 'The papers behind the model and its methods, and where the data comes from.')}
  <section class="sp" style="grid-template-columns:1fr 1fr">{B.refs()}</section>
</div>
{ft()}
"""


DESIGN = Design(
    num=13, slug="brownian", name="Brownian",
    concept="Randomness as the visual language: a full-bleed fan of real simulated paths, the Monte Carlo check up front.",
    memorable="The home page is 60 simulated one-year paths from the project's own simulator, with the headline laid over them.",
    layout="Full-bleed hero chart with an overlaid title box, then asymmetric 5/7 spreads that swap sides.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Work+Sans:wght@400;500;600;700&display=swap",
    display_font=S, body_font=W,
    type_sample="Volatility is a random walk too.",
    type_note="Syne 700–800 for headlines and figures; Work Sans 400–700 for text, tables and charts.",
    ink=INK, css=CSS, rail_side="r", default_dark=False,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
