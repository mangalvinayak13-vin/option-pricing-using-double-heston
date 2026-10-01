// Springboard: the site as an iPhone home screen. Widgets of mixed sizes on a grouped background,
// app icons for every page, a frosted dock that magnifies under the cursor, iOS large titles.
// Content comes from core/pages.js, the same sections every theme shows.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc } from '../core/util.js';
import { factorTrace } from '../core/factors.js';
import { renderPage, inner } from '../core/layout.js';

const SPAN = { full: 12, wide: 8, half: 6, narrow: 4, quarter: 3 };
// widget widths that make each page's grid tile cleanly (content is unchanged)
const TWEAK = { 'finding:pool': 7, 'finding:magnets-why': 5 };

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

function page(id, ctx) {
  return `<div class="sb-status">${B.ticker(ctx)}</div><main id="main" class="sb">${renderPage(id, ctx, renderers(ctx))}<div class="wrap">${B.dock(ctx, { size: 60 })}${B.footer(ctx)}</div></main>`;
}

function mount(app) {
  const stops = [];
  app.querySelectorAll('[data-trace]').forEach(el => stops.push(factorTrace(el, { span: 2, speed: 0.2, lw: 2.6 })));
  return () => stops.forEach(s => s.stop());
}

export default { nav: { kind: 'dashes', side: 'l' }, page, mount };
