"""06 · Long Read — an essay: a serif reading column, margin notes, figures that break out wide."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#FFFFFF", surf="#F7F6F4", raised="#EFEDEA", line="#DAD7D2", grid="#EEECE8", ink="#1A1A1A",
             body="#333333", muted="#66625C", acc="#9E1B32", on_acc="#FFFFFF", up="#1A7F4B", down="#B3261E",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#121412", surf="#1A1C1A", raised="#232623", line="#333733", grid="#232623", ink="#E6E8E3",
            body="#C6C9C3", muted="#9A9E97", acc="#FF6B81", on_acc="#121412", up="#3DD68C", down="#FF6B6B",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

SERIF = "Newsreader,Georgia,serif"
SANS = "'Public Sans',Helvetica,sans-serif"
CSS = f"""
.mast{{height:64px;display:flex;align-items:center;gap:28px;padding:0 250px 0 200px;border-bottom:1px solid var(--line);font-family:{SANS};font-size:15px;color:var(--muted)}}
.mast b{{font-family:{SERIF};font-size:22px;font-weight:600;font-style:italic;color:var(--ink)}}
.art{{padding:80px 0 120px 200px;display:flex;flex-direction:column}}
.kick{{font-family:{SANS};font-size:15px;font-weight:600;color:var(--acc)}}
.h1{{margin:14px 0 0;font-family:{SERIF};font-weight:600;font-size:68px;line-height:1.02;letter-spacing:-.02em;max-width:1000px}}
.dek{{margin:22px 0 0;font-family:{SERIF};font-style:italic;font-size:26px;line-height:1.4;color:var(--body);max-width:880px}}
.by{{margin:22px 0 48px;font-family:{SANS};font-size:15px;color:var(--muted)}}
.er{{display:grid;grid-template-columns:640px 300px;column-gap:72px;margin-top:30px}}
.et p{{margin:0 0 20px;font-family:{SERIF};font-size:21px;line-height:1.66;color:var(--body)}}
.et p:first-child::first-letter{{}}
.et h2{{margin:36px 0 16px;font-family:{SERIF};font-size:36px;font-weight:600;line-height:1.1;color:var(--ink)}}
.sn{{font-family:{SANS};font-size:15px;line-height:1.55;color:var(--muted);padding-top:6px;display:flex;flex-direction:column;gap:14px}}
.sn b{{color:var(--ink)}}
.fig{{margin:48px 0 8px;display:flex;flex-direction:column;gap:12px}}
.fig figcaption{{font-family:{SANS};font-size:15px;line-height:1.5;color:var(--muted);max-width:760px}}
.fig figcaption b{{color:var(--acc)}}
.pull{{margin:40px 0;font-family:{SERIF};font-style:italic;font-size:40px;line-height:1.2;color:var(--ink);max-width:960px}}
.b-tick{{height:36px;display:flex;align-items:center;padding:0 250px 0 200px;font-family:{SANS};font-size:14px;white-space:nowrap;border-bottom:1px solid var(--line)}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-family:{SANS};font-size:16px}}
.b-tb th{{text-align:right;font-weight:600;font-size:13px;color:var(--muted);padding:9px 12px;border-bottom:2px solid var(--ink)}}
.b-tb td{{text-align:right;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb tr.sel td{{font-weight:700;background:var(--surf)}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc);font-weight:600}}.b-lab{{font-family:{SANS};font-size:13px;font-weight:600;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0;font-family:{SANS};padding:22px 0;border-top:2px solid var(--ink);border-bottom:1px solid var(--line)}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:44px;border:1px solid var(--line);border-radius:3px;background:var(--bg);color:var(--ink);font:500 16px {SANS};padding:0 10px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:44px;border:1px solid var(--line);border-radius:3px;overflow:hidden}}
.b-seg span{{display:flex;align-items:center;justify-content:center;font-weight:600;color:var(--muted)}}.b-seg span.on{{background:var(--ink);color:var(--bg)}}
.b-btn{{height:44px;padding:0 20px;border-radius:3px;border:0;background:var(--acc);color:var(--on-acc);font:700 16px {SANS};cursor:pointer;display:inline-flex;align-items:center}}
.b-btn.sec{{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}}
.b-sl{{display:grid;grid-template-columns:30px 1fr 72px;gap:12px;align-items:center;padding:10px 0;border-bottom:1px solid var(--line);font-family:{SANS}}}
.b-sl b{{font-family:{SERIF};font-size:22px;font-style:italic;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:5px;font-size:14px;color:var(--muted)}}
.b-sl input{{width:100%;accent-color:#9E1B32}}.b-sl output{{text-align:right;font-weight:700;font-size:16px}}
.b-greek{{display:flex;flex-direction:column;gap:3px;font-family:{SANS}}}.b-greek b{{font-family:{SERIF};font-size:34px;font-weight:600}}
.b-num{{display:flex;flex-direction:column;gap:4px;font-family:{SANS}}}.b-num b{{font-family:{SERIF};font-size:44px;font-weight:600;color:var(--acc);line-height:1}}.b-num span{{font-size:14.5px;line-height:1.45;color:var(--muted)}}
.b-eq{{display:flex;flex-direction:column;gap:6px;margin:0 0 22px}}.b-eqn{{font-family:{SERIF};font-style:italic;font-size:28px;line-height:1.45;color:var(--ink);padding-left:22px;border-left:2px solid var(--acc)}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:18px}}.b-steps li{{display:grid;grid-template-columns:36px 1fr;gap:12px}}
.b-steps .b-n{{font-family:{SERIF};font-size:30px;font-style:italic;color:var(--acc);line-height:1}}.b-steps li>span{{display:flex;flex-direction:column;gap:4px}}
.b-steps li>span>b{{font-family:{SERIF};font-size:21px}}.b-steps li>span>span{{font-family:{SERIF};font-size:19px;line-height:1.6;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0 0 0 16px;border-left:2px solid var(--line);display:flex;flex-direction:column;gap:14px;font-family:{SANS}}}
.b-lin li{{display:flex;flex-direction:column;gap:2px}}.b-lin .b-y{{font-size:15px}}.b-lin li.now .b-y{{color:var(--acc)}}.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{color:var(--muted)}}
.b-list{{margin:0 0 20px;padding-left:26px;display:flex;flex-direction:column;gap:10px;font-family:{SERIF};font-size:20px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;background:var(--surf);display:flex;align-items:center;justify-content:center;cursor:pointer}}
.b-video figcaption{{margin-top:10px;font-family:{SANS};font-size:15px;color:var(--muted)}}
.b-person{{display:flex;flex-direction:column;gap:4px;padding-top:16px;border-top:2px solid var(--ink)}}.b-person .b-ph{{display:none}}
.b-person b{{font-family:{SERIF};font-size:26px;font-weight:600}}.b-person>span:last-child{{font-family:{SANS};color:var(--muted);font-size:15px}}
.b-refs h2{{margin:0 0 10px;font-family:{SERIF};font-size:28px;font-weight:600}}.b-refs ol{{list-style:none;margin:0 0 34px;padding:0;display:flex;flex-direction:column;gap:14px}}
.b-refs li{{display:grid;grid-template-columns:44px 1fr;font-family:{SERIF};font-size:19px;line-height:1.5}}.b-refs .b-rn{{font-family:{SANS};font-size:15px;color:var(--acc);padding-top:3px}}
.b-refs .b-rt{{font-style:italic;color:var(--body)}}.b-refs .b-sub{{font-family:{SANS};font-size:15px}}
.b-chip{{font-family:{SANS};font-size:14px;font-weight:600;padding:5px 12px;border:1px solid var(--line);border-radius:3px}}.b-chip.on{{background:var(--ink);color:var(--bg);border-color:var(--ink)}}
.b-links{{width:1012px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:26px;margin-top:80px;padding-top:26px;border-top:2px solid var(--ink)}}
.b-links a{{display:flex;align-items:center;gap:12px;font-family:{SANS}}}.b-links a>span{{display:flex;flex-direction:column}}.b-links b{{font-size:16px}}.b-links a>span>span{{color:var(--muted);font-size:14px}}
.ft{{padding:26px 250px 40px 200px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-family:{SANS};font-size:14px;color:var(--muted)}}
"""

INK = Ink(font=SANS, size=13, line_w=2.6, grid="var(--grid)", axis="var(--ink)", bar_radius=0)


def mast():
    return f'<header class="mast"><b>The Double Heston Review</b><span>{esc(X.STATUS)}</span></header>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def row(main, side=""):
    return f'<div class="er"><div class="et">{main}</div><aside class="sn">{side}</aside></div>'


def fig(n, chart, cap, width=1012):
    return f'<figure class="fig" style="width:{width}px">{chart}<figcaption><b>Figure {n}.</b> {esc(cap)}</figcaption></figure>'


def head(kick, h, dek=None):
    d = f'<p class="dek">{esc(dek)}</p>' if dek else ""
    return f'<span class="kick">{esc(kick)}</span><h1 class="h1">{esc(h)}</h1>{d}<p class="by">A B.Tech physics project on the Double Heston model. Prices: NSE, close of {X.LAST_DAY}.</p>'


def P(*paras):
    return "".join(f"<p>{esc(p)}</p>" for p in paras)


def home():
    n = X.w("NIFTY 50")
    K = X.K
    return f"""
{B.ticker()}
{mast()}
<article class="art">
  {head('Essay', 'What a moving volatility buys you, and what it costs.', X.A_SHORT + ' ' + X.TWIST)}
  {row(P('An option is a bet on how far a price might move, so its price depends on volatility. Black–Scholes treats volatility as one fixed number. Real option prices disagree: protection against a fall usually costs more than the same-sized bet on a rise.', 'Double Heston lets volatility move, and gives it two parts that move at different speeds. That is enough to bend prices the way the market does: on all 2,400 real NSE option surfaces we tested, its best fit beat one fixed volatility.'), B.lineage())}
  {fig(1, B.smile(INK, 1012, 440), X.SMILE_CAPTION)}
  {row(P(X.TWO_CLOCKS + f' The slow one loses half of any shock in {X.HL["slow_years"]:.1f} years; the fast one in about {X.HL["fast_days"] / 7:.0f} weeks.', f'You can try it on the market. The NIFTY {inr(K["strike"], 0)} call expiring {X.EXPIRY} closed at ₹{inr(K["market"])} on {X.LAST_DAY}. At its starting settings Double Heston says ₹{inr(K["dh"])}: it assumes 20% volatility where the market priced about {K["market_iv"]:.1f}%.'),
         f'<div style="display:flex;align-items:center;gap:12px">{squircle("slow", 44, fill="var(--surf)", ring=False)}<span><b>Slow factor</b><br>κ 0.5, half-life {X.HL["slow_years"]:.1f} years</span></div><div style="display:flex;align-items:center;gap:12px">{squircle("fast", 44, fill="var(--acc)", ink="var(--on-acc)", ring=False)}<span><b>Fast factor</b><br>κ 5.0, half-life {X.HL["fast_days"]:.0f} days</span></div><span><b>NIFTY 50</b> {inr(n["last"])} <span class="{arrow(n["pct"])[1]}">{arrow(n["pct"])[0]} {abs(n["pct"]):.2f}%</span><br>close, {X.LAST_DAY}</span>')}
  <p class="pull">“{esc(X.FINDING_LINE)}”</p>
  {row(P(X.FINDING_SUB, 'On simulated surfaces where the right answer was known, the fitted settings scored 1.80 on recovery, where always guessing the typical value scores 1.00. A near-perfect price fit is not the same as knowing the settings.'), f'<span>{esc(X.RATIO and "")}Equally good means within 10% of the best fit’s price error, from 16 starting points per surface.</span><a class="b-model" href="Finding.dc.html">{X.CTA["finding"]}</a>')}
  {fig(2, B.bars(INK, 1012), 'Median distance between equally good fits, setting by setting, against two parameter sets picked at random.')}
  {B.page_links('Main', 40, fill='var(--surf)')}
</article>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{mast()}
<article class="art">
  {head('Market', 'The prices behind the curves', X.MARKET_SUB)}
  {row(P(f'RELIANCE closed at ₹{inr(r[4])} on {X.LAST_DAY}. Figure 1 shows its last 62 trading days as daily candles: green when the day closed higher, red when it closed lower.'), '<span style="display:flex;gap:6px;flex-wrap:wrap"><span class="b-chip">1M</span><span class="b-chip on">3M</span><span class="b-chip">Line</span><span class="b-chip on">Candles</span></span>' + ''.join(f'<span><b>{k}</b> {v}</span>' for k, v in B.rel_stats()))}
  {fig(1, B.rel_candles(INK, 1012, 480, 8), 'RELIANCE, daily candlesticks from the official NSE files, 1 Jul to 25 Sep 2026, with volume.')}
  {row(P('Table 1 lists the stocks on the watchlist, with their last 62 days as a sparkline. ' + X.UNIVERSE), f'<span><b>Table 1</b> Close on {X.LAST_DAY} and the day’s change.</span>')}
  <div style="width:1012px;margin-top:16px">{B.watch_table(names=True, spark=(90, 26))}</div>
  {fig(2, B.nifty_line(INK, 1012, 260), 'NIFTY 50 closing level. Index levels are published as closes, so this is a line, not candles.')}
</article>
{ft()}
"""


def model():
    K = X.K
    return f"""
{mast()}
<article class="art">
  {head('The model', 'Pricing one option, in public', 'Pick a listed option, price it with Double Heston, and set it against what the market paid.')}
  <div style="width:1012px">{B.pricing_form()}</div>
  {row(P(f'The NIFTY {inr(K["strike"], 0)} call expiring {X.EXPIRY} closed at ₹{inr(K["market"])}. Double Heston, at its starting settings, prices it at ₹{inr(K["dh"])}, a gap of ₹{inr(X.GAP)}. A Monte Carlo simulation of 20,000 paths gives ₹{inr(K["mc"])} ± {K["mc_se"]:.2f}, so the formula and the simulation agree.', X.MODEL_EXPLAIN),
         ''.join(f'<div class="b-num"><b{" style=color:var(--ink)" if i != 1 else ""}>{v}</b><span>{c}</span></div>' for i, (v, c) in enumerate(((f'₹{inr(K["market"])}', f'market close, IV {K["market_iv"]:.2f}%'), (f'₹{inr(K["dh"])}', f'Double Heston, IV {K["dh_iv"]:.2f}%'), (f'+₹{inr(X.GAP)}', 'model minus market')))))}
  {fig(1, B.market_smile(INK, 1012, 400, 52), 'Implied volatility by strike, expiry ' + X.EXPIRY + '. Circles: the market, from NSE closing prices. Line: Double Heston at its starting settings.')}
  {row(P('Table 1 is the option chain around the money, with the model’s call price beside the market’s.'), f'<span>{esc(X.MODEL_SOURCE)}</span>')}
  <div style="width:1012px;margin-top:16px">{B.chain_table()}</div>
  {row('<h2>The ten settings</h2>' + P('Each factor has five settings. Both break the Feller condition at these values, so either variance can touch zero; the simulator’s full truncation keeps prices valid.'), f'<span class="dn">{esc(X.FELLER["slow"])}</span><span class="dn">{esc(X.FELLER["fast"])}</span>')}
  <div style="width:1012px;display:grid;grid-template-columns:1fr 1fr;gap:48px"><div>{B.sliders('slow')}</div><div>{B.sliders('fast')}</div></div>
  <div style="width:1012px;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:24px;margin-top:40px;padding-top:22px;border-top:2px solid var(--ink)">{B.greeks()}</div>
</article>
{ft()}
"""


def maths():
    return f"""
{mast()}
<article class="art">
  {head('How it works', 'Two variances and one integral', X.MATHS_INTRO)}
  {row(B.equations(), '<span>Notation: S is the price, vᵢ the variance of factor i, κ the speed back to normal, θ the long-run level, ξ the volatility of volatility, ρ the price–volatility link.</span>')}
  {row(B.steps(), '<span>The code prices with the characteristic function and checks every headline price by simulation.</span>')}
  {fig(1, B.smile(INK, 1012, 420), 'The bend at the starting settings, against one fixed volatility.')}
  {fig(2, B.skew(INK, 1012, 320), f'Skew by time to expiry, in volatility points. The fast factor (half-life about {X.HL["fast_days"] / 7:.0f} weeks) shapes short-dated options; the slow one ({X.HL["slow_years"]:.1f} years) holds up the long end.')}
</article>
{ft()}
"""


def finding():
    return f"""
{mast()}
<article class="art">
  {head('The finding', X.FIND_HEAD)}
  {row('<h2>' + esc(X.PROOF1_HEAD) + '</h2>' + P(X.PROOF1, X.PROOF1_NET), B.nums(X.PROOF1_NUMS))}
  {row('<h2>' + esc(X.PROOF2_HEAD) + '</h2>' + P(X.PROOF2), B.nums(X.PROOF2_NUMS))}
  {fig(1, B.hist(INK, 1012, 300), 'How far apart the equally good fits landed on each of the 2,379 surfaces that had more than one.')}
  {row(P(X.PER_PARAM))}
  {fig(2, B.bars(INK, 1012), 'The same distance, setting by setting.')}
  {row(P(X.rel_line()), '<span style="display:flex;gap:6px;flex-wrap:wrap">' + B.picks() + '</span>')}
  {fig(3, B.stock(INK, 1012), 'RELIANCE, 60 trading days: the best fit’s price error against a flat volatility, and how far apart the equally good fits landed.')}
  {row(P(X.HELDOUT, X.BACKTEST))}
</article>
{ft()}
"""


def about():
    return f"""
{mast()}
<article class="art">
  {head('About', X.ABOUT_HEAD)}
  <div style="width:1012px;margin-bottom:20px">{B.video()}</div>
  {row('<h2>Method and data</h2>' + P(*X.METHOD), f'<span>{esc(X.ALSO)}</span><a class="b-model" href="https://{X.REPO}">{esc(X.REPO)}</a>')}
  {row('<h2>Limits</h2>' + B.bullet_list(X.LIMITS))}
</article>
{ft()}
"""


def team():
    return f"""
{mast()}
<article class="art">
  {head('Team', X.TEAM_HEAD, X.TEAM_INTRO)}
  <div style="width:1012px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:28px">{B.team_cards(icon=False)}</div>
  {row('<h2>Supervisor</h2>' + P(X.SUPERVISOR[0] + ', ' + X.SUPERVISOR[1]) + '<h2>Thanks</h2>' + B.bullet_list(X.THANKS))}
</article>
{ft()}
"""


def references():
    return f"""
{mast()}
<article class="art">
  {head('References', 'Sources', 'The papers behind the model and its methods, and where the data comes from.')}
  <div style="width:880px">{B.refs()}</div>
</article>
{ft()}
"""


DESIGN = Design(
    num=6, slug="long-read", name="Long Read",
    concept="An essay: a serif reading column with margin notes; figures and tables break out wide; numbers live in sentences.",
    memorable="Live prices written into the prose, with margin notes carrying the definitions.",
    layout="640-px reading column plus a 300-px margin-note column; figures span both; one pull quote per page.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400;1,6..72,600&family=Public+Sans:wght@400;600;700&display=swap",
    display_font=SERIF, body_font=SERIF,
    type_sample="What a moving volatility buys you",
    type_note="Newsreader 400/600 (and italic) for headlines and text; Public Sans for notes, tables, forms and charts.",
    ink=INK, css=CSS, rail_side="l", default_dark=False,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}, "fast": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
