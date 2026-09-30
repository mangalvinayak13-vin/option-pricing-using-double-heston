// The single source of what every page says. Each page is an ordered list of sections, and every
// theme renders every section: themes change how things look and where they sit, never what the
// page contains. Section keys are the same in all themes, so a theme change keeps the visitor on
// the same section (and links like model.html#smile work everywhere).
//
// section: { key, kind: 'hero' | 'head' | 'panel', title, lead, body, note, size, ico }
//   size is a hint: 'full' | 'wide' (≈2/3) | 'half' | 'narrow' (≈1/3)
import * as B from './blocks.js';
import { esc, inr } from './util.js';
import { store } from './state.js';
import { icon } from './icons.js';

export function sections(page, ctx) {
  const C = ctx.C, D = ctx.D, K = D.contract;
  switch (page) {
    case 'home': {
      const nifty = D.watch.find(x => x.sym === 'NIFTY 50');
      const [a, c] = nifty.pct >= 0 ? ['▲', 'up'] : ['▼', 'dn'];
      const R = B.priceReadouts(ctx);
      return [
        { key: 'hero', kind: 'hero', q: C.Q, title: C.A_SHORT, title2: 'Reading its settings? No.', lead: `${C.A_LONG} ${C.TWIST}`,
          ctas: [['model.html', C.CTA.model], ['finding.html', C.CTA.finding]] },
        { key: 'nifty', title: 'NIFTY 50', ico: 'market', size: 'half', note: `Close ${C.LAST_DAY}`,
          body: `<div class="s-big"><b class="num">${inr(nifty.last)}</b><span class="num ${c}">${a} ${Math.abs(nifty.pct).toFixed(2)}%</span></div>${B.chart('indexLine', 200)}` },
        { key: 'option', title: 'One option', ico: 'model', size: 'narrow',
          body: `<p class="s-k">${R.contract}, expires ${esc(C.EXPIRY)}, ${K.dte} days</p>
            <div class="s-pair s-pair-model"><span>Double Heston</span>${R.dh}</div><div class="s-pair"><span>Market close</span>${R.mkt}</div>
            <p class="s-fine">The model assumes 20% volatility; the market priced ${K.market_iv.toFixed(1)}%.</p>` },
        { key: 'finding', title: 'The finding', ico: 'finding', size: 'narrow', accent: true,
          body: `<p class="s-find">${Math.round(D.ambiguity_summary.share_with_multiple_equivalents * 100)}% of 2,400 real surfaces fit equally well with different settings.</p>
            <div class="s-big s-big-xl"><b class="num" data-count="${D.ratio_to_random.toFixed(1)}" data-dp="1" data-suf="×">${D.ratio_to_random.toFixed(1)}×</b></div>
            <p class="s-fine">further apart than two random parameter sets</p>` },
        { key: 'bend', title: C.BEND_HEAD, ico: 'model', size: 'wide', lead: C.BEND, body: B.chart('smileBend', 380) },
        { key: 'factors', title: 'Two factors, live', ico: 'fast', size: 'narrow', lead: C.FACTORS,
          body: `<div class="factor-trace s-trace" data-trace></div><div class="s-legend"><span><i class="s-sw s-sw-f"></i>Fast, κ 5.0, half-life ${esc(C.FAST_HL)}</span><span><i class="s-sw s-sw-s"></i>Slow, κ 0.5, half-life ${esc(C.SLOW_HL)}</span></div>` },
        { key: 'pair', title: C.PAIR_HEAD, ico: 'finding', size: 'wide', lead: C.PAIR_LEDE, body: B.chart('pairPart', 360) },
        { key: 'params', title: 'Which settings the prices pin down', ico: 'maths', size: 'narrow', lead: C.PER_PARAM,
          body: B.chart('paramBars', 0, { only: ['kappa_s', 'kappa_f', 'sigma_s', 'v0_f', 'v0_s'], rowH: 34, labelW: 150 }) },
      ];
    }
    case 'market': {
      const sym = store.get('market.sym', 'RELIANCE');
      return [
        { key: 'top', kind: 'head', title: 'Market', lead: C.MARKET_SUB },
        { key: 'chart', size: 'wide', body: `<div class="s-stock">${B.stockHead(ctx, sym)}</div><div class="s-ctrls">${B.marketControls()}</div>${B.candleChart(470)}<div class="s-stats">${B.stockStats(ctx, sym)}</div>` },
        { key: 'watch', title: 'Watchlist', ico: 'market', size: 'narrow', note: 'Pick one to chart it', body: `<div class="s-scroll">${B.stocksList(ctx)}</div>` },
        { key: 'nifty', title: 'NIFTY 50', ico: 'market', size: 'half', note: `${C.N_DAYS} trading days`, body: B.chart('indexLine', 260, { which: 'NIFTY' }) },
        { key: 'banknifty', title: 'NIFTY BANK', ico: 'market', size: 'half', note: `${C.N_DAYS} trading days`, body: B.chart('indexLine', 260, { which: 'BANKNIFTY' }) },
        { key: 'covers', title: 'What the site covers', ico: 'about', size: 'full', lead: `${C.UNIVERSE} ${C.STATUS}.` },
      ];
    }
    case 'model': {
      const R = B.priceReadouts(ctx);
      return [
        { key: 'top', kind: 'head', title: 'Price an option', lead: 'Pick a listed NIFTY option, price it with Double Heston, and set it against what the market paid. Move any of the ten settings and the model reprices.' },
        { key: 'form', title: 'The option', ico: 'model', size: 'full', body: B.pricingForm(ctx) },
        { key: 'price', title: 'Double Heston', ico: 'model', size: 'narrow', body: `<div class="s-bignum s-model">${R.dh}</div><p class="s-fine">Implied volatility ${R.dhIv}. Monte Carlo check, 20,000 paths: ${R.mc}</p>` },
        { key: 'market', title: 'Market close', ico: 'market', size: 'narrow', body: `<div class="s-bignum">${R.mkt}</div><p class="s-fine">Implied volatility ${R.mktIv}. NSE close, ${esc(C.LAST_DAY)}.</p>` },
        { key: 'gap', title: 'Model minus market', ico: 'finding', size: 'narrow', body: `<div class="s-bignum">${R.gap}</div><p class="s-fine">${R.status}</p>` },
        { key: 'explain', kind: 'note', size: 'full', lead: C.MODEL_EXPLAIN },
        { key: 'smile', title: 'The smile at this expiry', ico: 'model', size: 'wide', body: B.chart('marketSmile', 380) },
        { key: 'greeks', title: 'Greeks', ico: 'maths', size: 'narrow', body: `<div class="s-greeks">${B.greeks(ctx)}</div>` },
        { key: 'sliders', title: 'Slow factor', ico: 'slow', size: 'half', note: `half-life at κ 0.5: ${C.SLOW_HL}`, body: `${B.fellerLine(ctx, 'slow')}${B.sliders(ctx, 'slow')}` },
        { key: 'sliders-fast', title: 'Fast factor', ico: 'fast', size: 'half', note: `half-life at κ 5.0: ${C.FAST_HL}`, body: `${B.fellerLine(ctx, 'fast')}${B.sliders(ctx, 'fast')}` },
        { key: 'reset', kind: 'note', size: 'full', body: `<div class="s-row-note"><span class="b-sub">${esc(C.FELLER_NOTE)}</span><button class="btn ghost" type="button" data-action="reset">Reset to starting settings</button></div>` },
        { key: 'chain', title: 'Option chain, 27 Oct 2026', ico: 'market', size: 'full', body: `<div class="s-scroll-x">${B.chainTable(ctx)}</div>`, note: 'Pick a row to price that strike' },
        { key: 'source', kind: 'note', size: 'full', fine: C.MODEL_SOURCE },
      ];
    }
    case 'maths':
      return [
        { key: 'top', kind: 'head', title: 'How it works', lead: C.MATHS_INTRO },
        { key: 'bend', title: C.BEND_HEAD, ico: 'model', size: 'full', lead: C.BEND, body: B.chart('smileBend', 400) },
        { key: 'eq', title: 'The equations', ico: 'maths', size: 'wide', body: B.equations(ctx) },
        { key: 'lineage', title: 'Where it comes from', ico: 'references', size: 'narrow', body: B.lineage(ctx, 'b-lin s-lin') },
        { key: 'steps', title: 'Five steps from settings to a price', ico: 'maths', size: 'full', body: B.steps(ctx) },
        { key: 'decay', title: C.FACTORS_HEAD, ico: 'slow', size: 'half', lead: C.TWO_CLOCKS, body: B.chart('decay', 320) },
        { key: 'skew', title: 'Skew by time to expiry', ico: 'model', size: 'half', lead: C.SKEW_NOTE, body: B.chart('skew', 320) },
        { key: 'fan', title: 'Check by simulation', ico: 'fast', size: 'full', lead: C.FAN_NOTE, body: B.chart('fan', 420) },
        { key: 'surface', title: 'The whole surface', ico: 'maths', size: 'full', lead: C.SURFACE_NOTE, body: B.chart('surface', 420) },
      ];
    case 'finding': {
      const sym = store.get('finding.sym', 'RELIANCE');
      return [
        { key: 'top', kind: 'head', title: C.FIND_HEAD, lead: C.TWIST },
        { key: 'proof1', title: C.PROOF1_HEAD, ico: 'maths', size: 'half', lead: C.PROOF1, body: `<div class="s-nums">${B.nums(C.PROOF1_NUMS)}</div>`, fine: C.PROOF1_NET },
        { key: 'proof2', title: C.PROOF2_HEAD, ico: 'market', size: 'half', lead: C.PROOF2, body: `<div class="s-nums">${B.nums(C.PROOF2_NUMS)}</div>` },
        { key: 'hist', title: `How far apart equally good fits landed, ${D.hist.n.toLocaleString('en-IN')} surfaces`, ico: 'finding', size: 'full', body: B.chart('hist', 320) },
        { key: 'params', title: 'Setting by setting', ico: 'maths', size: 'full', lead: C.PER_PARAM, body: B.chart('paramBars', 0) },
        { key: 'pair', kind: 'head', level: 2, title: C.PAIR_HEAD, lead: C.PAIR_LEDE },
        { key: 'pool', title: 'Bharti Airtel, 39-day options', ico: 'model', size: 'wide', body: B.chart('pairPool', 400) },
        { key: 'magnets-why', title: C.PAIR_MAGNETS_HEAD, ico: 'finding', size: 'narrow', lead: `${C.PAIR_MAGNETS} ${C.PAIR_TYPICAL}` },
        { key: 'magnets', title: 'The ten settings of each fit', ico: 'maths', size: 'full', body: B.chart('pairMagnets', 0), fine: C.PAIR_NOTE },
        { key: 'part', title: C.PAIR_PART_HEAD, ico: 'finding', size: 'full', lead: C.PAIR_PART, body: B.chart('pairPart', 400) },
        { key: 'six', title: 'All six equally good fits', ico: 'finding', size: 'full', lead: C.PAIR_SIX, body: B.chart('pairSix', 0) },
        { key: 'stock', title: 'One stock, day by day', ico: 'market', size: 'full',
          body: `<div class="s-ctrls">${B.stockPicker(ctx)}</div><p class="s-lead" data-bind="stock-line">${esc(B.stockLine(ctx, sym))}</p>${B.chart('stockPanel', 0, { sym })}` },
        { key: 'heldout', title: 'Dates it never saw', ico: 'model', size: 'half', body: B.nums([[`${(D.consolidated.g8.median_network_relative * 100).toFixed(1)}%`, C.HELDOUT]]) },
        { key: 'backtest', title: 'A trading test', ico: 'market', size: 'half', body: B.nums([['0 of 210', C.BACKTEST]]) },
      ];
    }
    case 'about':
      return [
        { key: 'top', kind: 'head', title: 'About', lead: C.ABOUT_HEAD },
        { key: 'video', title: 'The explainer video', ico: 'video', size: 'wide', body: B.video(ctx) },
        { key: 'method', title: 'Method and data', ico: 'maths', size: 'narrow', body: `<div class="s-paras">${C.METHOD.map(m => `<p>${esc(m)}</p>`).join('')}</div>` },
        { key: 'limits', title: 'Limits', ico: 'about', size: 'half', body: B.bulletList(C.LIMITS) },
        { key: 'also', title: 'Also explored', ico: 'fast', size: 'half', lead: C.ALSO },
      ];
    case 'team':
      return [
        { key: 'top', kind: 'head', title: C.TEAM_HEAD, lead: C.TEAM_INTRO },
        ...C.TEAM.map(([n, r], i) => ({ key: i ? `person-${i}` : 'team', size: 'quarter', person: true,
          body: `<div class="b-person">${icon('team', { size: 72, tint: ['teal', 'blue', 'orange', 'indigo'][i % 4] })}<b>${esc(n)}</b><span class="b-sub">${esc(r)}</span></div>` })),
        { key: 'supervisor', title: 'Supervisor', ico: 'about', size: 'half', body: `<div class="b-person"><b>${esc(C.SUPERVISOR[0])}</b><span class="b-sub">${esc(C.SUPERVISOR[1])}</span></div>` },
        { key: 'thanks', title: 'Thanks', ico: 'references', size: 'half', body: B.bulletList(C.THANKS) },
      ];
    case 'references':
      return [
        { key: 'top', kind: 'head', title: 'References', lead: 'The papers behind the model and its methods, and where the data comes from.' },
        ...C.REFS.map(([g], k) => ({ key: k ? `refs-${k}` : 'refs', title: g, ico: 'references', size: 'half', body: B.refs(ctx, 'b-refs s-refs', true, { group: k, heading: false }) })),
      ];
    default:
      return [];
  }
}

// every theme ends each page with these, in its own style
export const FOOTER_PARTS = ['apps', 'footer'];
