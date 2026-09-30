// Springboard: the site as an iPhone home screen. Widgets of mixed sizes on a grouped background,
// app icons for every page, a frosted dock that magnifies under the cursor, iOS large titles.
// Content comes from core/pages.js, the same sections every theme shows.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc } from '../core/util.js';
import { factorTrace } from '../core/factors.js';
import { reduced } from '../core/motion.js';
import { renderPage, inner } from '../core/layout.js';

const SPAN = { full: 12, wide: 8, half: 6, narrow: 4, quarter: 3 };
// widget widths that make each page's grid tile cleanly (content is unchanged)
const TWEAK = { 'home:option': 3, 'home:finding': 3, 'home:pair': 7, 'home:params': 5, 'finding:pool': 7, 'finding:magnets-why': 5 };

function widget(ctx, s, i) {
  const span = TWEAK[`${ctx.page}:${s.key}`] || SPAN[s.size] || 12;
  const head = s.title ? `<header class="sb-wh">${s.ico ? icon(s.ico, { size: 28 }) : ''}<h3>${esc(s.title)}</h3>${s.note ? `<span class="sb-wh-r">${esc(s.note)}</span>` : ''}</header>` : '';
  return `<article class="sb-w sb-s${span}${s.accent ? ' sb-w-acc' : ''}" data-glint data-anim data-sec="${s.key}" style="--i:${i % 12}">${head}<div class="sb-wb">${inner(s)}</div></article>`;
}

const renderers = ctx => ({
  hero: s => `<header class="sb-head sb-hero wrap" data-sec="${s.key}"><p class="sb-q">${esc(s.q)}</p>
    <h1 class="sb-title sb-title-xl">${esc(s.title)}<br><span class="sb-title-2">${esc(s.title2)}</span></h1>
    <p class="sb-sub">${esc(s.lead)}</p><div class="sb-cta">${s.ctas.map(([h, l], k) => `<a class="btn${k ? ' ghost' : ''}" href="${h}">${esc(l)}</a>`).join('')}</div></header>`,
  head: s => s.level === 2
    ? `<div class="sb-st wrap" data-sec="${s.key}"><h2>${esc(s.title)}</h2>${s.lead ? `<p>${esc(s.lead)}</p>` : ''}</div>`
    : `<header class="sb-head wrap" data-sec="${s.key}"><h1 class="sb-title">${esc(s.title)}</h1>${s.lead ? `<p class="sb-sub">${esc(s.lead)}</p>` : ''}</header>`,
  panel: (s, i) => widget(ctx, s, i),
  note: s => `<div class="sb-note sb-s12" data-sec="${s.key}">${inner(s)}</div>`,
  group: html => `<div class="sb-grid wrap">${html}</div>`,
});

function dock(ctx) {
  return `<nav class="sb-dock-wrap wrap" aria-label="Main pages"><div class="sb-dock">${['home', 'market', 'model', 'finding', 'about'].map(id => {
    const p = ctx.pages.find(x => x.id === id);
    return `<a href="${p.file}" class="sb-dock-i${id === ctx.page ? ' cur' : ''}"${id === ctx.page ? ' aria-current="page"' : ''}>${icon(id, { size: 64 })}<span class="sb-dock-l">${esc(p.label)}</span></a>`;
  }).join('')}</div></nav>`;
}

const apps = ctx => `<section class="sb-apps wrap" data-sec="apps" aria-label="All pages"><div class="sb-appgrid">${ctx.pages.map(p =>
  `<a href="${p.file}" class="sb-app"${p.id === ctx.page ? ' aria-current="page"' : ''}>${icon(p.id, { size: 76 })}<span>${esc(p.label)}</span></a>`).join('')}</div></section>`;

function page(id, ctx) {
  return `<div class="sb-status">${B.ticker(ctx)}</div><main id="main" class="sb">${renderPage(id, ctx, renderers(ctx))}${apps(ctx)}${dock(ctx)}<div class="wrap">${B.footer(ctx)}</div></main>`;
}

function mount(app) {
  const stops = [];
  app.querySelectorAll('[data-trace]').forEach(el => stops.push(factorTrace(el, { span: 2, speed: 0.2, lw: 2.6 })));
  // dock magnification (macOS): icons near the cursor grow, transform only
  const dock = app.querySelector('.sb-dock');
  if (dock && !reduced() && matchMedia('(hover: hover)').matches) {
    const items = [...dock.querySelectorAll('.sb-dock-i')];
    let raf = 0, x = null;
    const apply = () => {
      raf = 0;
      items.forEach(it => {
        const r = it.getBoundingClientRect();
        const d = x == null ? 1e9 : Math.abs(x - (r.left + r.width / 2));
        const s = 1 + 0.42 * Math.exp(-(d * d) / (2 * 70 * 70));
        it.style.transform = `translateY(${(-(s - 1) * 30).toFixed(1)}px) scale(${s.toFixed(3)})`;
      });
    };
    dock.addEventListener('pointermove', e => { x = e.clientX; raf ||= requestAnimationFrame(apply); });
    dock.addEventListener('pointerleave', () => { x = null; raf ||= requestAnimationFrame(apply); });
  }
  return () => stops.forEach(s => s.stop());
}

export default { nav: { kind: 'dashes', side: 'l' }, page, mount };
