// Interaction test: drives a headless Chrome over the DevTools protocol with real pointer and key
// events (no packages needed; Node's built-in WebSocket). Server must be running on :8765.
//   node website/tools/interact.mjs [theme]
// Checks: no console errors; click toggles light/dark; hold opens the theme menu without flipping the
// switch; right-click and ArrowDown open it; keyboard picks a theme in place and keeps a slider value;
// a slider reprices through the worker; the dash nav opens near the cursor; frame rate while animating.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';

const THEME = process.argv[2] || 'springboard';
const OUT = new URL('../.shots/interact/', import.meta.url);
mkdirSync(OUT, { recursive: true });
const PORT = 9333;
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', `--remote-debugging-port=${PORT}`, '--window-size=1440,900', '--force-device-scale-factor=1',
  `--user-data-dir=/tmp/dh-cdp-${Date.now()}`, 'about:blank'], { stdio: 'ignore' });

let ws, id = 0;
const pending = new Map(), events = [];
async function connect() {
  for (let i = 0; i < 50; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const page = list.find(t => t.type === 'page');
      if (page) { ws = new WebSocket(page.webSocketDebuggerUrl); break; }
    } catch { /* not up yet */ }
    await sleep(200);
  }
  await new Promise(r => ws.addEventListener('open', r, { once: true }));
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } else if (m.method) events.push(m);
  });
}
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evalJS = async expr => (await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
const mouse = (type, x, y, extra = {}) => send('Input.dispatchMouseEvent', { type, x, y, button: 'left', buttons: type === 'mousePressed' ? 1 : 0, clickCount: 1, pointerType: 'mouse', ...extra });
const key = async (k, code = k) => {
  const text = { Enter: '\r', ' ': ' ' }[k];
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, text, windowsVirtualKeyCode: { ArrowDown: 40, ArrowUp: 38, Enter: 13, Escape: 27, ' ': 32 }[k] || 0 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code });
};
const shot = async name => { const r = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(new URL(`${name}.png`, OUT), Buffer.from(r.result.data, 'base64')); };
const results = [];
const check = (name, ok, detail = '') => { results.push([ok ? 'PASS' : 'FAIL', name, detail]); };

async function load(path) {
  await send('Page.navigate', { url: `http://localhost:8765/${path}` });
  for (let i = 0; i < 60; i++) { if (await evalJS("document.body && document.body.dataset.ready === '1'")) break; await sleep(150); }
  await sleep(600);
}

async function fps(ms = 1200) {
  return evalJS(`new Promise(r => { let n = 0, worst = 0, last = performance.now(); const t0 = last;
    const f = t => { n++; worst = Math.max(worst, t - last); last = t; if (t - t0 < ${ms}) requestAnimationFrame(f); else r({ fps: Math.round(n * 1000 / (t - t0)), worstFrameMs: Math.round(worst) }); };
    requestAnimationFrame(f); })`);
}

try {
  await connect();
  await send('Page.enable'); await send('Runtime.enable'); await send('Log.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await load(`model.html?theme=${THEME}&mode=light`);
  const sw = await evalJS(`(() => { const r = document.querySelector('.lgs').getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()`);

  // click toggles the mode
  await mouse('mouseMoved', ...sw); await mouse('mousePressed', ...sw); await sleep(80); await mouse('mouseReleased', ...sw); await sleep(500);
  check('click toggles to dark', (await evalJS('document.documentElement.dataset.mode')) === 'dark');
  await mouse('mousePressed', ...sw); await sleep(80); await mouse('mouseReleased', ...sw); await sleep(500);
  check('click toggles back to light', (await evalJS('document.documentElement.dataset.mode')) === 'light');

  // hold: lens swells, menu opens at ~0.5 s, the switch does not flip
  await mouse('mousePressed', ...sw); await sleep(300);
  check('holding swells the lens', await evalJS("document.querySelector('.lgs').classList.contains('holding')"));
  await shot(`${THEME}-hold`);
  await sleep(400); await mouse('mouseReleased', ...sw); await sleep(700);
  check('hold opens the theme menu', await evalJS("document.querySelector('.tmenu').classList.contains('open')"));
  check('hold does not flip the switch', (await evalJS('document.documentElement.dataset.mode')) === 'light');
  check('menu marks the current theme', (await evalJS("document.querySelector('.tmenu [aria-checked=true]')?.dataset.themeId")) === THEME);
  await shot(`${THEME}-menu`);
  await key('Escape'); await sleep(300);
  check('Esc closes the menu', !(await evalJS("document.querySelector('.tmenu').classList.contains('open')")));
  check('focus returns to the switch', await evalJS("document.activeElement === document.querySelector('.lgs')"));

  // right-click opens it; a click outside closes it
  await mouse('mousePressed', ...sw, { button: 'right', buttons: 2 }); await mouse('mouseReleased', ...sw, { button: 'right', buttons: 0 }); await sleep(600);
  check('right-click opens the menu', await evalJS("document.querySelector('.tmenu').classList.contains('open')"));
  await mouse('mousePressed', 700, 600); await mouse('mouseReleased', 700, 600); await sleep(400);
  check('click outside closes the menu', !(await evalJS("document.querySelector('.tmenu').classList.contains('open')")));

  // a slider reprices through the worker; the value survives a theme change
  const before = await evalJS("document.querySelector('[data-bind=dh]').textContent");
  await evalJS("(() => { const s = document.querySelector('[data-param=v0_2]'); s.value = 0.01; s.dispatchEvent(new Event('input', { bubbles: true })); })()");
  await sleep(1600);
  const after = await evalJS("document.querySelector('[data-bind=dh]').textContent");
  check('slider reprices the option', before !== after, `${before} -> ${after}`);
  check('status says repriced', /Repriced/.test(await evalJS("document.querySelector('[data-bind=status]').textContent")));

  // keyboard: focus the switch, ArrowDown opens the menu, ArrowDown + Enter picks the next theme
  await evalJS("document.querySelector('.lgs').focus()");
  await key('ArrowDown'); await sleep(600);
  check('ArrowDown opens the menu', await evalJS("document.querySelector('.tmenu').classList.contains('open')"));
  const target = await evalJS("(() => { const a = [...document.querySelectorAll('.tmenu [role=menuitemradio]')]; const i = a.findIndex(b => b === document.activeElement); return a[(i + 1) % a.length].dataset.themeId; })()");
  await key('ArrowDown'); await key('Enter'); await sleep(1400);
  check('keyboard picks a theme in place', (await evalJS('document.documentElement.dataset.theme')) === target, target);
  check('page did not reload (slider value kept)', (await evalJS("document.querySelector('[data-param=v0_2]').value")) === '0.01');
  check('repriced value kept after theme change', (await evalJS("document.querySelector('[data-bind=dh]').textContent")) === after);
  await shot(`${THEME}-after-switch`);

  // back to the theme under test; the dash nav opens near the cursor
  await load(`index.html?theme=${THEME}&mode=dark`);
  await mouse('mouseMoved', 400, 450); await sleep(200);
  for (let x = 300; x >= 30; x -= 30) { await mouse('mouseMoved', x, 450); await sleep(16); }
  const navF = fps(900);
  for (let y = 380; y <= 540; y += 8) { await mouse('mouseMoved', 30, y); await sleep(16); }
  const nf = await navF;
  await sleep(300);
  const open = await evalJS("!!document.querySelector('.mdash.open, .fnav.open')");
  check('side nav opens near the cursor', open);
  check('frame rate while the nav animates', nf.fps >= 55, JSON.stringify(nf));
  await shot(`${THEME}-nav`);
  await mouse('mouseMoved', 900, 450); await sleep(900);
  check('side nav relaxes when the cursor leaves', !(await evalJS("!!document.querySelector('.mdash.open, .fnav.open')")));
  const idle = await fps(1000);
  check('frame rate at rest (ticker running)', idle.fps >= 55, JSON.stringify(idle));

  const errs = events.filter(e => (e.method === 'Runtime.exceptionThrown') || (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error') ||
    (e.method === 'Log.entryAdded' && e.params.entry.level === 'error'));
  check('no console errors', errs.length === 0, errs.map(e => JSON.stringify(e.params).slice(0, 240)).join(' | '));
} catch (e) {
  results.push(['FAIL', 'test harness', String(e)]);
} finally {
  for (const [s, n, d] of results) console.log(s, n, d ? `(${d})` : '');
  ws?.close(); chrome.kill();
}
