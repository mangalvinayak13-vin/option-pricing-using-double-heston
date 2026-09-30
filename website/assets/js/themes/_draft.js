// Temporary layout for themes not yet built: the same sections as every other theme (core/pages.js),
// in a plain column, so all information is present while the themed layouts are being made.
import * as B from '../core/blocks.js';
import { esc } from '../core/util.js';
import { renderPage, inner } from '../core/layout.js';
import { factorTrace } from '../core/factors.js';

const r = {
  hero: s => `<header class="wrap dr-sec" data-sec="${s.key}"><p class="s-k">${esc(s.q)}</p><h1>${esc(s.title)} ${esc(s.title2)}</h1><p class="dr-lede">${esc(s.lead)}</p>
    <p>${s.ctas.map(([h, l], k) => `<a class="btn${k ? ' ghost' : ''}" href="${h}">${esc(l)}</a>`).join(' ')}</p></header>`,
  head: s => `<header class="wrap dr-sec" data-sec="${s.key}">${s.level === 2 ? `<h2>${esc(s.title)}</h2>` : `<h1>${esc(s.title)}</h1>`}${s.lead ? `<p class="dr-lede">${esc(s.lead)}</p>` : ''}</header>`,
  panel: s => `<section class="dr-panel" data-sec="${s.key}">${s.title ? `<h3>${esc(s.title)}${s.note ? ` <span class="b-sub">${esc(s.note)}</span>` : ''}</h3>` : ''}${inner(s)}</section>`,
  group: html => `<div class="wrap dr-grid">${html}</div>`,
};

export default {
  nav: { kind: 'dashes', side: 'l' },
  page: (id, ctx) => `<main id="main" class="dr">${B.ticker(ctx)}${renderPage(id, ctx, r)}<div class="wrap">${B.pageLinks(ctx)}${B.footer(ctx)}</div></main>`,
  mount(app) { const s = [...app.querySelectorAll('[data-trace]')].map(el => factorTrace(el)); return () => s.forEach(x => x.stop()); },
};
