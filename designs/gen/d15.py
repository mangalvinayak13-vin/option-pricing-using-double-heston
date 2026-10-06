"""15 · Ferro — monochrome chrome and liquid black; the smile as a glossy ferrofluid tube."""
from __future__ import annotations

import json
import math
from pathlib import Path

import blocks as B
import content as X
import kit
from design import Design, check_tokens
from kit import Ink, arrow, esc, inr, squircle, svg

LIGHT = dict(bg="#E9EBEE", surf="#F5F6F8", raised="#DCDFE4", line="#B4BAC3", grid="#D3D7DD", ink="#0A0A0A",
             body="#2E3136", muted="#50555D", acc="#0A0A0A", on_acc="#F5F6F8", up="#127A3E", down="#B3261E",
             on_up="#FFFFFF", track_off="#E3E3E6", ferro="#0A0A0B", ferro_hi="#A9AFB6")
DARK = dict(bg="#050505", surf="#121314", raised="#1C1D1F", line="#36383C", grid="#1A1B1D", ink="#F2F2F2",
            body="#C9CBCF", muted="#9A9DA3", acc="#D9DCE1", on_acc="#050505", up="#3DDC84", down="#FF5A5A",
            on_up="#04120B", track_off="#39393D", ferro="#050505", ferro_hi="#F2F4F8")

SO = "Sora,sans-serif"
EP = "Epilogue,Helvetica,sans-serif"
CSS = f"""
.t-light{{--plate:linear-gradient(180deg,#FBFCFD 0%,#E1E5EA 48%,#C9CFD7 100%);--tube:#0A0A0B;--tubehi:rgba(255,255,255,.85);--liq-top:#3B3F45;--dots:#FFFFFF}}
.t-dark{{--plate:linear-gradient(180deg,#26282C 0%,#15161A 55%,#0B0C0E 100%);--tube:#000000;--tubehi:rgba(255,255,255,.75);--liq-top:#34373C;--dots:#FFFFFF}}
.top{{height:60px;display:flex;align-items:center;gap:22px;padding:0 250px 0 72px;font-size:14.5px;color:var(--muted)}}.top b{{font-family:{SO};font-weight:700;font-size:18px;color:var(--ink);letter-spacing:.02em}}
.plate{{margin:0 150px 0 72px;border-radius:6px;background:var(--plate);box-shadow:inset 0 1px 0 rgba(255,255,255,.7),inset 0 -1px 0 rgba(0,0,0,.25),0 1px 0 var(--line);padding:48px 48px 36px;display:grid;grid-template-columns:5fr 7fr;gap:40px;align-items:center}}
.pg{{padding:64px 150px 110px 72px;display:flex;flex-direction:column;gap:84px}}
.h1{{margin:0;font-family:{SO};font-weight:700;font-size:60px;line-height:1.02;letter-spacing:-.03em}}
.h2{{margin:0;font-family:{SO};font-weight:600;font-size:34px;line-height:1.1;letter-spacing:-.02em}}
.lede{{margin:0;font-size:20px;line-height:1.55;color:var(--body);max-width:860px}}
.p{{margin:0;font-size:18px;line-height:1.6;color:var(--body)}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:start}}
.ridge{{height:46px;display:block}}
.b-tick{{height:36px;display:flex;align-items:center;padding:0 250px 0 72px;font-size:14px;white-space:nowrap;border-bottom:1px solid var(--line)}}
.b-tick-in{{flex:1;min-width:0;display:flex;gap:26px;overflow:hidden}}.b-ti{{display:inline-flex;gap:8px}}.b-ti-lab{{color:var(--muted)}}
.b-tb{{width:100%;border-collapse:collapse;font-size:16px}}
.b-tb th{{text-align:right;font-weight:600;font-size:13.5px;color:var(--muted);padding:10px;border-bottom:2px solid var(--ink)}}
.b-tb td{{text-align:right;padding:10px;border-bottom:1px solid var(--line);white-space:nowrap}}
.b-tb th:first-child,.b-tb td:first-child{{text-align:left}}.b-tb tr.sel td{{background:var(--ink);color:var(--bg);font-weight:700}}.b-tb tr.sel td *{{color:var(--bg)}}
.b-sub{{color:var(--muted)}}.b-model{{font-weight:800;text-decoration:underline;text-underline-offset:4px}}.b-lab{{font-size:13.5px;font-weight:600;color:var(--muted)}}
.b-form{{display:grid;grid-template-columns:1.3fr 1.3fr 1fr 1fr auto;gap:14px;align-items:end;margin:0}}
.b-form label,.b-form fieldset{{display:flex;flex-direction:column;gap:6px;border:0;margin:0;padding:0;min-width:0}}
.b-form select,.b-form input{{height:50px;border-radius:4px;border:1px solid var(--line);background:var(--surf);color:var(--ink);font:500 17px {EP};padding:0 14px}}
.b-seg{{display:grid;grid-template-columns:1fr 1fr;height:50px;border:1px solid var(--line);border-radius:4px;overflow:hidden}}.b-seg span{{display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--muted)}}.b-seg span.on{{background:var(--ink);color:var(--bg)}}
.b-btn{{height:52px;padding:0 26px;border-radius:4px;border:0;background:var(--ink);color:var(--bg);font:700 17px {EP};cursor:pointer;display:inline-flex;align-items:center}}.b-btn.sec{{background:transparent;color:var(--ink);border:1.5px solid var(--ink)}}
.b-sl{{display:grid;grid-template-columns:34px 1fr 78px;gap:14px;align-items:center;padding:11px 0;border-bottom:1px solid var(--line)}}
.b-sl b{{font-family:{SO};font-size:19px}}.b-sl label{{display:flex;flex-direction:column;gap:5px;font-size:15px;color:var(--muted)}}.b-sl input{{width:100%;accent-color:#0A0A0A}}.b-sl output{{text-align:right;font-weight:700;font-size:17px}}
.b-greek{{display:flex;flex-direction:column;gap:4px;padding:16px;background:var(--surf);border-radius:4px}}.b-greek b{{font-family:{SO};font-size:32px;font-weight:700}}
.b-num{{display:flex;flex-direction:column;gap:8px}}.b-num b{{font-family:{SO};font-size:58px;font-weight:700;letter-spacing:-.03em;line-height:1}}.b-num span{{font-size:16px;line-height:1.45;color:var(--body)}}
.b-eq{{display:flex;flex-direction:column;gap:8px;padding:18px 0;border-bottom:1px solid var(--line)}}.b-eqn{{font-family:{SO};font-size:24px;font-weight:500;line-height:1.45}}
.b-steps{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:20px}}.b-steps li{{display:grid;grid-template-columns:50px 1fr;gap:12px}}
.b-steps .b-n{{font-family:{SO};font-size:34px;font-weight:700;line-height:1}}.b-steps li>span{{display:flex;flex-direction:column;gap:5px}}.b-steps li>span>b{{font-size:18px}}.b-steps li>span>span{{font-size:16.5px;line-height:1.55;color:var(--body)}}
.b-lin{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:30px}}.b-lin li{{display:flex;flex-direction:column;gap:6px}}.b-lin .b-y{{font-family:{SO};font-size:52px;font-weight:700}}.b-lin li>span{{display:flex;flex-direction:column}}.b-lin li>span>span{{color:var(--muted)}}
.b-list{{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:10px;font-size:17.5px;line-height:1.55;color:var(--body)}}
.b-video{{margin:0}}.b-video button{{width:100%;aspect-ratio:16/9;border:0;border-radius:6px;background:var(--plate);display:flex;align-items:center;justify-content:center;cursor:pointer}}.b-video figcaption{{margin-top:12px;font-size:15px;color:var(--muted)}}
.b-person{{display:flex;flex-direction:column;gap:6px}}.b-person .b-ph{{aspect-ratio:1/1;border-radius:6px;background:var(--plate);display:flex;align-items:center;justify-content:center;margin-bottom:10px}}.b-person b{{font-family:{SO};font-size:21px}}.b-person>span:last-child{{color:var(--muted);font-size:15px}}
.b-refs h2{{margin:0 0 10px;font-family:{SO};font-size:24px}}.b-refs ol{{list-style:none;margin:0 0 34px;padding:0}}.b-refs li{{display:grid;grid-template-columns:48px 1fr;padding:12px 0;border-bottom:1px solid var(--line);font-size:16.5px;line-height:1.5}}.b-refs .b-rn{{font-family:{SO};font-weight:700}}.b-refs .b-rt{{color:var(--body)}}
.b-chip{{font-size:14px;font-weight:700;padding:7px 14px;border-radius:4px;border:1px solid var(--line)}}.b-chip.on{{background:var(--ink);color:var(--bg);border-color:var(--ink)}}
.b-links{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:22px}}.b-links a{{display:flex;align-items:center;gap:14px}}.b-links a>span{{display:flex;flex-direction:column}}.b-links b{{font-size:17px}}.b-links a>span>span{{color:var(--muted);font-size:14px}}
.ft{{padding:24px 150px 36px 72px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-size:14px;color:var(--muted)}}
"""

INK = Ink(font=EP, size=13.5, line_w=3, grid="var(--grid)", axis="var(--ink)", model="var(--ink)", ref="var(--muted)", bar_radius=2)


def tube_smile(w=720, h=420, left=52):
    """The smile as a glossy black tube: a thick dark stroke with a thin specular highlight on top."""
    pts = X.D["smile_30d"]
    xs, ys = kit.Scale(80, 120, left, w - 16), kit.Scale(14, 27.5, h - 36, 20)
    out = []
    for v in (16, 20, 24):
        out.append(kit.L(left, ys(v), w - 16, ys(v), "var(--line)", 1, "2 6" if v != 20 else None))
        out.append(kit.T(left - 10, ys(v) + 4, f"{v}%", INK, anchor="end"))
    for k in (80, 90, 100, 110, 120):
        out.append(kit.T(xs(k), h - 10, f"{k}%", INK, anchor="middle"))
    out.append(kit.T(w - 16, ys(20) - 10, "one fixed volatility, 20%", INK, anchor="end"))
    line = [(xs(a), ys(b)) for a, b in pts]
    out.append(kit.P(line, "var(--tube)", 16))
    out.append(kit.P([(x, y - 4) for x, y in line], "var(--tubehi)", 2.2))
    out.append(kit.T(xs(80) + 16, ys(pts[0][1]) - 20, f"Double Heston, {pts[0][1]:.1f}% at strike 80", INK, fill="var(--ink)", weight=700))
    out.append(kit.T(xs(120) - 4, ys(pts[-1][1]) + 34, f"{pts[-1][1]:.1f}% at strike 120", INK, fill="var(--ink)", anchor="end", weight=700))
    return svg(w, h, "Implied volatility by strike at 30 days drawn as a glossy black tube: from 26.2% at strike 80 to 15.5% at strike 120; one fixed volatility is 20%", "".join(out))


# ---- one real surface, fitted twice (ferro_pair.py / ferro_curves.py re-run the research's own multi-start fit)
PAIR = json.loads((Path(__file__).resolve().parent / "ferro_pair.json").read_text())
FA, FB = PAIR["a"], PAIR["b"]
SPOT = PAIR["spot"]
ERR_A, ERR_B = PAIR["a_rmse"] * SPOT, PAIR["b_rmse"] * SPOT
TERM = PAIR["term"]
HI = dict(zip(PAIR["names"], PAIR["phys_hi"]))


def _t(k, day):
    return TERM[k][TERM["days"].index(day)] * 100


def half_life(kappa):
    d = math.log(2) / kappa * 365
    return f"{d / 365:.1f} yr" if d >= 300 else f"{d:.0f} days"


GAP_1Y = _t("a", 365) - _t("b", 365)
PAIR_LEDE = (f"Double Heston prices options by letting volatility move, and it fits real NSE prices well. "
             f"Here is Bharti Airtel's option surface at the close on 21 Aug 2026, fitted twice. Both fits miss the "
             f"market by ₹{ERR_A:.2f} an option on average. One says a volatility shock takes "
             f"{half_life(FA['kappa_s'])} to fade by half; the other says {half_life(FB['kappa_f'])} to "
             f"{half_life(FB['kappa_s'])}.")
PART_HEAD = f"Where the market trades, they agree. A year out, they're {GAP_1Y:.1f} points apart."
PART = (f"That day Bharti Airtel had options expiring in 4 and 39 days, and both fits price them alike. Ask them "
        f"about a one-year option, which isn't traded, and fit A says {_t('a', 365):.1f}% volatility while fit B says "
        f"{_t('b', 365):.1f}%. The prices give no reason to prefer either.")
TYPICAL = (f"This surface had {PAIR['equivalents']} equally good fits out of 16 starts, and their spread, "
           f"{PAIR['median_dispersion']:.2f}, is the median of all 2,400 surfaces. It is the typical case, not the worst.")
MAG_NOTE = ("Spike height is the size of each setting on its own scale. * pressed against the fit's upper search "
            "limit for that setting.")

COLS = [  # (key, header, height 0-1, value text)
    ("kappa", "Speed back to normal", lambda v: math.log(v / 0.1) / math.log(300), lambda v: f"half-life {half_life(v)}"),
    ("theta", "Long-run level", lambda v: math.sqrt(max(v, 0)) / 0.7, lambda v: f"{math.sqrt(max(v, 0)) * 100:.0f}% vol"),
    ("sigma", "Volatility of volatility", lambda v: v, lambda v: f"{v:.2f}"),
    ("rho", "Link to price moves", lambda v: (v + 1) / 2, lambda v: f"{v:+.2f}"),
    ("v0", "Today's level", lambda v: math.sqrt(max(v, 0)) / 0.3, lambda v: f"{math.sqrt(max(v, 0)) * 100:.1f}% vol"),
]


def spike(cx, base, h, half_w, fill="var(--tube)", hi=True):
    """One ferrofluid spike: concave flanks rising to a point, with a thin specular line on the left flank."""
    h = max(h, 4)
    top = base - h
    d = (f"M{cx - half_w:.1f},{base:.1f} C{cx - half_w * .35:.1f},{base - 2:.1f} {cx - 3:.1f},{base - h * .62:.1f} "
         f"{cx:.1f},{top:.1f} C{cx + 3:.1f},{base - h * .62:.1f} {cx + half_w * .35:.1f},{base - 2:.1f} {cx + half_w:.1f},{base:.1f} Z")
    out = f'<path d="{d}" style="fill:{fill};stroke:var(--ferro-hi);stroke-opacity:.55;stroke-width:1"></path>'
    if hi and h > 14:
        out += (f'<path d="M{cx - 2.2:.1f},{top + 6:.1f} C{cx - 3.5:.1f},{base - h * .5:.1f} {cx - half_w * .28:.1f},{base - 6:.1f} '
                f'{cx - half_w * .55:.1f},{base - 2:.1f}" style="fill:none;stroke:var(--tubehi);stroke-width:1.4;opacity:.7"></path>')
    return out


def dotted(pts, gap):
    """Fit B: white dots ringed in the liquid's black, readable on the plate and on the liquid alike."""
    return (kit.P(pts, "var(--tube)", 7.5, f"0.1 {gap}") + kit.P(pts, "var(--dots)", 3.6, f"0.1 {gap}"))


def pool(w=700, h=430, left=54, gid="pool"):
    """The 39-day smile as a pool of ferrofluid: fit A is the liquid, fit B rides it dotted, market quotes are rings."""
    sd = PAIR["smile_dense"]
    xs, ys = kit.Scale(0.90, 1.10, left, w - 14), kit.Scale(14, 18, h - 44, 30)
    base = ys(14)
    out = [f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--liq-top)"></stop>'
           f'<stop offset="1" style="stop-color:var(--tube)"></stop></linearGradient></defs>']
    for v in (15, 16, 17, 18):
        out.append(kit.L(left, ys(v), w - 14, ys(v), "var(--line)", 1, "2 6"))
        out.append(kit.T(left - 10, ys(v) + 4, f"{v}%", INK, anchor="end"))
    for m in (0.90, 0.95, 1.00, 1.05, 1.10):
        out.append(kit.T(xs(m), h - 18, f"{m * 100:.0f}%", INK, anchor="middle"))
    out.append(kit.T((left + w - 14) / 2, h - 1, "strike, as % of the share price", INK, anchor="middle"))
    a = [(xs(m), ys(v * 100)) for m, v in zip(sd["m"], sd["a"]) if v]
    b = [(xs(m), ys(v * 100)) for m, v in zip(sd["m"], sd["b"]) if v]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in a) + f" {a[-1][0]:.1f},{base:.1f} {a[0][0]:.1f},{base:.1f}"
    out.append(f'<polygon points="{poly}" style="fill:url(#{gid})"></polygon>')
    out.append(kit.P([(x, y + 3) for x, y in a], "var(--tubehi)", 2))
    out.append(dotted(b, 8))
    for s in PAIR["slots"]:
        if s["rank"] != 2 or s["obs_iv"] is None:
            continue
        otm = (s["type"] == "put") == (s["moneyness"] <= 1.0)
        if otm:
            out.append(kit.C(xs(s["moneyness"]), ys(s["obs_iv"] * 100), 6.5, "var(--surf)", "var(--ink)", 2.2))
    lx = left + 10
    out.append(kit.C(lx + 6, 14, 6, "var(--surf)", "var(--ink)", 2))
    out.append(kit.T(lx + 20, 19, "market close, 39-day options", INK, fill="var(--ink)"))
    out.append(kit.R(lx + 250, 7, 26, 14, "var(--tube)", rx=3))
    out.append(kit.T(lx + 284, 19, "fit A", INK, fill="var(--ink)", weight=700))
    out.append(dotted([(lx + 340, 14), (lx + 368, 14)], 8))
    out.append(kit.T(lx + 376, 19, "fit B", INK, fill="var(--ink)", weight=700))
    return svg(w, h, "Bharti Airtel 39-day implied volatility by strike: market quotes, and two different Double Heston fits whose curves lie on top of each other", "".join(out))


def magnets(w=1218, row_h=150, label_w=150, which=(("Fit A", FA), ("Fit B", FB))):
    """The ten settings of each fit as a strip of spikes, slow factor then fast factor, same columns for both fits."""
    cw = (w - label_w) / 10
    top = 66
    out = []
    for g, (lab, x0) in enumerate((("Slow factor", 0), ("Fast factor", 5))):
        gx = label_w + x0 * cw
        out.append(kit.T(gx + 8, 16, lab, INK, fill="var(--ink)", weight=700, size=15))
        out.append(kit.L(gx + 8, 24, gx + 5 * cw - 8, 24, "var(--ink)", 1.5))
    for i in range(10):
        _, head, *_ = COLS[i % 5]
        words = head.split(" ")
        l1 = " ".join(words[:(len(words) + 1) // 2]) if len(words) > 2 else head
        l2 = " ".join(words[(len(words) + 1) // 2:]) if len(words) > 2 else ""
        out.append(kit.T(label_w + i * cw + cw / 2, 40 if l2 else 48, l1, INK, anchor="middle", size=12.5))
        if l2:
            out.append(kit.T(label_w + i * cw + cw / 2, 55, l2, INK, anchor="middle", size=12.5))
    for r, (lab, fit) in enumerate(which):
        base = top + (r + 1) * row_h - 34
        out.append(f'<text x="0" y="{base - 40:.1f}" style="fill:var(--ink);font-family:{SO};font-size:22px;font-weight:700">{lab}</text>')
        err = ERR_A if fit is FA else ERR_B
        out.append(kit.T(0, base - 16, f"misses by ₹{err:.2f}", INK, size=13))
        out.append(kit.L(label_w, base, w, base, "var(--line)", 1))
        for i in range(10):
            key, _, hfun, vfun = COLS[i % 5]
            name = f"{key}_{'s' if i < 5 else 'f'}"
            v = fit[name]
            cx = label_w + i * cw + cw / 2
            out.append(spike(cx, base, max(0.0, min(1.0, hfun(v))) * (row_h - 50), cw * 0.34))
            star = "*" if abs(v - HI[name]) < 1e-3 * max(1, abs(HI[name])) else ""
            out.append(kit.T(cx, base + 20, vfun(v) + star, INK, anchor="middle", fill="var(--ink)", weight=600, size=13))
    return svg(w, top + len(which) * row_h + 6, "The ten settings of two equally good fits drawn as spikes; the two strips look very different", "".join(out))


def parting(w=1218, h=420, left=56, right=150):
    """At-the-money volatility from 4 days to 2 years under both fits; the traded expiries are shaded."""
    xs, ys = kit.Scale(4, 730, left, w - right, log=True), kit.Scale(8, 46, h - 40, 16)
    out = [kit.R(xs(4), 16, xs(39) - xs(4), h - 56, "var(--raised)"),
           kit.T(xs(4) + 10, 36, "traded that day", INK, fill="var(--ink)", weight=700),
           kit.T(xs(4) + 10, 54, "4 and 39 days", INK)]
    for v in (10, 20, 30, 40):
        out.append(kit.L(left, ys(v), w - right, ys(v), "var(--line)", 1, "2 6"))
        out.append(kit.T(left - 10, ys(v) + 4, f"{v}%", INK, anchor="end"))
    for dd, lab in ((4, "4 days"), (39, "39 days"), (90, "3 months"), (180, "6 months"), (365, "1 year"), (730, "2 years")):
        out.append(kit.T(xs(dd), h - 14, lab, INK, anchor="middle"))
    a = [(xs(dd), ys(v * 100)) for dd, v in zip(TERM["days"], TERM["a"])]
    b = [(xs(dd), ys(v * 100)) for dd, v in zip(TERM["days"], TERM["b"])]
    out.append(kit.P(a, "var(--ferro-hi)", 13).replace("stroke-width:13", "stroke-width:13;opacity:.45"))
    out.append(kit.P(a, "var(--tube)", 10))
    out.append(kit.P([(x, y - 2.5) for x, y in a], "var(--tubehi)", 1.8))
    out.append(dotted(b, 10))
    # market at-the-money quotes (average of the at-the-money call and put implied vols)
    for rank, dd in ((1, 4), (2, 39)):
        vs = [s["obs_iv"] for s in PAIR["slots"] if s["rank"] == rank and abs(s["moneyness"] - 1) < 0.01 and s["obs_iv"]]
        out.append(kit.C(xs(dd), ys(sum(vs) / len(vs) * 100), 6.5, "var(--surf)", "var(--ink)", 2.2))
    x1 = xs(365)
    out.append(kit.L(x1, ys(_t("a", 365)) + 10, x1, ys(_t("b", 365)) - 10, "var(--ink)", 1.5, "3 4"))
    out.append(kit.T(x1 + 12, (ys(_t("a", 365)) + ys(_t("b", 365))) / 2 + 5, f"{GAP_1Y:.1f} points", INK, fill="var(--ink)", weight=700, size=16))
    ea, eb = a[-1], b[-1]
    out.append(kit.T(ea[0] + 16, ea[1] + 5, f"fit A {TERM['a'][-1] * 100:.1f}%", INK, fill="var(--ink)", weight=700, size=15))
    out.append(kit.T(eb[0] + 16, eb[1] + 5, f"fit B {TERM['b'][-1] * 100:.1f}%", INK, fill="var(--ink)", weight=700, size=15))
    out.append(kit.T(eb[0] + 16, eb[1] + 23, "at 2 years", INK))
    out.append(kit.C(xs(60), 30, 6, "var(--surf)", "var(--ink)", 2))
    out.append(kit.T(xs(60) + 14, 35, "market, at the money", INK))
    return svg(w, h, f"At-the-money volatility by time to expiry for two equally good fits: equal on the traded 4- and 39-day expiries, {GAP_1Y:.1f} points apart at one year", "".join(out))


def board_all(w=1218, row_h=58, label_w=250):
    """All six equally good fits, setting by setting, on natural scales. Bunched spikes: pinned down. Scattered: not."""
    right = 70
    tw = w - label_w - right
    scales = {
        "kappa": (kit.Scale(0.1, 30, 0, tw, log=True), [(0.1, "6.9 yr"), (1, "8 months"), (10, "25 days"), (30, "8 days")], lambda v: v),
        "theta": (kit.Scale(0, 70, 0, tw), [(0, "0%"), (35, "35%"), (70, "70%")], lambda v: math.sqrt(max(v, 0)) * 100),
        "sigma": (kit.Scale(0, 1, 0, tw), [(0, "0"), (0.5, "0.5"), (1, "1")], lambda v: v),
        "rho": (kit.Scale(-1, 1, 0, tw), [(-1, "−1"), (0, "0"), (1, "+1")], lambda v: v),
        "v0": (kit.Scale(0, 30, 0, tw), [(0, "0%"), (15, "15%"), (30, "30%")], lambda v: math.sqrt(max(v, 0)) * 100),
    }
    names = {"kappa": "Speed back to normal (half-life)", "theta": "Long-run level (vol)", "sigma": "Volatility of volatility",
             "rho": "Link to price moves", "v0": "Today's level (vol)"}
    out, y = [], 0
    for g, suf in (("Slow factor", "s"), ("Fast factor", "f")):
        out.append(kit.T(0, y + 22, g, INK, fill="var(--ink)", weight=700, size=16))
        y += 34
        for key in ("kappa", "theta", "sigma", "rho", "v0"):
            sc, ticks, conv = scales[key]
            base = y + row_h - 18
            out.append(kit.T(0, base - 4, names[key], INK, fill="var(--ink)", size=14))
            out.append(kit.L(label_w, base, label_w + tw, base, "var(--line)", 1))
            for tv, tl in ticks:
                out.append(kit.T(label_w + sc(tv), base + 16, tl, INK, anchor="middle", size=11.5))
            vals = sorted((conv(e[f"{key}_{suf}"]) for e in PAIR["all_equivalent"]))
            for v in vals:
                out.append(spike(label_w + sc(min(max(v, sc.d0), sc.d1)), base, row_h - 26, 9, hi=False))
            lo, hi = sc(min(max(vals[0], sc.d0), sc.d1)), sc(min(max(vals[-1], sc.d0), sc.d1))
            out.append(kit.T(label_w + tw + 16, base - 4, "pinned" if hi - lo < tw * 0.12 else "loose", INK,
                             fill="var(--ink)" if hi - lo >= tw * 0.12 else "var(--muted)", weight=700, size=13))
            y += row_h
        y += 14
    return svg(w, y, "Each of the six equally good fits for Bharti Airtel on 21 Aug 2026, drawn as a spike on each setting's scale", "".join(out))


def ridge(w=1218):
    """A horizontal row of ferrofluid spikes, used as a section divider."""
    parts = []
    n = 26
    step = w / n
    for i in range(n):
        cx = step * (i + 0.5)
        d = abs(i - n / 2) / (n / 2)
        hgt = 10 + 26 * (1 - d ** 1.4)
        parts.append(f"L{cx - step * 0.42:.1f},44 C{cx - step * 0.16:.1f},40 {cx - 3:.1f},{44 - hgt * 0.7:.1f} {cx:.1f},{44 - hgt:.1f} "
                     f"C{cx + 3:.1f},{44 - hgt * 0.7:.1f} {cx + step * 0.16:.1f},40 {cx + step * 0.42:.1f},44")
    d_ = "M0,46 " + " ".join(parts) + f" L{w},46 Z"
    return (f'<svg class="ridge" width="{w}" height="46" viewBox="0 0 {w} 46" aria-hidden="true">'
            f'<path d="{d_}" style="fill:var(--tube);stroke:var(--ferro-hi);stroke-opacity:.4;stroke-width:1"></path></svg>')


def top():
    return f'<header class="top"><b>ferro</b><span>Double Heston. {esc(X.STATUS)}</span></header>'


def ft():
    return f'<footer class="ft"><span>{esc(B.FOOT[0])}</span><span>{esc(B.FOOT[1])}</span></footer>'


def head(h, lede=None):
    return f'<section style="display:flex;flex-direction:column;gap:18px"><h1 class="h1">{esc(h)}</h1>{f"<p class=lede>{esc(lede)}</p>" if lede else ""}</section>'


def home():
    return f"""
{B.ticker()}
{top()}
<section class="plate" style="margin-top:28px"><div style="display:flex;flex-direction:column;gap:22px"><span class="b-lab" style="font-size:15px">{esc(X.Q)} For fitting today's prices, yes. For reading its settings, no.</span><h1 class="h1">Same surface, different magnets.</h1><p class="p" style="font-size:18.5px">{esc(PAIR_LEDE)}</p>
  <span style="display:flex;gap:12px"><a class="b-btn" href="Model.dc.html">{X.CTA['model']}</a><a class="b-btn sec" href="Finding.dc.html">{X.CTA['finding']}</a></span></div>{pool(700, 430)}</section>
<div class="pg">
  <section style="display:flex;flex-direction:column;gap:22px"><div class="two" style="align-items:end"><h2 class="h2">Underneath, the ten settings look nothing alike.</h2><p class="p">Ferrofluid takes its shape from magnets you can't see, and different magnets can raise the same surface. Option prices are the surface; the model's ten settings are the magnets.</p></div>
  {magnets()}<span class="b-sub" style="font-size:14px">{esc(MAG_NOTE)}</span></section>
  {ridge()}
  <section style="display:flex;flex-direction:column;gap:22px"><div class="two" style="align-items:end"><h2 class="h2">{esc(PART_HEAD)}</h2><p class="p">{esc(PART)}</p></div>{parting()}</section>
  <section class="two"><div style="display:flex;flex-direction:column;gap:18px"><h2 class="h2">{esc(X.TWIST)}</h2><p class="p">{esc(TYPICAL)} {esc(X.FINDING_LINE)}</p><a class="b-model" href="Finding.dc.html">{X.CTA['finding']}</a></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:28px">{B.nums(X.PROOF2_NUMS)}</div></section>
  {B.page_links('Main', 44, fill='var(--surf)')}
</div>
{ft()}
"""


def market():
    r = X.REL_LAST
    return f"""
{top()}
<div class="pg">
  {head('Market', X.MARKET_SUB)}
  <section style="display:flex;flex-direction:column;gap:16px"><div style="display:flex;align-items:baseline;justify-content:space-between"><span style="display:flex;align-items:baseline;gap:16px"><b class="h2">RELIANCE</b><span class="h1" style="font-size:52px">{inr(r[4])}</span><span style="font-weight:700;font-size:18px">{B.rel_change()}</span></span><span style="display:flex;gap:6px"><span class="b-chip">1M</span><span class="b-chip on">3M</span><span class="b-chip">Line</span><span class="b-chip on">Candles</span></span></div>
  {B.rel_candles(INK, 1218, 470, 8)}<div style="display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px">{''.join(f'<div class="b-greek"><span class="b-lab">{k}</span><b style="font-size:22px">{v}</b></div>' for k, v in B.rel_stats())}</div></section>
  {ridge()}
  <section class="two"><div>{B.watch_table(names=True, spark=(72, 24))}</div><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">NIFTY 50</h2>{B.nifty_line(INK, 560, 250)}<p class="p">{esc(X.UNIVERSE)}</p></div></section>
</div>
{ft()}
"""


def model():
    K_ = X.K
    return f"""
{top()}
<div class="pg">
  {head('Price an option', 'Pick a listed option, price it with Double Heston, and set it against what the market paid.')}
  {B.pricing_form()}
  <section style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:28px">{B.nums([(f'₹{inr(K_["market"])}', f'market close, IV {K_["market_iv"]:.2f}%'), (f'₹{inr(K_["dh"])}', f'Double Heston, IV {K_["dh_iv"]:.2f}%. {X.MC_LINE}'), (f'+₹{inr(X.GAP)}', 'model minus market')])}</section>
  <p class="lede">{esc(X.MODEL_EXPLAIN)}</p>
  <section class="two"><div>{B.market_smile(INK, 560, 360, 50)}</div><div>{B.chain_table(('Strike', 'Call', 'IV', 'Model', 'Put', 'IV'))}</div></section>
  {ridge()}
  <section class="two"><div><h2 class="h2" style="font-size:26px">Slow factor</h2><p class="dn" style="margin:6px 0 0">{esc(X.FELLER['slow'])}</p>{B.sliders('slow')}</div><div><h2 class="h2" style="font-size:26px">Fast factor</h2><p class="dn" style="margin:6px 0 0">{esc(X.FELLER['fast'])}</p>{B.sliders('fast')}</div></section>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:-50px"><span class="b-sub">{esc(X.FELLER_NOTE)}</span><button class="b-btn sec" type="button">Reset to starting settings</button></div>
  <section style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px">{B.greeks()}</section>
  <span class="b-sub" style="font-size:14px">{esc(X.MODEL_SOURCE)}</span>
</div>
{ft()}
"""


def maths():
    return f"""
{top()}
<div class="pg">
  {head('How it works', X.MATHS_INTRO)}
  <section class="two"><div>{B.equations()}</div><div>{B.steps()}</div></section>
  {ridge()}
  <section class="two"><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">The bend</h2>{tube_smile(560, 330)}</div><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Skew by time to expiry</h2>{B.skew(INK, 560, 330)}</div></section>
  {B.lineage()}
</div>
{ft()}
"""


def finding():
    return f"""
{top()}
<div class="pg">
  {head(X.FIND_HEAD)}
  <section class="two"><div style="display:flex;flex-direction:column;gap:16px"><h2 class="h2">{esc(X.PROOF1_HEAD)}</h2><p class="p">{esc(X.PROOF1)}</p><p class="b-sub" style="margin:0;font-size:15.5px;line-height:1.55">{esc(X.PROOF1_NET)}</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:28px">{B.nums(X.PROOF1_NUMS)}</div></section>
  <section class="two"><div style="display:flex;flex-direction:column;gap:16px"><h2 class="h2">{esc(X.PROOF2_HEAD)}</h2><p class="p">{esc(X.PROOF2)}</p></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:28px">{B.nums(X.PROOF2_NUMS)}</div></section>
  {B.hist(INK, 1218, 300)}
  {ridge()}
  <section style="display:flex;flex-direction:column;gap:18px"><div class="two" style="align-items:end"><h2 class="h2">One surface, six equally good fits</h2><p class="p">Bharti Airtel, 21 Aug 2026: 16 starts, {PAIR['equivalents']} fits within 10% of the best price error. Each spike is one fit. Where they bunch, the prices pin the setting down; where they scatter, they don't.</p></div>{board_all()}</section>
  <section class="two">{B.bars(INK, 560, label_w=210)}<p class="p">{esc(X.PER_PARAM)}</p></section>
  <section style="display:flex;flex-direction:column;gap:14px"><div style="display:flex;justify-content:space-between;align-items:center"><h2 class="h2">One stock, day by day</h2><span style="display:flex;gap:6px">{B.picks()}</span></div><p class="p">{esc(X.rel_line())}</p>{B.stock(INK, 1218)}</section>
  <section class="two">{B.nums([(f'{X.G8["median_network_relative"] * 100:.1f}%', X.HELDOUT), ('0 of 210', X.BACKTEST)])}</section>
</div>
{ft()}
"""


def about():
    return f"""
{top()}
<div class="pg">
  {head(X.ABOUT_HEAD)}
  <section class="two">{B.video(icon_fill='var(--ink)', icon_ink='var(--bg)')}<div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Method and data</h2>{''.join(f'<p class="p">{esc(m)}</p>' for m in X.METHOD)}</div></section>
  {ridge()}
  <section class="two"><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Limits</h2>{B.bullet_list(X.LIMITS)}</div><div style="display:flex;flex-direction:column;gap:14px"><h2 class="h2">Also explored</h2><p class="p">{esc(X.ALSO)}</p><a class="b-model" href="https://{X.REPO}">{esc(X.REPO)}</a></div></section>
</div>
{ft()}
"""


def team():
    return f"""
{top()}
<div class="pg">
  {head(X.TEAM_HEAD, X.TEAM_INTRO)}
  <section style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:26px">{B.team_cards()}</section>
  <section class="two"><div><span class="b-lab">Supervisor</span><h2 class="h2">{esc(X.SUPERVISOR[0])}</h2><p class="p">{esc(X.SUPERVISOR[1])}</p></div><div><span class="b-lab">Thanks</span>{B.bullet_list(X.THANKS)}</div></section>
</div>
{ft()}
"""


def references():
    return f"""
{top()}
<div class="pg">
  {head('References', 'The papers behind the model and its methods, and where the data comes from.')}
  <section class="two">{B.refs()}</section>
</div>
{ft()}
"""


DESIGN = Design(
    num=15, slug="ferro", name="Ferro",
    concept="Same surface, different magnets: one real NSE surface fitted twice, drawn as ferrofluid over magnets, in chrome and liquid black.",
    memorable="Bharti Airtel's 39-day smile as a pool of ferrofluid that two very different fits raise identically; their ten settings drawn as spike strips.",
    layout="One chrome plate hero, then calm two-column sections split by ferrofluid ridges; black carries emphasis, not colour.",
    light=LIGHT, dark=DARK,
    fonts_url="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Epilogue:wght@400;500;700;800&display=swap",
    display_font=SO, body_font=EP,
    type_sample="Same surface, different magnets.",
    type_note="Sora 600–700 for headlines and numbers; Epilogue 400–800 for text; emphasis by weight, never by hue.",
    ink=INK, css=CSS, rail_side="r", default_dark=False,
    icon_fills={"model": {"fill": "var(--ink)", "ink": "var(--bg)"}},
)
DESIGN.pages = {"Main": home, "Market": market, "Model": model, "Maths": maths, "Finding": finding,
                "About": about, "Team": team, "References": references}
check_tokens(DESIGN)
