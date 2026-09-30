// Shared charts. Each chart is drawn at its container's real width (so text stays the size the CSS
// sets, readable on a projector), painted only through theme tokens and CSS classes, and animated in
// when it scrolls into view. Candles are always green up / red down with the price axis on the right.
import { esc, inr, scale, ticks, uid, shortDate, clamp, median } from './util.js';
import { whenInView, tween, ease, reduced } from './motion.js';

// ------------------------------------------------------------------ svg helpers
const f1 = v => (Math.round(v * 10) / 10).toString();
export const dPath = pts => 'M' + pts.map(p => f1(p[0]) + ',' + f1(p[1])).join('L');
const L = (x1, y1, x2, y2, cls = 'grid', extra = '') => `<line x1="${f1(x1)}" y1="${f1(y1)}" x2="${f1(x2)}" y2="${f1(y2)}" class="${cls}" ${extra}/>`;
const T = (x, y, s, cls = '', anchor = 'start', extra = '') => `<text x="${f1(x)}" y="${f1(y)}" text-anchor="${anchor}" class="${cls}" ${extra}>${esc(s)}</text>`;
const Pa = (pts, cls, extra = '') => `<path d="${dPath(pts)}" class="${cls}" ${extra}/>`;
const R = (x, y, w, h, cls, extra = '') => `<rect x="${f1(x)}" y="${f1(y)}" width="${f1(Math.max(0, w))}" height="${f1(Math.max(0, h))}" class="${cls}" ${extra}/>`;
const Ci = (x, y, r, cls, extra = '') => `<circle cx="${f1(x)}" cy="${f1(y)}" r="${r}" class="${cls}" ${extra}/>`;
const FS = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--fs-chart')) || 14.5;

// ------------------------------------------------------------------ registry + mounting
const REG = {};
export function registerChart(name, fn) { REG[name] = fn; }

// <div class="chart" data-chart="smileBend" data-h="380" data-o='{"...":...}'></div>
export function mountCharts(scope, ctx) {
  const els = [...scope.querySelectorAll('.chart[data-chart]')];
  els.forEach(el => renderChart(el, ctx, true));
  const ro = new ResizeObserver(entries => {
    for (const en of entries) {
      const el = en.target;
      const w = Math.round(en.contentRect.width);
      if (w && Math.abs(w - (el._w || 0)) > 2) renderChart(el, ctx, false);
    }
  });
  els.forEach(el => ro.observe(el));
  return () => ro.disconnect();
}

export function renderChart(el, ctx, first, extra) {
  const fn = REG[el.dataset.chart];
  if (!fn) return;
  const w = Math.max(260, Math.round(el.clientWidth || el.parentElement.clientWidth || 600));
  el._w = w;
  // theme presentation options (e.g. a glow) first; the page's own options and live state win
  const o = Object.assign({}, ctx.chartOpts?.[el.dataset.chart] || {}, el.dataset.o ? JSON.parse(el.dataset.o) : {}, el._opts || {}, extra || {});
  o.h = +(el.dataset.h || o.h || 360);
  if (w < 560) o.h = Math.round(o.h * clamp(w / 560, 0.72, 1));
  o.fs = FS();
  const out = fn(w, o, ctx, el);
  const id = uid('ch');
  el.innerHTML = `<svg viewBox="0 0 ${w} ${out.h}" width="${w}" height="${out.h}" role="img" aria-label="${esc(out.label)}" id="${id}">${out.body}<g class="hov" aria-hidden="true"></g></svg><div class="ctip" aria-hidden="true"></div>`;
  const svg = el.firstElementChild;
  if (!el.hasAttribute('data-anim')) el.setAttribute('data-anim', '');
  if (!first || reduced()) el.classList.add('is-in');
  if (out.hover) hover(el, svg, out.hover);
  if (out.after) {
    if (first && !reduced() && !el.classList.contains('is-in')) whenInView(el, () => out.after(svg, true));
    else out.after(svg, false);
  }
  el._out = out;
}

function hover(el, svg, H) {
  const g = svg.querySelector('.hov');
  const tip = el.querySelector('.ctip');
  const vb = svg.viewBox.baseVal;
  let last = -1;
  const show = e => {
    const r = svg.getBoundingClientRect();
    const x = (e.clientX - r.left) * (vb.width / r.width);
    const y = (e.clientY - r.top) * (vb.height / r.height);
    if (x < H.x0 - 10 || x > H.x1 + 10 || y < 0 || y > vb.height) return hide();
    let i = 0, best = Infinity;
    H.xs.forEach((xx, k) => { const dd = Math.abs(xx - x); if (dd < best) { best = dd; i = k; } });
    if (i !== last) {
      last = i;
      const px = H.xs[i];
      g.innerHTML = L(px, H.top, px, H.bottom, 'hover-line', 'style="opacity:1"') +
        (H.ys ? H.ys(i).map(yy => (yy == null ? '' : Ci(px, yy, 5, 'c-dot-mk'))).join('') : '');
      tip.innerHTML = H.html(i);
    }
    const scaleX = r.width / vb.width;
    tip.style.left = `${H.xs[i] * scaleX}px`;
    tip.style.top = `${Math.max(8, (H.tipY ? H.tipY(i) : H.top) * (r.height / vb.height))}px`;
    tip.classList.add('on');
  };
  const hide = () => { last = -1; g.innerHTML = ''; tip.classList.remove('on'); };
  svg.addEventListener('pointermove', show);
  svg.addEventListener('pointerleave', hide);
}

// animate a path's d from one set of points to another (same length); spring settle
export function morphPath(path, from, to, dur = 1100, e = t => ease.spring(t, 0.72, 8.5)) {
  path._cancel?.();
  path._cancel = tween(dur, k => path.setAttribute('d', dPath(to.map((p, i) => [from[i][0] + (p[0] - from[i][0]) * k, from[i][1] + (p[1] - from[i][1]) * k]))), e);
}

// ------------------------------------------------------------------ the bend: flat BS -> DH smile
registerChart('smileBend', (w, o, ctx) => {
  const pts = ctx.D.smile_30d;
  const h = o.h, left = 52, right = 16, top = 34, bottom = 44;
  const xs = scale(80, 120, left, w - right), ys = scale(13.5, 27.5, h - bottom, top);
  let b = '';
  for (const v of [16, 20, 24]) b += L(left, ys(v), w - right, ys(v)) + T(left - 10, ys(v) + 5, `${v}%`, '', 'end');
  b += L(left, h - bottom, w - right, h - bottom, 'axis');
  for (const k of [80, 90, 100, 110, 120]) b += T(xs(k), h - bottom + 22, `${k}%`, '', 'middle');
  b += T((left + w - right) / 2, h - 4, 'Strike, as a percentage of today\'s price', '', 'middle');
  b += L(xs(100), top - 6, xs(100), h - bottom, 'c-ref', 'style="stroke-dasharray:2 5"');
  b += L(left, ys(20), w - right, ys(20), 'c-ref');
  b += T(w - right, ys(20) - 10, o.flatLabel || 'One fixed volatility (Black–Scholes), 20%', 't-ink', 'end');
  const P = pts.map(([k, v]) => [xs(k), ys(v)]);
  const flat = pts.map(([k]) => [xs(k), ys(20)]);
  if (o.glow) {
    const fid = uid('glow');
    b += `<defs><filter id="${fid}" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="${o.glow}"/></filter></defs>`;
    b += `<path d="${dPath(P)}" class="c-model bend-glow" filter="url(#${fid})" style="stroke-width:${o.glow * 1.6};opacity:.55"/>`;
  }
  b += `<path d="${dPath(P)}" class="c-model bend-line" style="stroke-width:${o.lw || 'var(--c-lw, 3.5)'}"/>`;
  b += `<g class="bend-labels">` +
    Ci(P[0][0], P[0][1], 6, 'c-fill-model a-pop', 'style="--d:900ms"') + Ci(P[P.length - 1][0], P[P.length - 1][1], 6, 'c-fill-model a-pop', 'style="--d:1000ms"') +
    T(P[0][0] + 12, P[0][1] - 12, `Double Heston, ${pts[0][1].toFixed(1)}% at strike 80`, 't-strong a-fade', 'start', 'style="--d:1000ms"') +
    T(P[P.length - 1][0] - 4, P[P.length - 1][1] + 28, `${pts[pts.length - 1][1].toFixed(1)}% at strike 120`, 't-strong a-fade', 'end', 'style="--d:1100ms"') +
    T(xs(100) + 8, h - bottom - 10, "today's price", 'a-fade', 'start', 'style="--d:1100ms"') + '</g>';
  return {
    h, body: b,
    label: `Implied volatility by strike at 30 days: one fixed volatility is flat at 20%; Double Heston bends from ${pts[0][1].toFixed(1)}% at strike 80 to ${pts[pts.length - 1][1].toFixed(1)}% at strike 120`,
    hover: { xs: P.map(p => p[0]), x0: left, x1: w - right, top, bottom: h - bottom, ys: i => [P[i][1]], tipY: i => P[i][1] - 6,
      html: i => `Strike <b>${pts[i][0]}%</b>: Double Heston <b>${pts[i][1].toFixed(1)}%</b>, flat <b>20.0%</b>` },
    after(svg, animate) {
      if (!animate) return;
      const line = svg.querySelector('.bend-line'), glow = svg.querySelector('.bend-glow');
      line.setAttribute('d', dPath(flat));
      setTimeout(() => morphPath(line, flat, P, 1500, t => ease.spring(t, 0.58, 7.5)), 350);
      // the blurred glow is expensive to redraw every frame: it appears once the line has settled
      if (glow) {
        glow.style.opacity = '0';
        setTimeout(() => { glow.style.transition = 'opacity .8s ease'; glow.style.opacity = '.55'; }, 1900);
      }
    },
  };
});

// ------------------------------------------------------------------ market smile on the model page
registerChart('marketSmile', (w, o, ctx, el) => {
  const D = ctx.D, K = D.contract;
  const res = el._res; // latest model result, if repriced
  const lo = D.chain[0].strike - 50, hi = D.chain[D.chain.length - 1].strike + 50;
  const mk = D.chain.filter(r => r.mkt_iv).map(r => [r.strike, r.mkt_iv]);
  const dh = res ? res.smile.filter(([k, v]) => v != null && k >= lo && k <= hi) : D.chain.map(r => [r.strike, r.dh_iv]);
  const all = [...mk.map(p => p[1]), ...dh.map(p => p[1])];
  const y0 = Math.floor(Math.min(...all) - 1.5), y1 = Math.ceil(Math.max(...all) + 1.5);
  const h = o.h, left = 50, right = 16, top = 40, bottom = 44;
  const xs = scale(lo, hi, left, w - right), ys = scale(y0, y1, h - bottom, top);
  let b = '';
  for (const v of ticks(y0, y1, 4)) b += L(left, ys(v), w - right, ys(v)) + T(left - 10, ys(v) + 5, `${v}%`, '', 'end');
  b += L(left, h - bottom, w - right, h - bottom, 'axis');
  for (const k of ticks(lo, hi, w < 600 ? 3 : 5).filter(k => k % 50 === 0)) b += T(xs(k), h - bottom + 22, inr(k, 0), '', 'middle');
  b += T((left + w - right) / 2, h - 4, 'Strike (NIFTY, 27 Oct 2026 expiry)', '', 'middle');
  b += L(xs(K.spot), top, xs(K.spot), h - bottom, 'c-ref', 'style="stroke-dasharray:2 5"') + T(xs(K.spot) + 6, h - bottom - 8, `spot ${inr(K.spot)}`, '');
  const strike = o.strike || K.strike;
  b += L(xs(strike), top, xs(strike), h - bottom, 'axis', 'style="stroke:var(--ink);stroke-width:1.5;opacity:.5"');
  const P = dh.map(([k, v]) => [xs(k), ys(v)]);
  b += Pa(P, 'c-model a-draw ms-line', 'pathLength="1"');
  b += mk.map(([k, v], i) => Ci(xs(k), ys(v), 5.5, 'c-dot-mk a-pop', `style="--i:${i};--d:500ms"`)).join('');
  b += `<g class="a-fade" style="--d:300ms">` + Ci(left + 8, 16, 5.5, 'c-dot-mk') + T(left + 20, 21, 'Market, NSE close 25 Sep', 't-ink') +
    L(left + 250, 16, left + 280, 16, 'c-model') + T(left + 290, 21, res ? 'Double Heston, your settings' : 'Double Heston, starting settings', 't-ink') + '</g>';
  const byK = new Map(mk);
  return {
    h, body: b, points: P,
    label: 'Implied volatility by strike for the 27 Oct 2026 NIFTY expiry: market closing prices against Double Heston',
    hover: { xs: dh.map(p => xs(p[0])), x0: left, x1: w - right, top, bottom: h - bottom, ys: i => [P[i][1], byK.has(dh[i][0]) ? ys(byK.get(dh[i][0])) : null],
      tipY: i => Math.min(P[i][1], byK.has(dh[i][0]) ? ys(byK.get(dh[i][0])) : 1e9) - 8,
      html: i => `Strike <b>${inr(dh[i][0], 0)}</b>: model <b>${dh[i][1].toFixed(2)}%</b>${byK.has(dh[i][0]) ? `, market <b>${byK.get(dh[i][0]).toFixed(2)}%</b>` : ''}` },
  };
});

// ------------------------------------------------------------------ candles (and line mode)
registerChart('candles', (w, o, ctx) => {
  const sym = o.sym || 'RELIANCE';
  let rows = ctx.D.equity[sym] || [];
  if (o.range === '1M') rows = rows.slice(-21);
  const n = rows.length;
  const h = o.h, axisW = 86, top = 14, timeH = 28;
  const pw = w - axisW;
  const volH = (h - top - timeH) * 0.2;
  const pb = h - timeH - volH - 14;
  let lo = Math.min(...rows.map(r => r[3])), hi = Math.max(...rows.map(r => r[2]));
  const pad = (hi - lo) * 0.07; lo -= pad; hi += pad;
  const y = scale(lo, hi, pb, top);
  const sw = pw / (n + 1.5), bw = Math.max(2, sw * 0.62);
  const last = rows[n - 1][4], prev = rows[n - 1][6], yl = y(last);
  const vmax = Math.max(...rows.map(r => r[5]));
  let b = '';
  for (const tv of ticks(lo, hi, 5)) { b += L(0, y(tv), pw, y(tv)); if (Math.abs(y(tv) - yl) > 22) b += T(pw + 12, y(tv) + 5, inr(tv, 0)); }
  const every = Math.max(1, Math.round(n / (w < 700 ? 4 : 6)));
  const xsC = [];
  if (o.mode === 'line') {
    const P = rows.map((r, i) => [sw * (i + 0.75), y(r[4])]);
    rows.forEach((_, i) => xsC.push(P[i][0]));
    b += `<path d="${dPath(P)}L${f1(P[n - 1][0])},${f1(pb)}L${f1(P[0][0])},${f1(pb)}Z" class="c-area a-fade" style="--d:600ms"/>`;
    b += Pa(P, 'c-model a-draw', 'pathLength="1"');
  }
  rows.forEach((r, i) => {
    const [dt, op, hh, ll, c, v] = r;
    const cx = sw * (i + 0.75);
    if (o.mode !== 'line') xsC.push(cx);
    const up = c >= op;
    const col = up ? 'up' : 'dn';
    if (o.mode !== 'line') {
      const yt = y(Math.max(op, c)), yb = y(Math.min(op, c));
      b += `<g class="a-rise" style="--i:${i}">${L(cx, y(hh), cx, y(ll), `${col}-s`, 'style="stroke-width:1.4"')}${R(cx - bw / 2, yt, bw, Math.max(1.5, yb - yt), `${col}-f`, 'rx="1.2"')}</g>`;
    }
    const vh = v / vmax * volH;
    b += R(cx - bw / 2, h - timeH - vh, bw, vh, `${col}-f a-rise`, `style="--i:${i};opacity:.38"`);
    if (i % every === 0) b += T(cx, h - 7, shortDate(dt), '', 'middle');
  });
  b += L(0, h - timeH, pw, h - timeH, 'axis');
  b += T(pw + 12, h - timeH - volH + 12, 'Volume', '', 'start', 'style="font-size:12.5px"');
  const col = last >= prev ? 'up' : 'dn';
  b += `<g class="a-fade" style="--d:900ms">` + L(0, y(prev), pw, y(prev), 'c-ref', 'style="opacity:.6"') + T(8, y(prev) - 7, `prev close ${inr(prev)}`, '', 'start', 'style="font-size:12.5px"') +
    L(0, yl, pw, yl, `${col}-s`, 'style="stroke-dasharray:4 3"') + R(pw + 3, yl - 12, axisW - 3, 24, `${col}-f`, 'rx="4"') +
    T(pw + 10, yl + 5.5, inr(last), '', 'start', 'style="fill:var(--on-up);font-weight:700"') + '</g>';
  return {
    h, body: b,
    label: `${sym} daily ${o.mode === 'line' ? 'closing prices' : 'candlesticks'}, ${shortDate(rows[0][0])} to ${shortDate(rows[n - 1][0])} 2026, NSE closing data; green closed higher, red lower`,
    hover: { xs: xsC, x0: 0, x1: pw, top, bottom: h - timeH, ys: i => (o.mode === 'line' ? [y(rows[i][4])] : []), tipY: i => y(rows[i][2]) - 8,
      html: i => { const r = rows[i]; const ch = r[4] - r[6]; return `<b>${shortDate(r[0])}</b>&nbsp; O ${inr(r[1])} H ${inr(r[2])} L ${inr(r[3])} C <b>${inr(r[4])}</b> <span style="color:${ch >= 0 ? 'var(--up)' : 'var(--down)'}">${ch >= 0 ? '▲' : '▼'} ${Math.abs(ch / r[6] * 100).toFixed(2)}%</span>`; } },
  };
});

// ------------------------------------------------------------------ index line
registerChart('indexLine', (w, o, ctx) => {
  const which = o.which || 'NIFTY';
  const data = ctx.D.index_close[which];
  const h = o.h, left = 70, right = 12, top = 16, bottom = 34;
  const vals = data.map(d => d[1]);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.12; lo -= pad; hi += pad;
  const xs = scale(0, data.length - 1, left, w - right), ys = scale(lo, hi, h - bottom, top);
  let b = '';
  for (const v of ticks(lo, hi, 4)) b += L(left, ys(v), w - right, ys(v)) + T(left - 10, ys(v) + 5, inr(v, 0), '', 'end');
  b += L(left, h - bottom, w - right, h - bottom, 'axis');
  [0, 21, 42, data.length - 1].forEach(i => { b += T(xs(i), h - 10, shortDate(data[i][0]), '', 'middle'); });
  const P = data.map((d, i) => [xs(i), ys(d[1])]);
  b += `<path d="${dPath(P)}L${f1(P[P.length - 1][0])},${f1(h - bottom)}L${f1(P[0][0])},${f1(h - bottom)}Z" class="c-area a-fade" style="--d:500ms"/>`;
  b += Pa(P, 'c-model a-draw', 'pathLength="1"');
  b += Ci(P[P.length - 1][0], P[P.length - 1][1], 5, 'c-fill-model a-pop', 'style="--d:1300ms"');
  const name = which === 'NIFTY' ? 'NIFTY 50' : 'NIFTY BANK';
  return { h, body: b, label: `${name} closing level over ${data.length} trading days, 1 Jul to 25 Sep 2026`,
    hover: { xs: P.map(p => p[0]), x0: left, x1: w - right, top, bottom: h - bottom, ys: i => [P[i][1]], tipY: i => P[i][1] - 8,
      html: i => `${shortDate(data[i][0])}: <b>${inr(data[i][1])}</b>` } };
});

// ------------------------------------------------------------------ sparkline (inline)
export function sparkline(closes, w = 90, h = 28) {
  const lo = Math.min(...closes), hi = Math.max(...closes), span = (hi - lo) || 1;
  const P = closes.map((v, i) => [i / (closes.length - 1) * w, 2 + (hi - v) / span * (h - 4)]);
  const col = closes[closes.length - 1] >= closes[0] ? 'var(--up)' : 'var(--down)';
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><path d="${dPath(P)}" style="fill:none;stroke:${col};stroke-width:1.8;stroke-linejoin:round;stroke-linecap:round"/></svg>`;
}

// ------------------------------------------------------------------ dispersion histogram
registerChart('hist', (w, o, ctx) => {
  const H_ = ctx.D.hist, rand = ctx.D.random_pair_median;
  const h = o.h, left = 12, right = 12, bottom = 34, top = 58;
  const xs = scale(H_.edges[0], H_.edges[H_.edges.length - 1], left, w - right), ys = scale(0, Math.max(...H_.counts) * 1.08, h - bottom, top);
  const bw = xs(H_.edges[1]) - xs(H_.edges[0]);
  let b = '';
  H_.counts.forEach((c, i) => { if (c) b += R(xs(H_.edges[i]) + 1, ys(c), bw - 2, h - bottom - ys(c), 'c-fill-model a-rise', `rx="2" style="--i:${i};opacity:.9"`); });
  b += L(left, h - bottom, w - right, h - bottom, 'axis');
  for (let v = 0; v <= 9; v++) b += T(xs(v), h - bottom + 22, String(v), '', 'middle');
  const xr = xs(rand), xm = xs(H_.median);
  b += `<g class="a-fade" style="--d:700ms">` + L(xr, 10, xr, h - bottom, 'c-alt', 'style="stroke-dasharray:4 4;stroke-width:1.6"') +
    T(xr + 8, 24, 'Two random parameter sets', 't-strong') + T(xr + 8, 44, `median ${rand.toFixed(2)}`) +
    L(xm, 10, xm, h - bottom, 'c-model', 'style="stroke-width:2.6"') + T(xm + 10, 24, 'Equally good fits', 't-strong') + T(xm + 10, 44, `median ${H_.median.toFixed(2)}`) + '</g>';
  return { h, body: b, label: `Histogram of how far apart equally good fits landed on ${H_.n.toLocaleString('en-IN')} real surfaces: median ${H_.median.toFixed(2)} against ${rand.toFixed(2)} for two random parameter sets` };
});

// ------------------------------------------------------------------ per-setting bars
const PLAIN = {
  kappa_s: ['Speed back to normal', 'slow', 'κ'], kappa_f: ['Speed back to normal', 'fast', 'κ'],
  sigma_s: ['Volatility of volatility', 'slow', 'ξ'], sigma_f: ['Volatility of volatility', 'fast', 'ξ'],
  rho_s: ['Price–volatility link', 'slow', 'ρ'], rho_f: ['Price–volatility link', 'fast', 'ρ'],
  theta_s: ['Long-run level', 'slow', 'θ'], theta_f: ['Long-run level', 'fast', 'θ'],
  v0_s: ["Today's level", 'slow', 'v₀'], v0_f: ["Today's level", 'fast', 'v₀'],
};
registerChart('paramBars', (w, o, ctx) => {
  let rows = [...ctx.D.per_param].sort((a, b) => b.fits - a.fits);
  if (o.only) rows = rows.filter(r => o.only.includes(r.name));
  const narrow = w < 640;
  const rowH = o.rowH || 38, labelW = narrow ? Math.min(o.labelW || 150, 150) : Math.max(o.labelW || 290, 290);
  const top = narrow || w - labelW < 450 ? 64 : 42;
  const h = top + rowH * rows.length + 40;
  const xs = scale(0, 6, labelW, w - 52);
  const stackLegend = narrow || w - labelW < 450;
  const lx = narrow ? 0 : labelW, ly2 = stackLegend ? 44 : 19, lx2 = stackLegend ? lx : labelW + 200;
  let b = `<g class="a-fade">${R(lx, 8, 24, 12, 'c-fill-model', 'rx="3"')}${T(lx + 32, 19, 'Equally good fits')}` +
    `${L(lx2 + 12, ly2 - 14, lx2 + 12, ly2 + 4, 'c-alt', 'style="stroke-width:2.6"')}${T(lx2 + 32, ly2, 'Two random parameter sets')}</g>`;
  for (let v = 0; v <= 6; v++) b += L(xs(v), top - 4, xs(v), top + rowH * rows.length, v ? 'grid' : 'axis') + T(xs(v), top + rowH * rows.length + 22, String(v), '', 'middle');
  rows.forEach((r, i) => {
    const [name, fac, sym] = PLAIN[r.name];
    const yc = top + rowH * i + rowH / 2;
    b += T(0, yc + 5, w < 640 ? `${sym} ${fac}` : `${name}, ${fac}`, 't-ink');
    const bh = rowH * 0.48;
    b += R(xs(0), yc - bh / 2, xs(r.fits) - xs(0), bh, 'c-fill-model a-grow', `rx="3" style="--i:${i}"`);
    b += L(xs(r.random), yc - rowH * 0.4, xs(r.random), yc + rowH * 0.4, 'c-alt a-pop', `style="stroke-width:2.6;--i:${i};--d:400ms"`);
    b += T(Math.max(xs(r.fits), xs(r.random)) + 9, yc + 5, r.fits.toFixed(2), 't-strong a-fade', 'start', `style="--i:${i};--d:500ms"`);
  });
  b += T(narrow ? 0 : labelW, h - 2, narrow ? 'Distance between fits, in training-data spreads' : 'Median distance between the fits, in spreads of the training data', '', 'start', 'style="font-size:12.5px"');
  return { h, body: b, label: 'How far apart equally good fits land for each setting, against two random parameter sets' };
});

// ------------------------------------------------------------------ one stock, day by day
registerChart('stockPanel', (w, o, ctx) => {
  const sym = o.sym || 'RELIANCE';
  const rows = ctx.D.per_stock[sym];
  const rand = ctx.D.random_pair_median;
  const n = rows.length;
  const left = 56, rm = w < 700 ? 20 : 200, topH = 210, gap = 64, botH = 170;
  const h = topH + gap + botH + 34;
  const xs = scale(0, n - 1, left, w - rm);
  const emax = Math.max(...rows.map(r => Math.max(r[1], r[2]))) * 100 * 1.12;
  const ye = scale(0, emax, topH, 34);
  let b = T(left, 16, 'Price error each day, as a share of the stock price', 't-ink');
  for (const v of ticks(0, emax, 3)) b += L(left, ye(v), w - rm, ye(v), v ? 'grid' : 'axis') + T(left - 8, ye(v) + 5, `${+v.toPrecision(2)}%`, '', 'end');
  const PF = rows.map((r, i) => [xs(i), ye(r[2] * 100)]), PD = rows.map((r, i) => [xs(i), ye(r[1] * 100)]);
  b += Pa(PF, 'c-alt a-draw', 'pathLength="1" style="stroke-dasharray:1 1;stroke-width:1.8;opacity:.75"');
  b += Pa(PD, 'c-model a-draw', 'pathLength="1" style="--d:200ms"');
  if (w >= 700) {
    let yf = PF[n - 1][1], yd = PD[n - 1][1];
    if (Math.abs(yf - yd) < 36) { const m = (yf + yd) / 2; [yf, yd] = yf < yd ? [m - 18, m + 18] : [m + 18, m - 18]; }
    b += T(w - rm + 14, yf + 5, 'Flat volatility', 'a-fade') + T(w - rm + 14, yd + 5, 'Double Heston, best fit', 't-strong a-fade');
  }
  const y0 = topH + gap, yd_ = scale(0, 9, y0 + botH, y0 + 12);
  b += T(left, y0 - 14, 'How far apart the equally good fits landed that day', 't-ink');
  for (const v of [0, 3, 6, 9]) b += L(left, yd_(v), w - rm, yd_(v), v ? 'grid' : 'axis') + T(left - 8, yd_(v) + 5, String(v), '', 'end');
  const bw = (w - rm - left) / n * 0.62;
  rows.forEach((r, i) => { b += R(xs(i) - bw / 2, yd_(Math.min(9, r[3])), bw, yd_(0) - yd_(Math.min(9, r[3])), 'c-fill-model a-rise', `rx="1.5" style="--i:${i};opacity:.9"`); });
  b += L(left, yd_(rand), w - rm, yd_(rand), 'c-alt', 'style="stroke-dasharray:4 4;stroke-width:1.6"');
  if (w >= 700) b += T(w - rm + 14, yd_(rand) + 1, 'Two random', 't-strong') + T(w - rm + 14, yd_(rand) + 19, `parameter sets, ${rand.toFixed(2)}`);
  const seen = {};
  rows.forEach((r, i) => { seen[r[0].slice(0, 7)] ??= i; });
  Object.entries(seen).forEach(([m, i]) => { b += T(xs(i), h - 6, { '07': 'Jul', '08': 'Aug', '09': 'Sep' }[m.slice(5)] || m); });
  return { h, body: b, label: `${sym}, ${n} trading days: best-fit price error against a flat volatility, and how far apart the equally good fits landed each day`,
    hover: { xs: rows.map((_, i) => xs(i)), x0: left, x1: w - rm, top: 30, bottom: y0 + botH, ys: i => [PD[i][1], PF[i][1]], tipY: i => Math.min(PD[i][1], PF[i][1]) - 8,
      html: i => `<b>${shortDate(rows[i][0])}</b>: best fit ${(rows[i][1] * 100).toFixed(3)}%, flat ${(rows[i][2] * 100).toFixed(3)}%, fits ${rows[i][3].toFixed(2)} apart` } };
});

// ------------------------------------------------------------------ skew by maturity
registerChart('skew', (w, o, ctx) => {
  const rows = ctx.D.skew_by_T;
  const h = o.h, left = 40, right = 16, top = 30, bottom = 40;
  const xs = scale(7, 730, left, w - right, true), ys = scale(0, 4, h - bottom, top);
  let b = '';
  for (const v of [0, 1, 2, 3, 4]) b += L(left, ys(v), w - right, ys(v), v ? 'grid' : 'axis') + T(left - 10, ys(v) + 5, String(v), '', 'end');
  const lab = { 7: '1 wk', 30: '1 mo', 90: '3 mo', 365: '1 yr', 730: '2 yr' };
  for (const k of [7, 30, 90, 365, 730]) b += T(xs(k), h - bottom + 22, lab[k], '', 'middle');
  const P = rows.map(r => [xs(r[0]), ys(r[1])]);
  b += Pa(P, 'c-model a-draw', 'pathLength="1"');
  b += P.map((p, i) => Ci(p[0], p[1], 4.5, 'c-fill-model a-pop', `style="--i:${i};--d:700ms"`)).join('');
  b += T(P[0][0] + 10, P[0][1] - 14, `${rows[0][1].toFixed(1)} points at 1 week`, 't-strong a-fade', 'start', 'style="--d:900ms"');
  b += T(P[P.length - 1][0], P[P.length - 1][1] + 26, `${rows[rows.length - 1][1].toFixed(1)} at 2 years`, 't-strong a-fade', 'end', 'style="--d:1000ms"');
  return { h, body: b, label: `Skew by time to expiry: ${rows[0][1].toFixed(1)} volatility points at one week falling to ${rows[rows.length - 1][1].toFixed(1)} at two years`,
    hover: { xs: P.map(p => p[0]), x0: left, x1: w - right, top, bottom: h - bottom, ys: i => [P[i][1]], tipY: i => P[i][1] - 8,
      html: i => `${rows[i][0]} days: skew <b>${rows[i][1].toFixed(2)}</b> points, at-the-money <b>${rows[i][2].toFixed(1)}%</b>` } };
});

// ------------------------------------------------------------------ shock decay (two clocks)
registerChart('decay', (w, o, ctx) => {
  const HL = ctx.D.half_life;
  const h = o.h, left = 52, right = 18, top = 20, bottom = 40;
  const xs = scale(0, 2, left, w - right), ys = scale(0, 1, h - bottom, top);
  let b = '';
  for (const v of [0, 0.5, 1]) b += L(left, ys(v), w - right, ys(v), v ? 'grid' : 'axis') + T(left - 10, ys(v) + 5, `${v * 100}%`, '', 'end');
  for (const yr of [0, 0.5, 1, 1.5, 2]) b += T(xs(yr), h - bottom + 22, `${yr} yr`, '', 'middle');
  b += L(left, ys(0.5), w - right, ys(0.5), 'c-ref');
  b += T(xs(1.2), ys(0.5) + 22, 'half of the shock gone', '', 'middle');
  const tsx = Array.from({ length: 121 }, (_, i) => i / 60);
  b += Pa(tsx.map(t => [xs(t), ys(Math.exp(-0.5 * t))]), 'c-alt a-draw slow-line', 'pathLength="1" style="stroke-width:var(--c-lw, 3.5)"');
  b += Pa(tsx.map(t => [xs(t), ys(Math.exp(-5 * t))]), 'c-model a-draw fast-line', 'pathLength="1" style="--d:250ms"');
  const hs = HL.slow_years, hf = HL.fast_days / 365;
  b += Ci(xs(hs), ys(0.5), 6.5, 'a-pop', 'style="fill:var(--c-alt, var(--ink));--d:1300ms"') + Ci(xs(hf), ys(0.5), 6.5, 'c-fill-model a-pop', 'style="--d:1100ms"');
  const slowLab = `slow: half gone in ${hs.toFixed(1)} years`, room = w - right - xs(hs) > slowLab.length * o.fs * 0.56 + 16;
  b += T(room ? xs(hs) + 12 : xs(hs) - 4, ys(0.5) - 16, slowLab, 't-strong a-fade', room ? 'start' : 'end', 'style="--d:1400ms"');
  b += T(xs(hf) + 14, ys(0.5) - 14, `fast: ${HL.fast_days.toFixed(0)} days`, 't-strong a-fade', 'start', 'style="--d:1200ms"');
  return { h, body: b, label: `Share of a volatility shock left over two years: the fast factor loses half in ${HL.fast_days.toFixed(0)} days, the slow factor in ${hs.toFixed(1)} years` };
});

// ------------------------------------------------------------------ Monte Carlo fan
registerChart('fan', (w, o, ctx) => {
  const F = ctx.D.fan, q = F.quantiles, n = q['50'].length, npaths = o.paths || 60;
  const h = o.h, left = 48, right = w < 700 ? 16 : 130, top = 16, bottom = 34;
  let lo = Math.min(...F.paths.slice(0, npaths).map(p => Math.min(...p)), ...q['5']) - 3;
  let hi = Math.max(...F.paths.slice(0, npaths).map(p => Math.max(...p)), ...q['95']) + 3;
  const xs = scale(0, n - 1, left, w - right), ys = scale(lo, hi, h - bottom, top);
  let b = '';
  for (const v of ticks(lo, hi, 4)) b += L(left, ys(v), w - right, ys(v)) + T(left - 8, ys(v) + 5, String(v), '', 'end');
  const band = (a, c) => q[a].map((v, i) => [xs(i), ys(v)]).concat(q[c].map((v, i) => [xs(i), ys(v)]).reverse());
  b += `<path d="${dPath(band('95', '5'))}Z" class="c-fill-model a-fade" style="opacity:.10;--d:900ms"/>`;
  b += `<path d="${dPath(band('75', '25'))}Z" class="c-fill-model a-fade" style="opacity:.16;--d:1000ms"/>`;
  F.paths.slice(0, npaths).forEach((p, j) => {
    b += Pa(p.map((v, i) => [xs(i), ys(v)]), 'fan-path a-draw', `pathLength="1" style="--d:${(j * 18)}ms;fill:none;stroke:var(--c-path, var(--muted));stroke-width:1;opacity:.5"`);
  });
  b += Pa(q['50'].map((v, i) => [xs(i), ys(v)]), 'c-model a-draw', 'pathLength="1" style="--d:1100ms"');
  if (w >= 700) for (const [k, lab] of [['95', '95th percentile'], ['50', 'median'], ['5', '5th percentile']]) b += T(w - right + 10, ys(q[k][n - 1]) + 5, lab, k === '50' ? 't-strong a-fade' : 'a-fade', 'start', 'style="--d:1400ms"');
  for (const [i, lab] of [[0, 'today'], [Math.floor(n / 2), '6 months'], [n - 1, '1 year']]) b += T(xs(i), h - 8, lab, '', 'middle');
  return { h, body: b, label: `${npaths} simulated Double Heston price paths over one year from 100, with the middle 50% and 90% bands` };
});

// ------------------------------------------------------------------ implied-vol surface (heat)
registerChart('surface', (w, o, ctx) => {
  const S = ctx.D.surface;
  const vals = S.iv.flat().filter(v => v != null);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const left = 92, top = 12, right = 14, bottom = 40;
  const h = o.h;
  const cw = (w - left - right) / S.strikes.length, ch = (h - top - bottom) / S.days.length;
  const lab = { 7: '1 week', 14: '2 weeks', 30: '1 month', 60: '2 months', 90: '3 months', 180: '6 months', 365: '1 year' };
  let b = '';
  S.days.forEach((dd, r) => {
    const yy = top + r * ch;
    b += T(left - 12, yy + ch / 2 + 5, lab[dd], '', 'end');
    S.iv[r].forEach((v, c) => {
      const x = left + c * cw;
      if (v == null) { b += R(x + 1.5, yy + 1.5, cw - 3, ch - 3, '', 'rx="5" style="fill:var(--raised)"') + T(x + cw / 2, yy + ch / 2 + 5, '≈ 0', '', 'middle'); return; }
      const k = (v - lo) / (hi - lo + 1e-9);
      const pct = Math.round(12 + k * 80);
      b += `<g class="a-pop" style="--i:${r * S.strikes.length + c};--d:0ms">` + R(x + 1.5, yy + 1.5, cw - 3, ch - 3, '', `rx="5" style="fill:color-mix(in oklab, var(--c-heat, var(--acc)) ${pct}%, var(--bg))"`) +
        T(x + cw / 2, yy + ch / 2 + 5, v.toFixed(1), '', 'middle', `style="fill:${k > 0.55 ? 'var(--on-acc)' : 'var(--ink)'};font-weight:600;font-size:13px"`) + '</g>';
    });
  });
  S.strikes.forEach((k, c) => { b += T(left + c * cw + cw / 2, h - 14, `${k}%`, '', 'middle'); });
  return { h, body: b, label: 'Implied volatility surface at the starting settings: rows are time to expiry, columns are strike as a percentage of today\'s price' };
});

// ------------------------------------------------------------------ one surface, fitted twice (ferro_pair.json)
registerChart('pairPool', (w, o, ctx) => {
  const P = ctx.P, sd = P.smile_dense;
  const h = o.h, left = 50, right = 14, top = 44, bottom = 46;
  const xs = scale(0.90, 1.10, left, w - right), ys = scale(14, 18, h - bottom, top);
  const gid = uid('pool');
  let b = `<defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--liq-top, color-mix(in srgb, var(--c-model, var(--acc)) 45%, transparent))"/><stop offset="1" style="stop-color:var(--liq-bot, color-mix(in srgb, var(--c-model, var(--acc)) 8%, transparent))"/></linearGradient></defs>`;
  for (const v of [15, 16, 17, 18]) b += L(left, ys(v), w - right, ys(v)) + T(left - 10, ys(v) + 5, `${v}%`, '', 'end');
  for (const m of [0.90, 0.95, 1.00, 1.05, 1.10]) b += T(xs(m), h - bottom + 22, `${Math.round(m * 100)}%`, '', 'middle');
  b += T((left + w - right) / 2, h - 4, 'Strike, as a percentage of the share price', '', 'middle');
  const A = sd.m.map((m, i) => [xs(m), ys(sd.a[i] * 100)]), B = sd.m.map((m, i) => [xs(m), ys(sd.b[i] * 100)]);
  const base = ys(14);
  b += `<path d="${dPath(A)}L${f1(A[A.length - 1][0])},${f1(base)}L${f1(A[0][0])},${f1(base)}Z" class="pair-liquid a-rise" style="fill:url(#${gid})"/>`;
  b += Pa(A, 'c-model pair-a a-draw', 'pathLength="1"');
  b += Pa(B, 'pair-b a-fade', 'style="--d:900ms"');
  const mk = P.slots.filter(s => s.rank === 2 && s.obs_iv && ((s.type === 'put') === (s.moneyness <= 1)));
  b += mk.map((s, i) => Ci(xs(s.moneyness), ys(s.obs_iv * 100), 6.5, 'c-dot-mk a-pop', `style="--i:${i};--d:1100ms"`)).join('');
  b += `<g class="a-fade" style="--d:200ms">${Ci(left + 8, 16, 6, 'c-dot-mk')}${T(left + 22, 21, 'Market close, 39-day options', 't-ink')}` +
    `${R(left + 250, 10, 26, 12, 'c-fill-model', 'rx="3"')}${T(left + 284, 21, 'Fit A', 't-strong')}` +
    `${L(left + 338, 16, left + 370, 16, 'pair-b')}${T(left + 378, 21, 'Fit B', 't-strong')}</g>`;
  return { h, body: b, label: 'Bharti Airtel 39-day implied volatility by strike: market quotes, and two different Double Heston fits whose curves lie on top of each other' };
});

const COLS = [
  ['kappa', 'Speed back to normal', v => Math.log(v / 0.1) / Math.log(300), v => `half-life ${halfLife(v)}`],
  ['theta', 'Long-run level', v => Math.sqrt(Math.max(v, 0)) / 0.7, v => `${(Math.sqrt(Math.max(v, 0)) * 100).toFixed(0)}% vol`],
  ['sigma', 'Volatility of volatility', v => v, v => v.toFixed(2)],
  ['rho', 'Link to price moves', v => (v + 1) / 2, v => (v < 0 ? '−' : '+') + Math.abs(v).toFixed(2)],
  ['v0', "Today's level", v => Math.sqrt(Math.max(v, 0)) / 0.3, v => `${(Math.sqrt(Math.max(v, 0)) * 100).toFixed(1)}% vol`],
];
export function halfLife(k) { const d = Math.log(2) / k * 365; return d >= 300 ? `${(d / 365).toFixed(1)} yr` : `${d.toFixed(0)} days`; }
// ferrofluid spikes with depth (Ferro): cone shading lit from the left, a darker right edge, a
// specular streak down the lit flank, a bright tip and a soft contact shadow. defs3d() once per svg.
export function defs3d(id) {
  return `<defs><linearGradient id="${id}b" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" style="stop-color:var(--ferro)"/><stop offset=".26" style="stop-color:var(--ferro-sheen, #6B7079)"/>
      <stop offset=".44" style="stop-color:var(--ferro)"/><stop offset=".86" style="stop-color:var(--ferro)"/><stop offset="1" style="stop-color:#000"/></linearGradient>
    <linearGradient id="${id}s" x1="0" x2="0" y1="0" y2="1"><stop offset="0" style="stop-color:#fff;stop-opacity:.9"/><stop offset="1" style="stop-color:#fff;stop-opacity:0"/></linearGradient>
    <radialGradient id="${id}c"><stop offset="0" style="stop-color:#000;stop-opacity:.35"/><stop offset="1" style="stop-color:#000;stop-opacity:0"/></radialGradient></defs>`;
}
export function spike3d(id, cx, base, h, hw, extra = '') {
  h = Math.max(h, 4);
  const top = base - h;
  const shade = h > 10 ? `<path d="M${f1(cx - 1.4)},${f1(top + 4)} Q${f1(cx - hw * 0.2)},${f1(base - h * 0.45)} ${f1(cx - hw * 0.58)},${f1(base - 2)}" style="fill:none;stroke:url(#${id}s);stroke-width:1.6;stroke-linecap:round;opacity:.85"/>` +
    `<circle cx="${f1(cx - 0.5)}" cy="${f1(top + 2.5)}" r="1.3" style="fill:#fff;opacity:.8"/>` : '';
  return `<g class="spike3d" ${extra}><ellipse cx="${f1(cx)}" cy="${f1(base + 1)}" rx="${f1(hw * 1.25)}" ry="3.2" style="fill:url(#${id}c)"/>` +
    `<path d="${spikePath(cx, base, h, hw)}" style="fill:url(#${id}b);stroke:var(--ferro-hi);stroke-opacity:.35;stroke-width:.8"/>${shade}</g>`;
}
export function spikePath(cx, base, h, hw) {
  h = Math.max(h, 4);
  return `M${f1(cx - hw)},${f1(base)} C${f1(cx - hw * 0.35)},${f1(base - 2)} ${f1(cx - 3)},${f1(base - h * 0.62)} ${f1(cx)},${f1(base - h)} C${f1(cx + 3)},${f1(base - h * 0.62)} ${f1(cx + hw * 0.35)},${f1(base - 2)} ${f1(cx + hw)},${f1(base)} Z`;
}
registerChart('pairMagnets', (w, o, ctx) => {
  const P = ctx.P, names = P.names, hiB = Object.fromEntries(names.map((n, i) => [n, P.phys_hi[i]]));
  const narrow = w < 900;
  const labelW = narrow ? 0 : 150, cw = (w - labelW) / 10, rowH = 156, top = 70;
  const fits = [['Fit A', P.a, P.a_rmse * P.spot], ['Fit B', P.b, P.b_rmse * P.spot]];
  const h = top + fits.length * rowH + (narrow ? fits.length * 30 : 0);
  const sid = uid('sp');
  let b = o.spike3d ? defs3d(sid) : '';
  [['Slow factor', 0], ['Fast factor', 5]].forEach(([lab, x0]) => {
    const gx = labelW + x0 * cw;
    b += T(gx + 8, 16, lab, 't-strong') + L(gx + 8, 25, gx + 5 * cw - 8, 25, 'axis', 'style="stroke:var(--ink);stroke-width:1.5"');
  });
  for (let i = 0; i < 10; i++) {
    const words = COLS[i % 5][1].split(' ');
    const cut = Math.ceil(words.length / 2);
    const cx = labelW + i * cw + cw / 2;
    if (words.length > 2) b += T(cx, 44, words.slice(0, cut).join(' '), '', 'middle', 'style="font-size:12.5px"') + T(cx, 59, words.slice(cut).join(' '), '', 'middle', 'style="font-size:12.5px"');
    else b += T(cx, 52, COLS[i % 5][1], '', 'middle', 'style="font-size:12.5px"');
  }
  fits.forEach(([lab, fit, err], r) => {
    const yTop = top + r * (rowH + (narrow ? 30 : 0)) + (narrow ? 30 : 0);
    const base = yTop + rowH - 34;
    if (narrow) b += T(0, yTop - 6, `${lab}: misses by ₹${err.toFixed(2)} an option`, 't-strong');
    else b += T(0, base - 44, lab, 't-strong', 'start', 'style="font-size:22px;font-family:var(--font-display)"') + T(0, base - 20, `misses by ₹${err.toFixed(2)}`, '', 'start', 'style="font-size:13px"');
    b += L(labelW, base, w, base, 'axis');
    for (let i = 0; i < 10; i++) {
      const [key, , hf, vf] = COLS[i % 5];
      const name = `${key}_${i < 5 ? 's' : 'f'}`;
      const v = fit[name];
      const cx = labelW + i * cw + cw / 2;
      const sh = clamp(hf(v), 0, 1) * (rowH - 56);
      b += o.spike3d ? spike3d(sid, cx, base, sh, cw * 0.34, `class="a-rise" style="--i:${r * 10 + i};--d:${r * 250}ms"`)
        : `<path d="${spikePath(cx, base, sh, cw * 0.34)}" class="spike a-rise" style="--i:${r * 10 + i};--d:${r * 250}ms"/>`;
      const star = Math.abs(v - hiB[name]) < 1e-3 * Math.max(1, Math.abs(hiB[name])) ? '*' : '';
      b += T(cx, base + 21, vf(v) + star, 't-ink', 'middle', `style="font-weight:600;font-size:${narrow ? 11 : 13}px"`);
    }
  });
  return { h, body: b, label: 'The ten settings of two equally good fits to one real surface, drawn as spikes: the two rows look very different' };
});
registerChart('pairPart', (w, o, ctx) => {
  const P = ctx.P, T_ = P.term;
  const h = o.h, left = 56, right = w < 700 ? 20 : 150, top = 16, bottom = 40;
  const xs = scale(4, 730, left, w - right, true), ys = scale(8, 46, h - bottom, top);
  let b = R(xs(4), top, xs(39) - xs(4), h - bottom - top, '', 'style="fill:var(--raised)"') + T(xs(4) + 10, top + 22, 'traded that day', 't-strong') + T(xs(4) + 10, top + 42, '4 and 39 days');
  for (const v of [10, 20, 30, 40]) b += L(left, ys(v), w - right, ys(v)) + T(left - 10, ys(v) + 5, `${v}%`, '', 'end');
  for (const [dd, lab] of [[4, '4 days'], [39, '39 days'], [90, '3 months'], [180, '6 months'], [365, '1 year'], [730, '2 years']]) b += T(xs(dd), h - bottom + 22, lab, '', 'middle');
  const A = T_.days.map((dd, i) => [xs(dd), ys(T_.a[i] * 100)]), B = T_.days.map((dd, i) => [xs(dd), ys(T_.b[i] * 100)]);
  b += Pa(A, 'c-model pair-a a-draw', 'pathLength="1"');
  b += Pa(B, 'pair-b a-fade', 'style="--d:700ms"');
  for (const [rank, dd] of [[1, 4], [2, 39]]) {
    const vs = P.slots.filter(s => s.rank === rank && Math.abs(s.moneyness - 1) < 0.01 && s.obs_iv).map(s => s.obs_iv);
    b += Ci(xs(dd), ys(vs.reduce((a, c) => a + c, 0) / vs.length * 100), 6.5, 'c-dot-mk a-pop', 'style="--d:300ms"');
  }
  const i1 = T_.days.indexOf(365), a1 = T_.a[i1] * 100, b1 = T_.b[i1] * 100;
  b += `<g class="a-fade" style="--d:1500ms">${L(xs(365), ys(a1) + 10, xs(365), ys(b1) - 10, 'axis', 'style="stroke:var(--ink);stroke-width:1.5;stroke-dasharray:3 4"')}` +
    T(xs(365) + 12, (ys(a1) + ys(b1)) / 2 + 5, `${(a1 - b1).toFixed(1)} points`, 't-strong t-big') + '</g>';
  if (w >= 700) {
    const ea = A[A.length - 1], eb = B[B.length - 1];
    b += T(ea[0] + 14, ea[1] + 5, `Fit A ${(T_.a[T_.a.length - 1] * 100).toFixed(1)}%`, 't-strong a-fade', 'start', 'style="--d:1500ms"');
    b += T(eb[0] + 14, eb[1] + 5, `Fit B ${(T_.b[T_.b.length - 1] * 100).toFixed(1)}%`, 't-strong a-fade', 'start', 'style="--d:1500ms"') + T(eb[0] + 14, eb[1] + 24, 'at 2 years', 'a-fade', 'start', 'style="--d:1500ms"');
  }
  const lg = xs(39) + 24;
  b += `<g class="a-fade">${Ci(lg + 6, top + 16, 6, 'c-dot-mk')}${T(lg + 20, top + 21, 'market, at the money')}` +
    `${L(lg, top + 42, lg + 28, top + 42, 'c-model')}${T(lg + 38, top + 47, 'Fit A')}${L(lg + 96, top + 42, lg + 124, top + 42, 'pair-b')}${T(lg + 134, top + 47, 'Fit B')}</g>`;
  return { h, body: b, label: `At-the-money volatility by time to expiry for two equally good fits: equal on the traded 4- and 39-day expiries, ${(a1 - b1).toFixed(1)} points apart at one year`,
    hover: { xs: A.map(p => p[0]), x0: left, x1: w - right, top, bottom: h - bottom, ys: i => [A[i][1], B[i][1]], tipY: i => Math.min(A[i][1], B[i][1]) - 8,
      html: i => `${T_.days[i]} days: fit A <b>${(T_.a[i] * 100).toFixed(1)}%</b>, fit B <b>${(T_.b[i] * 100).toFixed(1)}%</b>` } };
});
registerChart('pairSix', (w, o, ctx) => {
  const P = ctx.P, narrow = w < 760;
  const labelW = narrow ? 150 : 250, right = narrow ? 14 : 30, rowH = 56, tw = w - labelW - right;
  const sc = {
    kappa: [scale(0.1, 30, 0, tw, true), [[0.1, '6.9 yr'], [1, '8 months'], [10, '25 days'], [30, '8 days']], v => v],
    theta: [scale(0, 70, 0, tw), [[0, '0%'], [35, '35%'], [70, '70%']], v => Math.sqrt(Math.max(v, 0)) * 100],
    sigma: [scale(0, 1, 0, tw), [[0, '0'], [0.5, '0.5'], [1, '1']], v => v],
    rho: [scale(-1, 1, 0, tw), [[-1, '−1'], [0, '0'], [1, '+1']], v => v],
    v0: [scale(0, 30, 0, tw), [[0, '0%'], [15, '15%'], [30, '30%']], v => Math.sqrt(Math.max(v, 0)) * 100],
  };
  const nm = { kappa: 'Speed back to normal', theta: 'Long-run level', sigma: 'Volatility of volatility', rho: 'Link to price moves', v0: "Today's level" };
  const sid = uid('sp');
  let b = o.spike3d ? defs3d(sid) : '', y = 0, i = 0;
  for (const [g, suf] of [['Slow factor', 's'], ['Fast factor', 'f']]) {
    b += T(0, y + 22, g, 't-strong', 'start', 'style="font-size:16px"');
    y += 34;
    for (const key of ['kappa', 'theta', 'sigma', 'rho', 'v0']) {
      const [s, tk, conv] = sc[key];
      const base = y + rowH - 18;
      b += T(0, base - 4, nm[key], 't-ink', 'start', `style="font-size:${narrow ? 13 : 14.5}px"`);
      b += L(labelW, base, labelW + tw, base, 'axis');
      for (const [tv, tl] of tk) b += T(labelW + s(tv), base + 17, tl, '', 'middle', 'style="font-size:12px"');
      const vals = P.all_equivalent.map(e => conv(e[`${key}_${suf}`])).sort((a, c) => a - c);
      vals.forEach(v => {
        const x = labelW + s(clamp(v, s.d0, s.d1));
        b += o.spike3d ? spike3d(sid, x, base, rowH - 26, 9, `class="a-rise" style="--i:${i++}"`) : `<path d="${spikePath(x, base, rowH - 26, 9)}" class="spike a-rise" style="--i:${i++}"/>`;
      });
      y += rowH;
    }
    y += 16;
  }
  return { h: y, body: b, label: 'Each of the six equally good fits for Bharti Airtel on 21 Aug 2026, drawn as a spike on each setting\'s scale' };
});

// median helper re-export for pages
export { median };
