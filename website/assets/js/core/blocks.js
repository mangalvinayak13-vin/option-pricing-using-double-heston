// Shared content blocks. Neutral class names (b-*) that each theme styles its own way; the words
// and numbers come from content.json / site.json. Live values carry data-bind for the controllers.
import { esc, inr, arrow, fmt } from './util.js';
import { sparkline } from './charts.js';
import { icon } from './icons.js';
import { store } from './state.js';
import { DEFAULT_PARAMS, SLIDER_KEYS } from './model.js';

const w = (ctx, sym) => ctx.D.watch.find(x => x.sym === sym);

// ------------------------------------------------------------------ ticker (seamless loop)
export function ticker(ctx, { label = true, model = true, syms } = {}) {
  const C = ctx.C;
  const items = (syms || C.FEATURED).map(s => {
    const v = w(ctx, s);
    const [a, c] = arrow(v.pct);
    return `<span class="tick-i"><b>${esc(s)}</b><span class="num">${inr(v.last)}</span><span class="${c} num">${a} ${Math.abs(v.pct).toFixed(2)}%</span></span>`;
  });
  if (model) C.TICKER_MODEL.forEach(([k, v]) => items.push(`<span class="tick-i tick-m"><span class="m">${esc(k)}</span><b class="num">${esc(v)}</b></span>`));
  const run = items.join('<span class="tick-sep" aria-hidden="true"></span>') + '<span class="tick-sep" aria-hidden="true"></span>';
  return `<div class="tick b-tick" role="region" aria-label="Closing prices on ${esc(C.LAST_DAY)} and the model's outputs, scrolling">
    ${label ? `<span class="b-tick-lab">Close ${esc(C.LAST_DAY)}</span>` : ''}
    <div class="tick-track"><div class="tick-run">${run}</div><div class="tick-run" aria-hidden="true">${run}</div></div></div>`;
}

// ------------------------------------------------------------------ market
export function watchTable(ctx, { syms, spark = [84, 26], names = true, cols = ['Symbol', '62 days', 'Close', 'Day'] } = {}) {
  const C = ctx.C, sel = store.get('market.sym', 'RELIANCE');
  const list = syms || [...C.FEATURED, 'BHARTIARTL', 'KOTAKBANK', 'BAJFINANCE', 'MARUTI', 'TCS', 'WIPRO'].filter((s, i, a) => a.indexOf(s) === i && w(ctx, s));
  const rows = list.map(s => {
    const v = w(ctx, s);
    const [a, c] = arrow(v.pct);
    const pick = ctx.D.equity[s] ? `data-sym="${s}"` : '';
    return `<tr ${pick} class="${s === sel ? 'sel' : ''}"><td>${pick ? `<button type="button" class="b-sym" ${pick} aria-pressed="${s === sel}">` : '<span class="b-sym">'}<b>${esc(s)}</b>${names ? `<span class="b-sub">${esc(C.NAMES[s] || '')}</span>` : ''}${pick ? '</button>' : '</span>'}</td>` +
      `<td class="b-spark">${sparkline(v.closes, spark[0], spark[1])}</td><td class="num">${inr(v.last)}</td><td class="num ${c}">${a} ${Math.abs(v.pct).toFixed(2)}%</td></tr>`;
  });
  return `<table class="b-tb b-watch" data-ctl="watch"><caption class="vh">Closing prices, ${esc(C.LAST_DAY)}. Pick a stock to chart it.</caption><thead><tr>${cols.map((h, i) => `<th scope="col"${i ? ' class="num"' : ''}>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`;
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
  return [['Open', inr(r[1])], ['High', inr(r[2])], ['Low', inr(r[3])], ['Close', inr(r[4])], ['Prev close', inr(r[6])], ['Volume', `${(r[5] / 1e5).toFixed(1)} lakh`]]
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
    dh: `<b class="num" data-bind="dh" data-v="${K.dh}">₹${inr(K.dh)}</b>`,
    dhIv: `<span class="num" data-bind="dh-iv" data-v="${K.dh_iv}">${K.dh_iv.toFixed(2)}%</span>`,
    mkt: `<b class="num" data-bind="mkt">₹${inr(row.call)}</b>`,
    mktIv: `<span class="num" data-bind="mkt-iv">${row.call_iv.toFixed(2)}%</span>`,
    gap: `<b class="num" data-bind="gap" data-v="${K.dh - row.call}">+₹${inr(K.dh - row.call)}</b>`,
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
    return `<div class="b-sl"><b class="b-sym-g">${sym}</b><label for="${id}"><span>${esc(name)}</span><input id="${id}" type="range" min="${lo}" max="${hi}" step="${key.startsWith('rho') ? 0.01 : (hi - lo) / 400}" value="${v}" data-param="${key}" data-dp="${f}"></label><output for="${id}" class="num" data-out="${key}">${v.toFixed(f)}</output></div>`;
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
export function nums(items, cls = 'b-num', count = true) {
  return items.map(([n, c, raw]) => {
    const counter = count && raw ? ` data-count="${raw.v}" data-fmt="${raw.f || 'num'}" data-dp="${raw.dp ?? 2}"${raw.pre ? ` data-pre="${raw.pre}"` : ''}${raw.suf ? ` data-suf="${esc(raw.suf)}"` : ''}` : '';
    return `<div class="${cls}"><b class="num"${counter}>${esc(n)}</b><span>${esc(c)}</span></div>`;
  }).join('');
}

export function equations(ctx, cls = 'b-eq') {
  const C = ctx.C;
  return [['The price moves with two variances', C.EQ_PRICE], ['Each variance pulls back to its own level', C.EQ_VAR], ['Independent factors multiply', C.EQ_CF],
    ['The price is one integral (Gil-Pelaez)', C.EQ_CALL], ['A factor never touches zero when', C.EQ_FELLER]]
    .map(([l, e]) => `<div class="${cls}"><span class="b-lab">${esc(l)}</span><div class="b-eqn">${esc(e)}</div></div>`).join('');
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

export function refs(ctx, cls = 'b-refs', numbered = true) {
  let n = 0;
  return ctx.C.REFS.map(([g, items]) => `<section class="${cls}"><h2>${esc(g)}</h2><ol>${items.map(([a, t, s]) => {
    n++;
    return `<li>${numbered ? `<span class="b-rn num">[${n}]</span>` : ''}<span><b>${esc(a)}</b> <span class="b-rt">${esc(t)}</span> <span class="b-sub">${esc(s)}</span></span></li>`;
  }).join('')}</ol></section>`).join('');
}

export function pageLinks(ctx, { size = 60, cls = 'b-links', tint, skip = true, desc = true } = {}) {
  return `<nav class="${cls}" aria-label="All pages">${ctx.C.PAGES.filter(p => !skip || p[0] !== ctx.page).map(([id, file, label, d]) =>
    `<a href="${file}" class="press">${icon(id, { size, tint: typeof tint === 'function' ? tint(id) : tint })}<span><b>${esc(label)}</b>${desc ? `<span>${esc(d)}</span>` : ''}</span></a>`).join('')}</nav>`;
}

export function footer(ctx, cls = 'b-foot') {
  return `<footer class="${cls}"><span>Not trading advice. Prices are NSE closing prices from ${esc(ctx.C.LAST_DAY)}; during market hours the site would show live Upstox prices in the same places.</span><a href="https://${esc(ctx.C.REPO)}" rel="noopener">${esc(ctx.C.REPO)}</a></footer>`;
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
