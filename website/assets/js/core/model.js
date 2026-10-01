// Page-side model client. Requests go to the Web Worker (model-worker.js); only the newest answer is
// used. The starting settings' results are already in site.json, so the first render needs no call.

export const PARAM_KEYS = ['v0_1', 'kappa1', 'theta1', 'xi1', 'rho1', 'v0_2', 'kappa2', 'theta2', 'xi2', 'rho2'];
export const DEFAULT_PARAMS = { v0_1: 0.02, kappa1: 0.5, theta1: 0.02, xi1: 0.3, rho1: -0.7, v0_2: 0.02, kappa2: 5.0, theta2: 0.02, xi2: 0.5, rho2: -0.7 };
// slider order in content SLIDERS: (factor, symbol, name, value, lo, hi) -> parameter key
export const SLIDER_KEYS = { slow: ['v0_1', 'kappa1', 'theta1', 'xi1', 'rho1'], fast: ['v0_2', 'kappa2', 'theta2', 'xi2', 'rho2'] };

let worker = null, seq = 0, newest = 0;
const waiting = new Map();

function ensure() {
  if (worker) return worker;
  worker = new Worker('assets/js/core/model-worker.js');
  worker.onmessage = ({ data }) => {
    const w = waiting.get(data.id);
    if (!w) return;
    waiting.delete(data.id);
    if (data.id !== newest || data.aborted) w({ stale: true });
    else if (data.error) w({ error: data.error });
    else w({ res: data.res });
  };
  worker.onerror = () => { waiting.forEach(w => w({ error: 'The pricing worker stopped.' })); waiting.clear(); };
  return worker;
}

// price({strike, kind, params, mc}) -> Promise<{res}|{error}|{stale}>
export function price(req) {
  const id = ++seq;
  newest = id;
  ensure().postMessage({ id, req });
  return new Promise(resolve => waiting.set(id, resolve));
}

export const OFFLINE_HELP = 'Live repricing needs the local model server. Start it with: python3 website/serve.py';

// Feller check (2κθ > ξ²), same rule as the pricer's feller_condition
export function feller(p, f) {
  const [k, t, x] = f === 'slow' ? [p.kappa1, p.theta1, p.xi1] : [p.kappa2, p.theta2, p.xi2];
  return { lhs: 2 * k * t, rhs: x * x, ok: 2 * k * t > x * x };
}
