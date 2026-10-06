// Ferro: chrome and liquid black. A brushed-chrome hero plate, calm two-column rows split by
// ferrofluid ridges, chrome icons, the ferrofluid side nav, and the two variance factors shown as
// pools that turn from water into ferrofluid driven by their real settings.
// Content comes from core/pages.js, the same sections every theme shows.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc, uid } from '../core/util.js';
import { renderPage } from '../core/layout.js';
import { ferroPool } from '../core/ferro-pool.js';
import { FACTORS } from '../core/factors.js';
import { store } from '../core/state.js';
import { DEFAULT_PARAMS } from '../core/model.js';

// a quiet divider: a hairline with a small bead of ferrofluid in the middle, shaded like the spikes
function ridge() {
  const W = 240, base = 22, peaks = [[96, 5], [108, 9], [120, 13], [132, 9], [144, 5]];
  let d = `M60,${base}`;
  for (const [cx, h] of peaks) {
    d += ` L${cx - 7},${base} C${cx - 3},${base - 1} ${cx - 1.6},${base - h * 0.62} ${cx},${base - h} C${cx + 1.6},${base - h * 0.62} ${cx + 3},${base - 1} ${cx + 7},${base}`;
  }
  d += ` L180,${base} Q120,${base + 5} 60,${base} Z`;
  const id = uid('ferg');
  return `<div class="fe-ridge wrap" aria-hidden="true"><span class="fe-ridge-line"></span><svg viewBox="0 0 ${W} 30" width="${W}" height="30">
    <defs><linearGradient id="${id}" x1="0" x2="1"><stop offset="0" style="stop-color:var(--ferro)"/><stop offset=".38" style="stop-color:var(--ferro-sheen)"/><stop offset=".55" style="stop-color:var(--ferro)"/><stop offset="1" style="stop-color:var(--ferro)"/></linearGradient></defs>
    <path d="${d}" style="fill:url(#${id})"/></svg><span class="fe-ridge-line"></span></div>`;
}

const ico = k => (k ? icon(k, { size: 38, tint: 'chrome' }) : '');

const renderers = ctx => ({
  hero: s => `<section class="fe-plate-wrap wrap" data-sec="${s.key}"><div class="fe-plate" data-anim><span class="fe-shine" aria-hidden="true"></span>
      ${s.q ? `<p class="fe-q">${esc(s.q)}</p>` : ''}<h1 class="fe-h1">${esc(s.title)} <span class="fe-liquid">${esc(s.title2)}</span></h1>${s.by ? `<p class="hero-by fe-by">${esc(s.by)}</p>` : ''}
      <p class="fe-lede">${esc(s.lead)}</p>
      ${s.ctas?.length ? `<div class="fe-cta"><a class="btn" href="${s.ctas[0][0]}">${esc(s.ctas[0][1])}</a><a class="btn sec" href="${s.ctas[1][0]}">${esc(s.ctas[1][1])}</a></div>` : ''}</div></section>`,
  head: s => (s.level === 2
    ? `${ridge()}<header class="fe-head fe-head2 wrap" data-sec="${s.key}"><h2>${esc(s.title)}</h2>${s.lead ? `<p class="fe-lede">${esc(s.lead)}</p>` : ''}</header>`
    : `<header class="fe-head wrap" data-sec="${s.key}"><h1 class="fe-h1">${esc(s.title)}</h1>${s.lead ? `<p class="fe-lede">${esc(s.lead)}</p>` : ''}</header>`),
  panel: (s, i) => {
    const stack = s.size === 'full' || !s.title;
    const text = `${s.title ? `<div class="fe-t">${ico(s.ico)}<h2>${esc(s.title)}</h2></div>` : ''}${s.note ? `<p class="fe-note">${esc(s.note)}</p>` : ''}${s.lead ? `<p class="s-lead">${esc(s.lead)}</p>` : ''}`;
    const body = `${s.body || ''}${s.fine ? `<p class="s-fine">${esc(s.fine)}</p>` : ''}`;
    if (!s.body && !s.fine) return `<section class="fe-row fe-textonly${s.accent ? ' fe-acc' : ''}" data-sec="${s.key}" data-anim style="--i:${i % 8}"><div class="fe-rl">${text}</div></section>`;
    return `<section class="fe-row ${stack ? 'fe-stack' : ''}${s.accent ? ' fe-acc' : ''}" data-sec="${s.key}" data-anim style="--i:${i % 8}">
      ${text ? `<div class="fe-rl">${text}</div>` : ''}<div class="fe-rr">${body}</div></section>`;
  },
  note: s => `<div class="fe-row fe-textonly fe-plain" data-sec="${s.key}">${s.lead ? `<p class="s-lead">${esc(s.lead)}</p>` : ''}${s.body || ''}${s.fine ? `<p class="s-fine">${esc(s.fine)}</p>` : ''}</div>`,
  group: (html, g) => `${g ? ridge() : ''}<div class="fe-group wrap">${html}</div>`,
});

function page(id, ctx) {
  return `<div class="fe-tick">${B.ticker(ctx)}</div>
    <header class="fe-mast wrap"><a class="fe-brand" href="index.html">Double Heston</a><span class="fe-status">${esc(ctx.C.STATUS)}</span></header>
    <main id="main" class="fe">${renderPage(id, ctx, renderers(ctx))}${ridge()}<div class="wrap fe-end">${B.dock(ctx, { size: 54, tint: 'chrome' })}${B.footer(ctx)}</div></main>`;
}

// the factors as pools: home page (both), model page (one per slider group, following the sliders)
function mount(app) {
  const stops = [];
  app.querySelectorAll('[data-trace]').forEach(host => {
    host.classList.add('fe-pools');
    host.innerHTML = '<div class="fp" data-f="fast"><span class="fp-l">Fast factor</span></div><div class="fp" data-f="slow"><span class="fp-l">Slow factor</span></div>';
    host.querySelectorAll('.fp').forEach((el, k) => {
      const f = el.dataset.f;
      stops.push(ferroPool(el, { params: FACTORS[f], label: `${f === 'fast' ? 'Fast' : 'Slow'} factor`, seed: 5 + k }));
    });
  });
  const params = { ...DEFAULT_PARAMS, ...store.get('model.params', {}) };
  [['sliders', 'slow', '1'], ['sliders-fast', 'fast', '2']].forEach(([key, f, n]) => {
    const sec = app.querySelector(`[data-sec="${key}"] .fe-rr`);
    if (!sec) return;
    const el = document.createElement('div');
    el.className = 'fp fp-model';
    sec.prepend(el);
    const pick = () => ({ kappa: params[`kappa${n}`], theta: params[`theta${n}`], xi: params[`xi${n}`], v0: params[n === '1' ? 'v0_1' : 'v0_2'] });
    const pool = ferroPool(el, { params: pick(), label: `${f === 'fast' ? 'Fast' : 'Slow'} factor at your settings`, seed: n === '1' ? 3 : 5 });
    stops.push(pool);
    sec.querySelectorAll('[data-param]').forEach(inp => inp.addEventListener('input', () => { params[inp.dataset.param] = +inp.value; pool.set(pick()); }));
    app.querySelectorAll('[data-action="reset"]').forEach(b => b.addEventListener('click', () => { Object.assign(params, DEFAULT_PARAMS); pool.set(pick()); }));
  });
  return () => stops.forEach(s => s.stop());
}

export default {
  nav: { kind: 'ferro' },
  chartOpts: { smileBend: { lw: 5 }, pairMagnets: { spike3d: true }, pairSix: { spike3d: true } },
  page, mount,
};
