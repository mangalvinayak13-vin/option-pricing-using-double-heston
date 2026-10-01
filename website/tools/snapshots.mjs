// The best snapshots: real 1440 x 900 screens of the strongest moments, with motion on and animations
// finished. Server must be running on :8765.   node website/tools/snapshots.mjs  -> website/snapshots/*.png
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';

// SNAP_OUT and SNAP_LIST (a JSON list in the same shape) take ad-hoc shots for checking a section
const OUT = process.env.SNAP_OUT ? new URL(`file://${process.env.SNAP_OUT.replace(/\/?$/, '/')}`) : new URL('../snapshots/', import.meta.url);
mkdirSync(OUT, { recursive: true });
// [file name, theme, mode, page, section key (or null for the top), extra action]
const SHOTS = process.env.SNAP_LIST ? JSON.parse(process.env.SNAP_LIST) : [
  ['01-ferro-home', 'ferro', 'light', 'index.html', null],
  ['02-ferro-journey', 'ferro', 'light', 'index.html', 'journey'],
  ['03-ferro-pinn-vs-ann-3d', 'ferro', 'light', 'index.html', 'nn', 'fig'],
  ['04-ferro-factor-pools', 'ferro', 'dark', 'how-it-works.html', 'factors'],
  ['05-ferro-magnets', 'ferro', 'light', 'results.html', 'magnets'],
  ['06-ferro-nav-open', 'ferro', 'dark', 'model.html', 'sliders', 'nav'],
  ['07-glass-home-dark', 'glass', 'dark', 'index.html', null],
  ['08-glass-pinn-vs-ann-3d', 'glass', 'dark', 'index.html', 'nn', 'fig'],
  ['09-glass-bend', 'glass', 'light', 'how-it-works.html', 'bend'],
  ['10-springboard-key-results', 'springboard', 'light', 'index.html', 'key'],
  ['11-springboard-model', 'springboard', 'dark', 'model.html', 'price'],
  ['12-springboard-theme-menu', 'springboard', 'light', 'index.html', null, 'menu'],
  ['13-results-page', 'glass', 'light', 'results.html', 'results'],
  ['14-amber-home', 'amber', 'dark', 'index.html', null],
  ['15-instrument-home', 'instrument', 'light', 'index.html', null],
  ['16-trading-market', 'trading', 'dark', 'market.html', null],
  ['17-springboard-nav-open', 'springboard', 'dark', 'results.html', 'pair', 'nav-l'],
];
const PORT = 9336;
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${PORT}`,
  '--window-size=1440,900', '--hide-scrollbars', `--user-data-dir=/tmp/dh-snap-${Date.now()}`, 'about:blank'], { stdio: 'ignore' });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try { const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) ws = new WebSocket(p.webSocketDebuggerUrl); } catch { /* wait */ }
  await sleep(200);
}
if (ws.readyState !== WebSocket.OPEN) await new Promise(r => ws.addEventListener('open', r, { once: true }));
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async x => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
const mouse = (type, x, y, extra = {}) => send('Input.dispatchMouseEvent', { type, x, y, button: 'left', buttons: type === 'mousePressed' ? 1 : 0, clickCount: 1, ...extra });
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 2, mobile: false });

for (const [name, theme, mode, page, sec, act] of SHOTS) {
  await send('Page.navigate', { url: `http://localhost:8765/${page}?theme=${theme}&mode=${mode}` });
  for (let i = 0; i < 60; i++) { if (await ev("document.body && document.body.dataset.ready === '1'")) break; await sleep(150); }
  await sleep(900);
  if (sec) {
    await ev(`(() => { const el = document.querySelector('[data-sec="${sec}"]'); if (!el) return;
      const t = ${act === 'fig' ? `el.querySelector('.fig') || el` : 'el'}; scrollTo({ top: scrollY + t.getBoundingClientRect().top - 90, behavior: 'instant' }); })()`);
  }
  await sleep(3400); // let entrances, draws and the 3D sway settle
  if (act === 'menu') {
    const sw = await ev(`(() => { const r = document.querySelector('.lgs').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()`);
    await mouse('mouseMoved', ...sw); await mouse('mousePressed', ...sw); await sleep(700); await mouse('mouseReleased', ...sw); await sleep(900);
  }
  if (act === 'nav' || act === 'nav-l') {
    const right = act === 'nav';
    for (let x = 320; x >= 26; x -= 26) { await mouse('mouseMoved', right ? 1440 - x : x, 470); await sleep(16); }
    for (let y = 430; y <= 520; y += 6) { await mouse('mouseMoved', right ? 1414 : 26, y); await sleep(16); }
    await sleep(700);
  }
  const r = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(new URL(`${name}.png`, OUT), Buffer.from(r.result.data, 'base64'));
  console.log('saved', name);
}
ws.close(); chrome.kill();
