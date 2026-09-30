"""07 · Journal — the site typeset as a physics paper: abstract, numbered sections, equations, Fig. n."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#FAF8F3", surf="#FFFFFF", raised="#F1EDE4", line="#D6D0C2", grid="#ECE7DC", ink="#1F1D19",
             body="#34312B", muted="#5E5A52", acc="#2D3A87", on_acc="#FFFFFF", up="#1F7A45", down="#B23A2E",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#16151A", surf="#1D1C22", raised="#25242B", line="#35343C", grid="#24232A", ink="#ECE8DF",
            body="#CFCAC0", muted="#A39E94", acc="#9AA6FF", on_acc="#16151A", up="#4CC38A", down="#FF7A6B",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

SERIF = "'Source Serif 4',Georgia,serif"
CSS = f"""
.run{{height:52px;display:flex;align-items:center;justify-content:space-between;padding:0 250px 0 220px;border-bottom:1px solid var(--line);font-size:14px;font-style:italic;color:var(--muted)}}
.paper{{width:1000px;margin:0 auto;padding:64px 0 110px;display:flex;flex-direction:column;gap:30px;position:relative;left:-50px}}
.title{{margin:0;text-align:center;font-size:44px;font-weight:600;line-height:1.15;letter-spacing:-.01em}}
.auth{{text-align:center;font-size:18px;line-height:1.5;color:var(--body)}}.auth i{{color:var(--muted)}}
.abs{{margin:6px 60px 0;padding:20px 26px;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);font-size:17px;line-height:1.6;text-align:justify;hyphens:auto}}
.abs b{{font-variant:small-caps;letter-spacing:.04em}}
.cols{{column-count:2;column-gap:44px;font-size:17.5px;line-height:1.62;text-align:justify;hyphens:auto;color:var(--body)}}
.cols p{{margin:0 0 12px;text-indent:1.4em}}.cols p.ni{{text-indent:0}}
.sec{{margin:14px 0 8px;font-size:22px;font-weight:700;color:var(--ink)}}.sec span{{color:var(--acc);margin-right:10px}}
.eqr{{display:grid;grid-template-columns:1fr auto;align-items:center;margin:8px 0}}.eqr .eq{{text-align:center;font-size:22px;font-style:italic;color:var(--ink)}}.eqr .n{{font-size:17px;color:var(--muted)}}
.fig{{margin:8px 0;display:flex;flex-direction:column;gap:10px;align-items:center}}
.fig figcaption{{font-size:15.5px;line-height:1.5;color:var(--body);max-width:900px;text-align:justify}}.fig figcaption b{{color:var(--ink)}}
.b-tick{{height:34px;display:flex;align-items:center;padding:0 250px 0 220px;font-size:13.5px;white-space:nowrap;border-bottom:1px solid var(--line);font-variant-numeric:lining-nums}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:24px;overflow:hidden}}.b-ti{{display:inline-flex;gap:7px}}.b-ti-lab{{color:var(--muted);font-style:italic}}
.b-tb{{width:100%;border-collapse:collapse;font-size:15.5px;border-top:2px solid var(--ink);border-bottom:2px solid var(--ink)}}
.b-tb th{{text-align:right;font-weight:600;padding:8px 10px;border-bottom:1px solid var(--ink)}}
.b-tb td{{text-align:right;padding:7px 10px;white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb tr.sel td{{font-weight:700;color:var(--acc)}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc)}}.b-lab{{font-size:14px;font-style:italic;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0;padding:16px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:40px;border:1px solid var(--line);background:var(--surf);color:var(--ink);font:500 16px {SERIF};padding:0 10px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:40px;border:1px solid var(--line)}}.b-seg span{{display:flex;align-items:center;justify-content:center;color:var(--muted)}}.b-seg span.on{{background:var(--acc);color:var(--on-acc)}}
.b-btn{{height:40px;padding:0 18px;border:1px solid var(--acc);background:var(--acc);color:var(--on-acc);font:600 16px {SERIF};cursor:pointer;display:inline-flex;align-items:center}}.b-btn.sec{{background:transparent;color:var(--acc)}}
.b-sl{{display:grid;grid-template-columns:30px 1fr 70px;gap:12px;align-items:center;padding:7px 0;border-bottom:1px solid var(--grid)}}
.b-sl b{{font-size:20px;font-style:italic;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:4px;font-size:14.5px;font-style:italic;color:var(--muted)}}
.b-sl input{{width:100%;accent-color:#2D3A87}}.b-sl output{{text-align:right;font-size:16px}}
.b-greek{{display:flex;flex-direction:column;gap:2px;text-align:center}}.b-greek b{{font-size:26px;font-weight:600}}
.b-num{{display:flex;flex-direction:column;gap:4px;text-align:center}}.b-num b{{font-size:34px;font-weight:600;color:var(--acc)}}.b-num span{{font-size:14.5px;line-height:1.4;color:var(--muted);font-style:italic}}
.b-eq{{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;margin:0 0 10px}}.b-eq .b-lab{{grid-column:1/-1}}
.b-eqn{{text-align:center;font-size:23px;font-style:italic;color:var(--ink)}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:12px}}.b-steps li{{display:grid;grid-template-columns:34px 1fr;gap:8px}}
.b-steps .b-n{{color:var(--acc);font-size:18px}}.b-steps li>span>b{{font-size:17.5px}}.b-steps li>span>span{{display:block;font-size:17px;line-height:1.55;color:var(--body);text-align:justify}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;text-align:center}}
.b-lin li{{display:flex;flex-direction:column;gap:2px}}.b-lin .b-y{{font-size:28px;font-weight:600}}.b-lin li.now .b-y{{color:var(--acc)}}.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{color:var(--muted);font-style:italic}}
.b-list{{margin:0 0 12px;padding-left:24px;display:flex;flex-direction:column;gap:6px;font-size:17px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0;width:100%}}.b-video button{{width:100%;aspect-ratio:16/9;border:1px solid var(--line);background:var(--raised);display:flex;align-items:center;justify-content:center;cursor:pointer}}
.b-video figcaption{{margin-top:8px;font-size:15.5px;color:var(--body)}}
.b-person{{display:flex;flex-direction:column;align-items:center;text-align:center;gap:2px}}.b-person .b-ph{{display:none}}.b-person b{{font-size:19px}}.b-person>span:last-child{{font-style:italic;color:var(--muted);font-size:15px}}
.b-refs h2{{margin:10px 0 8px;font-size:19px;font-weight:700}}.b-refs ol{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px}}
.b-refs li{{display:grid;grid-template-columns:44px 1fr;font-size:16.5px;line-height:1.5;text-align:justify}}.b-refs .b-rn{{color:var(--acc)}}.b-refs .b-rt{{font-style:italic}}
.b-chip{{font-size:15px;padding:3px 10px;border:1px solid var(--line)}}.b-chip.on{{border-color:var(--acc);color:var(--acc);font-weight:700}}
.toc{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 44px;padding:18px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)}}
.toc a{{display:grid;grid-template-columns:40px 1fr auto;gap:8px;align-items:baseline;padding:6px 0;font-size:17px;border-bottom:1px dotted var(--line)}}.toc a span:first-child{{color:var(--acc)}}.toc a span:last-child{{color:var(--muted);font-style:italic;font-size:15px}}
.ft{{padding:22px 250px 34px 220px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-size:14px;font-style:italic;color:var(--muted)}}
"""

INK = Ink(font=SERIF, size=14, line_w=2.2, grid="transparent", axis="var(--ink)", text="var(--body)", strong="var(--ink)", bar_radius=0)

SECTION = {"Main": "1", "Market": "2", "Model": "3", "Maths": "4", "Finding": "5", "About": "6", "Team": "", "References": ""}


def run(page):
    return f'<div class="run"><span>Double Heston: a moving volatility, and what it can’t tell you</span><span>{esc(X.STATUS)}</span></div>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def sec(n, t):
    return f'<h2 class="sec">{f"<span>{n}</span>" if n else ""}{esc(t)}</h2>'


def eq(e, n):
    return f'<div class="eqr"><span class="eq">{esc(e)}</span><span class="n">({n})</span></div>'


def fig(n, chart, cap):
    return f'<figure class="fig">{chart}<figcaption><b>Fig. {n}.</b> {esc(cap)}</figcaption></figure>'


def P(*ps, first=True):
    return "".join(f'<p{" class=ni" if i == 0 and first else ""}>{esc(p)}</p>' for i, p in enumerate(ps))


def paper_head(title, abstract=None):
    a = f'<div class="abs"><b>Abstract.</b> {esc(abstract)}</div>' if abstract else ""
    return (f'<h1 class="title">{esc(title)}</h1><div class="auth">[Team member names]<br><i>[Department of Physics], [College] · [Event], 2026</i></div>{a}')


def toc():
    cells = "".join(f'<a href="{s}.dc.html"><span>{SECTION[s] or "–"}</span><span>{l}</span><span>{d}</span></a>' for s, l, d in kit.PAGES)
    return f'<nav class="toc" aria-label="Contents">{cells}</nav>'


def home():
    abstract = (f"{X.A_SHORT} {X.A_LONG} {X.TWIST} {X.FINDING_LINE} {X.FINDING_SUB}")
    return f"""
{B.ticker()}
{run('Main')}
<article class="paper">
  {paper_head('Double Heston on NSE options: a close price fit, and settings the prices cannot pin down', abstract)}
  {toc()}
  <div class="cols">
    {sec('1', 'Introduction')}
    {P('An option is a bet on how far a price might move, so its price depends on volatility. Black–Scholes (1973) treats volatility as one fixed number; real option prices disagree, because protection against a fall usually costs more than the same-sized bet on a rise.', 'Heston (1993) let volatility move. Christoffersen, Heston and Jacobs (2009) gave it two independent parts, a slow and a fast factor, each mean-reverting at its own speed; ten settings in all. Fig. 1 shows the resulting smile at the model’s starting settings.', X.TWO_CLOCKS + f' At the starting settings the slow factor’s half-life is {X.HL["slow_years"]:.1f} years and the fast factor’s about {X.HL["fast_days"] / 7:.0f} weeks.')}
  </div>
  {fig(1, B.smile(INK, 900, 400), X.SMILE_CAPTION + ' The dashed line is one fixed volatility of 20%.')}
  <div class="cols">
    {P(X.FINDING_LINE + ' ' + X.FINDING_SUB, 'Section 5 gives the evidence on simulated and real surfaces; Section 3 prices a listed NIFTY option against its NSE close; Section 4 sets out the equations.')}
  </div>
  {fig(2, B.bars(INK, 900), 'Median distance between equally good fits for each setting (bars) against two parameter sets drawn at random from the training data (ticks), 2,379 real surfaces.')}
</article>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{run('Market')}
<article class="paper">
  {sec('2', 'Market data')}
  <div class="cols">{P(X.MARKET_SUB, X.UNIVERSE, f'Fig. 3 shows RELIANCE over the 62 days as daily candlesticks; Table 1 gives the closing prices on {X.LAST_DAY}.')}</div>
  {fig(3, B.rel_candles(INK, 960, 460, 8), f'RELIANCE daily candlesticks, NSE bhavcopy, {X.FIRST_DAY} to {X.LAST_DAY}. Green: closed higher than it opened; red: closed lower. Volume below. Close on {X.LAST_DAY}: ₹{inr(r[4])}.')}
  <p class="b-lab" style="text-align:center;margin:0">Table 1. Watchlist, closing prices on {X.LAST_DAY}.</p>
  {B.watch_table(names=True, spark=(90, 24))}
  {fig(4, B.nifty_line(INK, 960, 250), 'NIFTY 50 closing level. Index levels are published as closes in the F&O file, so this is a line.')}
</article>
{ft()}
"""


def model():
    K = X.K
    return f"""
{run('Model')}
<article class="paper">
  {sec('3', 'Pricing a listed option')}
  <div class="cols">{P(f'We price the NIFTY {inr(K["strike"], 0)} call expiring {X.EXPIRY} ({K["dte"]} days), which closed at ₹{inr(K["market"])} on {X.LAST_DAY} (implied volatility {K["market_iv"]:.2f}%). At its starting settings Double Heston gives ₹{inr(K["dh"])} (implied volatility {K["dh_iv"]:.2f}%); a Monte Carlo check with 20,000 paths gives ₹{inr(K["mc"])} ± {K["mc_se"]:.2f}.', X.MODEL_EXPLAIN, X.MODEL_SOURCE)}</div>
  {B.pricing_form()}
  <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;padding:10px 0">{B.nums([(f'₹{inr(K["market"])}', 'market close'), (f'₹{inr(K["dh"])}', 'Double Heston, starting settings'), (f'+₹{inr(X.GAP)}', 'model minus market')])}</div>
  {fig(5, B.market_smile(INK, 900, 380, 52), 'Implied volatility by strike, expiry ' + X.EXPIRY + '. Open circles: NSE closing prices. Line: Double Heston at its starting settings.')}
  <p class="b-lab" style="text-align:center;margin:0">Table 2. Option chain around the money, NSE close, {X.LAST_DAY}.</p>
  {B.chain_table()}
  <p class="b-lab" style="text-align:center;margin:10px 0 0">Table 3. The ten settings. {esc(X.FELLER_NOTE)}</p>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:44px"><div><p class="b-lab" style="margin:0">Slow factor: {esc(X.FELLER['slow'])}</p>{B.sliders('slow')}</div><div><p class="b-lab" style="margin:0">Fast factor: {esc(X.FELLER['fast'])}</p>{B.sliders('fast')}</div></div>
  <div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:18px;padding:16px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)">{B.greeks()}</div>
</article>
{ft()}
"""


def maths():
    return f"""
{run('Maths')}
<article class="paper">
  {sec('4', 'The model')}
  <div class="cols">{P(X.MATHS_INTRO, 'Under the risk-neutral measure the price and the two variances follow')}</div>
  {eq(X.EQ_PRICE, 1)}{eq(X.EQ_VAR, 2)}
  <div class="cols">{P('Because the factors are independent, the characteristic function of the log price factorises,', first=True)}</div>
  {eq(X.EQ_CF, 3)}
  <div class="cols">{P('and a European call follows from one numerical integral by Gil-Pelaez inversion,')}</div>
  {eq(X.EQ_CALL, 4)}
  <div class="cols">{P('A factor’s variance stays away from zero when the Feller condition holds,')}</div>
  {eq(X.EQ_FELLER, 5)}
  <div class="cols">{B.steps()}</div>
  {fig(6, B.skew(INK, 900, 320), f'Skew, IV at 95% of spot minus IV at 105%, by time to expiry, starting settings. Half-lives: fast factor about {X.HL["fast_days"] / 7:.0f} weeks, slow factor {X.HL["slow_years"]:.1f} years.')}
  {B.lineage()}
</article>
{ft()}
"""


def finding():
    return f"""
{run('Finding')}
<article class="paper">
  {sec('5', 'The finding: ' + X.FIND_HEAD[0].lower() + X.FIND_HEAD[1:])}
  <div class="cols">{sec('5.1', X.PROOF1_HEAD)}{P(X.PROOF1, X.PROOF1_NET)}{sec('5.2', X.PROOF2_HEAD)}{P(X.PROOF2)}</div>
  <div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px;padding:14px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)">{B.nums(X.PROOF1_NUMS + X.PROOF2_NUMS)}</div>
  {fig(7, B.hist(INK, 940, 300), 'Distribution of the median pairwise distance between equally good fits on the 2,379 real surfaces with more than one, in spreads of the training data.')}
  <div class="cols">{sec('5.3', 'By setting')}{P(X.PER_PARAM)}</div>
  {fig(8, B.bars(INK, 900), 'Median distance between equally good fits, per setting, against two random parameter sets.')}
  <div class="cols">{sec('5.4', 'One stock, day by day')}{P(X.rel_line())}</div>
  {fig(9, B.stock(INK, 960), 'RELIANCE, 60 trading days. Top: price error of the best Double Heston fit and of one flat volatility. Bottom: distance between equally good fits.')}
  <div class="cols">{sec('5.5', 'Out of sample')}{P(X.HELDOUT, X.BACKTEST)}</div>
</article>
{ft()}
"""


def about():
    return f"""
{run('About')}
<article class="paper">
  {sec('6', 'Method, data and limits')}
  {B.video(icon_fill='var(--acc)', icon_ink='var(--on-acc)')}
  <div class="cols">{sec('6.1', 'Method and data')}{P(*X.METHOD)}{sec('6.2', 'Limits')}{B.bullet_list(X.LIMITS)}{sec('6.3', 'Also explored')}{P(X.ALSO)}<p class="ni">Code and data: <span class="b-model">{esc(X.REPO)}</span>.</p></div>
</article>
{ft()}
"""


def team():
    return f"""
{run('Team')}
<article class="paper">
  {sec('', 'Authors')}
  <div class="cols" style="column-count:1">{P(X.TEAM_INTRO)}</div>
  <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;padding:18px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink)">{B.team_cards(icon=False)}</div>
  {sec('', 'Supervision')}<div class="cols" style="column-count:1">{P(X.SUPERVISOR[0] + ', ' + X.SUPERVISOR[1] + '.')}</div>
  {sec('', 'Acknowledgements')}<div class="cols" style="column-count:1">{P(' '.join(X.THANKS))}</div>
</article>
{ft()}
"""


def references():
    return f"""
{run('References')}
<article class="paper">
  {sec('', 'References')}
  <div class="cols" style="text-align:left">{B.refs()}</div>
</article>
{ft()}
"""


DESIGN = Design(
    num=7, slug="journal", name="Journal",
    concept="The site typeset as a physics paper: title block, abstract, numbered sections, numbered equations, Fig. n.",
    memorable="Equations set like a paper, numbered at the right margin; every chart is a numbered figure.",
    layout="A 1000-px paper: centred title and abstract, justified two-column text, full-width figures and three-rule tables.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap",
    display_font=SERIF, body_font=SERIF,
    type_sample="dvᵢ = κᵢ(θᵢ − vᵢ) dt + ξᵢ √vᵢ dZᵢ",
    type_note="Source Serif 4 throughout: 600 for the title, 400 justified for text, italic for equations and captions.",
    ink=INK, css=CSS, rail_side="r", default_dark=False,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
