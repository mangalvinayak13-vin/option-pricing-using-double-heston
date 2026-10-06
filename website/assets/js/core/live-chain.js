// Live options for Price an option, on NIFTY 50, NIFTY BANK or any of the site's 40 F&O stocks. The page
// first renders the saved 25 Sep NIFTY chain (site.json); this swaps in the live chain for the chosen
// underlying from /api/price?chain=SYM -- the monthly expiry at least 14 days away, the 17 strikes around
// today's price -- and keeps its market side fresh. Any failure leaves the chain on the page as it was,
// and the page says which one it shows.
import { store } from './state.js';

const SPAN = 8; // strikes shown: the at-the-money strike ± this many strike spacings, like the saved chain
export const DEFAULT_SYM = 'NIFTY 50';

// the listed strike spacing: the commonest gap between neighbouring strikes (50 for NIFTY, 2.5 for ITC)
export function chainStep(chain) {
  const n = new Map();
  for (let i = 1; i < chain.length; i++) { const g = +(chain[i].strike - chain[i - 1].strike).toFixed(4); n.set(g, (n.get(g) || 0) + 1); }
  return [...n].sort((a, b) => b[1] - a[1])[0]?.[0] || 1;
}

const row = x => ({
  strike: x.strike, call: x.call, call_src: x.call_src, call_iv: x.call_iv, call_oi: x.call_oi, call_vol: x.call_vol,
  put: x.put, put_src: x.put_src, put_iv: x.put_iv, put_oi: x.put_oi, put_vol: x.put_vol, mkt_iv: x.mkt_iv,
  dh_call: null, dh_put: null, dh_iv: null, // the model's side arrives from the first reprice
});

async function fetchChain(ctx, sym) {
  try {
    const rate = (ctx.D.savedContract || ctx.D.contract).rate;
    const r = await fetch(`/api/price?chain=${encodeURIComponent(sym)}&r=${rate}`);
    const d = r.ok ? await r.json() : null;
    return d?.status === 'live' && d.rows?.length ? d : null;
  } catch { return null; }
}

// load the live chain for an underlying (default: the one last picked) and make it the page's contract;
// true when the page should re-render. On failure the page keeps the chain it has.
export async function loadLiveChain(ctx, sym = store.get('model.sym', DEFAULT_SYM)) {
  const d = await fetchChain(ctx, sym);
  if (!d) return false;
  const atm = d.rows.reduce((a, b) => (Math.abs(b.strike - d.spot) < Math.abs(a.strike - d.spot) ? b : a));
  const chain = d.rows.filter(x => Math.abs(x.strike - atm.strike) <= SPAN * d.step + 1e-9).map(row);
  ctx.D.savedContract ??= ctx.D.contract;
  ctx.D.contract = {
    live: true, sym, name: ctx.C.NAMES?.[sym] || '', step: d.step, asof: d.asof, date: d.asof.slice(0, 10), spot: d.spot,
    forward: d.forward, parity_strike: d.parity_strike, expiry: d.expiry, dte: d.dte, t: d.t, rate: d.rate, carry: d.carry,
    strike: atm.strike, market: atm.call, market_iv: atm.call_iv, oi: atm.call_oi, volume: atm.call_vol,
    dh: null, dh_iv: null, mc: null, mc_se: null, delta: null, gamma: null, vega: null, theta: null, rho: null,
  };
  ctx.D.chain = chain;
  store.set('model.sym', sym);
  if (!chain.some(x => x.strike === store.get('model.strike', atm.strike))) store.set('model.strike', atm.strike);
  return true;
}

// every minute after: update the market side in place for the strikes on the page; true if anything moved
export async function refreshLiveChain(ctx) {
  const K = ctx.D.contract;
  if (!K.live) return false;
  const sym = K.sym;
  const d = await fetchChain(ctx, sym);
  if (!d || d.expiry !== K.expiry || ctx.D.contract !== K || K.sym !== sym) return false; // the underlying changed meanwhile
  const by = new Map(d.rows.map(x => [x.strike, x]));
  let moved = d.spot !== K.spot;
  for (const r of ctx.D.chain) {
    const x = by.get(r.strike);
    if (!x) continue;
    if (x.call !== r.call || x.put !== r.put) moved = true;
    Object.assign(r, { ...row(x), dh_call: r.dh_call, dh_put: r.dh_put, dh_iv: r.dh_iv });
  }
  Object.assign(K, { asof: d.asof, spot: d.spot, forward: d.forward, parity_strike: d.parity_strike, t: d.t, dte: d.dte, carry: d.carry });
  return moved;
}

// the market a reprice is asked for: the chain on the page, live or saved
export const marketOf = ctx => {
  const K = ctx.D.contract;
  return { spot: K.spot, t: K.t ?? K.dte / 365, r: K.rate, q: K.carry, strikes: ctx.D.chain.map(r => r.strike) };
};

// a strike as it's listed: 22,650 or 202.5
export const strikeText = (k, inr) => inr(k, Number.isInteger(k) ? 0 : (Number.isInteger(k * 10) ? 1 : 2));

export const istTime = iso => new Date(iso).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: false });
export const longDate = iso => new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
