// Temporary layout used by themes that aren't built yet: every page's real content in a plain column,
// so the site runs end to end while the themed layouts are being made.
import * as B from '../core/blocks.js';
import { esc } from '../core/util.js';

const sec = (key, inner) => `<section class="wrap dr-sec" data-sec="${key}">${inner}</section>`;
const pages = {
  home: ctx => sec('hero', `<h1>${esc(ctx.C.Q)}</h1><p class="dr-lede">${esc(ctx.C.A_SHORT)} ${esc(ctx.C.TWIST)}</p>`) +
    sec('bend', `<h2>${esc(ctx.C.BEND_HEAD)}</h2><p>${esc(ctx.C.BEND)}</p>${B.chart('smileBend', 380)}`) +
    sec('pair', `<h2>${esc(ctx.C.PAIR_HEAD)}</h2><p>${esc(ctx.C.PAIR_LEDE)}</p>${B.chart('pairPart', 380)}`) +
    sec('links', B.pageLinks(ctx)),
  market: ctx => sec('market', `<h1>Market</h1><p class="dr-lede">${esc(ctx.C.MARKET_SUB)}</p><div class="dr-row">${B.marketControls()}</div>${B.candleChart(440)}${B.watchTable(ctx)}`),
  model: ctx => {
    const R = B.priceReadouts(ctx);
    return sec('pricing', `<h1>Price an option</h1>${B.pricingForm(ctx)}<p class="dr-lede">Double Heston ${R.dh} (${R.dhIv}) against the market's ${R.mkt}. ${R.status}</p>${B.chart('marketSmile', 360)}`) +
      sec('sliders', `<div class="dr-2"><div><h2>Slow factor</h2>${B.fellerLine(ctx, 'slow')}${B.sliders(ctx, 'slow')}</div><div><h2>Fast factor</h2>${B.fellerLine(ctx, 'fast')}${B.sliders(ctx, 'fast')}</div></div><button class="btn" data-action="reset" type="button">Reset to starting settings</button>`) +
      sec('chain', B.chainTable(ctx)) + sec('greeks', `<div class="dr-5">${B.greeks(ctx)}</div>`);
  },
  maths: ctx => sec('maths', `<h1>How it works</h1><p class="dr-lede">${esc(ctx.C.MATHS_INTRO)}</p>${B.equations(ctx)}${B.steps(ctx)}${B.chart('decay', 340)}${B.chart('fan', 380)}`),
  finding: ctx => sec('finding', `<h1>${esc(ctx.C.FIND_HEAD)}</h1>${B.chart('hist', 300)}${B.chart('paramBars', 0)}${B.stockPicker(ctx)}${B.chart('stockPanel', 0)}`),
  about: ctx => sec('about', `<h1>${esc(ctx.C.ABOUT_HEAD)}</h1>${B.video(ctx)}${B.bulletList(ctx.C.LIMITS)}`),
  team: ctx => sec('team', `<h1>The team</h1><div class="dr-5">${B.teamCards(ctx)}</div>`),
  references: ctx => sec('refs', `<h1>References</h1>${B.refs(ctx)}`),
};

export default {
  nav: { kind: 'dashes', side: 'l' },
  page: (id, ctx) => `<main id="main" class="dr">${B.ticker(ctx)}${pages[id](ctx)}<div class="wrap">${B.footer(ctx)}</div></main>`,
};
