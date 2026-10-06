// Scroll frame-rate probe: node website/tools/scrollfps.mjs <theme> <page.html> [css-to-inject]
// Prints fps and the worst frame while wheel-scrolling the whole page; the optional CSS lets you
// switch one effect off at a time to find what costs frames.
import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';

const [theme = 'glass', page = 'index.html', css = ''] = process.argv.slice(2);
const PORT = 9334;
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${PORT}`,
  '--window-size=1440,900', `--user-data-dir=/tmp/dh-sf-${Date.now()}`, 'about:blank'], { stdio: 'ignore' });
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
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: `http://localhost:8765/${page}?theme=${theme}&mode=dark` });
for (let i = 0; i < 60; i++) { if (await ev("document.body && document.body.dataset.ready === '1'")) break; await sleep(150); }
if (css) await ev(`(() => { const s = document.createElement('style'); s.textContent = ${JSON.stringify(css)}; document.head.appendChild(s); })()`);
await sleep(800);
const probe = ev(`new Promise(r => { let n = 0, worst = 0, last = performance.now(); const t0 = last; const f = t => { n++; worst = Math.max(worst, t - last); last = t;
  if (t - t0 < 2400) requestAnimationFrame(f); else r({ fps: Math.round(n * 1000 / (t - t0)), worst: Math.round(worst) }); }; requestAnimationFrame(f); })`);
for (let k = 0; k < 36; k++) { await send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: 700, y: 450, deltaX: 0, deltaY: 110 }); await sleep(60); }
console.log(theme, page, css ? `[${css.slice(0, 70)}]` : '[as built]', JSON.stringify(await probe));
ws.close(); chrome.kill();
