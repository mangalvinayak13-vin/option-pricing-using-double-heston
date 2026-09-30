"""10 · Swiss — a strict 12-column grid with black hairlines, giant numerals, one red."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#FFFFFF", surf="#F4F4F4", raised="#EBEBEB", line="#121212", grid="#E2E2E2", ink="#121212",
             body="#2B2B2B", muted="#595959", acc="#D23B16", on_acc="#FFFFFF", up="#127A3E", down="#B3121F",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#111111", surf="#1A1A1A", raised="#232323", line="#EDEDED", grid="#2C2C2C", ink="#F2F2F2",
            body="#D0D0D0", muted="#A3A3A3", acc="#FF5A2E", on_acc="#111111", up="#3DDC84", down="#FF4D5E",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

F = "'Instrument Sans',Helvetica,sans-serif"
CSS = f"""
.mast{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:24px;padding:14px 250px 14px 96px;border-bottom:1px solid var(--line);font-size:14px;align-items:baseline}}
.mast b{{grid-column:span 3;font-weight:700;font-size:16px}}.mast span{{grid-column:span 6;color:var(--muted)}}
.sw{{padding:0 48px 0 96px}}
.row{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:24px;padding:36px 0 44px;border-bottom:1px solid var(--line)}}
.lbl{{grid-column:1/span 3;font-size:15px;font-weight:700;line-height:1.35;padding-top:6px}}
.lbl span{{display:block;font-weight:400;color:var(--muted)}}
.body{{grid-column:4/span 9;min-width:0;display:flex;flex-direction:column;gap:22px}}
.giant{{margin:0;font-size:170px;font-weight:700;line-height:.86;letter-spacing:-.055em}}
.huge{{font-size:220px;font-weight:700;line-height:.82;letter-spacing:-.06em;color:var(--acc)}}
.h2{{margin:0;font-size:44px;font-weight:700;line-height:1.02;letter-spacing:-.03em}}
.p{{margin:0;font-size:19px;line-height:1.5;color:var(--body);max-width:760px}}
.cols2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:24px}}
.cols3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));column-gap:24px}}
.b-tick{{height:36px;display:flex;align-items:center;padding:0 250px 0 96px;font-size:13.5px;white-space:nowrap;border-bottom:1px solid var(--line)}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:28px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti b{{font-weight:700}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-size:16px}}
.b-tb th{{text-align:right;font-weight:700;font-size:13px;padding:8px 8px;border-bottom:1px solid var(--line)}}
.b-tb td{{text-align:right;padding:9px 8px;border-bottom:1px solid var(--grid);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb tr.sel td{{background:var(--acc);color:var(--on-acc)}}.b-tb tr.sel td *{{color:var(--on-acc)}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc);font-weight:700}}.b-lab{{font-size:13px;font-weight:700}}
.b-form{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr)) auto;gap:0 24px;align-items:end;margin:0}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:8px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:48px;border:0;border-bottom:2px solid var(--ink);background:transparent;color:var(--ink);font:500 18px {F};padding:0}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:48px;border:2px solid var(--ink)}}.b-seg span{{display:flex;align-items:center;justify-content:center;font-weight:700}}.b-seg span.on{{background:var(--ink);color:var(--bg)}}
.b-btn{{height:52px;padding:0 26px;border:0;background:var(--acc);color:var(--on-acc);font:700 17px {F};cursor:pointer;display:inline-flex;align-items:center}}.b-btn.sec{{background:transparent;color:var(--ink);border:2px solid var(--ink)}}
.b-sl{{display:grid;grid-template-columns:36px 1fr 80px;gap:14px;align-items:center;padding:10px 0;border-bottom:1px solid var(--grid)}}
.b-sl b{{font-size:22px;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:5px;font-size:14.5px;color:var(--muted)}}
.b-sl input{{width:100%;accent-color:#D23B16}}.b-sl output{{text-align:right;font-weight:700;font-size:18px}}
.b-greek{{display:flex;flex-direction:column;gap:4px;padding-top:12px;border-top:1px solid var(--line)}}.b-greek b{{font-size:44px;font-weight:700;letter-spacing:-.03em}}
.b-num{{display:flex;flex-direction:column;gap:8px;padding-top:12px;border-top:1px solid var(--line)}}.b-num b{{font-size:72px;font-weight:700;letter-spacing:-.04em;line-height:.9;color:var(--acc)}}.b-num span{{font-size:15.5px;line-height:1.45;color:var(--body)}}
.b-eq{{display:grid;grid-template-columns:3fr 9fr;gap:24px;padding:16px 0;border-bottom:1px solid var(--grid)}}.b-eq .b-lab{{font-weight:400;color:var(--muted);font-size:15px}}
.b-eqn{{font-size:26px;font-weight:500;line-height:1.35}}
.b-steps{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:24px}}.b-steps li{{display:flex;flex-direction:column;gap:10px;padding-top:12px;border-top:1px solid var(--line)}}
.b-steps .b-n{{font-size:56px;font-weight:700;color:var(--acc);line-height:.9}}.b-steps li>span{{display:flex;flex-direction:column;gap:6px}}.b-steps li>span>b{{font-size:17px}}.b-steps li>span>span{{font-size:14.5px;line-height:1.5;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}}.b-lin li{{display:flex;flex-direction:column;gap:8px;padding-top:12px;border-top:1px solid var(--line)}}
.b-lin .b-y{{font-size:96px;font-weight:700;letter-spacing:-.05em;line-height:.85}}.b-lin li.now .b-y{{color:var(--acc)}}.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>b{{font-size:18px}}.b-lin li>span>span{{color:var(--muted)}}
.b-list{{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:8px;font-size:17px;line-height:1.5;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;background:var(--ink);display:flex;align-items:center;justify-content:center;cursor:pointer}}.b-video figcaption{{margin-top:10px;font-size:15px;color:var(--muted)}}
.b-person{{display:flex;flex-direction:column;gap:6px;padding-top:12px;border-top:1px solid var(--line)}}.b-person .b-ph{{aspect-ratio:1/1;background:var(--surf);display:flex;align-items:center;justify-content:center;margin-bottom:8px}}
.b-person b{{font-size:24px;font-weight:700;letter-spacing:-.02em}}.b-person>span:last-child{{color:var(--muted);font-size:15px}}
.b-refs{{display:grid;grid-template-columns:3fr 9fr;column-gap:24px;padding:24px 0;border-bottom:1px solid var(--line)}}.b-refs h2{{margin:0;font-size:15px;font-weight:700}}
.b-refs ol{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:12px}}.b-refs li{{display:grid;grid-template-columns:48px 1fr;font-size:16.5px;line-height:1.5}}.b-refs .b-rn{{font-weight:700;color:var(--acc)}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{font-size:14px;font-weight:700;padding:6px 12px;border:1px solid var(--line)}}.b-chip.on{{background:var(--ink);color:var(--bg)}}
.b-links{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0 24px}}.b-links a{{display:flex;align-items:center;gap:12px;padding:16px 0;border-top:1px solid var(--line)}}.b-links a>span{{display:flex;flex-direction:column}}.b-links b{{font-size:17px}}.b-links a>span>span{{color:var(--muted);font-size:14px}}
.ft{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));column-gap:24px;padding:20px 48px 34px 96px;font-size:14px;color:var(--muted)}}.ft span:first-child{{grid-column:1/span 6}}.ft span:last-child{{grid-column:7/span 6;text-align:right}}
"""

INK = Ink(font=F, size=13, line_w=3, grid="var(--grid)", axis="var(--line)", bar_radius=0)


def mast():
    return f'<header class="mast"><b>Double Heston</b><span>{esc(X.STATUS)}</span></header>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def R(label, sub, body):
    s = f"<span>{esc(sub)}</span>" if sub else ""
    return f'<section class="row"><div class="lbl">{esc(label)}{s}</div><div class="body">{body}</div></section>'


def top(word, sub=None):
    s = f'<p class="p" style="margin-top:22px">{esc(sub)}</p>' if sub else ""
    return f'<section class="row" style="padding-top:28px"><div style="grid-column:1/span 12"><h1 class="giant">{esc(word)}</h1>{s}</div></section>'


def P(t, style=""):
    return f'<p class="p" style="{style}">{esc(t)}</p>'


def home():
    return f"""
{B.ticker()}
{mast()}
<div class="sw">
  {top('Double Heston', X.Q)}
  {R('Answer', 'for fitting today’s prices', f'<h2 class="h2">{esc(X.A_SHORT)}</h2>' + P(X.A_LONG) + P(X.TWIST))}
  {R('Figure 1', 'implied volatility by strike, 30 days', B.smile(INK, 1000, 420))}
  {R('Two factors', 'ten settings', f'<div class="cols3"><div class="b-num"><b>0.5</b><span>κ, slow factor. Half-life {X.HL["slow_years"]:.1f} years.</span></div><div class="b-num"><b>5.0</b><span>κ, fast factor. Half-life about {X.HL["fast_days"] / 7:.0f} weeks.</span></div><div class="b-num"><b style="color:var(--ink)">10</b><span>settings in all, five per factor.</span></div></div>' + P(X.TWO_CLOCKS))}
  {R('Finding', 'real NSE surfaces', f'<span class="huge">{X.SHARE * 100:.0f}%</span><h2 class="h2">{esc(X.FINDING_LINE)}</h2>' + P(X.FINDING_SUB) + f'<a class="b-model" href="Finding.dc.html">{X.CTA["finding"]}</a>')}
  {R('Pages', None, B.page_links('Main', 40, fill='var(--surf)'))}
</div>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{mast()}
<div class="sw">
  {top('Market', X.MARKET_SUB)}
  {R('RELIANCE', 'Reliance Industries, daily', f'<div style="display:flex;align-items:baseline;gap:22px"><span style="font-size:96px;font-weight:700;letter-spacing:-.05em;line-height:.9">{inr(r[4])}</span><span style="font-size:20px;font-weight:700">{B.rel_change()}</span></div><span style="display:flex;gap:6px">' + ''.join(f'<span class="b-chip{" on" if c else ""}">{t}</span>' for t, c in (("1M", 0), ("3M", 1), ("Line", 0), ("Candles", 1))) + '</span>' + B.rel_candles(INK, 1000, 460, 8) + '<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:24px">' + ''.join(f'<div class="b-num"><span>{k}</span><b style="font-size:24px;color:var(--ink);letter-spacing:-.01em">{v}</b></div>' for k, v in B.rel_stats()) + '</div>')}
  {R('Watchlist', 'close, ' + X.LAST_DAY, B.watch_table(names=True, spark=(90, 24)))}
  {R('NIFTY 50', 'closing level', B.nifty_line(INK, 1000, 240) + P(X.UNIVERSE))}
</div>
{ft()}
"""


def model():
    K = X.K
    return f"""
{mast()}
<div class="sw">
  {top('The model', 'Pick a listed option, price it with Double Heston, and set it against what the market paid.')}
  {R('Contract', X.CONTRACT, B.pricing_form())}
  {R('Price', X.CONTRACT_SUB, f'<div class="cols3"><div class="b-num"><b style="color:var(--ink)">₹{inr(K["market"])}</b><span>market close, IV {K["market_iv"]:.2f}%</span></div><div class="b-num"><b>₹{inr(K["dh"])}</b><span>Double Heston, IV {K["dh_iv"]:.2f}%. {esc(X.MC_LINE)}.</span></div><div class="b-num"><b style="color:var(--ink)">+{inr(X.GAP, 0)}</b><span>rupees, model minus market</span></div></div>' + P(X.MODEL_EXPLAIN))}
  {R('Figure 2', 'smile, market against model', B.market_smile(INK, 1000, 400, 52))}
  {R('Chain', 'NSE close, ' + X.LAST_DAY, B.chain_table())}
  {R('Settings', 'slow factor', f'<span class="dn" style="font-weight:700">{esc(X.FELLER["slow"])}</span>' + B.sliders('slow'))}
  {R('', 'fast factor', f'<span class="dn" style="font-weight:700">{esc(X.FELLER["fast"])}</span>' + B.sliders('fast') + f'<div style="display:flex;justify-content:space-between;align-items:center"><span class="b-sub">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div>')}
  {R('Greeks', None, f'<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:24px">{B.greeks()}</div>' + f'<span class="b-sub" style="font-size:14px">{esc(X.MODEL_SOURCE)}</span>')}
</div>
{ft()}
"""


def maths():
    return f"""
{mast()}
<div class="sw">
  {top('How it works', X.MATHS_INTRO)}
  {R('Equations', 'five lines', B.equations())}
  {R('Steps', 'from equation to price', B.steps())}
  {R('Figure 3', 'skew by time to expiry', B.skew(INK, 1000, 320))}
  {R('Lineage', '1973 to 2009', B.lineage())}
</div>
{ft()}
"""


def finding():
    return f"""
{mast()}
<div class="sw">
  {top('The finding', X.FIND_HEAD)}
  {R('Test 1', X.PROOF1_HEAD, f'<span class="huge">1.80</span>' + P(X.PROOF1) + f'<div class="cols3">{B.nums(X.PROOF1_NUMS)}</div>' + P(X.PROOF1_NET, 'font-size:16px;color:var(--muted)'))}
  {R('Test 2', X.PROOF2_HEAD, f'<span class="huge">{X.RATIO:.1f}×</span>' + P(X.PROOF2) + f'<div class="cols3">{B.nums(X.PROOF2_NUMS)}</div>')}
  {R('Figure 4', 'distance between equally good fits', B.hist(INK, 1000, 300))}
  {R('Figure 5', 'by setting', B.bars(INK, 1000) + P(X.PER_PARAM))}
  {R('Figure 6', 'RELIANCE, 60 days', f'<span style="display:flex;gap:6px;flex-wrap:wrap">{B.picks()}</span>' + P(X.rel_line()) + B.stock(INK, 1000))}
  {R('Test 3', 'out of sample', f'<div class="cols2"><div class="b-num"><b>{X.G8["median_network_relative"] * 100:.1f}%</b><span>{esc(X.HELDOUT)}</span></div><div class="b-num"><b style="color:var(--ink)">0/210</b><span>{esc(X.BACKTEST)}</span></div></div>')}
</div>
{ft()}
"""


def about():
    return f"""
{mast()}
<div class="sw">
  {top('About', X.ABOUT_HEAD)}
  {R('Video', 'explainer', B.video(icon_fill='var(--acc)', icon_ink='var(--on-acc)'))}
  {R('Method', 'and data', ''.join(P(m) for m in X.METHOD))}
  {R('Limits', None, B.bullet_list(X.LIMITS))}
  {R('Also', 'explored', P(X.ALSO) + f'<a class="b-model" href="https://{X.REPO}">{esc(X.REPO)}</a>')}
</div>
{ft()}
"""


def team():
    return f"""
{mast()}
<div class="sw">
  {top('Team', X.TEAM_INTRO)}
  {R('People', None, f'<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px">{B.team_cards()}</div>')}
  {R('Supervisor', None, f'<h2 class="h2" style="font-size:32px">{esc(X.SUPERVISOR[0])}</h2>' + P(X.SUPERVISOR[1]))}
  {R('Thanks', None, B.bullet_list(X.THANKS))}
</div>
{ft()}
"""


def references():
    return f"""
{mast()}
<div class="sw">
  {top('References', 'The papers behind the model and its methods, and where the data comes from.')}
  {B.refs()}
</div>
{ft()}
"""


DESIGN = Design(
    num=10, slug="swiss", name="Swiss",
    concept="A strict 12-column grid with black hairlines: giant flush-left headlines, giant red numerals, one red.",
    memorable="Page titles at 170 px and the headline numbers at 220 px in red, all hung on one 12-column grid.",
    layout="Every section is a hairline row: a 3-column label on the left, content in the remaining 9 columns.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;700&display=swap",
    display_font=F, body_font=F,
    type_sample="99% 3.9× 1.80",
    type_note="Instrument Sans 700 at display sizes with tight tracking; 400–500 for text. One family, many sizes.",
    ink=INK, css=CSS, rail_side="l", default_dark=False,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
