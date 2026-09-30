// Theme + mode state, persistence and the shared input store.
// The inline boot script in every page sets data-theme / data-mode before any CSS loads (no flash);
// this module keeps them in sync afterwards.

export const THEMES = [
  { id: 'springboard', name: 'Springboard', sub: 'Widgets and app icons', sw: ['#F2F2F7', '#FF9500'] },
  { id: 'glass', name: 'Glass', sub: 'Product page, frosted glass', sw: ['#000000', '#2997FF'] },
  { id: 'ferro', name: 'Ferro', sub: 'Chrome and liquid black', sw: ['#E9EBEE', '#0A0A0A'] },
  { id: 'amber', name: 'Amber', sub: 'Precision readouts', sw: ['#0F100E', '#F0B24A'] },
  { id: 'instrument', name: 'Instrument', sub: 'Lab scope traces', sw: ['#0F1419', '#7FB2E5'] },
  { id: 'trading', name: 'Trading', sub: 'Broker terminal', sw: ['#0B0E11', '#4C8DF6'] },
];
export const THEME_IDS = THEMES.map(t => t.id);
export const DEFAULT_THEME = document.documentElement.dataset.defaultTheme || 'glass';

const root = document.documentElement;
const listeners = new Set();
const sys = matchMedia('(prefers-color-scheme: dark)');

function read(k) { try { return localStorage.getItem(k); } catch { return null; } }
function write(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode: keep in memory */ } }

export const theme = () => root.dataset.theme;
export const mode = () => root.dataset.mode;
export const motionOK = () => !matchMedia('(prefers-reduced-motion: reduce)').matches;
export const on = fn => (listeners.add(fn), () => listeners.delete(fn));
const emit = (what, v) => listeners.forEach(fn => fn(what, v));

export function setMode(m, { persist = true } = {}) {
  if (m !== 'light' && m !== 'dark' || m === mode()) return;
  root.classList.add('mode-anim');
  root.dataset.mode = m;
  root.style.colorScheme = m;
  if (persist) write('dh.mode', m);
  emit('mode', m);
  setTimeout(() => root.classList.remove('mode-anim'), 400);
}

export function setTheme(t) {
  if (!THEME_IDS.includes(t) || t === theme()) return false;
  root.dataset.theme = t;
  write('dh.theme', t);
  emit('theme', t);
  return true;
}

// first visit follows the system; once the visitor flips the switch, their choice wins
sys.addEventListener('change', e => { if (!read('dh.mode')) setMode(e.matches ? 'dark' : 'light', { persist: false }); });

// ---- the input store: anything a visitor typed or picked survives a theme change and page moves
const STORE_KEY = 'dh.store.v1';
let bag = {};
try { bag = JSON.parse(sessionStorage.getItem(STORE_KEY) || '{}'); } catch { bag = {}; }
export const store = {
  get: (k, d) => (k in bag ? bag[k] : d),
  set(k, v) { bag[k] = v; try { sessionStorage.setItem(STORE_KEY, JSON.stringify(bag)); } catch { /* ignore */ } },
};
