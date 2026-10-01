// PINN vs ANN in 3D: each network's option-price surface at today's volatility (pinn_vs_ann.json),
// drawn as lit quads with the exact Double Heston price as a grey grid on top. Patches priced below
// zero (impossible for an option) are drawn in the "down" colour. Both views turn together: slowly
// on their own while on screen, by dragging, or with the arrow keys. Canvas 2D, no libraries.
//
// Two controls sit above the views:
//   Price | Error   Error draws network minus exact price on one fixed scale for both networks, over
//                   a grey grid at zero, so the gap itself is what you see.
//   training steps  replays training from pinn_vs_ann_steps.json (both networks' surfaces after 50 to
//                   10,000 steps), by slider or by Replay training, which glides between checkpoints.
import { loop, reduced } from './motion.js';

// a patch counts as an impossible price when it is below zero by more than 0.2% of the strike
export const NEG = -0.002;
// the error view's fixed scale: gaps beyond 2.5% of the strike are drawn at the cap
const ERR_CAP = 0.025;

function parseColor(c, fallback = [10, 132, 255]) {
  c = (c || '').trim();
  if (c.startsWith('#')) {
    const h = c.length === 4 ? c.slice(1).split('').map(x => x + x).join('') : c.slice(1, 7);
    return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16));
  }
  const m = c.match(/\d+(\.\d+)?/g);
  return m && m.length >= 3 ? m.slice(0, 3).map(Number) : fallback;
}

const fmtInt = n => n.toLocaleString('en-IN');

export function createPA3D(host, PA) {
  const S = PA.slice, ns = S.s.length, nt = S.tau.length;
  const fig = host.closest('figure') || host.parentElement;
  const $ = sel => fig.querySelector(sel);
  // frames: [{ step, ann, pinn, read: { ann: {rmse_rel, impossible}, pinn: {...} } }]; the final one is
  // always available from pinn_vs_ann.json, the earlier ones arrive with pinn_vs_ann_steps.json
  let frames = [{ step: PA.setup.steps, ann: S.ann, pinn: S.pinn, read: null }];
  let pos = 0;                 // fractional frame index while replaying
  let view = 'price';
  // price scale: the exact surface and every replayed network surface fit inside it
  let zmax = Math.max(...S.exact.flat(), ...S.ann.flat(), ...S.pinn.flat());
  let zmin = Math.min(0, ...S.ann.flat(), ...S.pinn.flat());
  const X = i => (i / (ns - 1)) * 2 - 1, Y = j => (j / (nt - 1)) * 2 - 1;
  const Zp = v => ((v - zmin) / (zmax - zmin)) * 1.25 - 0.45;
  const Ze = v => (Math.max(-ERR_CAP, Math.min(ERR_CAP, v)) / ERR_CAP) * 0.62 + 0.18;
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
  // fit the whole scene inside the panel over the whole sway, so the zoom stays steady while it turns
  let fit = { k: 1, ox: 0, oy: 0 };
  function refit() {
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const keep = yaw;
    for (const a of [keep, -1.17, -0.9, -0.62, -0.35, -0.07]) {
      yaw = a;
      const take = (x, y, z) => { const [p, q] = raw(x, y, z); x0 = Math.min(x0, p); x1 = Math.max(x1, p); y0 = Math.min(y0, q); y1 = Math.max(y1, q); };
      for (const [x, y] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { take(x, y, Zp(zmin)); take(x, y, Zp(zmax)); }
    }
    yaw = keep;
    const padX = 30, padTop = 44, padBottom = 58;  // room for the readout under each view
    const k = Math.min((W - 2 * padX) / (x1 - x0), (H - padTop - padBottom) / (y1 - y0));
    fit = { k, ox: padX + ((W - 2 * padX) - (x1 - x0) * k) / 2 - x0 * k, oy: padTop + ((H - padTop - padBottom) - (y1 - y0) * k) / 2 - y0 * k };
  }
  function project(x, y, z) {
    const [a, b, d] = raw(x, y, z);
    return [fit.ox + a * fit.k, fit.oy + b * fit.k, d];
  }

  // the network's prices at the current (possibly in-between) frame
  function pricesAt(net) {
    const i = Math.floor(pos), f = pos - i, A = frames[i][net], B = frames[Math.min(frames.length - 1, i + 1)][net];
    if (f < 1e-6 || A === B) return A;
    return A.map((row, j) => row.map((v, k) => v + (B[j][k] - v) * f));
  }

  function draw(v) {
    const g = v.g, price = pricesAt(v.net), err = view === 'error';
    const height = err ? (j, i) => Ze(price[j][i] - S.exact[j][i]) : (j, i) => Zp(price[j][i]);
    const floorZ = err ? Ze(-ERR_CAP) : Zp(0);
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    g.strokeStyle = col.axis; g.lineWidth = 1;
    const fl = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([x, y]) => project(x, y, floorZ));
    g.beginPath(); fl.forEach(([a, b], i) => (i ? g.lineTo(a, b) : g.moveTo(a, b))); g.closePath(); g.stroke();
    // quads of the network's surface, back to front
    const quads = [];
    for (let j = 0; j < nt - 1; j++) for (let i = 0; i < ns - 1; i++) {
      const c = [[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]].map(([a, b]) => [X(a), Y(b), height(b, a), price[b][a]]);
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
    // the exact pricer as a grey grid on top (in the error view: zero error, a flat grid)
    const ref = err ? () => Ze(0) : (j, i) => Zp(S.exact[j][i]);
    g.strokeStyle = col.mesh; g.globalAlpha = err ? 0.5 : 0.85; g.lineWidth = 1.2;
    for (let j = 0; j < nt; j += 3) { g.beginPath(); for (let i = 0; i < ns; i++) { const [a, b] = project(X(i), Y(j), ref(j, i)); i ? g.lineTo(a, b) : g.moveTo(a, b); } g.stroke(); }
    for (let i = 0; i < ns; i += 4) { g.beginPath(); for (let j = 0; j < nt; j++) { const [a, b] = project(X(i), Y(j), ref(j, i)); j ? g.lineTo(a, b) : g.moveTo(a, b); } g.stroke(); }
    g.globalAlpha = 1;
    g.fillStyle = col.text; g.font = `13px ${col.font}`;
    const lab = (txt, x, y, z) => { const [a, b] = project(x, y, z); g.fillText(txt, a, b); };
    lab('share price ÷ strike', 0.15, -1.25, floorZ); lab('time to expiry', 1.32, 0.8, floorZ);
    if (err) { lab('too high', -1.45, -1.1, Ze(ERR_CAP)); lab('too low', -1.45, -1.1, Ze(-ERR_CAP)); }
    else lab('price', -1.15, -1, Zp(zmax) + 0.05);
  }

  // readouts: the step, and each network's error and impossible prices on this slice
  const stepLabel = $('[data-pa-steplabel]'), slider = $('[data-pa-step]'), play = $('[data-pa-play]');
  const keyNet = $('[data-pa-keynet]'), keyExact = $('[data-pa-keyexact]');
  function readouts() {
    const fr = frames[Math.round(pos)];
    if (stepLabel) stepLabel.textContent = fmtInt(fr.step);
    if (slider && frames.length > 1) { slider.value = String(pos); slider.style.setProperty('--p', `${(pos / (frames.length - 1)) * 100}%`); }
    for (const net of ['ann', 'pinn']) {
      const el = $(`[data-pa-read="${net}"]`), r = fr.read?.[net];
      if (el && r) el.textContent = `On this slice: error ${(r.rmse_rel * 100).toFixed(1)}% of the average price · ${r.impossible ? fmtInt(r.impossible) : 'no'} impossible price${r.impossible === 1 ? '' : 's'}`;
    }
    if (keyNet) keyNet.textContent = view === 'error' ? `network minus exact price (gaps beyond ${ERR_CAP * 100}% of the strike drawn at the cap)` : "network's price";
    if (keyExact) keyExact.textContent = view === 'error' ? 'zero error' : 'exact Double Heston price';
  }

  const drawAll = () => { views.forEach(draw); readouts(); };
  size(); refit(); drawAll();

  // the training replay arrives separately so the page doesn't wait for it
  let alive = true;
  fetch('assets/data/pinn_vs_ann_steps.json').then(r => (r.ok ? r.json() : null)).then(d => {
    if (!alive || !d) return;
    const by = net => Object.fromEntries(d[net].map(f => [f.step, f]));
    const A = by('ann'), P = by('pinn');
    frames = d.checkpoints.filter(c => c > 0).map(c => ({ step: c, ann: A[c].grid, pinn: P[c].grid,
      read: { ann: { rmse_rel: A[c].rmse_rel, impossible: A[c].impossible }, pinn: { rmse_rel: P[c].rmse_rel, impossible: P[c].impossible } } }));
    // the last frame is the published run itself: keep its full-precision surfaces
    Object.assign(frames.at(-1), { ann: S.ann, pinn: S.pinn });
    for (const f of frames) for (const net of ['ann', 'pinn']) for (const row of f[net]) for (const v of row) { zmax = Math.max(zmax, v); zmin = Math.min(zmin, v); }
    pos = frames.length - 1;
    if (slider) { slider.max = String(frames.length - 1); slider.disabled = false; }
    refit(); drawAll();
  }).catch(() => {});
  if (slider) slider.disabled = true;

  // replay: glide from the first checkpoint to the last, about 0.6 s per checkpoint
  let replay = 0;
  const stopReplay = () => { if (replay) cancelAnimationFrame(replay); replay = 0; play?.setAttribute('aria-pressed', 'false'); };
  function startReplay() {
    stopReplay();
    if (frames.length < 2) return;
    play?.setAttribute('aria-pressed', 'true');
    pos = 0; drawAll();
    let last = performance.now();
    const still = reduced();
    const tick = now => {
      const dt = (now - last) / 1000;
      if (still) { if (dt < 0.7) { replay = requestAnimationFrame(tick); return; } pos = Math.floor(pos) + 1; last = now; }
      else { pos += dt / 0.6; last = now; }
      if (pos >= frames.length - 1) { pos = frames.length - 1; drawAll(); stopReplay(); return; }
      drawAll();
      replay = requestAnimationFrame(tick);
    };
    replay = requestAnimationFrame(tick);
  }
  play?.addEventListener('click', () => (replay ? stopReplay() : startReplay()));
  slider?.addEventListener('input', () => { stopReplay(); pos = Number(slider.value); drawAll(); });
  $('[data-seg="pa-view"]')?.addEventListener('seg', e => { view = e.detail; drawAll(); });

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
    if (!replay) views.forEach(draw);         // the replay redraws on its own
  });
  return { stop() { alive = false; stopReplay(); L.stop(); removeEventListener('resize', onResize); } };
}
