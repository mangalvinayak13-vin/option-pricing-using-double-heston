// "Magnetic dashes": a column of small squircle-ish dashes on the page edge. As the cursor comes
// near, dashes are pulled toward it (stretch, lean, shift) with a smooth falloff, and the page names
// appear. Page dashes are longer; the current page stays marked. Animates only while the cursor is
// near or the springs are still settling; works with the keyboard (focus opens it) and touch (tap).
import { motionOK } from './state.js';
import { clamp, esc } from './util.js';

const MINOR = 3;           // small dashes between two page dashes
const REACH = 230;         // px from the rail where the pull starts
const SIGMA = 58;          // vertical falloff of the pull
const K = 340, C = 27;     // spring stiffness and damping (per unit mass)

export function createDashNav({ pages, current, side = 'l' }) {
  const nav = document.createElement('nav');
  nav.className = `mdash side-${side}`;
  nav.setAttribute('aria-label', 'Pages');
  const n = pages.length + (pages.length - 1) * MINOR;
  let html = '<div class="mdash-panel" aria-hidden="true"></div><div class="mdash-hit" aria-hidden="true"></div>';
  const dashes = [];
  for (let i = 0; i < n; i++) {
    const p = i % (MINOR + 1) === 0 ? pages[i / (MINOR + 1)] : null;
    dashes.push({ page: p, s: 1, vs: 0, r: 0, vr: 0, x: 0, vx: 0, lo: 0, vlo: 0 });
    html += `<span class="mdash-d${p ? ' pg' : ''}${p && p.id === current ? ' cur' : ''}" data-i="${i}"></span>`;
  }
  pages.forEach((p, k) => {
    html += `<a class="mdash-a" href="${p.file}" data-k="${k}"${p.id === current ? ' aria-current="page"' : ''}><span class="mdash-l">${esc(p.label)}</span></a>`;
  });
  nav.innerHTML = html;
  // before the page content (after the switch), so the page list comes early in keyboard order
  const anchorEl = document.querySelector(".dh-controls") || document.querySelector(".skip");
  if (anchorEl) anchorEl.after(nav); else document.body.prepend(nav);
  const ac = new AbortController();
  const sig = { signal: ac.signal };

  const els = [...nav.querySelectorAll('.mdash-d')];
  const links = [...nav.querySelectorAll('.mdash-a')];
  const labels = links.map(a => a.querySelector('.mdash-l'));
  let H = 0, ys = [], box = null;

  function layout() {
    H = nav.offsetHeight;
    ys = dashes.map((_, i) => (i / (n - 1)) * H);
    els.forEach((el, i) => { el.style.top = `${ys[i]}px`; });
    links.forEach((a, k) => { a.style.top = `${ys[k * (MINOR + 1)]}px`; });
    box = nav.getBoundingClientRect();
  }
  layout();
  addEventListener('resize', () => { layout(); kick(); }, sig);

  // pointer state in nav coordinates; P = how close to the rail (0..1)
  let px = -1e4, py = H / 2, P = 0, forced = null, running = false, last = 0;
  const reduced = !motionOK();

  function targets() {
    let P_ = 0, cy = py;
    if (forced) { P_ = forced.P; cy = forced.y; }
    else if (px > -1e3) {
      const dx = side === 'l' ? px - 18 : (box.width - 18) - px;
      P_ = clamp(1 - (dx - 24) / REACH, 0, 1);
      if (cy < -80 || cy > H + 80) P_ *= clamp(1 - (Math.min(Math.abs(cy), Math.abs(cy - H)) - 80) / 120, 0, 1);
    }
    return { P: P_, cy };
  }

  function step(t) {
    const dt = Math.min(0.033, last ? (t - last) / 1000 : 0.016);
    last = t;
    const { P: P_, cy } = targets();
    P = P_;
    nav.classList.toggle('open', P > 0.32);
    let moving = false;
    const dxAbs = forced ? 60 : Math.max(30, Math.abs(side === 'l' ? px - 18 : (box.width - 18) - px));
    dashes.forEach((d, i) => {
      const dy = cy - ys[i];
      const g = Math.exp(-(dy * dy) / (2 * SIGMA * SIGMA));
      const s = P * g;
      const tS = 1 + (d.page ? 1.5 : 2.3) * s;
      let tR = Math.atan2(dy, dxAbs) * 180 / Math.PI * s * 0.85;
      tR = clamp(tR, -34, 34) * (side === 'l' ? 1 : -1);
      const tX = (side === 'l' ? 1 : -1) * 5 * s;
      const tLo = d.page ? P * (0.4 + 0.6 * Math.exp(-(dy * dy) / (2 * 110 * 110))) : 0;
      if (reduced) { d.s = tS; d.r = tR; d.x = tX; d.lo = tLo; d.vs = d.vr = d.vx = d.vlo = 0; }
      else {
        d.vs += (K * (tS - d.s) - C * d.vs) * dt; d.s += d.vs * dt;
        d.vr += (K * (tR - d.r) - C * d.vr) * dt; d.r += d.vr * dt;
        d.vx += (K * (tX - d.x) - C * d.vx) * dt; d.x += d.vx * dt;
        d.vlo += (K * 0.8 * (tLo - d.lo) - C * d.vlo) * dt; d.lo += d.vlo * dt;
      }
      if (Math.abs(tS - d.s) + Math.abs(d.vs) > 0.002 || Math.abs(tR - d.r) + Math.abs(d.vr) > 0.05 ||
          Math.abs(tLo - d.lo) + Math.abs(d.vlo) > 0.003) moving = true;
      els[i].style.transform = `translateX(${d.x.toFixed(2)}px) rotate(${d.r.toFixed(2)}deg) scaleX(${d.s.toFixed(3)})`;
      if (d.page) {
        const k = i / (MINOR + 1);
        const lo = clamp(d.lo, 0, 1);
        labels[k].style.opacity = lo.toFixed(3);
        labels[k].style.transform = `translateX(${((1 - lo) * (side === 'l' ? -8 : 8) + d.x * 2).toFixed(2)}px)`;
      }
    });
    if (moving || P > 0) requestAnimationFrame(step);
    else { running = false; last = 0; }
  }
  function kick() { if (!running) { running = true; requestAnimationFrame(step); } }

  // mouse / pen: listen on the document, but only wake up when the pointer is near the edge
  document.addEventListener('pointermove', e => {
    if (e.pointerType === 'touch') return;
    const x = e.clientX - box.left, y = e.clientY - box.top;
    const near = side === 'l' ? x < REACH + 60 : x > box.width - REACH - 60;
    if (near || P > 0) { px = x; py = y; kick(); }
  }, { passive: true, signal: ac.signal });
  document.addEventListener('pointerleave', () => { px = -1e4; kick(); }, sig);
  addEventListener('scroll', () => { box = nav.getBoundingClientRect(); }, { passive: true, signal: ac.signal });

  // keyboard: focusing a link opens the nav with the magnet at that link
  nav.addEventListener('focusin', e => {
    const a = e.target.closest('.mdash-a');
    if (a) { forced = { P: 1, y: parseFloat(a.style.top) }; kick(); }
  });
  nav.addEventListener('focusout', e => { if (!nav.contains(e.relatedTarget)) { forced = null; px = -1e4; kick(); } });

  // touch: tap the edge to open, tap a name to go, tap elsewhere to close
  nav.addEventListener('pointerdown', e => {
    if (e.pointerType !== 'touch') return;
    if (!forced) { e.preventDefault(); forced = { P: 1, y: H / 2 }; kick(); }
  });
  nav.addEventListener('click', e => {
    if (!nav.classList.contains('open') && e.target.closest('.mdash-a') && matchMedia('(hover: none)').matches) e.preventDefault();
  });
  document.addEventListener('pointerdown', e => {
    if (forced && e.pointerType === 'touch' && !nav.contains(e.target)) { forced = null; px = -1e4; kick(); }
  }, sig);

  return { el: nav, destroy() { ac.abort(); nav.remove(); } };
}
