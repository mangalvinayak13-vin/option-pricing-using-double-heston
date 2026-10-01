// The single source of what every page says. Each page is an ordered list of sections, and every
// theme renders every section: themes change how things look and where they sit, never what the
// page contains. Section keys are the same in all themes, so a theme change keeps the visitor on
// the same section (and links like model.html#smile work everywhere).
//
// section: { key, kind: 'hero' | 'head' | 'panel' | 'note', title, lead, body, note, size, ico }
//   size is a hint: 'full' | 'wide' (≈2/3) | 'half' | 'narrow' (≈1/3) | 'quarter'
// Every chart sits in a figure with a title and a "how to read it" line (content CHART_NOTES).
import * as B from './blocks.js';
import { esc, inr } from './util.js';
import { store } from './state.js';
import { icon } from './icons.js';

// a chart with its title and reading guide
export function fig(ctx, name, h, o, { note = name, title } = {}) {
  const [t, cap] = ctx.C.CHART_NOTES[note] || [];
  return `<figure class="fig"><figcaption class="fig-t">${esc(title || t || '')}</figcaption>${B.chart(name, h, o)}${cap ? `<p class="fig-cap">${esc(cap)}</p>` : ''}</figure>`;
}
const traceFig = ctx => {
  const [t, cap] = ctx.C.CHART_NOTES.factorTrace;
  return `<figure class="fig"><figcaption class="fig-t">${esc(t)}</figcaption><div class="factor-trace s-trace" data-trace></div>
    <div class="s-legend"><span><i class="s-sw s-sw-f"></i>Fast, κ 5.0, ξ 0.5, half-life ${esc(ctx.C.FAST_HL)}</span><span><i class="s-sw s-sw-s"></i>Slow, κ 0.5, ξ 0.3, half-life ${esc(ctx.C.SLOW_HL)}</span></div>
    <p class="fig-cap">${esc(cap)}</p></figure>`;
};

function journey(ctx) {
  const C = ctx.C, [t, cap] = C.CHART_NOTES.journey;
  return `<figure class="fig"><figcaption class="fig-t">${esc(t)}</figcaption>${B.chart('journey', 230)}<p class="fig-cap">${esc(cap)}</p></figure>
    <ol class="b-journey">${C.JOURNEY.map(([y, who, what], i) => `<li class="${y === '2026' ? 'now' : ''}" style="--i:${i}"><b class="b-jy num">${esc(y)}</b><span><b>${esc(who)}</b><span>${esc(what)}</span></span></li>`).join('')}</ol>`;
}

function done(ctx) {
  return `<ol class="b-done">${ctx.C.DONE.map(([h, d], i) => `<li style="--i:${i}"><b class="b-dn num">${i + 1}</b><span><b>${esc(h)}</b><span>${esc(d)}</span></span></li>`).join('')}</ol>`;
}

function pinnAnn(ctx) {
  const C = ctx.C, [t, cap] = C.CHART_NOTES.pinnAnn;
  return `<figure class="fig"><figcaption class="fig-t">${esc(t)}</figcaption>
    <div class="pa3d" data-pa3d tabindex="0" aria-label="${esc(t)}. Use the left and right arrow keys to turn the surfaces.">
      <div class="pa3d-cell"><span class="pa3d-l"><b>ANN</b> learned from 48 prices only</span><canvas data-net="ann" aria-hidden="true"></canvas></div>
      <div class="pa3d-cell"><span class="pa3d-l"><b>PINN</b> the same 48 prices, plus the pricing equation</span><canvas data-net="pinn" aria-hidden="true"></canvas></div>
    </div>
    <div class="pa3d-key"><span><i class="pa3d-k-net"></i>network's price surface</span><span><i class="pa3d-k-exact"></i>exact Double Heston price</span><span><i class="pa3d-k-neg"></i>price below zero by more than 0.2% of the strike (impossible)</span></div>
    <p class="fig-cap">${esc(cap)}</p></figure>
    <div class="s-nums">${B.nums(C.PA_NUMS)}</div><p class="s-lead">${esc(C.PA_RESULT)}</p><p class="s-fine">${esc(C.PA_NOTE)}</p>`;
}

function dataTable(ctx) {
  return `<div class="s-scroll-x"><table class="b-tb b-data"><caption class="vh">The data behind every result</caption><thead><tr><th scope="col">Data</th><th scope="col">Size</th><th scope="col">What it is</th></tr></thead><tbody>${ctx.C.DATA_SETS.map(([n, s, w]) =>
    `<tr><th scope="row">${esc(n)}</th><td class="num">${esc(s)}</td><td class="b-wrap">${esc(w)}</td></tr>`).join('')}</tbody></table></div>`;
}

function resultsTable(ctx) {
  const label = { good: 'Good news', mixed: 'Mixed', bad: 'Bad news' };
  return `<div class="s-scroll-x"><table class="b-tb b-results"><caption class="vh">Every result of the project</caption><thead><tr><th scope="col">Result</th><th scope="col">Value</th><th scope="col">What it measures</th><th scope="col">Reading</th></tr></thead><tbody>${ctx.C.RESULTS.map(([n, v, w, verdict]) =>
    `<tr><th scope="row">${esc(n)}</th><td class="num b-val">${esc(v)}</td><td class="b-wrap">${esc(w)}</td><td><span class="b-verdict b-v-${verdict}">${label[verdict]}</span></td></tr>`).join('')}</tbody></table></div>`;
}

const terms = ctx => `<dl class="b-terms">${ctx.C.TERMS.map(([t, d]) => `<div><dt>${esc(t)}</dt><dd>${esc(d)}</dd></div>`).join('')}</dl>`;

export function sections(page, ctx) {
  const C = ctx.C, D = ctx.D, K = D.contract;
  switch (page) {
    case 'home': {
      const nifty = D.watch.find(x => x.sym === 'NIFTY 50');
      const [a, c] = nifty.pct >= 0 ? ['▲', 'up'] : ['▼', 'dn'];
      const R = B.priceReadouts(ctx);
      return [
        { key: 'hero', kind: 'hero', q: C.Q, title: C.A_SHORT, title2: 'Reading its settings? No.', lead: `${C.A_LONG} ${C.TWIST}`,
          ctas: [['model.html', C.CTA.model], ['results.html', 'See every result']] },
        { key: 'journey', title: C.JOURNEY_HEAD, ico: 'references', size: 'full', lead: C.JOURNEY_LEDE, body: journey(ctx) },
        { key: 'done', title: C.DONE_HEAD, ico: 'maths', size: 'full', body: done(ctx) },
        { key: 'nn', title: C.PA_HEAD, ico: 'model', size: 'full', lead: C.PA_LEDE, body: pinnAnn(ctx) },
        { key: 'finding', title: 'The finding', ico: 'finding', size: 'narrow', accent: true,
          body: `<p class="s-find">${Math.round(D.ambiguity_summary.share_with_multiple_equivalents * 100)}% of 2,400 real surfaces fit equally well with different settings.</p>
            <div class="s-big s-big-xl"><b class="num" data-count="${D.ratio_to_random.toFixed(1)}" data-dp="1" data-suf="×">${D.ratio_to_random.toFixed(1)}×</b></div>
            <p class="s-fine">further apart than two random parameter sets</p>` },
        { key: 'option', title: 'One option', ico: 'model', size: 'narrow',
          body: `<p class="s-k">${R.contract}, expires ${esc(C.EXPIRY)}, ${K.dte} days</p>
            <div class="s-pair s-pair-model"><span>Double Heston</span>${R.dh}</div><div class="s-pair"><span>Market close</span>${R.mkt}</div>
            <p class="s-fine">The model assumes 20% volatility; the market priced ${K.market_iv.toFixed(1)}%.</p>` },
        { key: 'nifty', title: 'NIFTY 50', ico: 'market', size: 'narrow', note: `Close ${C.LAST_DAY}`,
          body: `<div class="s-big"><b class="num">${inr(nifty.last)}</b><span class="num ${c}">${a} ${Math.abs(nifty.pct).toFixed(2)}%</span></div>${fig(ctx, 'indexLine', 170, { which: 'NIFTY' }, { title: 'NIFTY 50, closing level by day' })}` },
        { key: 'bend', title: C.BEND_HEAD, ico: 'model', size: 'wide', lead: C.BEND, body: fig(ctx, 'smileBend', 380) },
        { key: 'factors', title: 'Two factors, live', ico: 'fast', size: 'narrow', lead: C.FACTORS, body: traceFig(ctx) },
        { key: 'pair', title: C.PAIR_HEAD, ico: 'finding', size: 'full', lead: C.PAIR_LEDE, body: fig(ctx, 'pairPart', 360) },
      ];
    }
    case 'market': {
      const sym = store.get('market.sym', 'RELIANCE');
      return [
        { key: 'top', kind: 'head', title: 'Market', lead: C.MARKET_SUB },
        { key: 'chart', size: 'wide', body: `<div class="s-stock">${B.stockHead(ctx, sym)}</div><div class="s-ctrls">${B.marketControls()}</div>
          <figure class="fig"><figcaption class="fig-t">${esc(C.CHART_NOTES.candles[0])}</figcaption>${B.candleChart(470)}<p class="fig-cap">${esc(C.CHART_NOTES.candles[1])}</p></figure>
          <div class="s-stats">${B.stockStats(ctx, sym)}</div>` },
        { key: 'watch', title: 'Watchlist', ico: 'market', size: 'narrow', note: 'Pick one to chart it', body: `<div class="s-scroll">${B.stocksList(ctx)}</div>` },
        { key: 'nifty', title: 'NIFTY 50', ico: 'market', size: 'half', note: `${C.N_DAYS} trading days`, body: fig(ctx, 'indexLine', 260, { which: 'NIFTY' }, { title: 'NIFTY 50, closing level by day' }) },
        { key: 'banknifty', title: 'NIFTY BANK', ico: 'market', size: 'half', note: `${C.N_DAYS} trading days`, body: fig(ctx, 'indexLine', 260, { which: 'BANKNIFTY' }, { title: 'NIFTY BANK, closing level by day' }) },
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
        { key: 'smile', title: 'The smile at this expiry', ico: 'model', size: 'wide', body: fig(ctx, 'marketSmile', 380) },
        { key: 'greeks', title: 'Greeks', ico: 'maths', size: 'narrow', body: `<div class="s-greeks">${B.greeks(ctx)}</div><p class="s-fine">How the model's price changes when one input moves, at your settings.</p>` },
        { key: 'sliders', title: 'Slow factor', ico: 'slow', size: 'half', note: `half-life at κ 0.5: ${C.SLOW_HL}`, body: `${B.fellerLine(ctx, 'slow')}${B.sliders(ctx, 'slow')}` },
        { key: 'sliders-fast', title: 'Fast factor', ico: 'fast', size: 'half', note: `half-life at κ 5.0: ${C.FAST_HL}`, body: `${B.fellerLine(ctx, 'fast')}${B.sliders(ctx, 'fast')}` },
        { key: 'reset', kind: 'note', size: 'full', body: `<div class="s-row-note"><span class="b-sub">${esc(C.FELLER_NOTE)}</span><button class="btn ghost" type="button" data-action="reset">Reset to starting settings</button></div>` },
        { key: 'chain', title: 'Option chain, 27 Oct 2026', ico: 'market', size: 'full', body: `<p class="fig-t">NSE closing prices and implied volatilities, with the model's price for each strike</p><div class="s-scroll-x">${B.chainTable(ctx)}</div><p class="fig-cap">Each row is one strike. Call and put columns are NSE closing prices; IV is the implied volatility they imply; the model columns are Double Heston at your settings. Pick a row to price that strike.</p>` },
        { key: 'source', kind: 'note', size: 'full', fine: C.MODEL_SOURCE },
      ];
    }
    case 'maths':
      return [
        { key: 'top', kind: 'head', title: 'How it works', lead: C.MATHS_INTRO },
        { key: 'bend', title: C.BEND_HEAD, ico: 'model', size: 'full', lead: C.BEND, body: fig(ctx, 'smileBend', 400) },
        { key: 'steps', title: 'Five steps from settings to a price', ico: 'maths', size: 'full', body: B.steps(ctx) },
        { key: 'eq', title: 'The equations', ico: 'maths', size: 'full', body: B.equations(ctx) },
        { key: 'decay', title: C.FACTORS_HEAD, ico: 'slow', size: 'half', lead: C.TWO_CLOCKS, body: fig(ctx, 'decay', 320) },
        { key: 'skew', title: 'Skew by time to expiry', ico: 'model', size: 'half', lead: C.SKEW_NOTE, body: fig(ctx, 'skew', 320) },
        { key: 'fan', title: 'Check by simulation', ico: 'fast', size: 'full', lead: C.FAN_NOTE, body: fig(ctx, 'fan', 420) },
        { key: 'surface', title: 'The whole surface', ico: 'maths', size: 'full', lead: C.SURFACE_NOTE, body: fig(ctx, 'surface', 420) },
      ];
    case 'finding': {
      const sym = store.get('finding.sym', 'RELIANCE');
      return [
        { key: 'top', kind: 'head', title: C.FIND_HEAD, lead: C.TWIST },
        { key: 'proof1', title: C.PROOF1_HEAD, ico: 'maths', size: 'half', lead: C.PROOF1, body: `<div class="s-nums">${B.nums(C.PROOF1_NUMS)}</div>`, fine: C.PROOF1_NET },
        { key: 'proof2', title: C.PROOF2_HEAD, ico: 'market', size: 'half', lead: C.PROOF2, body: `<div class="s-nums">${B.nums(C.PROOF2_NUMS)}</div>` },
        { key: 'hist', title: `How far apart equally good fits landed, ${D.hist.n.toLocaleString('en-IN')} surfaces`, ico: 'finding', size: 'full', body: fig(ctx, 'hist', 320) },
        { key: 'params', title: 'Setting by setting', ico: 'maths', size: 'full', lead: C.PER_PARAM, body: fig(ctx, 'paramBars', 0) },
        { key: 'pair', kind: 'head', level: 2, title: C.PAIR_HEAD, lead: C.PAIR_LEDE },
        { key: 'pool', title: 'Bharti Airtel, 39‑day options', ico: 'model', size: 'wide', body: fig(ctx, 'pairPool', 400) },
        { key: 'magnets-why', title: C.PAIR_MAGNETS_HEAD, ico: 'finding', size: 'narrow', lead: `${C.PAIR_MAGNETS} ${C.PAIR_TYPICAL}` },
        { key: 'magnets', title: 'The ten settings of each fit', ico: 'maths', size: 'full', body: fig(ctx, 'pairMagnets', 0), fine: C.PAIR_NOTE },
        { key: 'part', title: C.PAIR_PART_HEAD, ico: 'finding', size: 'full', lead: C.PAIR_PART, body: fig(ctx, 'pairPart', 400) },
        { key: 'six', title: 'All six equally good fits', ico: 'finding', size: 'full', lead: C.PAIR_SIX, body: fig(ctx, 'pairSix', 0) },
        { key: 'stock', title: 'One stock, day by day', ico: 'market', size: 'full',
          body: `<div class="s-ctrls">${B.stockPicker(ctx)}</div><p class="s-lead" data-bind="stock-line">${esc(B.stockLine(ctx, sym))}</p>${fig(ctx, 'stockPanel', 0, { sym })}` },
        { key: 'nets', kind: 'head', level: 2, title: C.NN_HEAD, lead: `${C.ANN_TEXT} ${C.PINN_TEXT}` },
        { key: 'heldout', title: 'The ANN on dates it never saw', ico: 'model', size: 'half', body: B.nums([[`${(D.consolidated.g8.median_network_relative * 100).toFixed(1)}%`, C.HELDOUT]]) },
        { key: 'backtest', title: 'The ANN against Black–Scholes', ico: 'market', size: 'half', body: B.nums([[C.BEAT_BS_NUM, C.BACKTEST]]) },
        { key: 'pinn', title: 'The PINN on real NIFTY options', ico: 'maths', size: 'full', body: `${B.nums([[`${C.PINN_NIFTY.ft_3.toFixed(2)}`, 'PINN calibrator, median error in volatility points'], [`${C.PINN_NIFTY.bs.toFixed(2)}`, 'Black–Scholes on the same quotes'], [`${C.PINN_NIFTY_BEST} of 10`, 'days the PINN was the best model']])}<p class="s-lead">${esc(C.PINN_MARKET)}</p>` },
      ];
    }
    case 'results':
      return [
        { key: 'top', kind: 'head', title: C.RESULTS_HEAD, lead: C.RESULTS_LEDE },
        { key: 'data', title: 'The data', ico: 'market', size: 'full', body: dataTable(ctx) },
        { key: 'results', title: 'Every result', ico: 'finding', size: 'full', body: resultsTable(ctx) },
        { key: 'terms', title: 'What the words mean', ico: 'about', size: 'full', body: terms(ctx) },
      ];
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
        { key: 'top', kind: 'head', title: 'References', lead: 'The papers behind the model and its methods, the history it grew from, and where the data comes from.' },
        ...C.REFS.map(([g], k) => ({ key: k ? `refs-${k}` : 'refs', title: g, ico: 'references', size: 'half', body: B.refs(ctx, 'b-refs s-refs', true, { group: k, heading: false }) })),
      ];
    default:
      return [];
  }
}
