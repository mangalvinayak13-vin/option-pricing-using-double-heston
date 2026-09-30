// Motion system. Charts animate in once when scrolled into view (and again when their data changes);
// numbers count up; long-running loops pause off-screen and in hidden tabs. Only transform/opacity
// are animated on HTML; SVG line draws use stroke-dashoffset on pathLength=1 paths. Reduced motion:
// everything shows its end state.
import { motionOK } from './state.js';
import { fmt } from './util.js';

const root = document.documentElement;
export const reduced = () => !motionOK();
if (!reduced()) root.classList.add('motion');

// ---- easing
export const ease = {
  outExpo: t => (t >= 1 ? 1 : 1 - 2 ** (-10 * t)),
  outCubic: t => 1 - (1 - t) ** 3,
  inOut: t => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2),
  // under-damped spring (same family as the CSS --spring-* curves)
  spring: (t, z = 0.62, w = 11) => {
    if (t >= 1) return 1;
    const wd = w * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t));
  },
};

// tween a number; returns a cancel function
export function tween(dur, fn, e = ease.outCubic, done) {
  if (reduced()) { fn(1); done && done(); return () => {}; }
  let raf, t0;
  const tick = t => {
    t0 ??= t;
    const k = Math.min(1, (t - t0) / dur);
    fn(e(k));
    if (k < 1) raf = requestAnimationFrame(tick); else done && done();
  };
  raf = requestAnimationFrame(tick);
  return () => cancelAnimationFrame(raf);
}

// ---- loops that must stop when off-screen or in a hidden tab
const loops = new Set();
export function loop(el, frame) {
  // frame(dt, t) returns nothing; runs only while el is on screen and the tab is visible
  const L = { el, frame, visible: false, raf: 0, last: 0 };
  const run = t => {
    const dt = Math.min(0.05, L.last ? (t - L.last) / 1000 : 0.016);
    L.last = t;
    L.frame(dt, t);
    L.raf = requestAnimationFrame(run);
  };
  L.start = () => { if (!L.raf && L.visible && !document.hidden) { L.last = 0; L.raf = requestAnimationFrame(run); } };
  L.stop = () => { cancelAnimationFrame(L.raf); L.raf = 0; };
  L.io = new IntersectionObserver(([en]) => { L.visible = en.isIntersecting; L.visible ? L.start() : L.stop(); }, { rootMargin: '80px' });
  L.io.observe(el);
  loops.add(L);
  return { stop() { L.stop(); L.io.disconnect(); loops.delete(L); } };
}
document.addEventListener('visibilitychange', () => loops.forEach(L => (document.hidden ? L.stop() : L.start())));
export function stopAllLoops() { loops.forEach(L => { L.stop(); L.io.disconnect(); }); loops.clear(); }

// ---- reveal-on-view: adds .is-in once; data-anim elements, [data-count] numbers, and callbacks
let io;
const onIn = new WeakMap();
export function whenInView(el, cb) { onIn.set(el, cb); io.observe(el); }
// called by the app before each render, so observers never hold nodes from a previous theme
export function resetObservers() { initIO(); }
initIO();
function initIO() {
  io?.disconnect();
  io = new IntersectionObserver(entries => {
    for (const en of entries) {
      if (!en.isIntersecting) continue;
      const el = en.target;
      io.unobserve(el);
      el.classList.add('is-in');
      if (el.hasAttribute('data-count')) countUp(el);
      const cb = onIn.get(el);
      if (cb) { onIn.delete(el); cb(el); }
    }
  }, { threshold: 0.18, rootMargin: '0px 0px -6% 0px' });
}

export function observe(scope) {
  scope.querySelectorAll('[data-anim],[data-count]').forEach(el => {
    if (reduced()) { el.classList.add('is-in'); if (el.hasAttribute('data-count')) countUp(el, true); }
    else io.observe(el);
  });
  initParallax(scope);
  initGlint(scope);
  initTickers(scope);
}

// numbers: <b data-count="600.4" data-fmt="rupee" data-dp="2">₹600.40</b>
export function countUp(el, instant = false) {
  const to = parseFloat(el.dataset.count);
  const dp = +(el.dataset.dp ?? 2);
  const f = fmt[el.dataset.fmt || 'num'] || fmt.num;
  const from = parseFloat(el.dataset.from ?? (to > 0 ? 0 : to));
  const write = v => { el.textContent = (el.dataset.pre || '') + f(v, dp) + (el.dataset.suf || ''); };
  if (instant || reduced()) return write(to);
  el._cancel = tween(+(el.dataset.dur || 1100), k => write(from + (to - from) * k), ease.outExpo);
}

// animate a number already on screen to a new value (model reprices)
export function retarget(el, to, { dp = 2, f = fmt.num, pre = '', suf = '', dur = 520 } = {}) {
  const from = parseFloat(el.dataset.v ?? to);
  el.dataset.v = to;
  if (!Number.isFinite(to)) { el.textContent = '–'; return; }
  if (reduced() || Math.abs(from - to) < 1e-9) { el.textContent = pre + f(to, dp) + suf; return; }
  el._cancel?.();
  el._cancel = tween(dur, k => { el.textContent = pre + f(from + (to - from) * k, dp) + suf; }, ease.outCubic);
}

// morph an SVG polyline's points from one array to another (same length)
export function morphPoints(poly, from, to, dur = 900, e = t => ease.spring(t, 0.7, 9)) {
  const set = k => poly.setAttribute('points', to.map((p, i) => `${(from[i][0] + (p[0] - from[i][0]) * k).toFixed(1)},${(from[i][1] + (p[1] - from[i][1]) * k).toFixed(1)}`).join(' '));
  poly._cancel?.();
  poly._cancel = tween(dur, set, e);
}

// ---- subtle parallax for hero layers: [data-parallax="0.06"]
let parallaxEls = [];
function initParallax(scope) {
  parallaxEls = reduced() ? [] : [...scope.querySelectorAll('[data-parallax]')];
}
let pq = false;
addEventListener('scroll', () => {
  if (!parallaxEls.length || pq) return;
  pq = true;
  requestAnimationFrame(() => {
    pq = false;
    const vh = innerHeight;
    for (const el of parallaxEls) {
      const r = el.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) continue;
      const c = (r.top + r.height / 2 - vh / 2) / vh;
      el.style.transform = `translate3d(0, ${(-c * parseFloat(el.dataset.parallax) * 100).toFixed(2)}px, 0)`;
    }
  });
}, { passive: true });

// ---- cursor-following highlight: [data-glint]; the light moves by transform only
function initGlint(scope) {
  if (reduced() || matchMedia('(hover: none)').matches) return;
  scope.querySelectorAll('[data-glint]').forEach(el => {
    let g = el.querySelector(':scope > .glint');
    if (!g) { g = document.createElement('span'); g.className = 'glint'; g.setAttribute('aria-hidden', 'true'); el.prepend(g); }
    let raf = 0, x = 0, y = 0;
    el.addEventListener('pointermove', e => {
      const r = el.getBoundingClientRect();
      x = e.clientX - r.left; y = e.clientY - r.top;
      if (!raf) raf = requestAnimationFrame(() => { raf = 0; g.style.transform = `translate3d(${x}px, ${y}px, 0)`; });
    }, { passive: true });
  });
}

// ---- tickers: pause when off-screen or in a hidden tab (CSS pauses on hover/focus)
const tickIO = new IntersectionObserver(es => es.forEach(en => en.target.classList.toggle('paused', !en.isIntersecting || document.hidden)));
function initTickers(scope) { scope.querySelectorAll('.tick').forEach(t => tickIO.observe(t)); }
document.addEventListener('visibilitychange', () => document.querySelectorAll('.tick').forEach(t => {
  if (document.hidden) t.classList.add('paused');
  else { const r = t.getBoundingClientRect(); t.classList.toggle('paused', r.bottom < 0 || r.top > innerHeight); }
}));
