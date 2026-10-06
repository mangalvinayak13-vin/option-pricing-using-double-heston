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

// Home: the project's two aims, numbered as the brief numbers them
const aims = ctx => `<ol class="b-done b-aims">${ctx.C.AIMS.map(([h, d], i) => `<li style="--i:${i}"><b class="b-dn num">${i + 1}</b><span><b>${esc(h)}</b><span>${esc(d)}</span></span></li>`).join('')}</ol>`;

function done(ctx) {
  return `<ol class="b-done">${ctx.C.DONE.map(([h, d], i) => `<li style="--i:${i}"><b class="b-dn num">${i + 1}</b><span><b>${esc(h)}</b><span>${esc(d)}</span></span></li>`).join('')}</ol>`;
}

function pinnAnn(ctx) {
  const C = ctx.C, [t, cap] = C.CHART_NOTES.pinnAnn;
  return `<p class="s-lead">${esc(C.PA_WHY)}</p><figure class="fig"><figcaption class="fig-t">${esc(t)}</figcaption>
    <div class="pa3d-ctl">${B.seg('pa-view', [['price', 'Price'], ['error', 'Error']], 'price', 'What the surfaces show')}
      <button class="btn ghost pa3d-play" type="button" data-pa-play>Replay training</button>
      <label class="pa3d-step"><span>After <b class="num" data-pa-steplabel>${C.PA_STEPS.at(-1).toLocaleString('en-IN')}</b> training steps</span>
        <input type="range" min="0" max="${C.PA_STEPS.length - 1}" step="any" value="${C.PA_STEPS.length - 1}" data-pa-step aria-label="Training steps" style="--p:100%"></label></div>
    <div class="pa3d" data-pa3d tabindex="0" aria-label="${esc(t)}. Use the left and right arrow keys to turn the surfaces.">
      <div class="pa3d-cell"><span class="pa3d-l"><b>ANN</b> learned from 48 prices only</span><canvas data-net="ann" aria-hidden="true"></canvas><span class="pa3d-r num" data-pa-read="ann" aria-live="polite"></span></div>
      <div class="pa3d-cell"><span class="pa3d-l"><b>PINN</b> the same 48 prices, plus the pricing equation</span><canvas data-net="pinn" aria-hidden="true"></canvas><span class="pa3d-r num" data-pa-read="pinn" aria-live="polite"></span></div>
    </div>
    <div class="pa3d-key"><span><i class="pa3d-k-net"></i><span data-pa-keynet>network's price</span></span><span><i class="pa3d-k-exact"></i><span data-pa-keyexact>exact Double Heston price</span></span><span><i class="pa3d-k-neg"></i>price below zero by more than 0.2% of the strike (impossible)</span></div>
    <p class="fig-cap">${esc(cap)}</p></figure>
    <div class="s-nums">${B.nums(dir(C.PA_NUMS, ['lower', 'lower', 'higher']))}</div><p class="s-lead">${esc(C.PA_RESULT)} ${esc(C.PA_REPLAY)}</p><p class="s-fine">${esc(C.PA_NOTE)}</p>`;
}

function dataTable(ctx) {
  return `<div class="s-scroll-x"><table class="b-tb b-data"><caption class="vh">The data behind every result</caption><thead><tr><th scope="col">Data</th><th scope="col">Size</th><th scope="col">What it is</th></tr></thead><tbody>${ctx.C.DATA_SETS.map(([n, s, w]) =>
    `<tr><th scope="row">${esc(n)}</th><td class="num">${esc(s)}</td><td class="b-wrap">${esc(w)}</td></tr>`).join('')}</tbody></table></div>`;
}

function resultsTable(ctx) {
  const label = { good: 'Good news', mixed: 'Mixed', bad: 'Bad news' };
  return `<p class="b-dir-note">${esc(ctx.C.RESULTS_DIRECTION)}</p><div class="s-scroll-x"><table class="b-tb b-results"><caption class="vh">Every result of the project</caption><thead><tr><th scope="col">Result</th><th scope="col">Value</th><th scope="col">What it measures</th><th scope="col">Reading</th></tr></thead><tbody>${ctx.C.RESULTS.map(([n, v, w, verdict]) => {
    const [b, pic, mean] = ctx.C.RESULT_INFO[n];
    return `<tr><th scope="row">${esc(n)}</th><td class="num b-val">${esc(v)}${B.better(b)}</td><td class="b-wrap">${esc(w)}${B.explain([pic, mean])}</td><td><span class="b-verdict b-v-${verdict}">${label[verdict]}</span></td></tr>`;
  }).join('')}</tbody></table></div>`;
}

// "Explain simply" for a section, if the content has one
const X = (ctx, k) => B.explain(ctx.C.EXPLAIN[k]);
// pair each number with which way is good news
const dir = (items, dirs) => items.map((it, i) => [it[0], it[1], dirs[i]]);

const terms = ctx => `<dl class="b-terms">${ctx.C.TERMS.map(([t, d]) => `<div><dt>${esc(t)}</dt><dd>${esc(d)}</dd></div>`).join('')}</dl>`;

export function sections(page, ctx) {
  const C = ctx.C, D = ctx.D, K = D.contract;
  switch (page) {
    // Home tells the story and gives the answer in four numbers; every result and its evidence
    // lives on the Results page, prices live on Market and Price an option, the maths on How it works.
    case 'home':
      return [
        // the headline is the story; the answer to the question opens the paragraph under it
        // only the physics: the line in quotes and where it starts, the two aims, the four models
        { key: 'hero', kind: 'hero', q: '', title: C.HERO_TITLE[0], title2: C.HERO_TITLE[1], keys: C.HERO_KEYS,
          by: C.HERO_BY, lead: C.HERO_LEAD, ctas: [] },
        { key: 'einstein', title: C.EINSTEIN_HEAD, ico: 'references', size: 'full', glass: true, body: B.einstein(ctx) },
        { key: 'aims', title: C.AIMS_HEAD, ico: 'maths', size: 'full', body: aims(ctx) },
        { key: 'models', kind: 'head', level: 2, title: C.MODELS_HEAD, lead: C.MODELS_LEDE },
        ...C.MODELS.map((m, i) => ({ key: `m-${m[0]}`, title: `${i + 1}. ${m[3]}`, note: m[1], ico: m[0] === 'dh' ? 'slow' : 'model',
          size: 'half', glass: true, body: B.modelCard(ctx, m) })),
      ];
    case 'market': {
      const sym = store.get('market.sym', 'RELIANCE');
      return [
        { key: 'top', kind: 'head', title: 'Market', lead: C.MARKET_SUB, action: ['model.html', C.CTA.model] },
        { key: 'live', kind: 'note', body: `<p class="b-live" data-bind="live-status">${esc(C.LIVE_LOADING)}</p>` },
        { key: 'chart', size: 'wide', body: `<div class="s-stock">${B.stockHead(ctx, sym)}</div><div class="s-ctrls">${B.marketControls()}</div>
          <figure class="fig"><figcaption class="fig-t">${esc(C.CHART_NOTES.candles[0])}</figcaption>${B.candleChart(470)}<p class="fig-cap">${esc(C.CHART_NOTES.candles[1])}</p></figure>
          <div class="s-stats">${B.stockStats(ctx, sym)}</div>` },
        { key: 'watch', title: C.WATCH_HEAD, ico: 'market', size: 'narrow', note: C.WATCH_NOTE, body: `<div class="s-scroll">${B.stocksList(ctx)}</div>` },
        { key: 'nifty', title: 'NIFTY 50', ico: 'market', size: 'half', note: `${C.N_DAYS} trading days`, body: fig(ctx, 'indexLine', 260, { which: 'NIFTY' }, { title: 'NIFTY 50, closing level by day' }) },
        { key: 'banknifty', title: 'NIFTY BANK', ico: 'market', size: 'half', note: `${C.N_DAYS} trading days`, body: fig(ctx, 'indexLine', 260, { which: 'BANKNIFTY' }, { title: 'NIFTY BANK, closing level by day' }) },
        { key: 'covers', title: C.COVERS_HEAD, ico: 'about', size: 'full', lead: `${C.UNIVERSE} ${C.STATUS}.` },
      ];
    }
    case 'model': {
      const R = B.priceReadouts(ctx);
      return [
        { key: 'top', kind: 'head', title: 'Price an option', action: ['market.html', C.MARKET_BUTTON], lead: C.MODEL_LEAD },
        { key: 'form', title: 'The option', ico: 'model', size: 'full', body: B.pricingForm(ctx) },
        { key: 'price', title: C.PRICE_HEADS.price, ico: 'model', size: 'narrow', body: `<div class="s-bignum s-model">${R.dh}</div><p class="s-fine">Implied volatility ${R.dhIv}. Check by 20,000 simulated futures: ${R.mc}</p>` },
        { key: 'market', title: C.PRICE_HEADS.market, ico: 'market', size: 'narrow', body: `<div class="s-bignum">${R.mkt}</div><p class="s-fine">Implied volatility ${R.mktIv}. NSE close, ${esc(C.LAST_DAY)}.</p>` },
        { key: 'gap', title: C.PRICE_HEADS.gap, ico: 'finding', size: 'narrow', body: `<div class="s-bignum">${R.gap}</div><p class="s-fine">${R.status}</p>` },
        { key: 'explain', kind: 'note', size: 'full', lead: C.MODEL_EXPLAIN },
        { key: 'smile', title: C.PRICE_HEADS.smile, ico: 'model', size: 'wide', body: fig(ctx, 'marketSmile', 380) },
        { key: 'greeks', title: C.PRICE_HEADS.greeks, ico: 'maths', size: 'narrow', body: `<div class="s-greeks">${B.greeks(ctx)}</div><p class="s-fine">${esc(C.GREEKS_NOTE)}</p>` },
        { key: 'sliders', title: C.PRICE_HEADS.sliders, ico: 'slow', size: 'half', note: `half of a shock gone in ${C.SLOW_HL}`, body: `${B.fellerLine(ctx, 'slow')}${B.sliders(ctx, 'slow')}` },
        { key: 'sliders-fast', title: C.PRICE_HEADS['sliders-fast'], ico: 'fast', size: 'half', note: `half of a shock gone in ${C.FAST_HL}`, body: `${B.fellerLine(ctx, 'fast')}${B.sliders(ctx, 'fast')}` },
        { key: 'reset', kind: 'note', size: 'full', body: `<div class="s-row-note"><span class="b-sub">${esc(C.FELLER_NOTE)}</span><button class="btn ghost" type="button" data-action="reset">Reset to starting settings</button></div>` },
        { key: 'chain', title: C.PRICE_HEADS.chain, ico: 'market', size: 'full', body: `<p class="fig-t">NSE closing prices and the jumpiness they imply, with the model's price for each strike</p><div class="s-scroll-x">${B.chainTable(ctx)}</div><p class="fig-cap">${esc(C.CHAIN_NOTE)}</p>` },
        { key: 'source', kind: 'note', size: 'full', fine: C.MODEL_SOURCE },
      ];
    }
    // How it works: centred, every formula on its theme's glass, then the ten settings and the charts
    case 'maths':
      return [
        { key: 'top', kind: 'head', title: 'How it works', lead: C.MATHS_INTRO },
        { key: 'bend', title: C.BEND_HEAD, ico: 'model', size: 'full', glass: true, lead: C.BEND, body: fig(ctx, 'smileBend', 400) + X(ctx, 'bend') },
        { key: 'formulas', kind: 'head', level: 2, title: C.FORMULAS_HEAD, lead: C.FORMULAS_LEDE },
        ...C.FORMULAS.map((f, i) => ({ key: `f-${f[0]}`, title: `${i + 1}. ${f[1]}`, ico: 'maths', size: 'full', glass: true, body: B.formula(ctx, f) })),
        { key: 'settings', kind: 'head', level: 2, title: C.SETTINGS_HEAD, lead: C.SETTINGS_LEDE },
        { key: 'settings-list', title: C.MATHS_HEADS['settings-list'], ico: 'slow', size: 'full', glass: true, body: B.settings(ctx) },
        { key: 'decay', title: C.FACTORS_HEAD, ico: 'slow', size: 'half', glass: true, lead: C.TWO_CLOCKS, body: fig(ctx, 'decay', 320) + X(ctx, 'decay') },
        { key: 'factors', title: C.MATHS_HEADS.factors, ico: 'fast', size: 'half', glass: true, lead: C.FACTORS, body: traceFig(ctx) + X(ctx, 'factors') },
        { key: 'skew', title: C.MATHS_HEADS.skew, ico: 'model', size: 'full', glass: true, lead: C.SKEW_NOTE, body: fig(ctx, 'skew', 320) + X(ctx, 'skew') },
        { key: 'fan', title: C.MATHS_HEADS.fan, ico: 'fast', size: 'full', glass: true, lead: C.FAN_NOTE, body: fig(ctx, 'fan', 420) + X(ctx, 'fan') },
        { key: 'surface', title: C.MATHS_HEADS.surface, ico: 'maths', size: 'full', glass: true, lead: C.SURFACE_NOTE, body: fig(ctx, 'surface', 420) + X(ctx, 'surface') },
      ];
    // the one place every result lives, all on glass: the answer, its evidence, the networks, then the full table
    case 'results': {
      const sym = store.get('finding.sym', 'RELIANCE');
      const g = true;
      return [
        { key: 'top', kind: 'head', title: C.RESULTS_PAGE_HEAD, lead: C.RESULTS_PAGE_LEDE },
        { key: 'key', title: C.KEY_HEAD, ico: 'results', size: 'full', glass: g, body: `<div class="s-nums">${B.nums(dir(C.KEY_NUMS, C.KEY_BETTER))}</div>` },
        { key: 'evidence', kind: 'head', level: 2, title: C.EVIDENCE_HEAD, lead: C.TWIST },
        { key: 'proof1', title: C.PROOF1_HEAD, ico: 'maths', size: 'half', glass: g, lead: C.PROOF1,
          body: `<div class="s-nums">${B.nums(dir(C.PROOF1_NUMS, ['lower', 'lower', 'lower']))}</div><p class="s-fine">${esc(C.PROOF1_NET)}</p>${X(ctx, 'proof1')}` },
        { key: 'proof2', title: C.PROOF2_HEAD, ico: 'market', size: 'half', glass: g, lead: C.PROOF2,
          body: `<div class="s-nums">${B.nums(dir(C.PROOF2_NUMS, ['lower', 'lower', 'higher']))}</div>${X(ctx, 'proof2')}` },
        { key: 'hist', title: `${C.HIST_HEAD}, ${D.hist.n.toLocaleString('en-IN')} price lists`, ico: 'finding', size: 'full', glass: g, body: fig(ctx, 'hist', 320) + X(ctx, 'hist') },
        { key: 'params', title: 'Setting by setting', ico: 'maths', size: 'full', glass: g, lead: C.PER_PARAM, body: fig(ctx, 'paramBars', 0) + X(ctx, 'params') },
        { key: 'pair', kind: 'head', level: 2, title: C.PAIR_HEAD, lead: C.PAIR_LEDE },
        { key: 'pool', title: C.RESULTS_HEADS.pool, ico: 'model', size: 'wide', glass: g, body: fig(ctx, 'pairPool', 400) },
        { key: 'magnets-why', title: C.PAIR_MAGNETS_HEAD, ico: 'finding', size: 'narrow', glass: g, lead: `${C.PAIR_MAGNETS} ${C.PAIR_TYPICAL}` },
        { key: 'magnets', title: C.RESULTS_HEADS.magnets, ico: 'maths', size: 'full', glass: g, body: `${fig(ctx, 'pairMagnets', 0)}<p class="s-fine">${esc(C.PAIR_NOTE)}</p>${X(ctx, 'magnets')}` },
        { key: 'part', title: C.PAIR_PART_HEAD, ico: 'finding', size: 'full', glass: g, lead: C.PAIR_PART, body: fig(ctx, 'pairPart', 400) + X(ctx, 'part') },
        { key: 'six', title: C.RESULTS_HEADS.six, ico: 'finding', size: 'full', glass: g, lead: C.PAIR_SIX, body: fig(ctx, 'pairSix', 0) + X(ctx, 'six') },
        { key: 'stock', title: C.RESULTS_HEADS.stock, ico: 'market', size: 'full', glass: g,
          body: `<div class="s-ctrls">${B.stockPicker(ctx)}</div><p class="s-lead" data-bind="stock-line">${esc(B.stockLine(ctx, sym))}</p>${fig(ctx, 'stockPanel', 0, { sym })}${X(ctx, 'stock')}` },
        { key: 'nets', kind: 'head', level: 2, title: C.NN_HEAD, lead: `${C.ANN_TEXT} ${C.PINN_TEXT}` },
        { key: 'heldout', title: C.RESULTS_HEADS.heldout, ico: 'model', size: 'half', glass: g,
          body: B.nums([[`${(D.consolidated.g8.median_network_relative * 100).toFixed(1)}%`, C.HELDOUT, 'lower']]) + X(ctx, 'heldout') },
        { key: 'backtest', title: C.RESULTS_HEADS.backtest, ico: 'market', size: 'half', glass: g, body: B.nums([[C.BEAT_BS_NUM, C.BACKTEST, 'higher']]) + X(ctx, 'backtest') },
        { key: 'pinn', title: C.RESULTS_HEADS.pinn, ico: 'maths', size: 'full', glass: g,
          body: `${B.nums([[`${C.PINN_NIFTY.ft_3.toFixed(2)}`, 'PINN, typical error in volatility points', 'lower'], [`${C.PINN_NIFTY.bs.toFixed(2)}`, 'Black–Scholes on the same prices', 'lower'], [`${C.PINN_NIFTY_BEST} of 10`, 'days the PINN was the best model', 'higher']])}<p class="s-lead">${esc(C.PINN_MARKET)}</p>${X(ctx, 'pinn')}` },
        { key: 'all', kind: 'head', level: 2, title: C.RESULTS_HEAD, lead: C.RESULTS_LEDE },
        { key: 'results', title: C.RESULTS_HEADS.results, ico: 'results', size: 'full', glass: g, body: resultsTable(ctx) },
        { key: 'data', title: C.RESULTS_HEADS.data, ico: 'market', size: 'full', glass: g, body: dataTable(ctx) },
        { key: 'terms', title: C.RESULTS_HEADS.terms, ico: 'about', size: 'full', glass: g, body: terms(ctx) },
      ];
    }
    case 'about':
      return [
        { key: 'top', kind: 'head', title: 'About', lead: C.ABOUT_HEAD },
        { key: 'video', title: C.ABOUT_HEADS.video, ico: 'video', size: 'wide', body: B.video(ctx) },
        { key: 'method', title: C.ABOUT_HEADS.method, ico: 'maths', size: 'narrow', body: `<div class="s-paras">${C.METHOD.map(m => `<p>${esc(m)}</p>`).join('')}</div>` },
        { key: 'limits', title: C.ABOUT_HEADS.limits, ico: 'about', size: 'half', body: B.bulletList(C.LIMITS) },
        { key: 'also', title: C.ABOUT_HEADS.also, ico: 'fast', size: 'half', lead: C.ALSO },
      ];
    case 'team':
      return [
        { key: 'top', kind: 'head', title: C.TEAM_HEAD, lead: C.TEAM_INTRO },
        ...C.TEAM.map(([n, r], i) => ({ key: i ? `person-${i}` : 'team', size: 'quarter', person: true,
          body: `<div class="b-person">${icon('team', { size: 72, tint: ['teal', 'blue', 'orange', 'indigo'][i % 4] })}<b>${esc(n)}</b><span class="b-sub">${esc(r)}</span></div>` })),
        { key: 'supervisor', title: C.SUPERVISOR_HEAD, ico: 'about', size: 'half', body: `<div class="b-person"><b>${esc(C.SUPERVISOR[0])}</b><span class="b-sub">${esc(C.SUPERVISOR[1])}</span></div>` },
        { key: 'thanks', title: 'Thanks', ico: 'references', size: 'half', body: B.bulletList(C.THANKS) },
      ];
    case 'references':
      return [
        { key: 'top', kind: 'head', title: 'References', lead: C.REFS_LEAD },
        ...C.REFS.map(([g], k) => ({ key: k ? `refs-${k}` : 'refs', title: g, ico: 'references', size: 'half', body: B.refs(ctx, 'b-refs s-refs', true, { group: k, heading: false }) })),
      ];
    default:
      return [];
  }
}
