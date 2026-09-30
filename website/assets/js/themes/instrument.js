// Instrument: a lab oscilloscope. Modules on an instrument face; every chart sits in a dark scope
// screen with a division grid and phosphor traces (dark in both modes, as real screens are).
// IBM Plex Sans with Plex Mono for readouts. Content comes from core/pages.js, like every theme.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc } from '../core/util.js';
import { factorTrace } from '../core/factors.js';
import { renderPage, inner } from '../core/layout.js';

const SPAN = { full: 12, wide: 8, half: 6, narrow: 4, quarter: 3 };
const TWEAK = { 'home:nifty': 6, 'home:option': 3, 'home:finding': 3, 'home:factors': 4, 'home:pair': 12, 'home:params': 12, 'finding:pool': 7, 'finding:magnets-why': 5 };

const renderers = ctx => ({
  hero: s => `<section class="in-hero wrap" data-sec="${s.key}" data-anim>
      <div class="in-hero-t"><p class="in-q">${esc(s.q)}</p><h1 class="in-h1">${esc(s.title)} <span>${esc(s.title2)}</span></h1>
        <p class="in-lede">${esc(s.lead)}</p><div class="in-cta"><a class="btn" href="${s.ctas[0][0]}">${esc(s.ctas[0][1])}</a><a class="btn sec" href="${s.ctas[1][0]}">${esc(s.ctas[1][1])}</a></div></div>
      <div class="in-scope" aria-hidden="true"><div class="in-scope-screen"><div class="factor-trace in-hero-trace" data-trace></div></div>
        <div class="in-knobs"><span class="in-knob"></span><span class="in-knob"></span><span class="in-knob in-knob-s"></span></div></div></section>`,
  head: s => (s.level === 2
    ? `<header class="in-h2 wrap" data-sec="${s.key}"><h2>${esc(s.title)}</h2>${s.lead ? `<p class="in-lede">${esc(s.lead)}</p>` : ''}</header>`
    : `<header class="in-head wrap" data-sec="${s.key}"><h1 class="in-h1">${esc(s.title)}</h1>${s.lead ? `<p class="in-lede">${esc(s.lead)}</p>` : ''}</header>`),
  panel: (s, i) => {
    const span = TWEAK[`${ctx.page}:${s.key}`] || SPAN[s.size] || 12;
    return `<article class="in-m in-s${span}${s.accent ? ' in-acc' : ''}" data-sec="${s.key}" data-anim style="--i:${i % 10}">
      <header class="in-mh">${s.ico ? icon(s.ico, { size: 26, tint: 'steel' }) : ''}<h3>${esc(s.title || '')}</h3>${s.note ? `<span class="in-meta">${esc(s.note)}</span>` : ''}<span class="in-led" aria-hidden="true"></span></header>
      <div class="in-mb">${inner(s)}</div></article>`;
  },
  note: s => `<div class="in-notes in-s12" data-sec="${s.key}">${inner(s)}</div>`,
  group: html => `<div class="in-grid wrap">${html}</div>`,
});

function page(id, ctx) {
  return `<div class="in-top"><a class="in-brand" href="index.html">Double Heston</a><div class="in-tickwrap">${B.ticker(ctx)}</div></div>
    <main id="main" class="in">${renderPage(id, ctx, renderers(ctx))}<div class="wrap in-end">${B.pageLinks(ctx, { size: 46, tint: 'steel' })}${B.footer(ctx)}</div></main>`;
}

function mount(app) {
  const stops = [...app.querySelectorAll('[data-trace]')].map(el => factorTrace(el, { span: 2, speed: 0.22, lw: el.classList.contains('in-hero-trace') ? 2.4 : 2, grid: !el.classList.contains('in-hero-trace') }));
  return () => stops.forEach(s => s.stop());
}

export default { nav: { kind: 'dashes', side: 'l' }, chartOpts: { smileBend: { lw: 2.8 } }, page, mount };
