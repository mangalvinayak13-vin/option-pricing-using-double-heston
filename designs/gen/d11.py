"""11 · Glass — an Apple product page: huge centred type, alternating bands, one frosted-glass panel per page."""
from __future__ import annotations

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle

LIGHT = dict(bg="#FFFFFF", surf="#F5F5F7", raised="#E8E8ED", line="#D2D2D7", grid="#EDEDF0", ink="#1D1D1F",
             body="#424245", muted="#6E6E73", acc="#0071E3", on_acc="#FFFFFF", up="#1D8C3C", down="#D70015",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#000000", surf="#161617", raised="#1D1D1F", line="#333336", grid="#1F1F21", ink="#F5F5F7",
            body="#D2D2D7", muted="#A1A1A6", acc="#2997FF", on_acc="#000000", up="#30D158", down="#FF453A",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

F = "'Albert Sans',Helvetica,sans-serif"
CSS = f"""
.t-light{{--glass:rgba(255,255,255,.58);--glassb:rgba(255,255,255,.75)}}.t-dark{{--glass:rgba(29,29,31,.55);--glassb:rgba(255,255,255,.14)}}
.gnav{{height:48px;display:flex;align-items:center;justify-content:center;gap:34px;padding:0 250px;font-size:13.5px;color:var(--body);border-bottom:1px solid var(--line)}}
.gnav b{{color:var(--ink);font-size:15px}}
.band{{padding:96px 150px 96px 110px;display:flex;flex-direction:column;align-items:center;gap:26px;text-align:center}}
.band.alt{{background:var(--surf)}}
.eyebrow{{font-size:19px;font-weight:600;color:var(--acc)}}
.hero{{margin:0;font-size:86px;font-weight:700;line-height:1.02;letter-spacing:-.035em;max-width:1080px}}
.h2{{margin:0;font-size:56px;font-weight:700;line-height:1.05;letter-spacing:-.03em;max-width:980px}}
.sub{{margin:0;font-size:24px;line-height:1.42;font-weight:500;color:var(--body);max-width:820px}}
.p{{margin:0;font-size:19px;line-height:1.55;color:var(--body);max-width:760px}}
.lnks{{display:flex;gap:26px;align-items:center}}.lnk{{font-size:19px;color:var(--acc)}}
.pill{{display:inline-flex;align-items:center;height:48px;padding:0 24px;border-radius:24px;background:var(--acc);color:var(--on-acc);font-size:17px;font-weight:600}}
.stage{{position:relative;width:1100px;padding:44px 40px 30px;border-radius:34px;overflow:hidden;background:var(--surf)}}
.band.alt .stage{{background:var(--bg)}}
.glow{{position:absolute;inset:0;filter:blur(38px);opacity:.55}}
.glass{{position:relative;background:var(--glass);border:1px solid var(--glassb);border-radius:26px;backdrop-filter:blur(26px) saturate(1.6);-webkit-backdrop-filter:blur(26px) saturate(1.6);padding:26px 28px;text-align:left}}
.tiles{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:20px;width:1100px}}
.tile{{background:var(--surf);border-radius:30px;padding:36px 30px;display:flex;flex-direction:column;align-items:center;gap:12px;text-align:center;min-width:0}}
.band.alt .tile{{background:var(--bg)}}
.stat{{font-size:84px;font-weight:700;letter-spacing:-.04em;line-height:.95}}
.b-tick{{height:34px;display:flex;align-items:center;padding:0 250px 0 110px;font-size:13px;white-space:nowrap;background:var(--surf)}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:7px}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-size:16px;text-align:right}}
.b-tb th{{font-weight:600;font-size:13.5px;color:var(--muted);padding:10px 12px;border-bottom:1px solid var(--line)}}
.b-tb td{{padding:11px 12px;border-bottom:1px solid var(--line);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb tr.sel td{{color:var(--acc);font-weight:600}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc);font-weight:600}}.b-lab{{font-size:13.5px;font-weight:600;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0;text-align:left}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:50px;border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:500 17px {F};padding:0 14px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:50px;padding:3px;border-radius:12px;background:var(--raised);box-sizing:border-box}}.b-seg span{{display:flex;align-items:center;justify-content:center;border-radius:9px;font-weight:600;color:var(--muted)}}.b-seg span.on{{background:var(--bg);color:var(--ink)}}
.b-btn{{height:50px;padding:0 26px;border-radius:25px;border:0;background:var(--acc);color:var(--on-acc);font:600 17px {F};cursor:pointer;display:inline-flex;align-items:center}}.b-btn.sec{{background:transparent;color:var(--acc);border:1.5px solid var(--acc)}}
.b-sl{{display:grid;grid-template-columns:34px 1fr 78px;gap:14px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line);text-align:left}}
.b-sl b{{font-size:21px;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:6px;font-size:15px;color:var(--muted)}}.b-sl input{{width:100%;accent-color:#0071E3}}.b-sl output{{text-align:right;font-weight:700;font-size:17px}}
.b-greek{{display:flex;flex-direction:column;align-items:center;gap:4px}}.b-greek b{{font-size:44px;font-weight:700;letter-spacing:-.03em}}.b-greek .b-sub{{font-size:14px}}
.b-num{{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center}}.b-num b{{font-size:72px;font-weight:700;letter-spacing:-.04em;line-height:.95}}.b-num span{{font-size:17px;line-height:1.4;color:var(--body);max-width:300px}}
.b-eq{{display:flex;flex-direction:column;align-items:center;gap:8px;padding:22px 0;border-bottom:1px solid var(--line)}}.b-eqn{{font-size:30px;font-weight:600;letter-spacing:-.01em}}
.b-steps{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:18px;width:1100px}}.b-steps li{{background:var(--surf);border-radius:26px;padding:24px 20px;display:flex;flex-direction:column;gap:12px;text-align:left}}
.band.alt .b-steps li{{background:var(--bg)}}.b-steps .b-n{{font-size:40px;font-weight:700;color:var(--acc)}}.b-steps li>span{{display:flex;flex-direction:column;gap:6px}}.b-steps li>span>b{{font-size:18px}}.b-steps li>span>span{{font-size:15px;line-height:1.5;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:flex;gap:60px}}.b-lin li{{display:flex;flex-direction:column;align-items:center;gap:6px}}.b-lin .b-y{{font-size:64px;font-weight:700;letter-spacing:-.03em}}.b-lin li.now .b-y{{color:var(--acc)}}
.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{color:var(--muted)}}
.b-list{{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:10px;font-size:18px;line-height:1.55;color:var(--body);text-align:left;max-width:800px}}
.b-video{{margin:0;width:1100px}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;border-radius:30px;background:var(--ink);display:flex;align-items:center;justify-content:center;cursor:pointer}}.b-video figcaption{{margin-top:14px;font-size:16px;color:var(--muted)}}
.b-person{{background:var(--surf);border-radius:30px;padding:34px 20px;display:flex;flex-direction:column;align-items:center;gap:8px}}.b-person .b-ph{{margin-bottom:8px}}.b-person b{{font-size:22px}}.b-person>span:last-child{{color:var(--muted);font-size:15px}}
.b-refs{{width:980px;text-align:left}}.b-refs h2{{margin:0 0 10px;font-size:28px;font-weight:700}}.b-refs ol{{list-style:none;margin:0 0 36px;padding:0}}.b-refs li{{display:grid;grid-template-columns:48px 1fr;padding:14px 0;border-bottom:1px solid var(--line);font-size:17px;line-height:1.5}}
.b-refs .b-rn{{color:var(--acc);font-weight:600}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{font-size:15px;font-weight:600;padding:8px 16px;border-radius:18px;background:var(--raised)}}.b-chip.on{{background:var(--ink);color:var(--bg)}}
.b-links{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:16px;width:1100px}}.b-links a{{display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center}}.b-links a>span{{display:flex;flex-direction:column}}.b-links b{{font-size:15px}}.b-links a>span>span{{color:var(--muted);font-size:13px}}
.ft{{padding:24px 150px 36px 110px;background:var(--surf);display:flex;justify-content:space-between;font-size:13px;color:var(--muted);border-top:1px solid var(--line)}}
"""

INK = Ink(font=F, size=14, line_w=4, grid="transparent", axis="var(--line)", bar_radius=4)


def gnav(current="Main"):
    items = "".join(f'<a href="{s}.dc.html"{" style=color:var(--ink);font-weight:600" if s == current else ""}>{l}</a>' for s, l, _ in kit.PAGES[1:6])
    return f'<nav class="gnav" aria-label="Sections"><b>Double Heston</b>{items}</nav>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])} {esc(X.STATUS)}.</span><span>{esc(B.FOOT[1])}</span></footer>'


def glow_smile():
    pts = X.D["smile_30d"]
    xs = kit.Scale(80, 120, 60, 1040)
    ys = kit.Scale(14, 27.5, 420, 30)
    body = kit.P([(xs(a), ys(b)) for a, b in pts], "var(--acc)", 60)
    return f'<svg class="glow" width="1100" height="480" viewBox="0 0 1100 480" aria-hidden="true">{body}</svg>'


def band(inner, alt=False):
    return f'<section class="band{" alt" if alt else ""}">{inner}</section>'


def home():
    return f"""
{B.ticker()}
{gnav()}
{band(f'<span class="eyebrow">Double Heston</span><h1 class="hero">Volatility that moves. Twice.</h1><p class="sub">{esc(X.A_SHORT)} {esc(X.A_LONG)}</p><span class="lnks"><a class="pill" href="Model.dc.html">{X.CTA["model"]}</a><a class="lnk" href="Finding.dc.html">{X.CTA["finding"]}</a></span>'
       f'<div class="stage">{glow_smile()}<div class="glass">{B.smile(INK, 1010, 420)}<span class="b-sub" style="font-size:15px">{esc(X.SMILE_CAPTION)}</span></div></div>')}
{band(f'<h2 class="h2">Two clocks. One slow, one fast.</h2><p class="p">{esc(X.TWO_CLOCKS)}</p><div class="tiles"><div class="tile" style="grid-column:span 3">{squircle("slow", 84, fill="var(--raised)", ring=False)}<span class="stat">1.4 yr</span><span class="p">half-life of the slow factor, κ 0.5</span></div><div class="tile" style="grid-column:span 3">{squircle("fast", 84, fill="var(--acc)", ink="var(--on-acc)", ring=False)}<span class="stat">7 wk</span><span class="p">half-life of the fast factor, κ 5.0</span></div><div class="tile" style="grid-column:span 6">{B.skew(INK, 980, 280)}<span class="b-sub">How steep the skew is, by time to expiry, in volatility points.</span></div></div>', alt=True)}
{band(f'<h2 class="h2">{esc(X.TWIST)}</h2><div class="tiles"><div class="tile" style="grid-column:span 2"><span class="stat" style="color:var(--acc)">{X.SHARE * 100:.0f}%</span><span class="p">of 2,400 real NSE surfaces fit equally well with different settings</span></div><div class="tile" style="grid-column:span 2"><span class="stat">{X.RATIO:.1f}×</span><span class="p">further apart than two random parameter sets</span></div><div class="tile" style="grid-column:span 2"><span class="stat">1.80</span><span class="p">recovery skill on simulated data, where 1.00 is guessing</span></div></div><a class="lnk" href="Finding.dc.html">{X.CTA["finding"]}</a>')}
{band(B.page_links('Main', 64), alt=True)}
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{gnav('Market')}
{band(f'<span class="eyebrow">Market</span><h1 class="hero">Real prices. Every stock we model.</h1><p class="sub">{esc(X.MARKET_SUB)}</p>'
       f'<div class="stage"><div class="glass"><div style="display:flex;align-items:baseline;justify-content:space-between"><span><b style="font-size:22px">RELIANCE</b> <span class="b-sub">Reliance Industries</span></span><span style="display:flex;gap:6px"><span class="b-chip">1M</span><span class="b-chip on">3M</span></span></div><div style="display:flex;align-items:baseline;gap:16px;margin:8px 0 14px"><span class="stat" style="font-size:64px">{inr(r[4])}</span><span style="font-size:19px;font-weight:600">{B.rel_change()}</span></div>{B.rel_candles(INK, 1010, 440, 10)}</div></div>')}
{band('<div class="tiles">' + ''.join(f'<div class="tile" style="grid-column:span 2;padding:26px"><span class="b-lab">{k}</span><span style="font-size:34px;font-weight:700">{v}</span></div>' for k, v in B.rel_stats()) + '</div>', alt=True)}
{band(f'<h2 class="h2">The watchlist.</h2><div style="width:1100px">{B.watch_table(names=True, spark=(90, 24))}</div><p class="p">{esc(X.UNIVERSE)}</p>')}
{band(f'<h2 class="h2">NIFTY 50.</h2><div class="stage">{B.nifty_line(INK, 1020, 260)}</div>', alt=True)}
{ft()}
"""


def model():
    K = X.K
    return f"""
{gnav('Model')}
{band(f'<span class="eyebrow">The model</span><h1 class="hero">Price any option.</h1><p class="sub">Pick a listed option. Double Heston prices it. The market says what it paid.</p><div class="stage" style="padding:30px">{B.pricing_form()}</div>')}
{band(f'<div class="tiles"><div class="tile" style="grid-column:span 2"><span class="b-lab">Market close</span><span class="stat">₹{inr(K["market"], 0)}</span><span class="p">IV {K["market_iv"]:.2f}%</span></div><div class="tile" style="grid-column:span 2"><span class="b-lab">Double Heston</span><span class="stat" style="color:var(--acc)">₹{inr(K["dh"], 0)}</span><span class="p">IV {K["dh_iv"]:.2f}%</span></div><div class="tile" style="grid-column:span 2"><span class="b-lab">Monte Carlo check</span><span class="stat">₹{inr(K["mc"], 0)}</span><span class="p">± {K["mc_se"]:.2f}, 20,000 paths</span></div></div><p class="p">{esc(X.MODEL_EXPLAIN)}</p>', alt=True)}
{band(f'<h2 class="h2">The smile, market against model.</h2><div class="stage">{glow_smile()}<div class="glass">{B.market_smile(INK, 1010, 400, 52)}</div></div><div style="width:1100px">{B.chain_table()}</div>')}
{band(f'<h2 class="h2">Ten settings.</h2><p class="p">{esc(X.FELLER_NOTE)}</p><div style="width:1100px;display:grid;grid-template-columns:1fr 1fr;gap:40px"><div><b style="font-size:20px">Slow factor</b><p class="b-sub dn" style="margin:4px 0 0">{esc(X.FELLER["slow"])}</p>{B.sliders("slow")}</div><div><b style="font-size:20px">Fast factor</b><p class="b-sub dn" style="margin:4px 0 0">{esc(X.FELLER["fast"])}</p>{B.sliders("fast")}</div></div><button class="b-btn sec" type="button">Reset to starting settings</button>', alt=True)}
{band(f'<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:20px;width:1100px">{B.greeks()}</div><p class="b-sub" style="margin:0;font-size:14px;max-width:900px">{esc(X.MODEL_SOURCE)}</p>')}
{ft()}
"""


def maths():
    return f"""
{gnav('Maths')}
{band(f'<span class="eyebrow">How it works</span><h1 class="hero">Two variances. One integral.</h1><p class="sub">{esc(X.MATHS_INTRO)}</p>')}
{band(f'<div class="stage"><div class="glass">{B.equations()}</div></div>', alt=True)}
{band(B.steps())}
{band(f'<h2 class="h2">From 1973 to 2009.</h2>{B.lineage()}', alt=True)}
{ft()}
"""


def finding():
    return f"""
{gnav('Finding')}
{band(f'<span class="eyebrow">The finding</span><h1 class="hero">A perfect fit. The wrong settings.</h1><p class="sub">{esc(X.FIND_HEAD)}</p>')}
{band(f'<h2 class="h2">{esc(X.PROOF1_HEAD)}.</h2><p class="p">{esc(X.PROOF1)}</p><div class="tiles">' + ''.join(f'<div class="tile" style="grid-column:span 2">{B.nums([(n, c)])}</div>' for n, c in X.PROOF1_NUMS) + f'</div><p class="p" style="font-size:16px;color:var(--muted)">{esc(X.PROOF1_NET)}</p>', alt=True)}
{band(f'<h2 class="h2">{esc(X.PROOF2_HEAD)}.</h2><p class="p">{esc(X.PROOF2)}</p><div class="stage">{B.hist(INK, 1020, 300)}</div><div class="tiles">' + ''.join(f'<div class="tile" style="grid-column:span 2">{B.nums([(n, c)])}</div>' for n, c in X.PROOF2_NUMS) + '</div>')}
{band(f'<h2 class="h2">Where they disagree.</h2><p class="p">{esc(X.PER_PARAM)}</p><div class="stage" style="background:var(--bg)">{B.bars(INK, 1000)}</div>', alt=True)}
{band(f'<h2 class="h2">One stock, day by day.</h2><span style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center">{B.picks()}</span><p class="p">{esc(X.rel_line())}</p><div class="stage">{B.stock(INK, 1020)}</div>')}
{band(f'<div class="tiles"><div class="tile" style="grid-column:span 3"><span class="stat">{X.G8["median_network_relative"] * 100:.1f}%</span><span class="p">{esc(X.HELDOUT)}</span></div><div class="tile" style="grid-column:span 3"><span class="stat">0 of 210</span><span class="p">{esc(X.BACKTEST)}</span></div></div>', alt=True)}
{ft()}
"""


def about():
    return f"""
{gnav('About')}
{band(f'<span class="eyebrow">About</span><h1 class="hero">{esc(X.ABOUT_HEAD)}</h1>{B.video(icon_fill="#FFFFFF", icon_ink="#1D1D1F")}')}
{band(f'<h2 class="h2">Method and data.</h2>' + ''.join(f'<p class="p">{esc(m)}</p>' for m in X.METHOD), alt=True)}
{band(f'<h2 class="h2">Limits.</h2>{B.bullet_list(X.LIMITS)}<p class="p">{esc(X.ALSO)}</p><a class="lnk" href="https://{X.REPO}">{esc(X.REPO)}</a>')}
{ft()}
"""


def team():
    return f"""
{gnav('Team')}
{band(f'<span class="eyebrow">Team</span><h1 class="hero">The people behind it.</h1><p class="sub">{esc(X.TEAM_INTRO)}</p><div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px;width:1100px">{B.team_cards()}</div>')}
{band(f'<span class="b-lab">Supervisor</span><h2 class="h2" style="font-size:40px">{esc(X.SUPERVISOR[0])}</h2><p class="p">{esc(X.SUPERVISOR[1])}</p><span class="b-lab" style="margin-top:20px">Thanks</span>{B.bullet_list(X.THANKS)}', alt=True)}
{ft()}
"""


def references():
    return f"""
{gnav('References')}
{band(f'<span class="eyebrow">References</span><h1 class="hero">Sources.</h1><p class="sub">The papers behind the model and its methods, and where the data comes from.</p>{B.refs()}')}
{ft()}
"""


DESIGN = Design(
    num=11, slug="glass", name="Glass",
    concept="An Apple product page: huge centred type, alternating bands, one frosted-glass panel over a glowing curve.",
    memorable="The smile chart floating in frosted glass over a soft glow of its own curve.",
    layout="Full-width alternating bands, centred; stats in tiles of different spans; one glass stage per page.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Albert+Sans:wght@400;500;600;700&display=swap",
    display_font=F, body_font=F,
    type_sample="Volatility that moves. Twice.",
    type_note="Albert Sans 700 at 56–86 px with tight tracking for headlines; 500 for subheads; 400 for text.",
    ink=INK, css=CSS, rail_side="r", default_dark=False,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
