// Model worker: keeps pricing work off the page's main thread. It talks to the local model server
// (website/serve.py, which runs the project's unchanged pricer), cancels requests that a newer one
// has replaced, caches answers by parameters, and passes back plain data for the charts.
'use strict';
let ctrl = null;
const cache = new Map();

self.onmessage = async ({ data }) => {
  const { id, req } = data;
  const key = JSON.stringify(req);
  if (cache.has(key)) { self.postMessage({ id, res: cache.get(key), cached: true }); return; }
  if (ctrl) ctrl.abort();
  ctrl = new AbortController();
  try {
    const r = await fetch('/api/price', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: key, signal: ctrl.signal });
    const body = await r.json();
    if (!r.ok) throw new Error(body.error || `HTTP ${r.status}`);
    cache.set(key, body);
    if (cache.size > 200) cache.delete(cache.keys().next().value);
    self.postMessage({ id, res: body });
  } catch (e) {
    if (e && e.name === 'AbortError') self.postMessage({ id, aborted: true });
    else self.postMessage({ id, error: String((e && e.message) || e) });
  }
};
