// The model's two variance factors, simulated live: dv = κ(θ − v)dt + ξ√v dZ with full truncation
// (the same scheme as the project's simulator), at the starting settings. The fast factor (κ 5)
// jitters and snaps back; the slow one (κ 0.5) drifts. Runs only while on screen.
import { loop, reduced } from './motion.js';

export const FACTORS = {
  slow: { kappa: 0.5, theta: 0.02, xi: 0.3, v0: 0.02 },
  fast: { kappa: 5.0, theta: 0.02, xi: 0.5, v0: 0.02 },
};

// small seeded PRNG + normals, so every visitor sees the same kind of path
export function rng(seed = 7) {
  let s = seed >>> 0;
  const u = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  let spare = null;
  u.normal = () => {
    if (spare !== null) { const v = spare; spare = null; return v; }
    let a, b, r;
    do { a = u() * 2 - 1; b = u() * 2 - 1; r = a * a + b * b; } while (r === 0 || r >= 1);
    const m = Math.sqrt(-2 * Math.log(r) / r);
    spare = b * m;
    return a * m;
  };
  return u;
}

export function cirStep(v, p, dt, z) {
  const vp = Math.max(v, 0);
  return v + p.kappa * (p.theta - vp) * dt + p.xi * Math.sqrt(vp) * Math.sqrt(dt) * z;
}

// a pre-run path, used for the static (reduced-motion) picture and to fill the trace at start
export function path(p, years, dt = 1 / 365, seed = 11) {
  const r = rng(seed), out = [];
  let v = p.v0;
  for (let t = 0; t <= years; t += dt) { out.push(Math.max(v, 0)); v = cirStep(v, p, dt, r.normal()); }
  return out;
}

// live trace on a canvas: two lines of volatility (√v, in %) scrolling right to left
export function factorTrace(host, { span = 2, speed = 0.22, lw = 2.4, grid = true } = {}) {
  const cv = document.createElement('canvas');
  cv.setAttribute('aria-hidden', 'true');
  host.appendChild(cv);
  const g = cv.getContext('2d');
  const dt = 1 / 365, N = Math.round(span / dt);
  const R = rng(19);
  const buf = { slow: path(FACTORS.slow, span, dt, 3), fast: path(FACTORS.fast, span, dt, 5) };
  let v = { slow: buf.slow[buf.slow.length - 1], fast: buf.fast[buf.fast.length - 1] };
  let acc = 0, W = 0, H = 0, dpr = 1, col = {};
  const size = () => {
    dpr = Math.min(2, devicePixelRatio || 1);
    W = host.clientWidth; H = host.clientHeight || 220;
    cv.width = W * dpr; cv.height = H * dpr; cv.style.width = W + 'px'; cv.style.height = H + 'px';
    const cs = getComputedStyle(host);
    col = { fast: cs.getPropertyValue('--c-model').trim() || cs.getPropertyValue('--acc').trim(), slow: cs.getPropertyValue('--c-alt').trim() || cs.getPropertyValue('--ink').trim(),
      grid: cs.getPropertyValue('--grid').trim(), muted: cs.getPropertyValue('--muted').trim(), font: cs.getPropertyValue('--font-chart').trim() || 'sans-serif' };
  };
  const draw = () => {
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    const top = 14, bot = H - 14, vmax = 0.36;
    const y = vol => bot - Math.min(vol, vmax) / vmax * (bot - top);
    if (grid) {
      g.strokeStyle = col.grid; g.lineWidth = 1; g.fillStyle = col.muted; g.font = `13px ${col.font}`;
      for (const p of [0, 0.1, 0.2, 0.3]) { g.beginPath(); g.moveTo(40, y(p)); g.lineTo(W, y(p)); g.stroke(); g.fillText(`${p * 100}%`, 0, y(p) + 4); }
    }
    for (const k of ['slow', 'fast']) {
      const b = buf[k], n = b.length;
      g.beginPath();
      for (let i = 0; i < n; i++) {
        const x = 44 + (i / (N - 1)) * (W - 52);
        const yy = y(Math.sqrt(b[i]));
        i ? g.lineTo(x, yy) : g.moveTo(x, yy);
      }
      g.strokeStyle = col[k]; g.lineWidth = lw; g.lineJoin = 'round'; g.stroke();
      const yl = y(Math.sqrt(b[n - 1]));
      g.fillStyle = col[k]; g.beginPath(); g.arc(W - 8, yl, 4.5, 0, Math.PI * 2); g.fill();
    }
  };
  size();
  addEventListener('resize', () => { size(); draw(); });
  draw();
  if (reduced()) return { stop() {} };
  return loop(host, dtSec => {
    acc += dtSec * speed;
    let steps = 0;
    while (acc >= dt && steps < 12) {
      acc -= dt; steps++;
      for (const k of ['slow', 'fast']) {
        v[k] = cirStep(v[k], FACTORS[k], dt, R.normal());
        buf[k].push(Math.max(v[k], 0));
        if (buf[k].length > N) buf[k].shift();
      }
    }
    if (steps) draw();
  });
}
