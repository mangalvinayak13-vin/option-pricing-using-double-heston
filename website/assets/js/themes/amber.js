// Amber: a precision instrument in amber on near-black. Square hairline panels with channel labels,
// a query prompt for the question and readouts for the answer, Schibsted Grotesk throughout with
// heavy numerals. Content comes from core/pages.js, the same sections every theme shows.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc } from '../core/util.js';
import { factorTrace } from '../core/factors.js';
import { renderPage, inner } from '../core/layout.js';

const SPAN = { full: 12, wide: 8, half: 6, narrow: 4, quarter: 3 };
const TWEAK = { 'home:nifty': 6, 'home:option': 3, 'home:finding': 3, 'home:factors': 4, 'home:pair': 12, 'home:params': 12, 'finding:pool': 7, 'finding:magnets-why': 5 };
const two = n => String(n).padStart(2, '0');

const renderers = ctx => {
  return {
    hero: s => `<section class="am-hero wrap" data-sec="${s.key}" data-anim>
      <p class="am-prompt"><span class="am-dollar" aria-hidden="true">$</span> ${esc(s.q)}<span class="am-caret" aria-hidden="true"></span></p>
      <div class="am-readouts">
        <div class="am-ro"><span class="am-ro-k">[fit]</span><b>${esc(s.title)}</b></div>
        <div class="am-ro am-ro-2"><span class="am-ro-k">[read]</span><b>${esc(s.title2)}</b></div>
      </div>
      <p class="am-lede">${esc(s.lead)}</p>
      <div class="am-cta"><a class="btn" href="${s.ctas[0][0]}">${esc(s.ctas[0][1])}</a><a class="btn sec" href="${s.ctas[1][0]}">${esc(s.ctas[1][1])}</a></div></section>`,
    head: s => (s.level === 2
      ? `<header class="am-h2 wrap" data-sec="${s.key}" data-anim><h2>${esc(s.title)}</h2>${s.lead ? `<p class="am-lede">${esc(s.lead)}</p>` : ''}</header>`
      : `<header class="am-head wrap" data-sec="${s.key}" data-anim><h1>${esc(s.title)}</h1>${s.lead ? `<p class="am-lede">${esc(s.lead)}</p>` : ''}</header>`),
    panel: (s, i) => {
      const span = TWEAK[`${ctx.page}:${s.key}`] || SPAN[s.size] || 12;
      return `<article class="am-p am-s${span}${s.accent ? ' am-acc' : ''}" data-sec="${s.key}" data-anim style="--i:${i % 10}">
        <header class="am-ph"><span class="am-ch" aria-hidden="true"></span>${s.ico ? icon(s.ico, { size: 24, tint: 'amber' }) : ''}<h3>${esc(s.title || '')}</h3>${s.note ? `<span class="am-note">${esc(s.note)}</span>` : ''}</header>
        <div class="am-pb">${inner(s)}</div></article>`;
    },
    note: s => `<div class="am-notes am-s12" data-sec="${s.key}">${inner(s)}</div>`,
    group: html => `<div class="am-grid wrap">${html}</div>`,
  };
};

function page(id, ctx) {
  const idx = ctx.pages.findIndex(p => p.id === id);
  return `<div class="am-tick">${B.ticker(ctx)}</div>
    <header class="am-bar wrap"><a class="am-brand" href="index.html">Double Heston</a><span class="am-chip"><i></i>${esc(ctx.C.STATUS)}</span>
      <span class="am-where">[${two(idx + 1)}] ${esc(ctx.pages[idx].label)}</span></header>
    <main id="main" class="am">${renderPage(id, ctx, renderers(ctx))}
      <div class="wrap am-end">${B.pageLinks(ctx, { size: 44, tint: 'amber' })}${B.footer(ctx)}</div></main>`;
}

function mount(app) {
  const stops = [...app.querySelectorAll('[data-trace]')].map(el => factorTrace(el, { span: 2, speed: 0.2, lw: 2.2 }));
  return () => stops.forEach(s => s.stop());
}

export default { nav: { kind: 'dashes', side: 'l' }, chartOpts: { smileBend: { lw: 3.5 } }, page, mount };
