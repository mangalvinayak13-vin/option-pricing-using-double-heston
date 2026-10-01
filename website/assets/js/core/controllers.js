// Theme-agnostic page behaviour, wired by data attributes: the model page (live repricing through the
// worker), the market page (symbol, range, chart type), and the Results page (stock picker).
// Every choice goes into the store, so it survives a theme change.
import { store } from './state.js';
import { inr, fmt, esc, arrow, debounce, $, $$ } from './util.js';
import { retarget } from './motion.js';
import { renderChart, morphPath } from './charts.js';
import { price, DEFAULT_PARAMS, OFFLINE_HELP, feller } from './model.js';
import { stockLine } from './blocks.js';
import { createPA3D } from './pa3d.js';

export function mountControllers(scope, ctx) {
  const stops = [];
  segs(scope);
  videoSlots(scope, ctx);
  if (scope.querySelector('[data-ctl="model-form"], [data-param]')) modelPage(scope, ctx);
  if (scope.querySelector('[data-chart="candles"]')) marketPage(scope, ctx);
  if (scope.querySelector('[data-in="finding-sym"]')) findingPage(scope, ctx);
  $$('[data-pa3d]', scope).forEach(el => stops.push(createPA3D(el, ctx.PA)));
  $$('.b-dock-in', scope).forEach(d => stops.push(dockMagnify(d)));
  return () => stops.forEach(s => s && s.stop && s.stop());
}

// the page dock magnifies under the cursor like the macOS Dock (transform only; rAF-throttled)
function dockMagnify(dock) {
  if (!matchMedia('(hover: hover)').matches || !document.documentElement.classList.contains('motion')) return null;
  const items = [...dock.querySelectorAll('.b-dock-i')];
  let raf = 0, x = null;
  const apply = () => {
    raf = 0;
    items.forEach(it => {
      const r = it.getBoundingClientRect();
      const d = x == null ? 1e9 : Math.abs(x - (r.left + r.width / 2));
      const s = 1 + 0.38 * Math.exp(-(d * d) / (2 * 64 * 64));
      it.style.transform = s > 1.001 ? `translateY(${(-(s - 1) * 26).toFixed(1)}px) scale(${s.toFixed(3)})` : '';
    });
  };
  const move = e => { x = e.clientX; raf ||= requestAnimationFrame(apply); };
  const leave = () => { x = null; raf ||= requestAnimationFrame(apply); };
  dock.addEventListener('pointermove', move);
  dock.addEventListener('pointerleave', leave);
  return { stop() { dock.removeEventListener('pointermove', move); dock.removeEventListener('pointerleave', leave); } };
}

// the explainer video: loads only when someone presses play; until a file is set, the slot says so
function videoSlots(scope, ctx) {
  $$('[data-video]', scope).forEach(btn => btn.addEventListener('click', () => {
    const src = ctx.C.VIDEO_SRC;
    const fig = btn.closest('figure');
    if (!src) {
      const cap = fig?.querySelector('figcaption');
      if (cap) { cap.textContent = 'The video hasn\'t been added yet. Put the file in website/assets/video/ and set VIDEO_SRC in website/tools/content.py.'; cap.setAttribute('role', 'status'); }
      return;
    }
    const v = document.createElement('video');
    v.src = src; v.controls = true; v.autoplay = true; v.playsInline = true;
    v.className = 'video-slot'; v.setAttribute('aria-label', 'Project explainer video');
    btn.replaceWith(v);
    v.focus();
  }));
}

// segmented controls: move the thumb under the pressed button (transform only)
function segs(scope) {
  $$('.seg', scope).forEach(s => {
    const place = () => {
      const on = s.querySelector('button[aria-pressed="true"]');
      const th = s.querySelector('.seg-thumb');
      if (!on || !th) return;
      th.style.width = `${on.offsetWidth}px`;
      th.style.transform = `translateX(${on.offsetLeft - 3}px)`;
    };
    place();
    new ResizeObserver(place).observe(s);
    s.addEventListener('click', e => {
      const b = e.target.closest('button[data-v]');
      if (!b || b.getAttribute('aria-pressed') === 'true') return;
      s.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      place();
      s.dispatchEvent(new CustomEvent('seg', { detail: b.dataset.v, bubbles: true }));
    });
  });
}

// ------------------------------------------------------------------ the model page
function modelPage(scope, ctx) {
  const K = ctx.D.contract;
  const bind = k => $$(`[data-bind="${k}"]`, scope);
  let params = { ...DEFAULT_PARAMS, ...store.get('model.params', {}) };
  let strike = store.get('model.strike', K.strike), kind = store.get('model.kind', 'call');
  const isDefault = () => Object.keys(DEFAULT_PARAMS).every(k => Math.abs(params[k] - DEFAULT_PARAMS[k]) < 1e-9) && strike === K.strike && kind === 'call';

  const setStatus = (txt, cls = '') => bind('status').forEach(el => { el.textContent = txt; el.dataset.state = cls; });

  // market values for the chosen contract are fixed data; only the model's side is recomputed
  function marketSide() {
    const row = ctx.D.chain.find(r => r.strike === strike);
    const px = row[kind], iv = row[`${kind}_iv`];
    bind('mkt').forEach(el => { el.textContent = `₹${inr(px)}`; });
    bind('mkt-iv').forEach(el => { el.textContent = iv != null ? `${iv.toFixed(2)}%` : '–'; });
    bind('contract').forEach(el => { el.textContent = `NIFTY ${inr(strike, 0)} ${kind}`; });
    $$('.b-chain tr[data-strike]', scope).forEach(tr => tr.classList.toggle('sel', +tr.dataset.strike === strike));
    return px;
  }

  // once the model has been asked, its numbers are live: stop entrance count-ups from writing the defaults
  const liveNumbers = () => ['dh', 'gap'].forEach(k => bind(k).forEach(el => { el.removeAttribute('data-count'); el._cancel?.(); }));

  // a number that moved flashes up or down (only the Trading theme styles .flash-up / .flash-dn)
  const flash = (el, to) => {
    const from = parseFloat(el.dataset.v);
    if (!Number.isFinite(from) || !Number.isFinite(to) || Math.abs(to - from) < 1e-9) return;
    el.classList.remove('flash-up', 'flash-dn');
    void el.offsetWidth;
    el.classList.add(to > from ? 'flash-up' : 'flash-dn');
  };

  function apply(res) {
    liveNumbers();
    const mkt = marketSide();
    bind('dh').forEach(el => { flash(el, res.price); retarget(el, res.price, { f: fmt.inr, pre: '₹' }); });
    bind('dh-iv').forEach(el => { flash(el, res.iv); retarget(el, res.iv, { suf: '%' }); });
    const gap = res.price - mkt;
    bind('gap').forEach(el => { flash(el, gap); retarget(el, gap, { f: v => (v < 0 ? '−' : '+') + '₹' + inr(Math.abs(v)) }); });
    if (res.mc) bind('mc').forEach(el => { el.textContent = `₹${inr(res.mc.price)} ± ${res.mc.se.toFixed(2)}`; });
    const g = res.greeks;
    [['delta', 3], ['gamma', 5], ['vega', 1], ['theta', 2], ['rho', 1]].forEach(([k, dp]) => bind(`g-${k}`).forEach(el => retarget(el, g[k], { dp })));
    Object.entries(res.chain).forEach(([k, v]) => {
      bind(`ch-call-${k}`).forEach(el => { el.textContent = inr(v.call); });
      bind(`ch-put-${k}`).forEach(el => { el.textContent = inr(v.put); });
    });
    for (const f of ['slow', 'fast']) {
      const fe = res.feller[f];
      bind(`feller-${f}`).forEach(el => {
        el.textContent = fe.ok ? `Feller condition holds: 2κθ = ${fe.lhs.toFixed(3)} is above ξ² = ${fe.rhs.toFixed(3)}`
          : `Feller condition fails: 2κθ = ${fe.lhs.toFixed(3)} is below ξ² = ${fe.rhs.toFixed(3)}`;
        el.dataset.ok = String(fe.ok);
      });
    }
    // the smile: re-render with the new curve, then morph from the old one
    $$('.chart[data-chart="marketSmile"]', scope).forEach(el => {
      const old = el._out?.points;
      el._res = res;
      el._opts = { strike };
      renderChart(el, ctx, false);
      const path = el.querySelector('.ms-line');
      const now = el._out.points;
      if (path && old && old.length === now.length) { path.setAttribute('d', ''); morphPath(path, old, now, 700); }
    });
  }

  const run = debounce(async () => {
    store.set('model.params', params); store.set('model.strike', strike); store.set('model.kind', kind);
    setStatus('Pricing…', 'busy');
    const r = await price({ strike, kind, params, mc: true });
    if (r.stale) return;
    if (r.error) { setStatus(/fetch|network|Failed/i.test(r.error) ? OFFLINE_HELP : `Couldn't price that: ${r.error}`, 'error'); return; }
    apply(r.res);
    setStatus(isDefault() ? 'Starting settings' : `Repriced in ${r.res.ms} ms by the project's pricer`, 'ok');
  }, 90);

  // sliders: outputs and Feller update instantly; the price follows (debounced)
  $$('[data-param]', scope).forEach(inp => {
    inp.addEventListener('input', () => {
      params[inp.dataset.param] = +inp.value;
      inp.style.setProperty('--p', `${((inp.value - inp.min) / (inp.max - inp.min) * 100).toFixed(2)}%`);
      $$(`[data-out="${inp.dataset.param}"]`, scope).forEach(o => { o.textContent = (+inp.value).toFixed(+inp.dataset.dp); });
      for (const f of ['slow', 'fast']) {
        const fe = feller(params, f);
        bind(`feller-${f}`).forEach(el => { el.dataset.ok = String(fe.ok); });
      }
      run();
    });
  });
  $$('[data-in="strike"]', scope).forEach(sel => sel.addEventListener('change', () => { strike = +sel.value; run(); }));
  $$('[data-seg="kind"]', scope).forEach(s => s.addEventListener('seg', e => { kind = e.detail; run(); }));
  $$('[data-action="reset"]', scope).forEach(b => b.addEventListener('click', () => {
    params = { ...DEFAULT_PARAMS };
    $$('[data-param]', scope).forEach(inp => { inp.value = params[inp.dataset.param]; inp.dispatchEvent(new Event('input')); });
  }));
  $$('.b-chain tr[data-strike]', scope).forEach(tr => {
    tr.tabIndex = 0;
    const pick = () => { strike = +tr.dataset.strike; $$('[data-in="strike"]', scope).forEach(s => { s.value = strike; }); run(); };
    tr.addEventListener('click', pick);
    tr.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
  });
  // a returning visitor (or a theme change) keeps their settings: reprice them once
  marketSide();
  if (!isDefault()) { liveNumbers(); run(); }
}

// ------------------------------------------------------------------ the market page
function marketPage(scope, ctx) {
  let sym = store.get('market.sym', 'RELIANCE'), range = store.get('market.range', '3M'), mode = store.get('market.mode', 'candles');
  const redraw = () => {
    store.set('market.sym', sym); store.set('market.range', range); store.set('market.mode', mode);
    $$('.chart[data-chart="candles"]', scope).forEach(el => { el._opts = { sym, range, mode }; replay(el, ctx); });
    const r = ctx.D.equity[sym].at(-1), ch = r[4] - r[6], [a, c] = arrow(ch);
    const set = (k, v) => $$(`[data-bind="${k}"]`, scope).forEach(el => { el.textContent = v; });
    set('m-sym', sym); set('m-name', ctx.C.NAMES[sym] || '');
    $$('[data-bind="m-last"]', scope).forEach(el => { el.textContent = inr(r[4]); });
    $$('[data-bind="m-chg"]', scope).forEach(el => { el.textContent = `${a} ${inr(Math.abs(ch))} (${Math.abs(ch / r[6] * 100).toFixed(2)}%)`; el.className = el.className.replace(/\b(up|dn)\b/g, '') + ' ' + c; });
    set('m-open', inr(r[1])); set('m-high', inr(r[2])); set('m-low', inr(r[3])); set('m-close', inr(r[4])); set('m-prev-close', inr(r[6])); set('m-volume', `${(r[5] / 1e5).toFixed(1)} lakh`);
    $$('button[data-sym]', scope).forEach(b => {
      const on = b.dataset.sym === sym;
      b.setAttribute('aria-pressed', String(on));
      b.closest('tr, li')?.classList.toggle('sel', on);
    });
  };
  $$('button[data-sym]', scope).forEach(b => b.addEventListener('click', () => { sym = b.dataset.sym; redraw(); }));
  $$('[data-seg="range"]', scope).forEach(s => s.addEventListener('seg', e => { range = e.detail; redraw(); }));
  $$('[data-seg="mode"]', scope).forEach(s => s.addEventListener('seg', e => { mode = e.detail; redraw(); }));
}

// ------------------------------------------------------------------ the Results page stock picker
function findingPage(scope, ctx) {
  $$('[data-in="finding-sym"]', scope).forEach(sel => sel.addEventListener('change', () => {
    const sym = sel.value;
    store.set('finding.sym', sym);
    $$('.chart[data-chart="stockPanel"]', scope).forEach(el => { el._opts = { sym }; replay(el, ctx); });
    $$('[data-bind="stock-line"]', scope).forEach(el => { el.textContent = stockLine(ctx, sym); });
  }));
}

// re-render a chart with new data and play its entrance again (end state at once with reduced motion)
function replay(el, ctx) {
  renderChart(el, ctx, false);
  if (!document.documentElement.classList.contains('motion')) return;
  el.classList.remove('is-in');
  void el.offsetWidth;
  requestAnimationFrame(() => el.classList.add('is-in'));
}

export { esc };
