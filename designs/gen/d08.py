"""08 · Apothecary — skincare-label calm: one quiet figure per screen, light type, an ingredient list of settings."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#ECEDE8", surf="#F5F6F2", raised="#E2E4DD", line="#C6C9BF", grid="#DADDD4", ink="#22251F",
             body="#3B3E36", muted="#5B5F56", acc="#566849", on_acc="#FFFFFF", up="#3A7545", down="#A2433A",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#1B1D19", surf="#22251F", raised="#2A2E27", line="#3A3E35", grid="#2A2D26", ink="#E4E6DF",
            body="#C3C7BD", muted="#9A9F93", acc="#A9BC94", on_acc="#1B1D19", up="#7FC48C", down="#E08A7C",
            on_up="#0E1A10", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

CSS = """
.lab{height:60px;display:flex;align-items:center;justify-content:space-between;padding:0 250px 0 140px;font-size:15px;color:var(--muted)}
.lab b{font-weight:600;color:var(--ink);letter-spacing:.02em}
.col{width:760px;margin:0 auto;padding:110px 0 140px;display:flex;flex-direction:column;gap:110px}
.sect{display:flex;flex-direction:column;gap:22px}
.no{font-size:14px;color:var(--muted);letter-spacing:.04em}
.h1{margin:0;font-weight:300;font-size:64px;line-height:1.08;letter-spacing:-.02em}
.h2{margin:0;font-weight:300;font-size:40px;line-height:1.12;letter-spacing:-.015em}
.p{margin:0;font-size:19px;line-height:1.7;color:var(--body);font-weight:400}
.rule{height:1px;background:var(--line)}
.big{font-weight:200;font-size:120px;line-height:.9;letter-spacing:-.04em}
.spec{display:grid;grid-template-columns:1fr auto;gap:0;border-top:1px solid var(--line)}
.spec>*{padding:13px 0;border-bottom:1px solid var(--line);font-size:17px}
.spec>span:nth-child(odd){color:var(--body)}.spec>span:nth-child(even){text-align:right;font-weight:600}
.b-tick{height:36px;display:flex;align-items:center;padding:0 250px 0 140px;font-size:13.5px;white-space:nowrap;color:var(--body);border-bottom:1px solid var(--line)}
.b-tick-in{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}.b-ti{display:inline-flex;gap:7px}.b-ti b{font-weight:600}.b-ti-lab{color:var(--muted)}
.b-tb{width:100%;border-collapse:collapse;font-size:16px}
.b-tb th{text-align:right;font-weight:400;font-size:13.5px;color:var(--muted);padding:10px 6px;border-bottom:1px solid var(--line)}
.b-tb td{text-align:right;padding:12px 6px;border-bottom:1px solid var(--line);white-space:nowrap}
.b-tb th:first-child,.b-tb td:first-child{text-align:left}.b-tb td b{font-weight:600}.b-tb tr.sel td{color:var(--acc);font-weight:600}
.b-sub{color:var(--muted)}.b-model{color:var(--acc)}.b-lab{font-size:13.5px;color:var(--muted)}
.b-form{display:grid;grid-template-columns:1fr 1fr;gap:16px 20px;margin:0}
.b-form label,.b-form fieldset{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}
.b-form select,.b-form input{height:48px;border:0;border-bottom:1px solid var(--ink);background:transparent;color:var(--ink);font:400 18px 'Hanken Grotesk',sans-serif;padding:0 2px}
.b-seg{display:flex;gap:18px;height:48px;align-items:center;border-bottom:1px solid var(--ink)}.b-seg span{color:var(--muted);font-size:18px}.b-seg span.on{color:var(--ink);font-weight:600}
.b-btn{grid-column:1/-1;height:54px;border-radius:27px;border:0;background:var(--ink);color:var(--bg);font:600 17px 'Hanken Grotesk',sans-serif;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;padding:0 28px}
.b-btn.sec{background:transparent;color:var(--ink);border:1px solid var(--ink)}
.b-sl{display:grid;grid-template-columns:34px 1fr 80px;gap:14px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}
.b-sl b{font-weight:300;font-size:22px;color:var(--acc)}.b-sl label{display:flex;flex-direction:column;gap:6px;font-size:15px;color:var(--muted)}
.b-sl input{width:100%;accent-color:#566849}.b-sl output{text-align:right;font-weight:600;font-size:17px}
.b-greek{display:grid;grid-template-columns:1fr auto;padding:13px 0;border-bottom:1px solid var(--line)}.b-greek .b-lab{font-size:17px;color:var(--body)}.b-greek b{font-weight:600;font-size:18px;text-align:right}.b-greek .b-sub{grid-column:1/-1;font-size:14px}
.b-num{display:flex;flex-direction:column;gap:8px}.b-num b{font-weight:200;font-size:72px;line-height:.95;letter-spacing:-.03em;color:var(--ink)}.b-num span{font-size:16px;line-height:1.5;color:var(--muted)}
.b-eq{display:flex;flex-direction:column;gap:8px;padding:22px 0;border-bottom:1px solid var(--line)}.b-eqn{font-weight:300;font-size:28px;line-height:1.4}
.b-steps{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}.b-steps li{display:grid;grid-template-columns:40px 1fr;gap:10px;padding:20px 0;border-bottom:1px solid var(--line)}
.b-steps .b-n{font-weight:300;font-size:22px;color:var(--muted)}.b-steps li>span{display:flex;flex-direction:column;gap:6px}.b-steps li>span>b{font-weight:600;font-size:18px}.b-steps li>span>span{font-size:17px;line-height:1.65;color:var(--body)}
.b-lin{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}.b-lin li{display:grid;grid-template-columns:120px 1fr;gap:10px;align-items:baseline;padding:16px 0;border-bottom:1px solid var(--line)}
.b-lin .b-y{font-weight:200;font-size:44px}.b-lin li.now .b-y{color:var(--acc)}.b-lin li>span{display:flex;flex-direction:column}.b-lin li>span>span{color:var(--muted)}
.b-list{margin:0;padding:0;list-style:none;display:flex;flex-direction:column}.b-list li{padding:14px 0;border-bottom:1px solid var(--line);font-size:17px;line-height:1.6;color:var(--body)}
.b-video{margin:0}.b-video button{width:100%;aspect-ratio:16/9;border:0;border-radius:4px;background:var(--raised);display:flex;align-items:center;justify-content:center;cursor:pointer}.b-video figcaption{margin-top:12px;font-size:15px;color:var(--muted)}
.b-person{display:grid;grid-template-columns:1fr auto;padding:18px 0;border-bottom:1px solid var(--line)}.b-person .b-ph{display:none}.b-person b{font-weight:400;font-size:24px}.b-person>span:last-child{color:var(--muted);font-size:15px;align-self:end}
.b-refs h2{margin:0 0 6px;font-weight:300;font-size:26px}.b-refs ol{list-style:none;margin:0 0 40px;padding:0}.b-refs li{display:grid;grid-template-columns:48px 1fr;padding:14px 0;border-bottom:1px solid var(--line);font-size:16.5px;line-height:1.55}
.b-refs .b-rn{color:var(--muted)}.b-refs .b-rt{color:var(--body)}
.b-chip{font-size:15px;color:var(--muted);padding:2px 0}.b-chip.on{color:var(--ink);font-weight:600;border-bottom:1px solid var(--ink)}
.b-links{display:flex;flex-direction:column;border-top:1px solid var(--line)}.b-links a{display:grid;grid-template-columns:44px 1fr auto;gap:16px;align-items:center;padding:14px 0;border-bottom:1px solid var(--line)}
.b-links a>span{display:contents}.b-links b{font-weight:400;font-size:19px}.b-links a>span>span{color:var(--muted);font-size:15px;text-align:right}
.ft{padding:30px 250px 44px 140px;display:flex;justify-content:space-between;font-size:14px;color:var(--muted)}
"""

INK = Ink(font="'Hanken Grotesk',sans-serif", size=13, line_w=1.8, grid="transparent", axis="var(--line)", bar_radius=0)


def lab():
    return f'<header class="lab"><b>double heston, no. 2009</b><span>{esc(X.STATUS)}</span></header>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def S(no, *parts):
    return f'<section class="sect"><span class="no">{esc(no)}</span>{"".join(parts)}</section>'


def P(t):
    return f'<p class="p">{esc(t)}</p>'


def ingredients():
    rows = []
    for f, sym, name, val, lo, hi in X.SLIDERS:
        fmt = f"{val:.4f}" if sym in ("v₀", "θ") else f"{val:.2f}"
        rows.append(f"<span>{sym} {name}, {f} factor</span><span>{fmt}</span>")
    return f'<div class="spec">{"".join(rows)}</div>'


def home():
    return f"""
{B.ticker()}
{lab()}
<div class="col">
  {S('the question', f'<h1 class="h1">{esc(X.Q)}</h1>', P(X.A_SHORT + ' ' + X.A_LONG))}
  {S('figure one', B.smile(INK, 760, 380), f'<span class="b-sub" style="font-size:15px">{esc(X.SMILE_CAPTION)}</span>')}
  {S('two factors', '<h2 class="h2">Two clocks, one slow, one quick.</h2>', P(X.TWO_CLOCKS), f'<div class="spec"><span>Slow factor, κ 0.5</span><span>half-life {X.HL["slow_years"]:.1f} years</span><span>Fast factor, κ 5.0</span><span>half-life {X.HL["fast_days"]:.0f} days</span><span>Settings in all</span><span>10</span></div>')}
  {S('the finding', f'<span class="big">{X.RATIO:.1f}×</span>', P(X.FINDING_LINE + ' ' + X.FINDING_SUB), f'<a class="b-model" style="font-size:18px" href="Finding.dc.html">{X.CTA["finding"]}</a>')}
  {S('contents', B.page_links('Main', 40, fill='var(--raised)'))}
</div>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{lab()}
<div class="col">
  {S('market', '<h1 class="h1">Market</h1>', P(X.MARKET_SUB))}
  {S('RELIANCE, close ' + X.LAST_DAY, f'<span class="big" style="font-size:96px">{inr(r[4])}</span><span style="font-size:18px">{B.rel_change()}</span>', '<span style="display:flex;gap:22px">' + ''.join(f'<span class="b-chip{" on" if c else ""}">{t}</span>' for t, c in (("1M", 0), ("3M", 1), ("Line", 0), ("Candles", 1))) + '</span>', B.rel_candles(INK, 760, 420, 12), '<div class="spec">' + ''.join(f'<span>{k}</span><span>{v}</span>' for k, v in B.rel_stats()) + '</div>')}
  {S('watchlist', B.watch_table(names=True, spark=(70, 22)))}
  {S('NIFTY 50, closing level', B.nifty_line(INK, 760, 230), P(X.UNIVERSE))}
</div>
{ft()}
"""


def model():
    K = X.K
    return f"""
{lab()}
<div class="col">
  {S('the model', '<h1 class="h1">Price an option</h1>', P('Pick a listed option, price it with Double Heston, and set it against what the market paid.'), B.pricing_form())}
  {S(esc(X.CONTRACT) + ', ' + X.EXPIRY, f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:30px">{B.nums([(f"₹{inr(K["market"])}", f"market close, IV {K['market_iv']:.2f}%"), (f"₹{inr(K["dh"])}", f"Double Heston, IV {K['dh_iv']:.2f}%")])}</div>', P(X.MODEL_EXPLAIN), f'<span class="b-sub" style="font-size:15px">{esc(X.MC_LINE)}</span>')}
  {S('the smile', B.market_smile(INK, 760, 360, 48), '<span class="b-sub" style="font-size:15px">Circles: the market, from NSE closing prices. Line: Double Heston at its starting settings.</span>')}
  {S('option chain', B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV')))}
  {S('ingredients: the ten settings', ingredients(), f'<span class="b-sub" style="font-size:15px">{esc(X.FELLER_NOTE)}</span>', B.sliders('slow'), B.sliders('fast'), '<button class="b-btn sec" type="button">Reset to starting settings</button>')}
  {S('greeks', f'<div>{B.greeks()}</div>', f'<span class="b-sub" style="font-size:14px">{esc(X.MODEL_SOURCE)}</span>')}
</div>
{ft()}
"""


def maths():
    return f"""
{lab()}
<div class="col">
  {S('how it works', '<h1 class="h1">Two variances, one integral.</h1>', P(X.MATHS_INTRO))}
  {S('the equations', B.equations())}
  {S('in five steps', B.steps())}
  {S('skew by time to expiry', B.skew(INK, 760, 300))}
  {S('lineage', B.lineage())}
</div>
{ft()}
"""


def finding():
    return f"""
{lab()}
<div class="col">
  {S('the finding', f'<h1 class="h1">{esc(X.FIND_HEAD)}</h1>')}
  {S('simulated surfaces', f'<span class="big">1.80</span>', P(X.PROOF1), f'<span class="b-sub" style="font-size:15px;line-height:1.6">{esc(X.PROOF1_NET)}</span>')}
  {S('real surfaces', f'<span class="big">{X.SHARE * 100:.0f}%</span>', P(X.PROOF2), B.hist(INK, 760, 260))}
  {S('by setting', P(X.PER_PARAM), B.bars(INK, 760, label_w=230))}
  {S('one stock', '<span style="display:flex;gap:18px;flex-wrap:wrap">' + B.picks() + '</span>', P(X.rel_line()), B.stock(INK, 760))}
  {S('out of sample', f'<span class="big" style="font-size:88px">0 of 210</span>', P(X.BACKTEST), P(X.HELDOUT))}
</div>
{ft()}
"""


def about():
    return f"""
{lab()}
<div class="col">
  {S('about', f'<h1 class="h1">{esc(X.ABOUT_HEAD)}</h1>')}
  {S('the video', B.video(icon_fill='var(--ink)', icon_ink='var(--bg)'))}
  {S('method and data', *[P(m) for m in X.METHOD])}
  {S('limits', B.bullet_list(X.LIMITS))}
  {S('also explored', P(X.ALSO), f'<a class="b-model" href="https://{X.REPO}">{esc(X.REPO)}</a>')}
</div>
{ft()}
"""


def team():
    return f"""
{lab()}
<div class="col">
  {S('team', f'<h1 class="h1">{esc(X.TEAM_HEAD)}</h1>', P(X.TEAM_INTRO))}
  {S('people', f'<div>{B.team_cards(icon=False)}</div>')}
  {S('supervisor', f'<div class="spec"><span>{esc(X.SUPERVISOR[0])}</span><span>{esc(X.SUPERVISOR[1])}</span></div>')}
  {S('thanks', B.bullet_list(X.THANKS))}
</div>
{ft()}
"""


def references():
    return f"""
{lab()}
<div class="col">
  {S('references', '<h1 class="h1">References</h1>', P('The papers behind the model and its methods, and where the data comes from.'))}
  <div>{B.refs()}</div>
</div>
{ft()}
"""


DESIGN = Design(
    num=8, slug="apothecary", name="Apothecary",
    concept="Skincare-label calm: a centred column, light type, one quiet figure per screen, the settings as an ingredient list.",
    memorable="The ten settings printed like an ingredient list, with their values as concentrations.",
    layout="One 760-px centred column, very large vertical gaps, hairline spec tables; nothing boxed, nothing loud.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@200;300;400;600&display=swap",
    display_font="'Hanken Grotesk',sans-serif", body_font="'Hanken Grotesk',Helvetica,sans-serif",
    type_sample="Two clocks, one slow, one quick.",
    type_note="Hanken Grotesk 200–300 for headlines and big figures, 400 for text, 600 for values.",
    ink=INK, css=CSS, rail_side="l", default_dark=False,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
