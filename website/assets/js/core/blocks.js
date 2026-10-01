// Shared content blocks. Neutral class names (b-*) that each theme styles its own way; the words
// and numbers come from content.json / site.json. Live values carry data-bind for the controllers.
import { esc, inr, arrow, fmt } from './util.js';
import { sparkline } from './charts.js';
import { icon } from './icons.js';
import { store } from './state.js';
import { DEFAULT_PARAMS, SLIDER_KEYS } from './model.js';

const w = (ctx, sym) => ctx.D.watch.find(x => x.sym === sym);

// ------------------------------------------------------------------ ticker (seamless loop)
// the running banner: equity prices only (stocks, not indices, nothing from the model)
export function ticker(ctx) {
  const C = ctx.C;
  const stocks = ctx.D.watch.filter(v => ctx.D.equity[v.sym] && ctx.C.NAMES[v.sym] !== 'Index').sort((a, b) => (b.vol || 0) - (a.vol || 0)).slice(0, 24);
  const items = stocks.map(v => {
    const [a, c] = arrow(v.pct);
    return `<span class="tick-i" data-sym="${esc(v.sym)}"><b>${esc(v.sym)}</b><span class="num" data-bind="price">${inr(v.last)}</span><span class="${c} num" data-bind="chg">${a} ${Math.abs(v.pct).toFixed(2)}%</span></span>`;
  });
  const run = items.join('<span class="tick-sep" aria-hidden="true"></span>') + '<span class="tick-sep" aria-hidden="true"></span>';
  return `<div class="tick b-tick" role="region" aria-label="Equity closing prices on ${esc(C.LAST_DAY)}, scrolling">
    <div class="tick-view"><div class="tick-track"><div class="tick-run">${run}</div><div class="tick-run" aria-hidden="true">${run}</div></div></div></div>`;
}

// the page dock: every page as an app icon, magnified under the cursor; sits above the footer text
export function dock(ctx, { size = 56, tint } = {}) {
  return `<nav class="b-dock" aria-label="All pages"><div class="b-dock-in">${ctx.pages.map(({ id, file, label }) =>
    `<a href="${file}" class="b-dock-i${id === ctx.navPage ? ' cur' : ''}"${id === ctx.page ? ' aria-current="page"' : ''}>${icon(id, { size, tint: typeof tint === 'function' ? tint(id) : tint })}<span class="b-dock-l">${esc(label)}</span></a>`).join('')}</div></nav>`;
}

// ------------------------------------------------------------------ market
export function watchTable(ctx, { syms, spark = [84, 26], names = true, cols = ['Symbol', '62 days', 'Close', 'Day'] } = {}) {
  const C = ctx.C, sel = store.get('market.sym', 'RELIANCE');
  const list = syms || [...C.FEATURED, 'BHARTIARTL', 'KOTAKBANK', 'BAJFINANCE', 'MARUTI', 'TCS', 'WIPRO'].filter((s, i, a) => a.indexOf(s) === i && w(ctx, s));
  const rows = list.map(s => {
    const v = w(ctx, s);
    const [a, c] = arrow(v.pct);
    const pick = ctx.D.equity[s] ? `data-sym="${s}"` : '';
    return `<tr data-sym="${s}" class="${s === sel ? 'sel' : ''}"><td>${pick ? `<button type="button" class="b-sym" ${pick} aria-pressed="${s === sel}">` : '<span class="b-sym">'}<b>${esc(s)}</b>${names ? `<span class="b-sub">${esc(C.NAMES[s] || '')}</span>` : ''}${pick ? '</button>' : '</span>'}</td>` +
      `<td class="b-spark">${sparkline(v.closes, spark[0], spark[1])}</td><td class="num" data-bind="price">${inr(v.last)}</td><td class="num ${c}" data-bind="chg">${a} ${Math.abs(v.pct).toFixed(2)}%</td></tr>`;
  });
  return `<table class="b-tb b-watch" data-ctl="watch"><caption class="vh">Closing prices, ${esc(C.LAST_DAY)}. Pick a stock or index to chart it.</caption><thead><tr>${cols.map((h, i) => `<th scope="col"${i ? ' class="num"' : ''}>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`;
}

// a Stocks-app style list: symbol and name, sparkline, price over a coloured change pill
export function stocksList(ctx, { syms, spark = [64, 26] } = {}) {
  const C = ctx.C, sel = store.get('market.sym', 'RELIANCE');
  const list = syms || [...C.FEATURED, 'BHARTIARTL', 'KOTAKBANK', 'BAJFINANCE', 'MARUTI', 'TCS', 'WIPRO'].filter((s, i, a) => a.indexOf(s) === i && w(ctx, s));
  return `<ul class="b-stocks" aria-label="Closing prices, ${esc(C.LAST_DAY)}. Pick a stock or index to chart it.">${list.map(s => {
    const v = w(ctx, s), [a, c] = arrow(v.pct), pick = !!ctx.D.equity[s];
    const inner = `<span class="bs-l"><b>${esc(s)}</b><span class="b-sub">${esc(C.NAMES[s] || '')}</span></span>${sparkline(v.closes, spark[0], spark[1])}
      <span class="bs-r"><b class="num" data-bind="price">${inr(v.last)}</b><span class="bs-pill ${c} num" data-bind="chg">${a} ${Math.abs(v.pct).toFixed(2)}%</span></span>`;
    return `<li class="${s === sel ? 'sel' : ''}" data-sym="${s}">${pick ? `<button type="button" class="bs-row" data-sym="${s}" aria-pressed="${s === sel}">${inner}</button>` : `<div class="bs-row">${inner}</div>`}</li>`;
  }).join('')}</ul>`;
}

export function stockHead(ctx, sym) {
  const r = ctx.D.equity[sym].at(-1);
  const ch = r[4] - r[6];
  const [a, c] = arrow(ch);
  return `<span class="b-sh-sym" data-bind="m-sym">${esc(sym)}</span><span class="b-sh-name" data-bind="m-name">${esc(ctx.C.NAMES[sym] || '')}</span>
    <span class="b-sh-last num" data-bind="m-last">${inr(r[4])}</span><span class="b-sh-chg num ${c}" data-bind="m-chg">${a} ${inr(Math.abs(ch))} (${Math.abs(ch / r[6] * 100).toFixed(2)}%)</span>`;
}

export function stockStats(ctx, sym) {
  const r = ctx.D.equity[sym].at(-1);
  return [['Open', inr(r[1])], ['High', inr(r[2])], ['Low', inr(r[3])], ['Close', inr(r[4])], ['Prev close', inr(r[6])], ['Volume', `${inr(r[5] / 1e5, 1)} lakh`]]
    .map(([k, v]) => `<div class="b-stat"><span>${k}</span><b class="num" data-bind="m-${k.toLowerCase().replace(' ', '-')}">${v}</b></div>`).join('');
}

export function seg(name, options, value, label) {
  return `<div class="seg" role="group" aria-label="${esc(label)}" data-seg="${name}">${options.map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${v === value}">${esc(l)}</button>`).join('')}<span class="seg-thumb" aria-hidden="true"></span></div>`;
}

export function marketControls() {
  return seg('range', [['1M', '1 month'], ['3M', '3 months']], store.get('market.range', '3M'), 'Time range') +
    seg('mode', [['candles', 'Candles'], ['line', 'Line']], store.get('market.mode', 'candles'), 'Chart type');
}

export function candleChart(h = 460) {
  const o = { sym: store.get('market.sym', 'RELIANCE'), range: store.get('market.range', '3M'), mode: store.get('market.mode', 'candles') };
  return `<div class="chart b-candles" data-chart="candles" data-h="${h}" data-o='${JSON.stringify(o)}'></div>`;
}

// ------------------------------------------------------------------ the model page
export function pricingForm(ctx, cls = 'b-form') {
  const K = ctx.D.contract, C = ctx.C;
  const strike = store.get('model.strike', K.strike), kind = store.get('model.kind', 'call');
  const opts = ctx.D.chain.map(r => `<option value="${r.strike}"${r.strike === strike ? ' selected' : ''}>${inr(r.strike, 0)}${r.strike === K.strike ? ' (at the money)' : ''}</option>`).join('');
  return `<form class="${cls}" data-ctl="model-form" onsubmit="return false">
    <div class="field"><span>Underlying</span><div class="b-fixed">NIFTY 50 <span class="b-sub num">${inr(K.spot)}</span></div></div>
    <div class="field"><span>Expiry</span><div class="b-fixed">${esc(C.EXPIRY)} <span class="b-sub">${K.dte} days</span></div></div>
    <label class="field"><span>Strike</span><select class="select num" data-in="strike">${opts}</select></label>
    <div class="field"><span>Type</span>${seg('kind', [['call', 'Call'], ['put', 'Put']], kind, 'Option type')}</div>
  </form>`;
}

// the model's outputs: every value is live (data-bind) and animates to its new number
export function priceReadouts(ctx) {
  const K = ctx.D.contract, row = ctx.D.chain.find(r => r.strike === K.strike);
  return {
    dh: `<b class="num" data-bind="dh" data-v="${K.dh}" data-count="${K.dh}" data-fmt="inr" data-pre="₹">₹${inr(K.dh)}</b>`,
    dhIv: `<span class="num" data-bind="dh-iv" data-v="${K.dh_iv}">${K.dh_iv.toFixed(2)}%</span>`,
    mkt: `<b class="num" data-bind="mkt">₹${inr(row.call)}</b>`,
    mktIv: `<span class="num" data-bind="mkt-iv">${row.call_iv.toFixed(2)}%</span>`,
    gap: `<b class="num" data-bind="gap" data-v="${K.dh - row.call}" data-count="${K.dh - row.call}" data-fmt="inr" data-pre="+₹">+₹${inr(K.dh - row.call)}</b>`,
    mc: `<span class="num" data-bind="mc">₹${inr(K.mc)} ± ${K.mc_se.toFixed(2)}</span>`,
    contract: `<span data-bind="contract">NIFTY ${inr(K.strike, 0)} call</span>`,
    status: `<span class="b-status" data-bind="status" role="status" aria-live="polite">Starting settings</span>`,
  };
}

export function chainTable(ctx, cols = ['Strike', 'Call', 'Call IV', 'Model call', 'Put', 'Put IV', 'Model put']) {
  const K = ctx.D.contract;
  const rows = ctx.D.chain.filter(r => Math.abs(r.strike - K.strike) <= 250).map(r =>
    `<tr data-strike="${r.strike}"${r.strike === store.get('model.strike', K.strike) ? ' class="sel"' : ''}><td class="num"><b>${inr(r.strike, 0)}</b></td><td class="num">${inr(r.call)}</td><td class="num b-sub">${r.call_iv.toFixed(1)}%</td>` +
    `<td class="num b-model" data-bind="ch-call-${r.strike}">${inr(r.dh_call)}</td><td class="num">${inr(r.put)}</td><td class="num b-sub">${r.put_iv.toFixed(1)}%</td><td class="num b-model" data-bind="ch-put-${r.strike}">${inr(r.dh_put)}</td></tr>`).join('');
  return `<table class="b-tb b-chain"><caption class="vh">NIFTY option chain, 27 Oct 2026 expiry: market closing prices and implied volatilities against the model</caption><thead><tr>${cols.map((c, i) => `<th scope="col"${i ? ' class="num"' : ''}>${c}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
}

export function sliders(ctx, factor) {
  const p = store.get('model.params', DEFAULT_PARAMS);
  return ctx.C.SLIDERS.filter(s => s[0] === factor).map(([, sym, name, , lo, hi], i) => {
    const key = SLIDER_KEYS[factor][i], v = p[key];
    const f = ['v0', 'theta'].some(k => key.startsWith(k)) ? 4 : 2;
    const id = `sl-${key}`;
    return `<div class="b-sl"><b class="b-sym-g">${sym}</b><label for="${id}"><span>${esc(name)}</span><input id="${id}" type="range" min="${lo}" max="${hi}" step="${f === 4 ? 0.0005 : 0.01}" value="${v}" data-param="${key}" data-dp="${f}" style="--p:${((v - lo) / (hi - lo) * 100).toFixed(2)}%"></label><output for="${id}" class="num" data-out="${key}">${v.toFixed(f)}</output></div>`;
  }).join('');
}

export function fellerLine(ctx, factor) {
  return `<p class="b-feller" data-bind="feller-${factor}">${esc(ctx.C.FELLER[factor])}</p>`;
}

export function greeks(ctx, cls = 'b-greek') {
  const K = ctx.D.contract;
  const units = { Delta: 'per ₹1 move in NIFTY', Gamma: 'change in delta per ₹1', Vega: '₹ per volatility point', Theta: '₹ per calendar day', Rho: '₹ per rate point' };
  const val = { Delta: [K.delta, 3], Gamma: [K.gamma, 5], Vega: [K.vega, 1], Theta: [K.theta, 2], Rho: [K.rho, 1] };
  return Object.keys(units).map(n => `<div class="${cls}"><span class="b-lab">${n}</span><b class="num" data-bind="g-${n.toLowerCase()}" data-v="${val[n][0]}">${fmt.num(val[n][0], val[n][1])}</b><span class="b-sub">${units[n]}</span></div>`).join('');
}

// ------------------------------------------------------------------ text blocks
// a plain number like "99%", "3.9×", "1.80" or "17.4%" counts up on first view; anything else stays as written
function autoRaw(n) {
  const m = /^([\d.]+)(%|×)?$/.exec(n);
  if (!m) return null;
  const dp = (m[1].split('.')[1] || '').length;
  return { v: +m[1], dp, suf: m[2] || '' };
}

export function nums(items, cls = 'b-num', count = true) {
  // [value, caption, optional: raw count-up spec (object) or 'higher' | 'lower' (which way is good news)]
  return items.map(([n, c, extra]) => {
    const raw = extra && typeof extra === 'object' ? extra : autoRaw(n), b = typeof extra === 'string' ? extra : '';
    const counter = count && raw ? ` data-count="${raw.v}" data-fmt="${raw.f || 'num'}" data-dp="${raw.dp ?? 2}"${raw.pre ? ` data-pre="${raw.pre}"` : ''}${raw.suf ? ` data-suf="${esc(raw.suf)}"` : ''}` : '';
    return `<div class="${cls}"><b class="num"${counter}>${esc(n)}</b><span>${esc(c)}</span>${better(b)}</div>`;
  }).join('');
}

// the model's equations, typeset in MathML (native in Safari and Chrome)
const mi = s => `<mi>${s}</mi>`, mo = s => (/[()]/.test(s) ? `<mo stretchy="false">${s}</mo>` : `<mo>${s}</mo>`), mn = s => `<mn>${s}</mn>`;
const sub = (b, s) => `<msub>${b}${s}</msub>`, sup = (b, s) => `<msup>${b}${s}</msup>`;
const sqrt = x => `<msqrt>${x}</msqrt>`, d = s => `<mi mathvariant="normal">d</mi>${s}`;
const vi = k => sub(mi('v'), mn(k));
const MATH = {
  price: `${d(mi('S'))}${mo('=')}${mo('(')}${mi('r')}${mo('−')}${mi('q')}${mo(')')}${mi('S')}${d(mi('t'))}${mo('+')}${sqrt(vi(1))}${mi('S')}${d(sub(mi('W'), mn(1)))}${mo('+')}${sqrt(vi(2))}${mi('S')}${d(sub(mi('W'), mn(2)))}`,
  variance: `${d(sub(mi('v'), mi('i')))}${mo('=')}${sub(mi('κ'), mi('i'))}${mo('(')}${sub(mi('θ'), mi('i'))}${mo('−')}${sub(mi('v'), mi('i'))}${mo(')')}${d(mi('t'))}${mo('+')}${sub(mi('ξ'), mi('i'))}${sqrt(sub(mi('v'), mi('i')))}${d(sub(mi('Z'), mi('i')))}` +
    `<mspace width="1em"/><mi mathvariant="normal">corr</mi>${mo('(')}${d(sub(mi('W'), mi('i')))}${mo(',')}${d(sub(mi('Z'), mi('i')))}${mo(')')}${mo('=')}${sub(mi('ρ'), mi('i'))}`,
  cf: `${mi('φ')}${mo('(')}${mi('u')}${mo(')')}${mo('=')}${sub(mi('φ'), mn(1))}${mo('(')}${mi('u')}${mo(')')}${mo('·')}${sub(mi('φ'), mn(2))}${mo('(')}${mi('u')}${mo(')')}`,
  call: `${mi('C')}${mo('=')}${sup(mi('e'), `<mrow>${mo('−')}${mi('r')}${mi('T')}</mrow>`)}${mo('[')}${mi('F')}${sub(mi('P'), mn(1))}${mo('−')}${mi('K')}${sub(mi('P'), mn(2))}${mo(']')}` +
    `<mspace width="1em"/>${sub(mi('P'), mi('j'))}${mo('=')}<mfrac>${mn(1)}${mn(2)}</mfrac>${mo('+')}<mfrac>${mn(1)}${mi('π')}</mfrac>` +
    `<msubsup>${mo('∫')}${mn(0)}${mi('∞')}</msubsup><mi mathvariant="normal">Re</mi>${mo('[')}<mfrac><mrow>${sup(mi('e'), `<mrow>${mo('−')}${mi('i')}${mi('u')}<mi mathvariant="normal">ln</mi>${mo('(')}${mi('K')}${mo('/')}${mi('F')}${mo(')')}</mrow>`)}${sub(mi('φ'), mi('j'))}${mo('(')}${mi('u')}${mo(')')}</mrow><mrow>${mi('i')}${mi('u')}</mrow></mfrac>${mo(']')}${d(mi('u'))}`,
  feller: `${mn(2)}${sub(mi('κ'), mi('i'))}${sub(mi('θ'), mi('i'))}${mo('>')}${sup(sub(mi('ξ'), mi('i')), mn(2))}`,
  mc: `${mi('C')}${mo('≈')}${sup(mi('e'), `<mrow>${mo('−')}${mi('r')}${mi('T')}</mrow>`)}<mfrac>${mn(1)}${mi('N')}</mfrac>` +
    `<munderover>${mo('∑')}<mrow>${mi('n')}${mo('=')}${mn(1)}</mrow>${mi('N')}</munderover>` +
    `<mi mathvariant="normal">max</mi>${mo('(')}<msubsup>${mi('S')}${mi('T')}<mrow>${mo('(')}${mi('n')}${mo(')')}</mrow></msubsup>${mo('−')}${mi('K')}${mo(',')}${mn(0)}${mo(')')}`,
};

// "Explain simply": a small dropdown that opens a glass squircle with an everyday picture and what it means here.
// Native <details>, so it works by keyboard and screen reader with no script; the opening animates in CSS.
export function explain(xp) {
  if (!xp) return '';
  const [picture, meaning] = xp;
  // unlabelled on purpose: a small glass disc with a downward triangle; aria-label carries the
  // name for anyone not seeing it (screen reader, no CSS) -- see base.css for the "why" note.
  return `<details class="xp"><summary class="glass" aria-label="Explain simply"><i class="xp-chev" aria-hidden="true"></i></summary>` +
    `<div class="xp-body glass squircle"><p class="xp-pic">${esc(picture)}</p><p class="xp-mean">${esc(meaning)}</p></div></details>`;
}

// which way is good news for a number: text and glyph, never colour alone
export const better = b => (b ? `<span class="b-better b-better-${b}">${b === 'higher' ? '▲ Higher is better' : '▼ Lower is better'}</span>` : '');

// one formula as a card: the formula, what it does, what each symbol means, and the dropdown
export function formula(ctx, [k, , plain, what, symbols]) {
  return `<div class="b-f"><div class="b-eqn"><math display="block" displaystyle="true" alttext="${esc(plain)}">${MATH[k]}</math></div>
    <p class="b-f-what">${esc(what)}</p>
    <dl class="b-symkey">${symbols.map(([sym, m]) => `<div><dt>${esc(sym)}</dt><dd>${esc(m)}</dd></div>`).join('')}</dl>
    ${explain(ctx.C.EXPLAIN[`f-${k}`])}</div>`;
}

// the ten settings: five rows, each with both factors' starting values and its dropdown
export function settings(ctx) {
  return `<ol class="b-set">${ctx.C.SETTINGS.map(([sym, name, ctl, up, slow, fast]) => `<li>
    <b class="b-set-sym">${esc(sym)}</b>
    <div class="b-set-txt"><h4>${esc(name)}</h4><p>${esc(ctl)}</p><p class="b-set-up"><span>Raise it:</span> ${esc(up)}</p>
      <p class="b-set-start num">Starts at ${esc(slow)} (slow) and ${esc(fast)} (fast)</p>${explain(ctx.C.EXPLAIN[`s-${sym}`])}</div></li>`).join('')}</ol>`;
}
export function equations(ctx, cls = 'b-eq') {
  const C = ctx.C;
  return [['The price moves with two variances', 'price', C.EQ_PRICE], ['Each variance pulls back to its own level (i = 1, 2)', 'variance', C.EQ_VAR],
    ['Independent factors multiply', 'cf', C.EQ_CF], ['The price is one integral (Gil-Pelaez)', 'call', C.EQ_CALL], ['A factor never touches zero when', 'feller', C.EQ_FELLER]]
    .map(([l, k, plain]) => `<div class="${cls}"><span class="b-lab">${esc(l)}</span><div class="b-eqn"><math displaystyle="true" alttext="${esc(plain)}">${MATH[k]}</math></div></div>`).join('');
}

export function steps(ctx, cls = 'b-steps', numbered = true) {
  return `<ol class="${cls}">${ctx.C.MATHS_STEPS.map(([h, t], i) => `<li>${numbered ? `<b class="b-n num">${i + 1}</b>` : ''}<span><b>${esc(h)}</b><span>${esc(t)}</span></span></li>`).join('')}</ol>`;
}

export function lineage(ctx, cls = 'b-lin') {
  return `<ol class="${cls}">${ctx.C.LINEAGE.map(([y, n, d]) => `<li${y === '2009' ? ' class="now"' : ''}><b class="b-y num">${y}</b><span><b>${esc(n)}</b><span>${esc(d)}</span></span></li>`).join('')}</ol>`;
}

export const bulletList = (items, cls = 'b-list') => `<ul class="${cls}">${items.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`;

export function video(ctx, { tint } = {}) {
  return `<figure class="b-video"><button type="button" class="video-slot" data-video aria-label="Play the project video (to be added)">
    ${icon('play', { size: 92, tint: tint || 'red' })}<span class="vs-cap">${esc(ctx.C.VIDEO_CAPTION.replace(' [Video to be added]', ''))}</span></button>
    <figcaption class="b-sub">The explainer video goes here. Drop the file into website/assets/video/ and it will play in this frame; nothing loads until someone presses play.</figcaption></figure>`;
}

export function teamCards(ctx, cls = 'b-person', { tint } = {}) {
  return ctx.C.TEAM.map(([n, r]) => `<div class="${cls}"><span class="b-ph">${icon('team', { size: 64, tint: tint || 'teal' })}</span><b>${esc(n)}</b><span class="b-sub">${esc(r)}</span></div>`).join('');
}

// references, numbered continuously across groups; { group: k } renders one group (numbers still global)
export function refs(ctx, cls = 'b-refs', numbered = true, { group, heading = true } = {}) {
  let n = 0;
  return ctx.C.REFS.map(([g, items], k) => {
    if (group != null && k !== group) { n += items.length; return ''; }
    return `<section class="${cls}">${heading ? `<h2>${esc(g)}</h2>` : ''}<ol>${items.map(([a, t, s]) => {
      n++;
      return `<li>${numbered ? `<span class="b-rn num">[${n}]</span>` : ''}<span><b>${esc(a)}</b> <span class="b-rt">${esc(t)}</span> <span class="b-sub">${esc(s)}</span></span></li>`;
    }).join('')}</ol></section>`;
  }).join('');
}

// every theme links to every page in the nav here, the current one marked (same links in every theme)
export function pageLinks(ctx, { size = 60, cls = 'b-links', tint, desc = true } = {}) {
  return `<nav class="${cls}" aria-label="All pages">${ctx.pages.map(({ id, file, label, desc: d }) =>
    `<a href="${file}" class="press"${id === ctx.page ? ' aria-current="page"' : ''}>${icon(id, { size, tint: typeof tint === 'function' ? tint(id) : tint })}<span><b>${esc(label)}</b>${desc ? `<span>${esc(d)}</span>` : ''}</span></a>`).join('')}</nav>`;
}

export function footer(ctx, cls = 'b-foot') {
  return `<footer class="${cls}"><span>Not trading advice. Prices are NSE closing prices from ${esc(ctx.C.LAST_DAY)}; live Upstox prices are planned for the same places.</span><span>Double Heston, a B.Tech physics project</span></footer>`;
}

export function stockPicker(ctx) {
  const sel = store.get('finding.sym', 'RELIANCE');
  const syms = Object.keys(ctx.D.per_stock).sort();
  return `<label class="field b-pick"><span>Stock</span><select class="select" data-in="finding-sym">${syms.map(s => `<option value="${s}"${s === sel ? ' selected' : ''}>${s}${ctx.C.NAMES[s] ? `, ${esc(ctx.C.NAMES[s])}` : ''}</option>`).join('')}</select></label>`;
}

export function stockLine(ctx, sym) {
  const rows = ctx.D.per_stock[sym];
  const med = a => { const s = [...a].sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const dh = med(rows.map(r => r[1])) * 100, fl = med(rows.map(r => r[2])) * 100, ds = med(rows.map(r => r[3]));
  const beat = rows.filter(r => r[1] <= r[2]).length;
  return `${sym}, day by day: its best Double Heston fit beat a flat volatility on ${beat === rows.length ? 'every one' : `${beat}`} of its ${rows.length} days (median price error ${dh.toFixed(2)}% of the share price, against ${fl.toFixed(2)}%). On the same days the equally good fits sat a median ${ds.toFixed(1)} apart.`;
}

export const chart = (name, h, o, cls = '') => `<div class="chart ${cls}" data-chart="${name}" data-h="${h}"${o ? ` data-o='${JSON.stringify(o)}'` : ''}></div>`;
