// Theme-agnostic page behaviour, wired by data attributes: the model page (live repricing through the
// worker), the market page (symbol, range, chart type), and the Results page (stock picker).
// Every choice goes into the store, so it survives a theme change.
import { store } from './state.js';
import { inr, fmt, esc, arrow, debounce, $, $$ } from './util.js';
import { retarget } from './motion.js';
import { renderChart, morphPath } from './charts.js';
import { price, DEFAULT_PARAMS, OFFLINE_HELP, feller } from './model.js';
import { stockLine } from './blocks.js';
import { marketOf, refreshLiveChain, istTime as hhmm } from './live-chain.js';
import { createPA3D } from './pa3d.js';

export function mountControllers(scope, ctx) {
  const stops = [];
  segs(scope);
  videoSlots(scope, ctx);
  stops.push(explainHover(scope));
  if (scope.querySelector('[data-ctl="model-form"], [data-param]')) { modelPage(scope, ctx); stops.push({ stop: () => stopModel?.() }); }
  if (scope.querySelector('[data-chart="candles"]')) stops.push(marketPage(scope, ctx));
  if (scope.querySelector('[data-in="finding-sym"]')) findingPage(scope, ctx);
  $$('[data-pa3d]', scope).forEach(el => stops.push(createPA3D(el, ctx.PA)));
  $$('.b-dock-in', scope).forEach(d => stops.push(dockMagnify(d)));
  stops.push(liveQuotes(scope, ctx));
  return () => stops.forEach(s => s && s.stop && s.stop());
}

// ------------------------------------------------------------------ live equity prices (Upstox)
// the Market page's header and day figures for one live quote; fields Upstox didn't send stay as they are
function liveStats(scope, v) {
  if (!v || v.last == null) return;
  $$('[data-bind="m-last"], [data-bind="m-close"]', scope).forEach(el => tick(el, v.last));
  $$('[data-bind="m-chg"]', scope).forEach(el => {
    const [a, c] = arrow(v.pct ?? 0);
    el.textContent = `${a} ${inr(Math.abs(v.chg ?? 0))} (${Math.abs(v.pct ?? 0).toFixed(2)}%)`;
    el.className = el.className.replace(/\b(up|dn)\b/g, '').trim() + ' ' + c;
  });
  if (v.open != null) $$('[data-bind="m-open"]', scope).forEach(el => { el.textContent = inr(v.open); });
  if (v.high != null) $$('[data-bind="m-high"]', scope).forEach(el => { el.textContent = inr(v.high); });
  if (v.low != null) $$('[data-bind="m-low"]', scope).forEach(el => { el.textContent = inr(v.low); });
  if (v.prev_close != null) $$('[data-bind="m-prev-close"]', scope).forEach(el => { el.textContent = inr(v.prev_close); });
  if (v.volume != null) $$('[data-bind="m-volume"]', scope).forEach(el => { el.textContent = `${inr(v.volume / 1e5, 1)} lakh`; });
}

// The ticker (every page) and the Market page's watchlist/header/stats poll /api/live and overlay
// it on the static NSE-close numbers already rendered server-side. Any failure (no token, offline,
// rate limit) leaves those static numbers exactly as they were -- never a blank or a "NaN".
function liveQuotes(scope, ctx) {
  if (!$('.tick-i[data-sym]', scope) && !scope.querySelector('[data-chart="candles"]')) return null;
  const C = ctx.C;
  const istTime = iso => new Date(iso).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  const setChg = (el, pct) => {
    const [a, c] = arrow(pct);
    el.textContent = `${a} ${Math.abs(pct).toFixed(2)}%`;
    el.className = el.className.replace(/\b(up|dn)\b/g, '').trim() + ' ' + c;
  };
  const apply = live => {
    const q = live.quotes || {};
    $$('[data-sym]', scope).forEach(row => {
      const v = q[row.dataset.sym];
      if (!v || v.last == null) return;
      const priceEl = row.querySelector('[data-bind="price"]'), chgEl = row.querySelector('[data-bind="chg"]');
      if (priceEl) tick(priceEl, v.last);
      if (chgEl && v.pct != null) setChg(chgEl, v.pct);
    });
    ctx.liveQuotes = q; // so picking another stock on the Market page shows its live figures at once
    liveStats(scope, q[store.get('market.sym', 'RELIANCE')]);
    const ok = live.status === 'live' && Object.keys(q).length;
    const state = live.market_open ? C.LIVE_OPEN.replace('{time}', istTime(live.asof))
      : live.holiday ? C.LIVE_HOLIDAY.replace('{day}', live.holiday) : C.LIVE_CLOSED;
    $$('[data-bind="live-status"]', scope).forEach(el => { el.textContent = ok ? state : C.LIVE_FALLBACK; });
    // the header chip says the saved NSE close until live prices arrive, then says they're live
    if (ok) $$('[data-bind="site-status"]', document).forEach(el => { el.textContent = state; });
  };
  // every 2 s while the market is open (the edge caches 1 s), every 15 s when it's shut; paused in a hidden tab
  let stopped = false, timer = 0, open = true;
  const poll = async () => {
    if (!document.hidden) {
      try { const r = await fetch('/api/live'); if (r.ok && !stopped) { const live = await r.json(); open = !!live.market_open; apply(live); } } catch { /* keep the static numbers */ }
    }
    if (!stopped) timer = setTimeout(poll, open ? 2000 : 15000);
  };
  timer = setTimeout(poll, 60);
  return { stop() { stopped = true; clearTimeout(timer); } };
}

// a price that moved flashes green (up) or red (down) for a moment, so a live tick is visible
function tick(el, v) {
  const was = parseFloat(el.dataset.last);
  el.textContent = inr(v);
  el.dataset.last = v;
  if (!Number.isFinite(was) || was === v) return;
  el.classList.remove('tick-up', 'tick-dn');
  void el.offsetWidth; // restart the animation if it's still running
  el.classList.add(v > was ? 'tick-up' : 'tick-dn');
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

// "Explain simply" dropdowns: open on hover for a real mouse (pointer: fine, hover: hover), with a
// short close delay so crossing from the summary into the body doesn't snap it shut. Touch stays
// tap-to-open -- there's no hover to speak of there, and the <details> element's own click toggle
// keeps working everywhere regardless (keyboard included), this only adds the hover affordance.
// Only the triangle disc itself opens it: the <details> spans the card's full width, so listening on
// it opened the explainer from anywhere along the triangle's row. Once open, the body keeps it open.
function explainHover(scope) {
  if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return null;
  const stops = [];
  $$('.xp', scope).forEach(el => {
    const sum = el.querySelector(':scope > summary');
    const body = el.querySelector(':scope > .xp-body');
    if (!sum) return;
    let closeTimer = 0;
    const open = () => { clearTimeout(closeTimer); el.open = true; };
    const stay = () => { if (el.open) clearTimeout(closeTimer); };
    const close = (e, wait = 200) => { clearTimeout(closeTimer); closeTimer = setTimeout(() => { el.open = false; }, wait); };
    // leaving the disc downward is on the way into the body: give the gap between them longer
    const leaveSum = e => close(e, e.clientY >= sum.getBoundingClientRect().bottom - 1 ? 700 : 200);
    sum.addEventListener('pointerenter', open);
    sum.addEventListener('pointerleave', leaveSum);
    body?.addEventListener('pointerenter', stay);
    body?.addEventListener('pointerleave', close);
    stops.push(() => {
      sum.removeEventListener('pointerenter', open); sum.removeEventListener('pointerleave', leaveSum);
      body?.removeEventListener('pointerenter', stay); body?.removeEventListener('pointerleave', close);
      clearTimeout(closeTimer);
    });
  });
  return stops.length ? { stop: () => stops.forEach(f => f()) } : null;
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
let stopModel = null;
function modelPage(scope, ctx) {
  stopModel?.();
  const K = ctx.D.contract;
  const bind = k => $$(`[data-bind="${k}"]`, scope);
  let params = { ...DEFAULT_PARAMS, ...store.get('model.params', {}) };
  let strike = store.get('model.strike', K.strike), kind = store.get('model.kind', 'call');
  if (!ctx.D.chain.some(r => r.strike === strike)) strike = K.strike; // a strike from another chain
  const isDefault = () => Object.keys(DEFAULT_PARAMS).every(k => Math.abs(params[k] - DEFAULT_PARAMS[k]) < 1e-9) && strike === K.strike && kind === 'call';

  const setStatus = (txt, cls = '') => bind('status').forEach(el => { el.textContent = txt; el.dataset.state = cls; });

  // market values for the chosen contract are fixed data; only the model's side is recomputed
  function marketSide() {
    const K = ctx.D.contract, row = ctx.D.chain.find(r => r.strike === strike);
    const px = row[kind], iv = row[`${kind}_iv`];
    bind('mkt').forEach(el => { el.textContent = px != null ? `₹${inr(px)}` : '–'; });
    bind('mkt-iv').forEach(el => { el.textContent = iv != null ? `${iv.toFixed(2)}%` : '–'; });
    if (K.live) bind('mkt-when').forEach(el => {
      el.textContent = `${row[`${kind}_src`] === 'mid' ? ctx.C.MKT_MID : ctx.C.MKT_LAST}, ${hhmm(K.asof)} IST`;
    });
    // the live chain's market columns and the underlying move between reprices
    for (const r of ctx.D.chain) for (const side of ['call', 'put']) {
      bind(`mk-${side}-${r.strike}`).forEach(el => { el.textContent = r[side] != null ? inr(r[side]) : '–'; });
      bind(`mk-${side}-iv-${r.strike}`).forEach(el => { el.textContent = r[`${side}_iv`] != null ? `${r[`${side}_iv`].toFixed(1)}%` : '–'; });
    }
    bind('spot').forEach(el => { el.textContent = inr(K.spot); });
    bind('dte').forEach(el => { el.textContent = `${K.dte} days`; });
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
    const gap = mkt != null ? res.price - mkt : NaN;
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
    const r = await price({ strike, kind, params, mc: true, market: marketOf(ctx) });
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
  if (!isDefault() || ctx.D.contract.live) { liveNumbers(); run(); }
  // live options: the market side refreshes each minute; a move in NIFTY or a quote reprices the model
  if (ctx.D.contract.live) {
    const tick = setInterval(async () => {
      if (document.hidden) return;
      if (await refreshLiveChain(ctx)) { marketSide(); run(); }
    }, 60000);
    stopModel = () => clearInterval(tick);
  }
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
    set('m-open', inr(r[1])); set('m-high', inr(r[2])); set('m-low', inr(r[3])); set('m-close', inr(r[4])); set('m-prev-close', inr(r[6]));
    set('m-volume', r[5] ? `${inr(r[5] / 1e5, 1)} lakh` : '—'); // Upstox reports no volume for an index
    liveStats(scope, ctx.liveQuotes?.[sym]);
    $$('button[data-sym]', scope).forEach(b => {
      const on = b.dataset.sym === sym;
      b.setAttribute('aria-pressed', String(on));
      b.closest('tr, li')?.classList.toggle('sel', on);
    });
  };
  $$('button[data-sym]', scope).forEach(b => b.addEventListener('click', () => { sym = b.dataset.sym; redraw(); extend(sym); }));
  $$('[data-seg="range"]', scope).forEach(s => s.addEventListener('seg', e => { range = e.detail; redraw(); }));
  $$('[data-seg="mode"]', scope).forEach(s => s.addEventListener('seg', e => { mode = e.detail; redraw(); }));

  // The saved history ends at the last NSE file; fill every trading day since then, today's candle
  // included, from Upstox daily candles (/api/live?candles=). Re-asked each minute while the page is
  // open, so today's candle keeps up; any failure leaves the saved history exactly as it was.
  const INDEX = { 'NIFTY 50': 'NIFTY', 'NIFTY BANK': 'BANKNIFTY' };
  const merge = (s, rows) => {
    const eq = ctx.D.equity[s];
    if (!eq || !rows?.length) return false;
    const ix = ctx.D.index_close[INDEX[s]];
    let changed = false;
    for (const [d, o, h, l, c, v] of rows) {
      const last = eq.at(-1);
      if (d < last[0] || (d === last[0] && last[4] === c)) continue;
      if (d === last[0]) eq[eq.length - 1] = [d, o, h, l, c, v, last[6]]; // today's candle, moved on
      else eq.push([d, o, h, l, c, v, last[4]]);
      if (ix) { if (ix.at(-1)[0] === d) ix.at(-1)[1] = c; else if (ix.at(-1)[0] < d) ix.push([d, c]); }
      changed = true;
    }
    return changed;
  };
  const since = new Map(); // first date we asked Upstox for, per symbol: one day after the saved history
  const extend = async s => {
    if (!ctx.D.equity[s]) return;
    if (!since.has(s)) { const d = new Date(ctx.D.equity[s].at(-1)[0] + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + 1); since.set(s, d.toISOString().slice(0, 10)); }
    try {
      const r = await fetch(`/api/live?candles=${encodeURIComponent(s)}&since=${since.get(s)}`);
      if (!r.ok || stopped) return;
      if (!merge(s, (await r.json()).rows)) return;
      if (s === sym) redraw();
      if (INDEX[s]) $$('.chart[data-chart="indexLine"]', scope).filter(el => (JSON.parse(el.dataset.o || '{}').which || 'NIFTY') === INDEX[s]).forEach(el => replay(el, ctx));
    } catch { /* keep the saved history */ }
  };
  let stopped = false;
  const refresh = () => [...new Set([sym, 'NIFTY 50', 'NIFTY BANK'])].forEach(extend);
  refresh();
  const timer = setInterval(refresh, 60000);
  return { stop() { stopped = true; clearInterval(timer); } };
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
