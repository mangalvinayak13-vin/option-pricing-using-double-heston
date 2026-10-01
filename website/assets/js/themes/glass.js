// Glass: an Apple product page. Huge centred type, alternating bands with soft colour light behind
// frosted-glass tiles, one hero stage where the flat line bends into the smile over a glow.
// Content comes from core/pages.js, the same sections every theme shows.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc } from '../core/util.js';
import { factorTrace } from '../core/factors.js';
import { renderPage, inner } from '../core/layout.js';

const SPAN = { full: 12, wide: 8, half: 6, narrow: 4, quarter: 3 };
const TWEAK = { 'finding:pool': 7, 'finding:magnets-why': 5 };
const CHEV = '<svg class="gl-chev" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.5 1.5 6.5 7l-5 5.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function tile(ctx, s, i) {
  const stage = false; // every full-width section is a centred feature (below)
  const span = stage ? 12 : (TWEAK[`${ctx.page}:${s.key}`] || SPAN[s.size] || 12);
  // full-width sections read like a product page: a big centred headline, then the content on a glass stage
  if (span === 12 && s.title) {
    return `<section class="gl-feature gl-s12" data-sec="${s.key}" data-anim style="--i:0">
      <header class="gl-fh">${s.ico ? icon(s.ico, { size: 44 }) : ''}<h2>${esc(s.title)}</h2>${s.lead ? `<p class="gl-lede">${esc(s.lead)}</p>` : ''}${s.note ? `<p class="gl-note-c">${esc(s.note)}</p>` : ''}</header>
      ${s.body || s.fine ? `<div class="gl-tile gl-stagebox" data-glint>${s.body || ''}${s.fine ? `<p class="s-fine">${esc(s.fine)}</p>` : ''}</div>` : ''}</section>`;
  }
  const head = s.title ? `<header class="gl-th">${s.ico ? icon(s.ico, { size: 34 }) : ''}<h3>${esc(s.title)}</h3>${s.note ? `<span class="gl-note">${esc(s.note)}</span>` : ''}</header>` : '';
  return `<article class="gl-tile gl-s${span}${s.accent ? ' gl-acc' : ''}${stage ? ' gl-stage' : ''}" data-glint data-anim data-sec="${s.key}" style="--i:${i % 10}">${head}<div class="gl-tb">${inner(s)}</div></article>`;
}

const renderers = ctx => ({
  hero: s => `<header class="gl-hero wrap" data-sec="${s.key}" data-anim>
      <p class="gl-q">${esc(s.q)}</p>
      <h1 class="gl-h1"><span>${esc(s.title)}</span> <span class="gl-grad">${esc(s.title2)}</span></h1>
      <p class="gl-lede">${esc(s.lead)}</p>
      <div class="gl-cta"><a class="btn" href="${s.ctas[0][0]}">${esc(s.ctas[0][1])}</a><a class="gl-link" href="${s.ctas[1][0]}">${esc(s.ctas[1][1])}${CHEV}</a></div></header>`,
  head: s => `<header class="${s.level === 2 ? 'gl-h2' : 'gl-head'} wrap" data-sec="${s.key}" data-anim>${s.level === 2 ? `<h2>${esc(s.title)}</h2>` : `<h1 class="gl-h1">${esc(s.title)}</h1>`}${s.lead ? `<p class="gl-lede">${esc(s.lead)}</p>` : ''}</header>`,
  panel: (s, i) => tile(ctx, s, i),
  note: s => `<div class="gl-notes gl-s12" data-sec="${s.key}">${inner(s)}</div>`,
  group: (html, g) => `<section class="gl-band gl-band-${g % 2}"><div class="gl-glow gl-glow-${g % 3}" aria-hidden="true" data-parallax="0.05"></div><div class="gl-grid wrap">${html}</div></section>`,
});

function globalNav(ctx) {
  return `<div class="gl-top"><div class="gl-tick">${B.ticker(ctx)}</div>
    <nav class="gl-gnav" aria-label="Site"><a class="gl-brand" href="index.html">Double Heston</a><div class="gl-links">${ctx.pages.filter(p => p.id !== 'home').map(p =>
      `<a href="${p.file}"${p.id === ctx.page ? ' aria-current="page"' : ''}>${esc(p.label)}</a>`).join('')}</div></nav></div>`;
}

function page(id, ctx) {
  return `${globalNav(ctx)}<main id="main" class="gl">${renderPage(id, ctx, renderers(ctx))}
    <section class="gl-band gl-band-end"><div class="wrap gl-end">${B.dock(ctx, { size: 58 })}${B.footer(ctx)}</div></section></main>`;
}

function mount(app) {
  const stops = [...app.querySelectorAll('[data-trace]')].map(el => factorTrace(el, { span: 2, speed: 0.2, lw: 2.6 }));
  return () => stops.forEach(s => s.stop());
}

export default {
  nav: { kind: 'dashes', side: 'l' },
  chartOpts: { smileBend: { glow: 9, lw: 4 } },
  page, mount,
};
