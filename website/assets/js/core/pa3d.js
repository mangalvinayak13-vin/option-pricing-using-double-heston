// PINN vs ANN in 3D: each network's option-price surface at today's volatility (pinn_vs_ann.json),
// drawn as lit quads with the exact Double Heston price as a grey mesh on top. Patches priced below
// zero (impossible for an option) are drawn in the "down" colour. Both views turn together: slowly
// on their own while on screen, by dragging, or with the arrow keys. Canvas 2D, no libraries.
import { loop, reduced } from './motion.js';

// a patch counts as an impossible price when it is below zero by more than 0.2% of the strike
export const NEG = -0.002;

function parseColor(c, fallback = [10, 132, 255]) {
  c = (c || '').trim();
  if (c.startsWith('#')) {
    const h = c.length === 4 ? c.slice(1).split('').map(x => x + x).join('') : c.slice(1, 7);
    return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
  }
  const m = c.match(/\d+(\.\d+)?/g);
  return m && m.length >= 3 ? m.slice(0, 3).map(Number) : fallback;
}

export function createPA3D(host, PA) {
  const S = PA.slice, ns = S.s.length, nt = S.tau.length;
  const zmax = Math.max(...S.exact.flat(), ...S.ann.flat(), ...S.pinn.flat());
  const zmin = Math.min(0, ...S.ann.flat(), ...S.pinn.flat());
  // world coordinates: x across (share price / strike), y depth (time to expiry), z up (price)
  const X = i => (i / (ns - 1)) * 2 - 1, Y = j => (j / (nt - 1)) * 2 - 1, Z = v => ((v - zmin) / (zmax - zmin)) * 1.25 - 0.45;
  const views = [...host.querySelectorAll('canvas[data-net]')].map(cv => ({ cv, g: cv.getContext('2d'), net: cv.dataset.net }));
  let yaw = -0.62, pitch = 0.5, t = 0, drag = null, W = 0, H = 0, dpr = 1, col = {};

  const size = () => {
    dpr = Math.min(2, devicePixelRatio || 1);
    views.forEach(v => {
      const r = v.cv.parentElement.getBoundingClientRect();
      W = Math.max(200, r.width); H = Math.round(Math.min(380, Math.max(240, W * 0.62)));
      v.cv.width = W * dpr; v.cv.height = H * dpr; v.cv.style.width = `${W}px`; v.cv.style.height = `${H}px`;
    });
    const cs = getComputedStyle(host);
    col = { acc: parseColor(cs.getPropertyValue('--c-model') || cs.getPropertyValue('--acc')), neg: parseColor(cs.getPropertyValue('--down'), [215, 0, 21]),
      mesh: cs.getPropertyValue('--muted').trim() || '#888', text: cs.getPropertyValue('--muted').trim() || '#888', axis: cs.getPropertyValue('--line').trim() || '#ccc',
      font: cs.getPropertyValue('--font-chart').trim() || 'sans-serif', dark: document.documentElement.dataset.mode === 'dark' };
  };

  // raw view coordinates (before fitting to the panel)
  function raw(x, y, z) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x1 = x * cy - y * sy, y1 = x * sy + y * cy;            // turn around the vertical axis
    const y2 = y1 * cp - z * sp, z2 = y1 * sp + z * cp;          // tip toward the viewer
    const f = 1 / (1 + y2 * 0.18);                               // gentle perspective
    return [x1 * f, -z2 * f, y2];
  }
  // fit the whole scene (floor, both networks' extremes, the exact surface) inside the panel, every frame
  let fit = { k: 1, ox: 0, oy: 0 };
  function refit() {
    // over the whole sway (and the current angle), so the zoom stays steady while the view turns
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const keep = yaw;
    for (const a of [keep, -1.17, -0.9, -0.62, -0.35, -0.07]) {
      yaw = a;
      const take = (x, y, z) => { const [p, q] = raw(x, y, z); x0 = Math.min(x0, p); x1 = Math.max(x1, p); y0 = Math.min(y0, q); y1 = Math.max(y1, q); };
      for (const [x, y] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { take(x, y, Z(zmin)); take(x, y, Z(zmax)); }
    }
    yaw = keep;
    const padX = 30, padTop = 44, padBottom = 34;
    const k = Math.min((W - 2 * padX) / (x1 - x0), (H - padTop - padBottom) / (y1 - y0));
    fit = { k, ox: padX + ((W - 2 * padX) - (x1 - x0) * k) / 2 - x0 * k, oy: padTop + ((H - padTop - padBottom) - (y1 - y0) * k) / 2 - y0 * k };
  }
  function project(x, y, z) {
    const [a, b, d] = raw(x, y, z);
    return [fit.ox + a * fit.k, fit.oy + b * fit.k, d];
  }

  function draw(v) {
    const g = v.g, grid = S[v.net];
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    // floor axes
    g.strokeStyle = col.axis; g.lineWidth = 1;
    const fl = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([x, y]) => project(x, y, Z(0)));
    g.beginPath(); fl.forEach(([a, b], i) => (i ? g.lineTo(a, b) : g.moveTo(a, b))); g.closePath(); g.stroke();
    // quads of the network's surface, back to front
    const quads = [];
    for (let j = 0; j < nt - 1; j++) for (let i = 0; i < ns - 1; i++) {
      const c = [[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]].map(([a, b]) => [X(a), Y(b), Z(grid[b][a]), grid[b][a]]);
      const p = c.map(q => project(q[0], q[1], q[2]));
      const ux = c[1][0] - c[0][0], uz = c[1][2] - c[0][2], vy = c[3][1] - c[0][1], vz = c[3][2] - c[0][2];
      const nx = -uz * vy, ny = -ux * vz, nz = ux * vy, nl = Math.hypot(nx, ny, nz) || 1;
      const light = Math.max(0, (nx * -0.35 + ny * -0.55 + nz * 0.76) / nl);
      quads.push({ p, d: (p[0][2] + p[1][2] + p[2][2] + p[3][2]) / 4, light, neg: c.some(q => q[3] < NEG) });
    }
    quads.sort((a, b) => b.d - a.d);
    for (const q of quads) {
      const base = q.neg ? col.neg : col.acc, k = 0.42 + 0.58 * q.light;
      const lift = col.dark ? 0.08 : 0;
      g.fillStyle = `rgb(${base.map(c => Math.round(Math.min(255, c * k + 255 * lift))).join(',')})`;
      g.beginPath(); q.p.forEach(([a, b], i) => (i ? g.lineTo(a, b) : g.moveTo(a, b))); g.closePath(); g.fill();
    }
    // the exact pricer as a light mesh on top
    g.strokeStyle = col.mesh; g.globalAlpha = 0.85; g.lineWidth = 1.2;
    for (let j = 0; j < nt; j += 3) { g.beginPath(); for (let i = 0; i < ns; i++) { const [a, b] = project(X(i), Y(j), Z(S.exact[j][i])); i ? g.lineTo(a, b) : g.moveTo(a, b); } g.stroke(); }
    for (let i = 0; i < ns; i += 4) { g.beginPath(); for (let j = 0; j < nt; j++) { const [a, b] = project(X(i), Y(j), Z(S.exact[j][i])); j ? g.lineTo(a, b) : g.moveTo(a, b); } g.stroke(); }
    g.globalAlpha = 1;
    // axis words
    g.fillStyle = col.text; g.font = `13px ${col.font}`;
    const lab = (txt, x, y, z) => { const [a, b] = project(x, y, z); g.fillText(txt, a, b); };
    lab('share price ÷ strike', 0.15, -1.25, Z(0)); lab('time to expiry', 1.1, 0.4, Z(0)); lab('price', -1.15, -1, Z(zmax) + 0.05);
  }

  const drawAll = () => views.forEach(draw);
  size(); refit(); drawAll();
  const onResize = () => { size(); refit(); drawAll(); };
  addEventListener('resize', onResize);
  host.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, yaw, pitch }; host.setPointerCapture(e.pointerId); });
  host.addEventListener('pointermove', e => {
    if (!drag) return;
    yaw = drag.yaw + (e.clientX - drag.x) * 0.008;
    pitch = Math.max(0.15, Math.min(1.1, drag.pitch + (e.clientY - drag.y) * 0.006));
    drawAll();
  });
  const end = () => { if (drag) { drag = null; refit(); drawAll(); } };
  host.addEventListener('pointerup', end); host.addEventListener('pointercancel', end);
  host.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); yaw += e.key === 'ArrowLeft' ? -0.12 : 0.12; drawAll(); }
  });
  const L = reduced() ? { stop() {} } : loop(host, dt => {
    if (drag) return;
    t += dt;
    yaw = -0.62 + Math.sin(t * 0.35) * 0.55;  // a slow, calm sway
    drawAll();
  });
  return { stop() { L.stop(); removeEventListener('resize', onResize); } };
}
