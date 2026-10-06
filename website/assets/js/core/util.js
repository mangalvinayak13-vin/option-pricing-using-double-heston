// Small shared helpers: escaping, number formats (Indian grouping), scales, ticks, timing.

export const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export function inr(v, dp = 2) {
  if (v == null || !Number.isFinite(v)) return '–';
  const neg = v < 0;
  let [whole, frac] = Math.abs(v).toFixed(dp).split('.');
  if (whole.length > 3) {
    let head = whole.slice(0, -3);
    const tail = whole.slice(-3);
    const parts = [];
    while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
    if (head) parts.unshift(head);
    whole = [...parts, tail].join(',');
  }
  return (neg ? '−' : '') + whole + (frac ? '.' + frac : '');
}

export const fmt = {
  inr, rupee: (v, dp = 2) => '₹' + inr(v, dp), pct: (v, dp = 2) => (v == null ? '–' : v.toFixed(dp) + '%'),
  num: (v, dp = 2) => (v == null ? '–' : (v < 0 ? '−' : '') + Math.abs(v).toFixed(dp)),
  signed: (v, dp = 2) => (v == null ? '–' : (v < 0 ? '−' : '+') + Math.abs(v).toFixed(dp)),
};

export function arrow(p) { return p >= 0 ? ['▲', 'up'] : ['▼', 'dn']; }

export function scale(d0, d1, r0, r1, log = false) {
  const f = log ? Math.log : x => x;
  const a = f(d0), b = f(d1);
  const s = v => r0 + (f(v) - a) / (b - a) * (r1 - r0);
  s.d0 = d0; s.d1 = d1; s.r0 = r0; s.r1 = r1;
  s.invert = y => { const t = a + (y - r0) / (r1 - r0) * (b - a); return log ? Math.exp(t) : t; };
  return s;
}

export function niceStep(span, target) {
  const raw = span / Math.max(target, 1);
  const mag = 10 ** Math.floor(Math.log10(raw));
  for (const m of [1, 2, 2.5, 5, 10]) if (raw <= m * mag) return m * mag;
  return 10 * mag;
}

export function ticks(lo, hi, target = 5) {
  const step = niceStep(hi - lo, target);
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const median = arr => { const s = [...arr].sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

export function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

// run at most once per animation frame, with the latest arguments
export function rafThrottle(fn) {
  let queued = false, last;
  return (...a) => { last = a; if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; fn(...last); }); } };
}

let uidN = 0;
export const uid = (p = 'u') => `${p}${(++uidN).toString(36)}`;

export const shortDate = d => `${+d.slice(8, 10)} ${'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')[+d.slice(5, 7) - 1]}`;

export const $ = (sel, el = document) => el.querySelector(sel);
export const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
