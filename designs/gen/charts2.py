"""Extra charts for the new concepts (12–20). All computed from site_data.json (the pricer's output)."""
from __future__ import annotations

import math

import content as X
import kit
from kit import Ink, L, P, R, C, T, Scale, svg, esc


def decay(ink: Ink, w=900, h=360, slow_col=None, fast_col=None, left=52):
    """Share of a volatility shock still left after t years: exp(-kappa t), kappa 0.5 and 5.0."""
    ts = [i / 100 * 2 for i in range(101)]
    xs, ys = Scale(0, 2, left, w - 20), Scale(0, 1, h - 34, 16)
    out = []
    for v in (0, 0.5, 1):
        out.append(L(left, ys(v), w - 20, ys(v), ink.grid if v else ink.axis))
        out.append(T(left - 10, ys(v) + 4, f"{v * 100:.0f}%", ink, anchor="end"))
    for yr in (0, 0.5, 1, 1.5, 2):
        out.append(T(xs(yr), h - 12, f"{yr:g} yr", ink, anchor="middle"))
    out.append(L(left, ys(0.5), w - 20, ys(0.5), ink.ref, 1, "4 4"))
    out.append(T(xs(0.8), ys(0.5) + 20, "half the shock gone", ink, anchor="middle"))
    sc, fc = slow_col or ink.strong, fast_col or ink.model
    out.append(P([(xs(t), ys(math.exp(-0.5 * t))) for t in ts], sc, ink.line_w))
    out.append(P([(xs(t), ys(math.exp(-5.0 * t))) for t in ts], fc, ink.line_w))
    hs, hf = X.HL["slow_years"], X.HL["fast_days"] / 365
    out.append(C(xs(hs), ys(0.5), 6, sc))
    out.append(C(xs(hf), ys(0.5), 6, fc))
    out.append(T(xs(hs) + 10, ys(0.5) - 12, f"slow: {hs:.1f} years", ink, fill=ink.strong, weight=700))
    out.append(T(xs(hf) + 12, ys(0.5) + 24, f"fast: {X.HL['fast_days']:.0f} days", ink, fill=ink.strong, weight=700))
    return svg(w, h, "Share of a volatility shock remaining over two years: the fast factor loses half in 51 days, the slow factor in 1.4 years", "".join(out))


def clock(ink: Ink, size, half_life_years, label, hand_col, face="var(--surf)"):
    """A dial whose full turn is two years; the hand points at the factor's half-life."""
    cx = cy = size / 2
    r = size / 2 - 8
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" style="fill:{face};stroke:var(--ink);stroke-width:3"></circle>']
    for m in range(24):
        a = math.radians(m * 15 - 90)
        r0 = r - (18 if m % 6 == 0 else 9)
        out.append(L(cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + (r - 3) * math.cos(a), cy + (r - 3) * math.sin(a), "var(--ink)", 3 if m % 6 == 0 else 1.5))
    for m, lab in ((0, "0"), (6, "6 mo"), (12, "1 yr"), (18, "18 mo")):
        a = math.radians(m * 15 - 90)
        out.append(T(cx + (r - 40) * math.cos(a), cy + (r - 40) * math.sin(a) + 5, lab, ink, anchor="middle", size=ink.size))
    frac = half_life_years / 2
    a1 = math.radians(frac * 360 - 90)
    large = 1 if frac > 0.5 else 0
    x1, y1 = cx + (r - 26) * math.cos(a1), cy + (r - 26) * math.sin(a1)
    out.append(f'<path d="M{cx},{cy - r + 26} A{r - 26},{r - 26} 0 {large} 1 {x1:.1f},{y1:.1f}" style="fill:none;stroke:{hand_col};stroke-width:10;stroke-linecap:round;opacity:.35"></path>')
    xh, yh = cx + (r - 30) * math.cos(a1), cy + (r - 30) * math.sin(a1)
    out.append(L(cx, cy, xh, yh, hand_col, 7))
    out.append(C(cx, cy, 9, hand_col))
    return svg(size, size, f"{label}: dial of two years, hand at the half-life", "".join(out))


def fan(ink: Ink, w=1100, h=440, n_paths=60, left=50, path_col=None):
    """Real simulated Double Heston paths (1 year, S0 = 100) with 5–95% and 25–75% bands."""
    F = X.D["fan"]
    q = F["quantiles"]
    n = len(q["50"])
    lo, hi = min(min(p) for p in F["paths"][:n_paths]), max(max(p) for p in F["paths"][:n_paths])
    lo, hi = min(lo, min(q["5"])) - 3, max(hi, max(q["95"])) + 3
    xs, ys = Scale(0, n - 1, left, w - 90), Scale(lo, hi, h - 30, 12)
    out = []
    for v in kit.ticks(lo, hi, 4):
        out.append(L(left, ys(v), w - 90, ys(v), ink.grid))
        out.append(T(left - 8, ys(v) + 4, f"{v:g}", ink, anchor="end"))
    band = [(xs(i), ys(v)) for i, v in enumerate(q["95"])] + [(xs(i), ys(v)) for i, v in reversed(list(enumerate(q["5"])))]
    out.append(f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in band)}" style="fill:{ink.model};opacity:.10"></polygon>')
    band2 = [(xs(i), ys(v)) for i, v in enumerate(q["75"])] + [(xs(i), ys(v)) for i, v in reversed(list(enumerate(q["25"])))]
    out.append(f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in band2)}" style="fill:{ink.model};opacity:.16"></polygon>')
    pc = path_col or ink.text
    for p in F["paths"][:n_paths]:
        out.append(P([(xs(i), ys(v)) for i, v in enumerate(p)], pc, 1, None) .replace("stroke-width:1", "stroke-width:1;opacity:.45"))
    out.append(P([(xs(i), ys(v)) for i, v in enumerate(q["50"])], ink.model, 3))
    for key, lab in (("95", "95th percentile"), ("50", "median"), ("5", "5th percentile")):
        out.append(T(w - 84, ys(q[key][-1]) + 4, lab, ink, fill=ink.strong, weight=700 if key == "50" else 400))
    for i, lab in ((0, "today"), (n // 2, "6 months"), (n - 1, "1 year")):
        out.append(T(xs(i), h - 8, lab, ink, anchor="middle"))
    return svg(w, h, f"{n_paths} simulated Double Heston price paths over one year from 100, with the middle 50% and 90% bands", "".join(out))


def density(ink: Ink, w=1000, h=380, left=40):
    """Model's distribution of log(S_T/S) at 32 days (20,000 paths) vs a normal curve with the same ATM vol."""
    Dn = X.D["density"]
    e, d = Dn["edges"], Dn["dh"]
    mids = [(e[i] + e[i + 1]) / 2 for i in range(len(d))]
    sig = Dn["atm_vol"] * math.sqrt(Dn["T"])
    mu = (X.K["rate"] - X.K["carry"]) * Dn["T"] - 0.5 * sig * sig  # same drift as the simulation
    norm = [math.exp(-((x - mu) ** 2) / (2 * sig * sig)) / (sig * math.sqrt(2 * math.pi)) for x in mids]
    ymax = max(max(d), max(norm)) * 1.1
    xs, ys = Scale(e[0], e[-1], left, w - 10), Scale(0, ymax, h - 30, 14)
    out = [L(left, h - 30, w - 10, h - 30, ink.axis)]
    bw = xs(e[1]) - xs(e[0])
    for i, v in enumerate(d):
        out.append(R(xs(e[i]) + .5, ys(v), bw - 1, (h - 30) - ys(v), ink.model, rx=0, opacity=.85))
    out.append(P([(xs(x), ys(v)) for x, v in zip(mids, norm)], ink.strong, 2.2, "6 5"))
    for pct in (-20, -10, 0, 10, 20):
        x = math.log(1 + pct / 100)
        if e[0] <= x <= e[-1]:
            out.append(T(xs(x), h - 10, f"{pct:+d}%" if pct else "0", ink, anchor="middle"))
    xl = xs(math.log(0.88))
    out.append(T(xl, ys(max(d) * 0.35) - 70, "fatter left tail:", ink, fill=ink.strong, weight=700, anchor="middle"))
    out.append(T(xl, ys(max(d) * 0.35) - 52, "big falls are likelier", ink, anchor="middle"))
    out.append(T(w - 14, 30, "Bars: Double Heston, 20,000 simulated paths", ink, anchor="end", fill=ink.strong))
    out.append(T(w - 14, 48, "Dashed: one fixed volatility, same at-the-money level", ink, anchor="end"))
    return svg(w, h, "Distribution of NIFTY's move to expiry under Double Heston (bars) against a normal curve with the same volatility (dashed)", "".join(out))


VIRIDIS = ["#440154", "#482878", "#3E4A89", "#31688E", "#26828E", "#1F9E89", "#35B779", "#6DCD59", "#B4DE2C", "#FDE725"]


def heat(ink: Ink, w=1000, h=520, left=90, top=20):
    """Implied-volatility surface (maturity × strike) at the starting settings, viridis."""
    S = X.D["surface"]
    days, ks, iv = S["days"], S["strikes"], S["iv"]
    vals = [v for row in iv for v in row if v is not None]
    lo, hi = min(vals), max(vals)
    cw = (w - left - 110) / len(ks)
    ch = (h - top - 40) / len(days)
    out = []
    for r, (dd, row) in enumerate(zip(days, iv)):
        y = top + r * ch
        out.append(T(left - 12, y + ch / 2 + 5, {7: "1 week", 14: "2 weeks", 30: "1 month", 60: "2 months", 90: "3 months", 180: "6 months", 365: "1 year"}[dd], ink, anchor="end"))
        for c, v in enumerate(row):
            x = left + c * cw
            if v is None:
                out.append(R(x + 1, y + 1, cw - 2, ch - 2, "var(--raised)"))
                out.append(T(x + cw / 2, y + ch / 2 + 5, "≈ 0", ink, anchor="middle"))
                continue
            k = min(9, int((v - lo) / (hi - lo + 1e-9) * 10))
            out.append(R(x + 1, y + 1, cw - 2, ch - 2, VIRIDIS[k], rx=3))
            out.append(T(x + cw / 2, y + ch / 2 + 5, f"{v:.1f}", ink, anchor="middle", fill="#FFFFFF" if k < 6 else "#111111", weight=600))
    for c, k in enumerate(ks):
        out.append(T(left + c * cw + cw / 2, h - 12, f"{k}%", ink, anchor="middle"))
    lx = w - 80
    for i, col in enumerate(reversed(VIRIDIS)):
        out.append(R(lx, top + i * 30, 26, 30, col))
    out.append(T(lx + 34, top + 12, f"{hi:.1f}%", ink))
    out.append(T(lx + 34, top + 300, f"{lo:.1f}%", ink))
    return svg(w, h, "Implied volatility surface at the starting settings: rows are time to expiry, columns are strike as a percentage of today's price", "".join(out))
