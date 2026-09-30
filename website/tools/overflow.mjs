// Horizontal overflow check at a given width (default 390 px, a phone): every page in every theme.
//   node website/tools/overflow.mjs [width]
// Reports pages whose document is wider than the viewport, and the widest offending elements.
import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';

const W = +(process.argv[2] || 390);
const THEMES = ['springboard', 'glass', 'ferro', 'amber', 'instrument', 'trading'];
const FILES = ['index.html', 'market.html', 'model.html', 'how-it-works.html', 'finding.html', 'about.html', 'team.html', 'references.html'];
const PORT = 9335;
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=/tmp/dh-of-${Date.now()}`, 'about:blank'], { stdio: 'ignore' });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try { const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json(); const p = l.find(t => t.type === 'page'); if (p) ws = new WebSocket(p.webSocketDebuggerUrl); } catch { /* wait */ }
  await sleep(200);
}
if (ws.readyState !== WebSocket.OPEN) await new Promise(r => ws.addEventListener('open', r, { once: true }));
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } });
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async x => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: 844, deviceScaleFactor: 1, mobile: true });
let bad = 0;
for (const t of THEMES) for (const f of FILES) {
  await send('Page.navigate', { url: `http://localhost:8765/${f}?theme=${t}&mode=light` });
  for (let i = 0; i < 60; i++) { if (await ev("document.body && document.body.dataset.ready === '1'")) break; await sleep(120); }
  await sleep(500);
  const r = await ev(`(() => { const vw = document.documentElement.clientWidth, sw = document.documentElement.scrollWidth;
    if (sw <= vw + 1) return null;
    const off = [...document.querySelectorAll('#main *')].filter(e => { const b = e.getBoundingClientRect(); return b.right > vw + 1 && getComputedStyle(e).position !== 'fixed'; })
      .filter(e => !e.closest('.tick, .b-scroll-x, .s-scroll-x, .chart, .gl-links, .b-eqn, .tick-view'))
      .slice(0, 4).map(e => (e.className && e.className.baseVal === undefined ? e.className : e.tagName) + ':' + Math.round(e.getBoundingClientRect().right));
    return { sw, vw, off }; })()`);
  if (r) { bad++; console.log(`${t} ${f} scrollWidth ${r.sw} > ${r.vw}`, r.off.join(' | ')); }
}
console.log(bad ? `${bad} pages overflow at ${W}px` : `no horizontal overflow at ${W}px`);
ws.close(); chrome.kill();
