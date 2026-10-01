// The site's entry point. Loads the shared data once, renders the current page in the current theme,
// and switches themes in place: the new theme's layout replaces the old one inside a view transition,
// inputs come back from the store, and the scroll stays on the same section.
import { THEMES, theme, setTheme, on, mode } from './core/state.js';
import { initControls } from './core/switch.js';
import { createDashNav } from './core/nav-dashes.js';
import { createFerroNav } from './core/nav-ferro.js';
import { observe, resetObservers, stopAllLoops, reduced } from './core/motion.js';
import { mountCharts } from './core/charts.js';
import { mountControllers } from './core/controllers.js';

const root = document.documentElement;
const app = document.getElementById('app');
const page = root.dataset.page || 'home';

// ?theme=ferro&mode=dark was applied (and remembered) by the boot script; tidy the address bar
if (location.search) {
  const q = new URLSearchParams(location.search);
  if (q.has('theme') || q.has('mode')) { q.delete('theme'); q.delete('mode'); history.replaceState(null, '', location.pathname + (q.toString() ? `?${q}` : '') + location.hash); }
}

const get = u => fetch(u).then(r => { if (!r.ok) throw new Error(`${u}: ${r.status}`); return r.json(); });
let ctx;
try {
  const [C, D, P, PA] = await Promise.all([get('assets/data/content.json'), get('assets/data/site.json'), get('assets/data/ferro_pair.json'),
    get('assets/data/pinn_vs_ann.json')]);
  const all = C.PAGES.map(([id, file, label, desc]) => ({ id, file, label, desc }));
  // navs list only the pages in the nav; a page outside it (Market) marks its parent page instead
  ctx = { page, C, D, P, PA, all, pages: all.filter(p => !C.NAV_PARENT[p.id]), navPage: C.NAV_PARENT[page] || page };
} catch (e) {
  app.innerHTML = `<div class="noscript"><h1>The site's data didn't load.</h1><p>Start the local server with <code>python3 website/serve.py</code> and open http://localhost:8765.</p></div>`;
  throw e;
}

const mods = {};
const load = id => (mods[id] ??= import(`./themes/${id}.js`).then(m => m.default));
let nav = null, unmountCharts = null, cleanups = [];

async function render(id) {
  const T = await load(id);
  resetObservers();
  stopAllLoops();
  unmountCharts?.();
  cleanups.forEach(f => f && f());
  cleanups = [];
  const label = ctx.all.find(p => p.id === page)?.label || 'Home';
  document.title = page === 'home' ? 'Double Heston' : `${label} | Double Heston`;
  ctx.chartOpts = T.chartOpts || {};
  app.innerHTML = T.page(page, ctx);
  const kind = T.nav?.kind || 'dashes', side = T.nav?.side || 'l';
  if (!nav || nav.kind !== kind || nav.side !== side) {
    nav?.destroy();
    nav = kind === 'ferro' ? createFerroNav({ pages: ctx.pages, current: ctx.navPage }) : createDashNav({ pages: ctx.pages, current: ctx.navPage, side });
    Object.assign(nav, { kind, side });
    root.dataset.nav = kind === 'ferro' ? 'r' : side; // the page reserves a strip on this side (base.css)
  }
  unmountCharts = mountCharts(app, ctx);
  cleanups.push(mountControllers(app, ctx));
  cleanups.push(T.mount?.(app, ctx));
  observe(app);
}

// keep the visitor on the same section across a theme change
function anchor() {
  const secs = [...app.querySelectorAll('[data-sec]')];
  const top = secs.find(s => s.getBoundingClientRect().bottom > 90);
  return top ? { key: top.dataset.sec, off: top.getBoundingClientRect().top } : { ratio: scrollY / Math.max(1, document.body.scrollHeight - innerHeight) };
}
function restore(a) {
  const el = a.key && app.querySelector(`[data-sec="${a.key}"]`);
  if (el) scrollTo({ top: scrollY + el.getBoundingClientRect().top - a.off, behavior: 'instant' });
  else if (a.ratio != null) scrollTo({ top: a.ratio * (document.body.scrollHeight - innerHeight), behavior: 'instant' });
}

let busy = false;
async function switchTheme(id) {
  if (busy || id === theme()) return;
  busy = true;
  try {
    await load(id); // fetch the new theme first so the swap is instant
    const a = anchor();
    const swap = async () => { setTheme(id); await render(id); restore(a); };
    if (document.startViewTransition && !reduced()) await document.startViewTransition(swap).finished.catch(() => {});
    else {
      app.classList.add('fading');
      await new Promise(r => setTimeout(r, reduced() ? 0 : 180));
      await swap();
      app.classList.remove('fading');
      if (!reduced()) { app.classList.add('fade-in'); setTimeout(() => app.classList.remove('fade-in'), 400); }
    }
    controls.sync();
  } finally { busy = false; }
}

const controls = initControls({ onTheme: switchTheme });
on(what => { if (what === 'mode') controls.sync(); });
await render(theme());
document.body.dataset.ready = '1';
document.fonts?.ready.then(() => { document.body.dataset.h = String(document.documentElement.scrollHeight); });
export { THEMES, mode };
