// Ferro's navigation: a chrome rail with a bead on the current page. As the cursor approaches, black
// ferrofluid wells out of the rail and spikes toward it (tallest nearest the cursor, leaning toward
// it), with glossy highlights; page names appear. Canvas, animated only while the cursor is near or
// the fluid is still settling. Keyboard (focus) and touch (tap) open it too.
import { motionOK, on } from './state.js';
import { clamp, esc } from './util.js';

const REACH = 240, SIGMA = 62, SITE_GAP = 20, K = 260, C = 22;

export function createFerroNav({ pages, current }) {
  const nav = document.createElement('nav');
  nav.className = 'fnav';
  nav.setAttribute('aria-label', 'Pages');
  const cur = Math.max(0, pages.findIndex(p => p.id === current));
  nav.innerHTML = `<div class="fnav-panel" aria-hidden="true"></div><canvas aria-hidden="true"></canvas><span class="fnav-rail" aria-hidden="true"></span>
    <span class="fnav-bead" aria-hidden="true"></span>` +
    pages.map((p, k) => `<a class="fnav-a" href="${p.file}"${k === cur ? ' aria-current="page"' : ''}><span class="fnav-l">${esc(p.label)}</span></a>`).join('');
  document.body.appendChild(nav);
  const ac = new AbortController();
  const sig = { signal: ac.signal };

  const canvas = nav.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const bead = nav.querySelector('.fnav-bead');
  const links = [...nav.querySelectorAll('.fnav-a')];
  const labels = links.map(a => a.querySelector('.fnav-l'));
  const PAD = 40; // canvas extends 40px above and below the rail
  let H = 0, CW = 200, CH = 0, dpr = 1, sites = [], ys = [], box, colors;

  function readColors() {
    const cs = getComputedStyle(document.documentElement);
    const dark = document.documentElement.dataset.mode === 'dark';
    // on a black page, pure black fluid would vanish: dark mode uses graphite so the body still reads
    colors = { fluid: dark ? '#1C1D21' : (cs.getPropertyValue('--ferro').trim() || '#0a0a0b'), hi: cs.getPropertyValue('--ferro-hi').trim() || '#c8ccd2', dark };
  }
  function layout() {
    H = nav.offsetHeight;
    CH = H + PAD * 2;
    dpr = Math.min(2, devicePixelRatio || 1);
    canvas.width = CW * dpr; canvas.height = CH * dpr;
    ys = pages.map((_, k) => (k / (pages.length - 1)) * H);
    links.forEach((a, k) => { a.style.top = `${ys[k]}px`; });
    bead.style.top = `${ys[cur]}px`;
    const n = Math.floor(H / SITE_GAP) + 1;
    sites = Array.from({ length: n }, (_, i) => ({ y: PAD + i * (H / (n - 1)), h: 0, v: 0, lean: 0, vl: 0 }));
    box = nav.getBoundingClientRect();
    readColors();
    draw(0);
  }

  let px = -1e4, py = 0, P = 0, mound = 0, vm = 0, forced = null, running = false, last = 0;
  const reduced = !motionOK();

  function target() {
    if (forced) return { P: forced.P, cy: forced.y };
    if (px < -1e3) return { P: 0, cy: py };
    const dx = (box.width - 17) - px;
    let p = clamp(1 - (dx - 20) / REACH, 0, 1);
    if (py < -60 || py > H + 60) p *= clamp(1 - (Math.min(Math.abs(py), Math.abs(py - H)) - 60) / 120, 0, 1);
    return { P: p, cy: py };
  }

  function draw() {
    const w = CW, rx = w - 17; // rail centre x in canvas px
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, CH);
    if (mound < 0.01 && sites.every(s => s.h < 0.3)) return;
    // the fluid edge: a mound hugging the rail plus the tallest spike at each height
    const edge = [];
    for (let y = PAD - 30; y <= PAD + H + 30; y += 2) {
      const g = Math.exp(-((y - PAD - cyNow) ** 2) / (2 * 120 * 120));
      let e = 4 + mound * 14 * g;
      for (const s of sites) {
        const u = Math.abs(y - (s.y + s.lean)) / 11;
        if (u < 1) e = Math.max(e, 4 + mound * 14 * g + s.h * (1 - u) ** 2.4);
      }
      edge.push([rx - 3 - e, y]);
    }
    const grad = ctx.createLinearGradient(rx - 90, 0, rx, 0);
    grad.addColorStop(0, colors.fluid);
    grad.addColorStop(0.7, colors.fluid);
    grad.addColorStop(1, colors.dark ? '#2a2c30' : '#34373c');
    ctx.beginPath();
    ctx.moveTo(rx, edge[0][1]);
    for (const [x, y] of edge) ctx.lineTo(x, y);
    ctx.lineTo(rx, edge[edge.length - 1][1]);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.globalAlpha = clamp(mound * 1.6, 0, 1);
    ctx.fill();
    // depth: shade each spike like a cone lit from above (bright upper flank, dark lower edge)
    ctx.globalAlpha = clamp(mound * 1.4, 0, 1);
    for (const s of sites) {
      if (s.h < 6) continue;
      const yc = s.y + s.lean, root = rx - 3 - (4 + mound * 14 * Math.exp(-((s.y - PAD - cyNow) ** 2) / (2 * 120 * 120)));
      ctx.beginPath();
      ctx.moveTo(root + 2, yc - 11);
      for (let k = -11; k <= 11; k += 1) ctx.lineTo(root - s.h * (1 - Math.abs(k) / 11) ** 2.4, yc + k);
      ctx.lineTo(root + 2, yc + 11);
      ctx.closePath();
      const sh = ctx.createLinearGradient(0, yc - 8, 0, yc + 8);
      sh.addColorStop(0, 'rgba(255,255,255,0)');
      sh.addColorStop(0.3, colors.dark ? 'rgba(210,216,224,0.40)' : 'rgba(170,176,186,0.45)');
      sh.addColorStop(0.5, 'rgba(255,255,255,0.03)');
      sh.addColorStop(0.8, 'rgba(0,0,0,0.35)');
      sh.addColorStop(1, 'rgba(0,0,0,0.45)');
      ctx.fillStyle = sh;
      ctx.fill();
    }
    // glossy rim and specular streaks on each spike's upper flank
    ctx.lineJoin = 'round';
    ctx.strokeStyle = colors.hi;
    ctx.globalAlpha = clamp(mound, 0, 1) * (colors.dark ? 0.9 : 0.55);
    ctx.lineWidth = 1;
    if (colors.dark) { ctx.shadowColor = colors.hi; ctx.shadowBlur = 6; }
    ctx.beginPath();
    edge.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.lineWidth = 1.6;
    ctx.lineCap = 'round';
    for (const s of sites) {
      if (s.h < 8) continue;
      const base = rx - 7 - mound * 10;
      ctx.globalAlpha = clamp(s.h / 60, 0, 0.85);
      ctx.beginPath();
      ctx.moveTo(base, s.y + s.lean - 6);
      ctx.quadraticCurveTo(base - s.h * 0.45, s.y + s.lean - 3.2, base - s.h * 0.86, s.y + s.lean - 0.8);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  let cyNow = 0;
  function step(t) {
    const dt = Math.min(0.033, last ? (t - last) / 1000 : 0.016);
    last = t;
    const { P: tp, cy } = target();
    P = tp; cyNow = cy;
    nav.classList.toggle('open', P > 0.3);
    let moving = false;
    const tm = P;
    if (reduced) { mound = tm; vm = 0; } else { vm += (K * (tm - mound) - C * vm) * dt; mound += vm * dt; }
    if (Math.abs(tm - mound) + Math.abs(vm) > 0.002) moving = true;
    const dxAbs = forced ? 60 : Math.max(30, (box.width - 17) - px);
    for (const s of sites) {
      const dy = (cy + PAD) - s.y;
      const g = Math.exp(-(dy * dy) / (2 * SIGMA * SIGMA));
      const th = P * 78 * g ** 1.3 * (0.85 + 0.15 * Math.cos(s.y * 0.7));
      const tl = clamp(dy * 0.28 * g * P * (60 / dxAbs), -9, 9);
      if (reduced) { s.h = th; s.lean = tl; s.v = s.vl = 0; }
      else {
        s.v += (K * (th - s.h) - C * s.v) * dt; s.h = Math.max(0, s.h + s.v * dt);
        s.vl += (K * (tl - s.lean) - C * s.vl) * dt; s.lean += s.vl * dt;
      }
      if (Math.abs(th - s.h) + Math.abs(s.v) > 0.15) moving = true;
    }
    labels.forEach((l, k) => {
      const dy = cy - ys[k];
      const lo = clamp(P * (0.4 + 0.6 * Math.exp(-(dy * dy) / (2 * 110 * 110))), 0, 1);
      l.style.opacity = lo.toFixed(3);
      l.style.transform = `translateX(${((1 - lo) * 8).toFixed(2)}px)`;
    });
    draw();
    if (moving || P > 0) requestAnimationFrame(step);
    else { running = false; last = 0; }
  }
  function kick() { if (!running) { running = true; requestAnimationFrame(step); } }

  layout();
  addEventListener('resize', () => { layout(); kick(); }, sig);
  const off = on(what => { if (what === 'mode') { readColors(); draw(); } });
  document.addEventListener('pointermove', e => {
    if (e.pointerType === 'touch') return;
    const x = e.clientX - box.left, y = e.clientY - box.top;
    if (x > box.width - REACH - 80 || P > 0) { px = x; py = y; kick(); }
  }, { passive: true, signal: ac.signal });
  document.addEventListener('pointerleave', () => { px = -1e4; kick(); }, sig);
  addEventListener('scroll', () => { box = nav.getBoundingClientRect(); }, { passive: true, signal: ac.signal });
  nav.addEventListener('focusin', e => {
    const a = e.target.closest('.fnav-a');
    if (a) { forced = { P: 1, y: parseFloat(a.style.top) }; kick(); }
  });
  nav.addEventListener('focusout', e => { if (!nav.contains(e.relatedTarget)) { forced = null; px = -1e4; kick(); } });
  nav.addEventListener('pointerdown', e => {
    if (e.pointerType === 'touch' && !forced) { e.preventDefault(); forced = { P: 1, y: ys[cur] }; kick(); }
  });
  nav.addEventListener('click', e => {
    if (!nav.classList.contains('open') && e.target.closest('.fnav-a') && matchMedia('(hover: none)').matches) e.preventDefault();
  });
  document.addEventListener('pointerdown', e => {
    if (forced && e.pointerType === 'touch' && !nav.contains(e.target)) { forced = null; px = -1e4; kick(); }
  }, sig);

  return { el: nav, destroy() { ac.abort(); off(); nav.remove(); } };
}
