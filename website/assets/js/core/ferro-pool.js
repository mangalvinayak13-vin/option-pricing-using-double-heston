// A pool for one variance factor. It starts as clear, calm water; when it comes into view it turns
// into ferrofluid, black, glossy and spiking. Each spike is driven by its own simulated variance
// under the factor's real settings, dv = κ(θ − v)dt + ξ√v dZ with full truncation, so a fast factor
// (large κ) reacts and settles quickly, a slow one drifts, and a larger ξ makes bigger spikes.
// Canvas; runs only while on screen; reduced motion draws the settled ferrofluid once.
import { loop, reduced, whenInView } from './motion.js';
import { rng, cirStep } from './factors.js';

export function ferroPool(host, { params, label, seed = 3, speed = 0.12 } = {}) {
  const cv = document.createElement('canvas');
  cv.className = 'fp-canvas';
  cv.setAttribute('role', 'img');
  host.appendChild(cv);
  const g = cv.getContext('2d');
  const R = rng(seed);
  let p = { ...params };
  const N = 17, dt = 1 / 365;
  let v = Array.from({ length: N }, () => p.v0 ?? p.theta);
  let W = 0, H = 0, dpr = 1, col = {}, t = 0, clock = 0, acc = 0, ferro = reduced() ? 1 : 0, started = reduced();

  const describe = () => cv.setAttribute('aria-label', `${label}: κ ${p.kappa.toFixed(2)}, ξ ${p.xi.toFixed(2)}. Ferrofluid spikes follow simulated variance: larger κ settles faster, larger ξ spikes higher.`);
  describe();
  const size = () => {
    dpr = Math.min(2, devicePixelRatio || 1);
    W = host.clientWidth; H = host.clientHeight || 170;
    cv.width = W * dpr; cv.height = H * dpr; cv.style.width = `${W}px`; cv.style.height = `${H}px`;
    const cs = getComputedStyle(host);
    col = { fluid: cs.getPropertyValue('--ferro').trim() || '#050505', hi: cs.getPropertyValue('--ferro-hi').trim() || '#c8ccd2',
      water: cs.getPropertyValue('--water').trim() || 'rgb(150 185 210 / .35)', waterLine: cs.getPropertyValue('--water-line').trim() || 'rgb(120 160 190 / .9)',
      dark: document.documentElement.dataset.mode === 'dark' };
  };

  function draw() {
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    const base = H - 26, span = W - 24, x0 = 12;
    const f = ferro, kxi = Math.min(2, p.xi / 0.5);
    const edge = [];
    for (let x = 0; x <= span; x += 3) {
      const ripple = Math.sin(x * 0.045 + clock * 1.6) * 2.2 + Math.sin(x * 0.11 - clock * 2.3) * 1.1;
      let spike = 0;
      for (let j = 0; j < N; j++) {
        const xj = (j + 0.5) / N * span;
        const u = Math.abs(x - xj) / (span / N * 0.5);
        if (u < 1) {
          const amp = Math.min(3, Math.max(0, v[j]) / p.theta) * 26 * kxi;
          spike = Math.max(spike, amp * (1 - u) ** 2.3);
        }
      }
      edge.push([x0 + x, base - 16 - (ripple * (1 - f)) - spike * f]);
    }
    // body
    g.beginPath();
    g.moveTo(x0, H - 6);
    edge.forEach(([x, y]) => g.lineTo(x, y));
    g.lineTo(x0 + span, H - 6);
    g.closePath();
    const gr = g.createLinearGradient(0, base - 90, 0, H);
    if (f < 1) { gr.addColorStop(0, col.water); gr.addColorStop(1, col.water); g.globalAlpha = 1 - f; g.fillStyle = gr; g.fill(); }
    if (f > 0) {
      const gf = g.createLinearGradient(0, base - 90, 0, H);
      gf.addColorStop(0, col.dark ? '#2b2d31' : '#3a3d42'); gf.addColorStop(0.35, col.fluid); gf.addColorStop(1, col.fluid);
      g.globalAlpha = f; g.fillStyle = gf; g.fill();
    }
    g.globalAlpha = 1;
    // surface line: a bright water line, then a glossy rim on the ferrofluid
    g.beginPath();
    edge.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y)));
    g.lineWidth = f < 1 ? 1.6 : 1.1;
    g.strokeStyle = f < 0.5 ? col.waterLine : col.hi;
    g.globalAlpha = f < 0.5 ? 1 - f : (col.dark ? 0.95 : 0.7) * f;
    if (col.dark && f > 0.5) { g.shadowColor = col.hi; g.shadowBlur = 6; }
    g.stroke();
    g.shadowBlur = 0;
    // specular streaks on each spike's left flank
    if (f > 0.3) {
      g.lineWidth = 1.5; g.lineCap = 'round'; g.strokeStyle = '#ffffff';
      for (let j = 0; j < N; j++) {
        const amp = Math.min(3, Math.max(0, v[j]) / p.theta) * 26 * kxi * f;
        if (amp < 10) continue;
        const xj = x0 + (j + 0.5) / N * span, top = base - 16 - amp, hw = span / N * 0.5;
        g.globalAlpha = Math.min(0.75, amp / 70) * f;
        g.beginPath(); g.moveTo(xj - 1.6, top + 5); g.quadraticCurveTo(xj - hw * 0.2, top + amp * 0.5, xj - hw * 0.55, base - 18); g.stroke();
      }
    }
    g.globalAlpha = 1;
  }

  function step(dtSec) {
    clock += dtSec;
    if (started && ferro < 1) ferro = Math.min(1, ferro + dtSec / 2.4);
    acc += dtSec * speed;
    let n = 0;
    while (acc >= dt && n < 20) { acc -= dt; n++; for (let j = 0; j < N; j++) v[j] = cirStep(v[j], p, dt, R.normal()); }
    draw();
  }

  size();
  if (reduced()) {
    // show the settled ferrofluid: run the variance forward a little so spikes differ
    for (let k = 0; k < 120; k++) for (let j = 0; j < N; j++) v[j] = cirStep(v[j], p, dt, R.normal());
    draw();
  } else {
    draw();
    whenInView(host, () => { started = true; });
  }
  const onResize = () => { size(); draw(); };
  addEventListener('resize', onResize);
  const L = reduced() ? { stop() {} } : loop(host, dt_ => step(dt_));
  return {
    set(np) { p = { ...p, ...np }; describe(); if (reduced()) draw(); },
    stop() { L.stop(); removeEventListener('resize', onResize); },
  };
}
