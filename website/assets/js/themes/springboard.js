// Springboard: the site as an iPhone home screen. Widgets of mixed sizes on a grouped background,
// app icons for every page, a frosted dock that magnifies under the cursor, iOS large titles.
import * as B from '../core/blocks.js';
import { icon } from '../core/icons.js';
import { esc, inr } from '../core/util.js';
import { factorTrace } from '../core/factors.js';
import { reduced } from '../core/motion.js';
import { store } from '../core/state.js';

// a widget: span on the 12-column grid, optional header with a small icon
const wg = (span, inner, { title, ico, note, cls = '', sec, i = 0, tint } = {}) =>
  `<article class="sb-w sb-s${span} ${cls}" data-glint data-anim ${sec ? `data-sec="${sec}"` : ''} style="--i:${i}">
    ${title ? `<header class="sb-wh">${ico ? icon(ico, { size: 28, tint }) : ''}<h3>${esc(title)}</h3>${note ? `<span class="sb-wh-r">${note}</span>` : ''}</header>` : ''}
    <div class="sb-wb">${inner}</div></article>`;

const head = (title, sub, sec = 'top') => `<header class="sb-head wrap" data-sec="${sec}"><h1 class="sb-title">${esc(title)}</h1>${sub ? `<p class="sb-sub">${esc(sub)}</p>` : ''}</header>`;
const grid = inner => `<div class="sb-grid wrap">${inner}</div>`;
const sectionTitle = (t, sub, sec) => `<div class="sb-st wrap" ${sec ? `data-sec="${sec}"` : ''}><h2>${esc(t)}</h2>${sub ? `<p>${esc(sub)}</p>` : ''}</div>`;

function statusBar(ctx) {
  return `<div class="sb-status">${B.ticker(ctx)}</div>`;
}

function dock(ctx) {
  const ids = ['home', 'market', 'model', 'finding', 'about'];
  return `<nav class="sb-dock-wrap wrap" aria-label="Main pages"><div class="sb-dock">${ids.map(id => {
    const p = ctx.pages.find(x => x.id === id);
    return `<a href="${p.file}" class="sb-dock-i${id === ctx.page ? ' cur' : ''}"${id === ctx.page ? ' aria-current="page"' : ''}>${icon(id, { size: 64 })}<span class="sb-dock-l">${esc(p.label)}</span></a>`;
  }).join('')}</div></nav>`;
}

function apps(ctx, title = 'Everything on the site') {
  return `<section class="sb-apps wrap" data-sec="apps" aria-label="${esc(title)}"><div class="sb-appgrid">${ctx.pages.map(p =>
    `<a href="${p.file}" class="sb-app"${p.id === ctx.page ? ' aria-current="page"' : ''}>${icon(p.id, { size: 76 })}<span>${esc(p.label)}</span></a>`).join('')}</div></section>`;
}

const shell = (ctx, body) => `${statusBar(ctx)}<main id="main" class="sb">${body}${apps(ctx)}${dock(ctx)}<div class="wrap">${B.footer(ctx)}</div></main>`;

// ------------------------------------------------------------------ pages
function home(ctx) {
  const C = ctx.C, D = ctx.D, K = D.contract, nifty = D.watch.find(x => x.sym === 'NIFTY 50');
  const R = B.priceReadouts(ctx);
  const [a, c] = nifty.pct >= 0 ? ['▲', 'up'] : ['▼', 'dn'];
  return shell(ctx, `
  <header class="sb-head sb-hero wrap" data-sec="hero">
    <p class="sb-q">${esc(C.Q)}</p>
    <h1 class="sb-title sb-title-xl">${esc(C.A_SHORT)}<br><span class="sb-title-2">${esc('Reading its settings? No.')}</span></h1>
    <p class="sb-sub">${esc(C.A_LONG)} ${esc(C.TWIST)}</p>
    <div class="sb-cta"><a class="btn" href="model.html">${esc(C.CTA.model)}</a><a class="btn ghost" href="finding.html">${esc(C.CTA.finding)}</a></div>
  </header>
  ${grid(`
    ${wg(6, `<div class="sb-big"><b class="num">${inr(nifty.last)}</b><span class="num ${c}">${a} ${Math.abs(nifty.pct).toFixed(2)}%</span></div>${B.chart('indexLine', 200)}`,
      { title: 'NIFTY 50', ico: 'market', note: `Close ${esc(C.LAST_DAY)}`, sec: 'nifty', i: 0 })}
    ${wg(3, `<p class="sb-k">${R.contract}, expires ${esc(C.EXPIRY)}, ${K.dte} days</p>
      <div class="sb-pair"><span>Double Heston</span>${R.dh}</div><div class="sb-pair"><span>Market close</span>${R.mkt}</div>
      <p class="sb-fine">The model assumes 20% volatility; the market priced ${K.market_iv.toFixed(1)}%.</p>`, { title: 'One option', ico: 'model', i: 1 })}
    ${wg(3, `<p class="sb-find">${esc(`${Math.round(D.ambiguity_summary.share_with_multiple_equivalents * 100)}% of 2,400 real surfaces fit equally well with different settings.`)}</p>
      <div class="sb-big sb-big-on"><b class="num" data-count="${D.ratio_to_random.toFixed(1)}" data-dp="1" data-suf="×">${D.ratio_to_random.toFixed(1)}×</b></div>
      <p class="sb-fine sb-on">further apart than two random parameter sets</p>`, { title: 'The finding', ico: 'finding', cls: 'sb-w-acc', i: 2 })}
    ${wg(8, `<p class="sb-lead">${esc(C.BEND)}</p>${B.chart('smileBend', 380)}`, { title: C.BEND_HEAD, ico: 'model', sec: 'bend', i: 3 })}
    ${wg(4, `<p class="sb-lead">${esc(C.FACTORS)}</p><div class="factor-trace sb-trace" data-trace></div>
      <div class="sb-legend"><span><i class="sb-sw sb-sw-f"></i>Fast, κ 5.0, half-life ${esc(C.FAST_HL)}</span><span><i class="sb-sw sb-sw-s"></i>Slow, κ 0.5, half-life ${esc(C.SLOW_HL)}</span></div>`,
      { title: 'Two factors, live', ico: 'fast', sec: 'factors', i: 4 })}
    ${wg(7, `<p class="sb-lead">${esc(C.PAIR_LEDE)}</p>${B.chart('pairPart', 360)}`, { title: C.PAIR_HEAD, ico: 'finding', sec: 'pair', i: 5 })}
    ${wg(5, `<p class="sb-lead">${esc(C.PER_PARAM)}</p>${B.chart('paramBars', 0, { only: ['kappa_s', 'kappa_f', 'sigma_s', 'v0_f', 'v0_s'], rowH: 34, labelW: 150 })}`,
      { title: 'Which settings the prices pin down', ico: 'maths', sec: 'params', i: 6 })}
  `)}`);
}

function market(ctx) {
  const C = ctx.C, selSym = store.get('market.sym', 'RELIANCE');
  return shell(ctx, `${head('Market', C.MARKET_SUB)}
  ${grid(`
    ${wg(8, `<div class="sb-stock">${B.stockHead(ctx, selSym)}</div><div class="sb-ctrls">${B.marketControls()}</div>${B.candleChart(470)}
      <div class="sb-stats">${B.stockStats(ctx, selSym)}</div>`, { sec: 'chart', cls: 'sb-w-pad', i: 0 })}
    ${wg(4, `<div class="sb-scroll">${B.stocksList(ctx)}</div>`, { title: 'Watchlist', ico: 'market', note: 'Tap to chart', sec: 'watch', i: 1 })}
    ${wg(6, B.chart('indexLine', 260, { which: 'NIFTY' }), { title: 'NIFTY 50', ico: 'market', note: `${C.N_DAYS} trading days`, sec: 'nifty', i: 2 })}
    ${wg(6, B.chart('indexLine', 260, { which: 'BANKNIFTY' }), { title: 'NIFTY BANK', ico: 'market', note: `${C.N_DAYS} trading days`, i: 3 })}
    ${wg(12, `<p class="sb-lead">${esc(C.UNIVERSE)} ${esc(C.STATUS)}.</p>`, { title: 'What the site covers', ico: 'about', i: 4 })}
  `)}`);
}

function model(ctx) {
  const C = ctx.C, R = B.priceReadouts(ctx);
  return shell(ctx, `${head('Price an option', 'Pick a listed NIFTY option, price it with Double Heston, and set it against what the market paid. Move any of the ten settings and the model reprices.')}
  ${grid(`
    ${wg(12, B.pricingForm(ctx), { title: 'The option', ico: 'model', sec: 'form', i: 0 })}
    ${wg(4, `<div class="sb-bignum">${R.dh}</div><p class="sb-fine">Implied volatility ${R.dhIv}. ${esc('Monte Carlo check, 20,000 paths:')} ${R.mc}</p>`, { title: 'Double Heston', ico: 'model', sec: 'price', i: 1 })}
    ${wg(4, `<div class="sb-bignum">${R.mkt}</div><p class="sb-fine">Implied volatility ${R.mktIv}. NSE close, ${esc(C.LAST_DAY)}.</p>`, { title: 'Market close', ico: 'market', i: 2 })}
    ${wg(4, `<div class="sb-bignum">${R.gap}</div><p class="sb-fine">${R.status}</p>`, { title: 'Model minus market', ico: 'finding', i: 3 })}
    ${wg(12, `<p class="sb-lead">${esc(C.MODEL_EXPLAIN)}</p>`, { cls: 'sb-w-note', i: 4 })}
    ${wg(8, B.chart('marketSmile', 380), { title: 'The smile at this expiry', ico: 'model', sec: 'smile', i: 5 })}
    ${wg(4, `<div class="sb-greeks">${B.greeks(ctx)}</div>`, { title: 'Greeks', ico: 'maths', sec: 'greeks', i: 6 })}
    ${wg(6, `${B.fellerLine(ctx, 'slow')}${B.sliders(ctx, 'slow')}`, { title: 'Slow factor', ico: 'slow', note: `half-life at κ 0.5: ${esc(C.SLOW_HL)}`, sec: 'sliders', i: 7 })}
    ${wg(6, `${B.fellerLine(ctx, 'fast')}${B.sliders(ctx, 'fast')}`, { title: 'Fast factor', ico: 'fast', note: `half-life at κ 5.0: ${esc(C.FAST_HL)}`, i: 8 })}
    <div class="sb-s12 sb-row-note"><span class="b-sub">${esc(C.FELLER_NOTE)}</span><button class="btn ghost" type="button" data-action="reset">Reset to starting settings</button></div>
    ${wg(12, `<div class="sb-scroll-x">${B.chainTable(ctx)}</div><p class="sb-fine">Tap a row to price that strike.</p>`, { title: 'Option chain, 27 Oct 2026', ico: 'market', sec: 'chain', i: 9 })}
    ${wg(12, `<p class="sb-fine">${esc(C.MODEL_SOURCE)}</p>`, { cls: 'sb-w-note', i: 10 })}
  `)}`);
}

function maths(ctx) {
  const C = ctx.C;
  return shell(ctx, `${head('How it works', C.MATHS_INTRO)}
  ${grid(`
    ${wg(12, `<p class="sb-lead">${esc(C.BEND)}</p>${B.chart('smileBend', 400)}`, { title: C.BEND_HEAD, ico: 'model', sec: 'bend', i: 0 })}
    ${wg(7, B.equations(ctx), { title: 'The equations', ico: 'maths', sec: 'eq', i: 1 })}
    ${wg(5, `${B.lineage(ctx, 'b-lin sb-lin')}`, { title: 'Where it comes from', ico: 'references', i: 2 })}
    ${wg(12, B.steps(ctx), { title: 'Five steps from settings to a price', ico: 'maths', sec: 'steps', i: 3 })}
    ${wg(6, `<p class="sb-lead">${esc(C.TWO_CLOCKS)}</p>${B.chart('decay', 320)}`, { title: C.FACTORS_HEAD, ico: 'slow', sec: 'decay', i: 4 })}
    ${wg(6, `<p class="sb-lead">${esc(C.SKEW_NOTE)}</p>${B.chart('skew', 320)}`, { title: 'Skew by time to expiry', ico: 'model', i: 5 })}
    ${wg(12, `<p class="sb-lead">${esc(C.FAN_NOTE)}</p>${B.chart('fan', 420)}`, { title: 'Check by simulation', ico: 'fast', sec: 'fan', i: 6 })}
    ${wg(12, `<p class="sb-lead">${esc(C.SURFACE_NOTE)}</p>${B.chart('surface', 420)}`, { title: 'The whole surface', ico: 'maths', sec: 'surface', i: 7 })}
  `)}`);
}

function finding(ctx) {
  const C = ctx.C, sym = store.get('finding.sym', 'RELIANCE');
  return shell(ctx, `${head(C.FIND_HEAD, C.TWIST)}
  ${grid(`
    ${wg(6, `<p class="sb-lead">${esc(C.PROOF1)}</p><div class="sb-nums">${B.nums(C.PROOF1_NUMS)}</div><p class="sb-fine">${esc(C.PROOF1_NET)}</p>`, { title: C.PROOF1_HEAD, ico: 'maths', sec: 'proof1', i: 0 })}
    ${wg(6, `<p class="sb-lead">${esc(C.PROOF2)}</p><div class="sb-nums">${B.nums(C.PROOF2_NUMS)}</div>`, { title: C.PROOF2_HEAD, ico: 'market', sec: 'proof2', i: 1 })}
    ${wg(12, B.chart('hist', 320), { title: 'How far apart equally good fits landed, 2,379 surfaces', ico: 'finding', sec: 'hist', i: 2 })}
    ${wg(12, `<p class="sb-lead">${esc(C.PER_PARAM)}</p>${B.chart('paramBars', 0)}`, { title: 'Setting by setting', ico: 'maths', sec: 'params', i: 3 })}
  `)}
  ${sectionTitle(C.PAIR_HEAD, C.PAIR_LEDE, 'pair')}
  ${grid(`
    ${wg(7, B.chart('pairPool', 400), { title: 'Bharti Airtel, 39-day options', ico: 'model', i: 0 })}
    ${wg(5, `<p class="sb-lead">${esc(C.PAIR_MAGNETS)}</p><p class="sb-lead">${esc(C.PAIR_TYPICAL)}</p>`, { title: C.PAIR_MAGNETS_HEAD, ico: 'finding', i: 1 })}
    ${wg(12, `${B.chart('pairMagnets', 0)}<p class="sb-fine">${esc(C.PAIR_NOTE)}</p>`, { title: 'The ten settings of each fit', ico: 'maths', sec: 'magnets', i: 2 })}
    ${wg(12, `<p class="sb-lead">${esc(C.PAIR_PART)}</p>${B.chart('pairPart', 400)}`, { title: C.PAIR_PART_HEAD, ico: 'finding', sec: 'part', i: 3 })}
    ${wg(12, `<p class="sb-lead">${esc(C.PAIR_SIX)}</p>${B.chart('pairSix', 0)}`, { title: 'All six equally good fits', ico: 'finding', sec: 'six', i: 4 })}
    ${wg(12, `<div class="sb-ctrls">${B.stockPicker(ctx)}</div><p class="sb-lead" data-bind="stock-line">${esc(B.stockLine(ctx, sym))}</p>${B.chart('stockPanel', 0, { sym })}`,
      { title: 'One stock, day by day', ico: 'market', sec: 'stock', i: 5 })}
    ${wg(6, B.nums([[`${(ctx.D.consolidated.g8.median_network_relative * 100).toFixed(1)}%`, C.HELDOUT]]), { title: 'Dates it never saw', ico: 'model', sec: 'heldout', i: 6 })}
    ${wg(6, B.nums([['0 of 210', C.BACKTEST]]), { title: 'A trading test', ico: 'market', i: 7 })}
  `)}`);
}

function about(ctx) {
  const C = ctx.C;
  return shell(ctx, `${head('About', C.ABOUT_HEAD)}
  ${grid(`
    ${wg(7, B.video(ctx), { title: 'The explainer video', ico: 'video', sec: 'video', i: 0 })}
    ${wg(5, `<div class="sb-paras">${C.METHOD.map(m => `<p>${esc(m)}</p>`).join('')}</div>`, { title: 'Method and data', ico: 'maths', sec: 'method', i: 1 })}
    ${wg(6, B.bulletList(C.LIMITS), { title: 'Limits', ico: 'about', sec: 'limits', i: 2 })}
    ${wg(6, `<p class="sb-lead">${esc(C.ALSO)}</p><p><a class="btn ghost" href="https://${esc(C.REPO)}" rel="noopener">Open the code on GitHub</a></p>`, { title: 'Also explored', ico: 'fast', i: 3 })}
  `)}`);
}

function team(ctx) {
  const C = ctx.C;
  return shell(ctx, `${head(C.TEAM_HEAD, C.TEAM_INTRO)}
  ${grid(`
    ${C.TEAM.map(([n, r], i) => wg(3, `<div class="b-person">${icon('team', { size: 72, tint: ['teal', 'blue', 'orange', 'indigo'][i % 4] })}<b>${esc(n)}</b><span class="b-sub">${esc(r)}</span></div>`, { sec: i ? '' : 'team', i })).join('')}
    ${wg(6, `<div class="b-person"><b>${esc(C.SUPERVISOR[0])}</b><span class="b-sub">${esc(C.SUPERVISOR[1])}</span></div>`, { title: 'Supervisor', ico: 'about', i: 4 })}
    ${wg(6, B.bulletList(C.THANKS), { title: 'Thanks', ico: 'references', i: 5 })}
  `)}`);
}

function references(ctx) {
  return shell(ctx, `${head('References', 'The papers behind the model and its methods, and where the data comes from.')}
  ${grid(ctx.C.REFS.map(([g], k) => wg(k < 2 ? 6 : 6, B.refs({ ...ctx, C: { ...ctx.C, REFS: [ctx.C.REFS[k]] } }, 'b-refs sb-refs', true).replace(/<h2>.*?<\/h2>/, ''),
    { title: g, ico: 'references', sec: k ? '' : 'refs', i: k })).join(''))}`);
}

const PAGES = { home, market, model, maths, finding, about, team, references };

// ------------------------------------------------------------------ behaviour
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

export default {
  nav: { kind: 'dashes', side: 'l' },
  page: (id, ctx) => PAGES[id](ctx),
  mount,
};
