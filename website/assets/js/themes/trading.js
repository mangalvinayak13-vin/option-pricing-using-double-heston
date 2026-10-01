// Trading: a broker terminal. Full-width desks of dense panes on 1-px seams, tab-style pane headers,
// Barlow Condensed numerals, an azure accent (green and red stay reserved for up and down).
// Content comes from core/pages.js, the same sections every theme shows.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc } from '../core/util.js';
import { factorTrace } from '../core/factors.js';
import { renderPage, inner } from '../core/layout.js';

const SPAN = { full: 12, wide: 8, half: 6, narrow: 4, quarter: 3 };
const TWEAK = { 'finding:pool': 7, 'finding:magnets-why': 5 };

const renderers = ctx => ({
  hero: s => `<section class="tr-hero" data-sec="${s.key}" data-anim><div class="tr-hero-in">
      <p class="tr-q">${esc(s.q)}</p><h1 class="tr-h1">${esc(s.title)} <span>${esc(s.title2)}</span></h1>
      <p class="tr-lede">${esc(s.lead)}</p><div class="tr-cta"><a class="btn" href="${s.ctas[0][0]}">${esc(s.ctas[0][1])}</a><a class="btn sec" href="${s.ctas[1][0]}">${esc(s.ctas[1][1])}</a></div></div></section>`,
  head: s => (s.level === 2
    ? `<header class="tr-pgt tr-pgt2" data-sec="${s.key}"><h2>${esc(s.title)}</h2>${s.lead ? `<p>${esc(s.lead)}</p>` : ''}</header>`
    : `<header class="tr-pgt" data-sec="${s.key}"><h1>${esc(s.title)}</h1>${s.lead ? `<p>${esc(s.lead)}</p>` : ''}</header>`),
  panel: (s, i) => {
    const span = TWEAK[`${ctx.page}:${s.key}`] || SPAN[s.size] || 12;
    return `<article class="tr-pane tr-s${span}${s.accent ? ' tr-acc' : ''}" data-sec="${s.key}" data-anim style="--i:${i % 12}">
      <header class="tr-ph">${s.ico ? icon(s.ico, { size: 22, tint: 'azure' }) : ''}<b>${esc(s.title || '')}</b>${s.note ? `<span class="tr-note">${esc(s.note)}</span>` : ''}</header>
      <div class="tr-pb">${inner(s)}</div></article>`;
  },
  note: s => `<div class="tr-pane tr-s12 tr-plain" data-sec="${s.key}"><div class="tr-pb">${inner(s)}</div></div>`,
  group: html => `<div class="tr-desk">${html}</div>`,
});

function page(id, ctx) {
  const nifty = ctx.D.watch.find(x => x.sym === 'NIFTY 50'), bank = ctx.D.watch.find(x => x.sym === 'NIFTY BANK');
  const ix = v => `<span><b>${esc(v.sym)}</b> <span class="num">${v.last.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span> <span class="num ${v.pct >= 0 ? 'up' : 'dn'}">${v.pct >= 0 ? '▲' : '▼'} ${Math.abs(v.pct).toFixed(2)}%</span></span>`;
  return `<div class="tr-top"><a class="tr-brand" href="index.html">Double<span>Heston</span></a><div class="tr-ix">${ix(nifty)}${ix(bank)}</div>
      <span class="tr-st"><i></i>${esc(ctx.C.STATUS)}</span></div>
    <div class="tr-tick">${B.ticker(ctx)}</div>
    <main id="main" class="tr">${renderPage(id, ctx, renderers(ctx))}<div class="tr-end">${B.dock(ctx, { size: 48, tint: 'azure' })}${B.footer(ctx)}</div></main>`;
}

function mount(app) {
  const stops = [...app.querySelectorAll('[data-trace]')].map(el => factorTrace(el, { span: 2, speed: 0.22, lw: 1.8 }));
  return () => stops.forEach(s => s.stop());
}

export default { nav: { kind: 'dashes', side: 'l' }, chartOpts: { smileBend: { lw: 2.6 } }, page, mount };
