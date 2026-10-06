"""14 · Blueprint — each page is a drawing sheet: zone-marked frame, title block, dimensioned charts."""
from __future__ import annotations

import blocks as B
import charts2 as C2
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle, svg

DARK = dict(bg="#0A2A66", surf="#0D3278", raised="#123C8A", line="#6F93D0", grid="#1A438C", ink="#EEF4FF",
            body="#CFDDF7", muted="#9DB6E2", acc="#FFD54A", on_acc="#0A2A66", up="#7CE3A6", down="#FF8F8F",
            on_up="#0A2A66", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")
LIGHT = dict(bg="#F4F8FF", surf="#FFFFFF", raised="#E6EEFB", line="#7F9DD2", grid="#DCE6F7", ink="#0A2A66",
             body="#22407A", muted="#46608F", acc="#1F5FD1", on_acc="#FFFFFF", up="#13804E", down="#C62F2F",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")

A = "Archivo,Helvetica,sans-serif"
N = "'Archivo Narrow',Helvetica,sans-serif"
CSS = f"""
.dh{{background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:24px 24px}}
.sheet{{position:relative;margin:56px 40px 40px 96px;border:2px solid var(--line);padding:0}}
.zone-t,.zone-b{{position:absolute;left:0;right:0;height:22px;display:grid;grid-template-columns:repeat(8,1fr);font-family:{N};font-size:12px;color:var(--muted)}}
.zone-t{{top:-24px}}.zone-b{{bottom:-24px}}.zone-t span,.zone-b span{{text-align:center;border-left:1px solid var(--line)}}
.zone-l{{position:absolute;top:0;bottom:0;left:-24px;width:22px;display:grid;grid-template-rows:repeat(6,1fr);font-family:{N};font-size:12px;color:var(--muted)}}.zone-l span{{display:flex;align-items:center;justify-content:center;border-top:1px solid var(--line)}}
.inner{{padding:40px 44px 44px;display:flex;flex-direction:column;gap:56px}}
.tblock{{align-self:flex-end;display:grid;grid-template-columns:repeat(4,auto);border:2px solid var(--line);font-family:{N};font-size:13px}}
.tblock div{{padding:8px 14px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:2px}}.tblock div:last-child{{border-right:0}}
.tblock span{{color:var(--muted)}}.tblock b{{font-family:{A};font-size:16px;color:var(--ink)}}
.h1{{margin:0;font-family:{A};font-weight:800;font-size:58px;line-height:1.02;letter-spacing:-.01em;text-transform:none}}
.h2{{margin:0;font-family:{A};font-weight:700;font-size:28px}}
.det{{font-family:{N};font-size:15px;color:var(--acc);font-weight:600}}
.lede{{margin:0;font-size:19px;line-height:1.55;color:var(--body);max-width:860px}}
.p{{margin:0;font-size:17.5px;line-height:1.6;color:var(--body)}}
.fr{{border:1px solid var(--line);padding:22px;display:flex;flex-direction:column;gap:14px;min-width:0;background:color-mix(in srgb,var(--bg) 70%,transparent)}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:start}}
.top{{position:absolute;top:0;left:96px;right:250px;height:40px;display:flex;align-items:center;gap:20px;font-family:{N};font-size:14px;color:var(--muted)}}.top b{{font-family:{A};color:var(--ink);font-size:16px}}
.b-tick{{height:40px;display:flex;align-items:center;padding:0 14px;border:1px solid var(--line);font-family:{N};font-size:15px;white-space:nowrap}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti-lab{{color:var(--acc)}}
.b-tb{{width:100%;border-collapse:collapse;font-family:{N};font-size:16px}}
.b-tb th{{text-align:right;font-weight:600;color:var(--muted);padding:8px 10px;border-bottom:1.5px solid var(--line)}}
.b-tb td{{text-align:right;padding:8px 10px;border-bottom:1px dashed var(--line);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb td b{{font-family:{A}}}.b-tb tr.sel td{{color:var(--acc);font-weight:700}}
.b-sub{{color:var(--muted)}}.b-model{{color:var(--acc);font-weight:700}}.b-lab{{font-family:{N};font-size:13.5px;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:46px;border:1.5px solid var(--line);background:transparent;color:var(--ink);font:500 17px {N};padding:0 12px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:46px;border:1.5px solid var(--line)}}.b-seg span{{display:flex;align-items:center;justify-content:center;font-family:{N};font-weight:600}}.b-seg span.on{{background:var(--acc);color:var(--on-acc)}}
.b-btn{{height:48px;padding:0 22px;border:0;background:var(--acc);color:var(--on-acc);font:700 16px {A};cursor:pointer;display:inline-flex;align-items:center}}.b-btn.sec{{background:transparent;color:var(--ink);border:1.5px solid var(--line)}}
.b-sl{{display:grid;grid-template-columns:34px 1fr 78px;gap:14px;align-items:center;padding:10px 0;border-bottom:1px dashed var(--line)}}
.b-sl b{{font-size:19px;color:var(--acc)}}.b-sl label{{display:flex;flex-direction:column;gap:5px;font-family:{N};font-size:14.5px;color:var(--muted)}}.b-sl input{{width:100%;accent-color:#FFD54A}}.b-sl output{{text-align:right;font-family:{N};font-weight:700;font-size:17px}}
.b-greek{{border:1px solid var(--line);padding:14px;display:flex;flex-direction:column;gap:4px}}.b-greek b{{font-family:{A};font-size:30px}}.b-greek .b-sub{{font-family:{N};font-size:14px}}
.b-num{{border:1px solid var(--line);padding:16px;display:flex;flex-direction:column;gap:6px}}.b-num b{{font-family:{A};font-size:44px;font-weight:800;color:var(--acc);line-height:1}}.b-num span{{font-family:{N};font-size:15px;line-height:1.4;color:var(--body)}}
.b-eq{{display:grid;grid-template-columns:260px 1fr;gap:20px;align-items:center;padding:14px 0;border-bottom:1px dashed var(--line)}}.b-eqn{{font-family:{A};font-size:22px;font-weight:500}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:16px}}.b-steps li{{display:grid;grid-template-columns:44px 1fr;gap:10px}}
.b-steps .b-n{{width:32px;height:32px;border:1.5px solid var(--acc);border-radius:16px;display:flex;align-items:center;justify-content:center;font-family:{N};color:var(--acc)}}
.b-steps li>span{{display:flex;flex-direction:column;gap:4px}}.b-steps li>span>b{{font-size:17px}}.b-steps li>span>span{{font-size:16px;line-height:1.55;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}}.b-lin li{{border:1px solid var(--line);padding:16px;display:flex;flex-direction:column;gap:4px}}.b-lin .b-y{{font-family:{A};font-size:38px;font-weight:800}}.b-lin li.now .b-y{{color:var(--acc)}}
.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{font-family:{N};color:var(--muted)}}
.b-list{{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:8px;font-size:17px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:1.5px solid var(--line);background:transparent;display:flex;align-items:center;justify-content:center;cursor:pointer}}.b-video figcaption{{margin-top:10px;font-family:{N};font-size:15px;color:var(--muted)}}
.b-person{{border:1px solid var(--line);padding:16px;display:flex;flex-direction:column;gap:4px}}.b-person .b-ph{{height:150px;border:1px dashed var(--line);display:flex;align-items:center;justify-content:center;margin-bottom:8px}}
.b-person b{{font-size:19px}}.b-person>span:last-child{{font-family:{N};color:var(--muted)}}
.b-refs{{border:1px solid var(--line);padding:18px}}.b-refs h2{{margin:0 0 8px;font-family:{N};font-size:15px;color:var(--acc)}}.b-refs ol{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px}}
.b-refs li{{display:grid;grid-template-columns:44px 1fr;font-size:15.5px;line-height:1.5}}.b-refs .b-rn{{font-family:{N};color:var(--acc)}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{font-family:{N};font-size:14px;padding:4px 10px;border:1px solid var(--line)}}.b-chip.on{{background:var(--acc);color:var(--on-acc);border-color:var(--acc)}}
.b-links{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));border:1.5px solid var(--line)}}.b-links a{{display:flex;flex-direction:column;align-items:center;gap:8px;padding:14px 6px;border-right:1px solid var(--line);text-align:center}}.b-links a:last-child{{border-right:0}}
.b-links a>span{{display:flex;flex-direction:column}}.b-links b{{font-size:14.5px}}.b-links a>span>span{{font-family:{N};color:var(--muted);font-size:12.5px}}
.ft{{padding:0 40px 30px 96px;display:flex;justify-content:space-between;font-family:{N};font-size:13.5px;color:var(--muted)}}
"""

INK = Ink(font=N, size=13.5, line_w=2.2, grid="transparent", axis="var(--line)", text="var(--muted)", strong="var(--ink)", bar_radius=0)

SHEET = {s: i + 1 for i, (s, _, _) in enumerate(kit.PAGES)}


def dim_v(x, y1, y2, label, side=1):
    """Vertical dimension line with arrow ends and a label."""
    t = 7
    return (kit.L(x, y1, x, y2, "var(--acc)", 1.4)
            + f'<path d="M{x - t / 2},{y1 + t} L{x},{y1} L{x + t / 2},{y1 + t}" style="fill:none;stroke:var(--acc);stroke-width:1.4"></path>'
            + f'<path d="M{x - t / 2},{y2 - t} L{x},{y2} L{x + t / 2},{y2 - t}" style="fill:none;stroke:var(--acc);stroke-width:1.4"></path>'
            + kit.T(x + 10 * side, (y1 + y2) / 2 + 5, label, INK, fill="var(--acc)", anchor="start" if side > 0 else "end", weight=700, size=14))


def smile_dim(w=900, h=420):
    pts = X.D["smile_30d"]
    body, xs, ys = kit.line_chart(w, h, [{"pts": pts, "color": "var(--ink)", "w": 2.4}], INK, (80, 120), (14, 27.5),
                                  [80, 90, 100, 110, 120], [16, 20, 24], x_fmt=lambda v: f"{v:.0f}%", y_fmt=lambda v: f"{v:g}%",
                                  refs=[(20, "one fixed volatility, 20%", "var(--muted)")], left=56)
    body += dim_v(xs(80) + 30, ys(pts[0][1]), ys(20), f"Δ {pts[0][1] - 20:.1f} vol pts")
    body += dim_v(xs(120) - 30, ys(20), ys(pts[-1][1]), f"Δ {20 - pts[-1][1]:.1f} vol pts", side=-1)
    body += kit.C(xs(80), ys(pts[0][1]), 5, "var(--acc)") + kit.C(xs(120), ys(pts[-1][1]), 5, "var(--acc)")
    body += kit.T(xs(80) + 10, ys(pts[0][1]) - 12, f"{pts[0][1]:.1f}% at strike 80", INK, fill="var(--ink)", weight=700)
    body += kit.T(xs(120) - 6, ys(pts[-1][1]) + 26, f"{pts[-1][1]:.1f}% at strike 120", INK, fill="var(--ink)", anchor="end", weight=700)
    return svg(w, h, "Implied volatility by strike at 30 days, dimensioned: 6.2 volatility points above a fixed 20% at strike 80, 4.5 below at strike 120", body)


def frame(stem, title, body):
    zt = "".join(f"<span>{i}</span>" for i in range(1, 9))
    zl = "".join(f"<span>{c}</span>" for c in "ABCDEF")
    tb = (f'<div class="tblock"><div><span>Project</span><b>Double Heston</b></div><div><span>Drawing</span><b>{esc(title)}</b></div>'
          f'<div><span>Sheet</span><b>{SHEET[stem]} of 8</b></div><div><span>Data</span><b>NSE close, {X.LAST_DAY}</b></div></div>')
    return (f'<div class="top"><b>DH-2009 drawing set</b><span>{esc(X.STATUS)}</span></div>'
            f'<div class="sheet"><div class="zone-t">{zt}</div><div class="zone-b">{zt}</div><div class="zone-l">{zl}</div>'
            f'<div class="inner">{body}{tb}</div></div>'
            f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>')


def head(h, lede=None):
    return f'<section style="display:flex;flex-direction:column;gap:14px"><h1 class="h1">{esc(h)}</h1>{f"<p class=lede>{esc(lede)}</p>" if lede else ""}</section>'


def det(letter, name):
    return f'<span class="det">Detail {letter}: {esc(name)}</span>'


def home():
    body = f"""
{B.ticker()}
{head(X.Q, X.A_SHORT + ' ' + X.A_LONG + ' ' + X.TWIST)}
<section class="fr">{det('A', 'the smile, 30 days, starting settings')}{smile_dim(1150, 440)}</section>
<section class="two"><div class="fr">{det('B', 'shock remaining over time')}{C2.decay(INK, 540, 300, slow_col='var(--ink)', fast_col='var(--acc)')}<p class="p" style="font-size:16px">{esc(X.TWO_CLOCKS)}</p></div>
  <div class="fr">{det('C', 'where equally good fits disagree')}{B.bars(INK, 540, row_h=28, label_w=200, legend=False, compact=True, only=('kappa_s', 'kappa_f', 'sigma_s', 'rho_s', 'theta_s', 'v0_s', 'v0_f'))}<p class="p" style="font-size:16px">{esc(X.FINDING_LINE)} {esc(X.FINDING_SUB)}</p></div></section>
{B.page_links('Main', 40, fill='transparent')}
"""
    return frame("Main", "General arrangement", body)


def market():
    r = X.REL_LAST
    body = f"""
{head('Market', X.MARKET_SUB)}
<section class="fr">{det('A', 'RELIANCE, daily, 62 trading days')}<div style="display:flex;align-items:baseline;gap:16px"><span class="h1" style="font-size:48px">{inr(r[4])}</span><span style="font-size:18px;font-weight:700">{B.rel_change()}</span><span style="margin-left:auto;display:flex;gap:6px"><span class="b-chip">1M</span><span class="b-chip on">3M</span></span></div>{B.rel_candles(INK, 1150, 460, 8)}
<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px">{''.join(f'<div class="b-num" style="padding:10px 12px"><span>{k}</span><b style="font-size:22px;color:var(--ink)">{v}</b></div>' for k, v in B.rel_stats())}</div></section>
<section class="two"><div class="fr">{det('B', 'watchlist')}{B.watch_table(spark=(70, 22))}</div><div class="fr">{det('C', 'NIFTY 50, closing level')}{B.nifty_line(INK, 540, 240)}<p class="p" style="font-size:16px">{esc(X.UNIVERSE)}</p></div></section>
"""
    return frame("Market", "Market data", body)


def model():
    K_ = X.K
    body = f"""
{head('The model', 'Pick a listed option, price it with Double Heston, and set it against what the market paid.')}
<section class="fr">{det('A', 'contract')}{B.pricing_form()}</section>
<section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px">{B.nums([(f'₹{inr(K_["market"])}', f'market close, IV {K_["market_iv"]:.2f}%'), (f'₹{inr(K_["dh"])}', f'Double Heston, IV {K_["dh_iv"]:.2f}%'), (f'₹{inr(K_["mc"])}', f'Monte Carlo, ± {K_["mc_se"]:.2f}'), (f'+₹{inr(X.GAP)}', 'model minus market')])}</section>
<p class="lede">{esc(X.MODEL_EXPLAIN)}</p>
<section class="two"><div class="fr">{det('B', 'smile, market against model')}{B.market_smile(INK, 540, 340, 50)}</div><div class="fr">{det('C', 'option chain')}{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div></section>
<section class="two"><div class="fr">{det('D', 'slow factor')}<span class="dn">{esc(X.FELLER['slow'])}</span>{B.sliders('slow')}</div><div class="fr">{det('E', 'fast factor')}<span class="dn">{esc(X.FELLER['fast'])}</span>{B.sliders('fast')}</div></section>
<div style="display:flex;justify-content:space-between;align-items:center"><span class="b-sub">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div>
<section style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px">{B.greeks()}</section>
<span class="b-sub" style="font-size:14px">{esc(X.MODEL_SOURCE)}</span>
"""
    return frame("Model", "Pricing an option", body)


def maths():
    body = f"""
{head('How it works', X.MATHS_INTRO)}
<section class="fr">{det('A', 'governing equations')}{B.equations()}</section>
<section class="two"><div class="fr">{det('B', 'procedure')}{B.steps()}</div><div class="fr">{det('C', 'skew by time to expiry')}{B.skew(INK, 540, 300)}<p class="p" style="font-size:16px">Half-lives: fast factor {X.HL['fast_days']:.0f} days, slow factor {X.HL['slow_years']:.1f} years.</p></div></section>
<section class="fr">{det('D', 'lineage')}{B.lineage()}</section>
"""
    return frame("Maths", "The model, equations", body)


def finding():
    body = f"""
{head(X.FIND_HEAD)}
<section class="two"><div class="fr">{det('A', X.PROOF1_HEAD.lower())}<p class="p">{esc(X.PROOF1)}</p><div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">{B.nums(X.PROOF1_NUMS)}</div><p class="p" style="font-size:15px;color:var(--muted)">{esc(X.PROOF1_NET)}</p></div>
  <div class="fr">{det('B', X.PROOF2_HEAD.lower())}<p class="p">{esc(X.PROOF2)}</p><div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">{B.nums(X.PROOF2_NUMS)}</div></div></section>
<section class="fr">{det('C', 'distance between equally good fits, 2,379 surfaces')}{B.hist(INK, 1150, 290)}</section>
<section class="two"><div class="fr">{det('D', 'by setting')}{B.bars(INK, 540, label_w=200)}</div><div class="fr" style="justify-content:center"><p class="p">{esc(X.PER_PARAM)}</p></div></section>
<section class="fr">{det('E', 'RELIANCE, 60 trading days')}<span style="display:flex;gap:6px">{B.picks()}</span><p class="p">{esc(X.rel_line())}</p>{B.stock(INK, 1150)}</section>
<section class="two">{B.nums([(f'{X.G8["median_network_relative"] * 100:.1f}%', X.HELDOUT), ('0 of 210', X.BACKTEST)])}</section>
"""
    return frame("Finding", "The finding", body)


def about():
    body = f"""
{head(X.ABOUT_HEAD)}
<section class="two"><div class="fr">{det('A', 'video')}{B.video()}</div><div class="fr">{det('B', 'method and data')}{''.join(f'<p class="p" style="font-size:16px">{esc(m)}</p>' for m in X.METHOD)}</div></section>
<section class="two"><div class="fr">{det('C', 'limits')}{B.bullet_list(X.LIMITS)}</div><div class="fr">{det('D', 'also explored')}<p class="p">{esc(X.ALSO)}</p><a class="b-model" href="https://{X.REPO}">{esc(X.REPO)}</a></div></section>
"""
    return frame("About", "About the project", body)


def team():
    body = f"""
{head(X.TEAM_HEAD, X.TEAM_INTRO)}
<section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px">{B.team_cards()}</section>
<section class="two"><div class="fr">{det('A', 'supervisor')}<b style="font-size:20px">{esc(X.SUPERVISOR[0])}</b><span class="b-sub">{esc(X.SUPERVISOR[1])}</span></div><div class="fr">{det('B', 'thanks')}{B.bullet_list(X.THANKS)}</div></section>
"""
    return frame("Team", "Team", body)


def references():
    body = f"""
{head('References', 'The papers behind the model and its methods, and where the data comes from.')}
<section class="two">{B.refs()}</section>
"""
    return frame("References", "References", body)


DESIGN = Design(
    num=14, slug="blueprint", name="Blueprint",
    concept="Every page is an engineering drawing sheet: zone-marked frame, title block, details, dimensioned charts.",
    memorable="The smile chart with dimension callouts measuring the skew: Δ 6.2 vol pts above 20% at strike 80.",
    layout="A bordered sheet with zone numbers and letters; framed 'details'; a title block with sheet n of 8.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;800&family=Archivo+Narrow:wght@400;500;600;700&display=swap",
    display_font=A, body_font=A,
    type_sample="Detail A: the smile, Δ 6.2 vol pts",
    type_note="Archivo 700–800 for titles and numbers; Archivo Narrow for labels, dimensions, tables and axes.",
    ink=INK, css=CSS, rail_side="l", default_dark=True,
    icon_fills={"model": {"fill": "var(--acc)", "ink": "var(--on-acc)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
