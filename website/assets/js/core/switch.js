// The Liquid Glass light/dark switch and its theme menu (top-right, every page, every theme).
// Click: toggle light/dark.  Hold ~0.5 s (the knob's lens swells meanwhile), right-click, or
// ArrowDown on the focused switch: open the theme menu. Opening the menu never flips the switch.
import { THEMES, theme, mode, setMode } from './state.js';
import { esc } from './util.js';

const HOLD_MS = 500;
const SWELL_DELAY = 110; // quick clicks shouldn't look like holds

const CHECK = '<svg class="tm-check" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.2 8.6 6.4 11.6 12.8 4.6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

export function initControls({ onTheme }) {
  const wrap = document.createElement('div');
  wrap.className = 'dh-controls';
  wrap.innerHTML = `
    <button type="button" class="ctl-label" aria-haspopup="menu" aria-controls="dh-tmenu" title="Choose a theme">${esc(nameOf(theme()))}</button>
    <button type="button" class="lgs" role="switch" aria-checked="${mode() === 'dark'}" aria-label="Dark mode"
      aria-haspopup="menu" aria-controls="dh-tmenu" aria-expanded="false" aria-describedby="dh-sw-hint"
      title="Click for light or dark. Hold, right-click or press the down arrow for themes."><span class="knob"></span></button>
    <span class="vh" id="dh-sw-hint">Hold, right-click or press the down arrow to choose a theme.</span>`;
  // right after the skip link, so keyboard users reach the switch first, not last
  const skip = document.querySelector('.skip');
  if (skip) skip.after(wrap); else document.body.prepend(wrap);

  const menu = document.createElement('div');
  menu.className = 'tmenu';
  menu.id = 'dh-tmenu';
  menu.setAttribute('role', 'menu');
  menu.setAttribute('aria-label', 'Theme');
  menu.innerHTML = `<div class="tm-head" aria-hidden="true">Theme</div>` + THEMES.map(t => `
    <button type="button" role="menuitemradio" data-theme-id="${t.id}" aria-checked="false" tabindex="-1">
      <span class="tm-sw" style="background:${t.sw[0]}" aria-hidden="true"><i style="background:${t.sw[1]}"></i></span>
      <span>${esc(t.name)}<span class="tm-sub">${esc(t.sub)}</span></span>${CHECK}</button>`).join('') +
    `<div class="tm-sep" aria-hidden="true"></div><div class="tm-mode" aria-hidden="true"><span>Click the switch for light or dark</span></div>`;
  document.body.appendChild(menu);

  const sw = wrap.querySelector('.lgs');
  const label = wrap.querySelector('.ctl-label');
  const items = [...menu.querySelectorAll('[role="menuitemradio"]')];
  let holdT = 0, swellT = 0, heldOpen = false, isOpen = false, lastOpener = sw;

  const sync = () => {
    sw.setAttribute('aria-checked', String(mode() === 'dark'));
    label.textContent = nameOf(theme());
    items.forEach(b => b.setAttribute('aria-checked', String(b.dataset.themeId === theme())));
  };
  sync();

  function place() {
    const r = sw.getBoundingClientRect();
    const w = menu.offsetWidth || 268;
    const right = Math.max(8, innerWidth - r.right - 6);
    menu.style.top = `${Math.round(r.bottom + 10)}px`;
    menu.style.left = `${Math.round(Math.max(8, innerWidth - right - w))}px`;
  }

  function open(focusItem = true, opener = sw) {
    if (isOpen) return;
    isOpen = true;
    lastOpener = opener;
    sync();
    place();
    menu.classList.add('open');
    sw.classList.add('menu-open');
    sw.setAttribute('aria-expanded', 'true');
    label.setAttribute('aria-expanded', 'true');
    const cur = items.find(b => b.dataset.themeId === theme()) || items[0];
    if (focusItem) requestAnimationFrame(() => cur.focus({ preventScroll: true }));
    document.addEventListener('pointerdown', outside, true);
  }

  function close(returnFocus = true) {
    if (!isOpen) return;
    isOpen = false;
    menu.classList.remove('open');
    sw.classList.remove('menu-open');
    sw.setAttribute('aria-expanded', 'false');
    label.setAttribute('aria-expanded', 'false');
    items.forEach(b => b.classList.remove('kbd'));
    document.removeEventListener('pointerdown', outside, true);
    if (returnFocus) lastOpener.focus({ preventScroll: true });
  }

  function outside(e) {
    if (!menu.contains(e.target) && !sw.contains(e.target) && !label.contains(e.target)) close(false);
  }

  function clearHold() {
    clearTimeout(holdT); clearTimeout(swellT);
    sw.classList.remove('holding', 'pressing');
  }

  // ---- pointer: press, hold, release
  sw.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    heldOpen = false;
    sw.classList.add('pressing');
    swellT = setTimeout(() => sw.classList.add('holding'), SWELL_DELAY);
    holdT = setTimeout(() => {
      heldOpen = true;
      sw.classList.remove('holding', 'pressing');
      if (isOpen) close(false); else open(true, sw);
    }, HOLD_MS);
  });
  sw.addEventListener('pointerup', () => { clearTimeout(holdT); clearTimeout(swellT); sw.classList.remove('holding', 'pressing'); });
  sw.addEventListener('pointerleave', clearHold);
  sw.addEventListener('pointercancel', clearHold);
  // click also covers Space/Enter from the keyboard; a hold that opened the menu swallows its click
  sw.addEventListener('click', e => {
    if (heldOpen) { heldOpen = false; e.preventDefault(); return; }
    if (isOpen) close(false);
    setMode(mode() === 'dark' ? 'light' : 'dark');
  });
  sw.addEventListener('contextmenu', e => { e.preventDefault(); clearHold(); heldOpen = false; open(true, sw); });
  sw.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || (e.altKey && e.key === 'ArrowDown') || e.key === 'ContextMenu' || (e.shiftKey && e.key === 'F10')) {
      e.preventDefault(); open(true, sw);
    }
  });
  label.addEventListener('click', () => (isOpen ? close() : open(true, label)));
  label.addEventListener('contextmenu', e => { e.preventDefault(); open(true, label); });
  label.addEventListener('keydown', e => { if (e.key === 'ArrowDown') { e.preventDefault(); open(true, label); } });

  // ---- menu keyboard: arrows, Home/End, Enter/Space, Esc, Tab
  menu.addEventListener('keydown', e => {
    const i = items.indexOf(document.activeElement);
    const go = j => { items.forEach(b => b.classList.remove('kbd')); const b = items[(j + items.length) % items.length]; b.classList.add('kbd'); b.focus(); };
    if (e.key === 'ArrowDown') { e.preventDefault(); go(i + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); go(i - 1); }
    else if (e.key === 'Home') { e.preventDefault(); go(0); }
    else if (e.key === 'End') { e.preventDefault(); go(items.length - 1); }
    else if (e.key === 'Escape') { e.preventDefault(); close(true); }
    else if (e.key === 'Tab') { close(false); }
    else if (e.key.length === 1 && /\w/.test(e.key)) {
      const j = items.findIndex(b => b.textContent.trim().toLowerCase().startsWith(e.key.toLowerCase()));
      if (j >= 0) go(j);
    }
  });
  menu.addEventListener('pointermove', e => {
    const b = e.target.closest('[role="menuitemradio"]');
    if (b && document.activeElement !== b) { items.forEach(x => x.classList.remove('kbd')); b.focus({ preventScroll: true }); }
  });
  items.forEach(b => b.addEventListener('click', () => {
    const id = b.dataset.themeId;
    close(true);
    if (id !== theme()) onTheme(id);
  }));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && isOpen) close(true); });
  addEventListener('resize', () => isOpen && place());

  return { sync, open, close };
}

function nameOf(id) { return (THEMES.find(t => t.id === id) || THEMES[0]).name; }
