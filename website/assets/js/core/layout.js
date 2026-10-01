// Walks a page's sections (pages.js) and hands each one to the theme's renderers, grouping runs of
// panels between headings. Guarantees every theme shows every section, in the same order.
import { sections } from './pages.js';
import { esc } from './util.js';

// r = { hero(sec, i), head(sec, i), panel(sec, i), note(sec, i), group(html, i) }
export function renderPage(page, ctx, r) {
  const secs = sections(page, ctx);
  let out = '', run = [], g = 0;
  const flush = () => { if (run.length) { out += r.group(run.join(''), g++); run = []; } };
  secs.forEach((s, i) => {
    if (s.kind === 'hero') { flush(); out += pre(r.hero(s, i), s); }
    else if (s.kind === 'head') { flush(); out += action(r.head(s, i), s); }
    else if (s.kind === 'note') run.push((r.note || r.panel)(s, i));
    else run.push(glass(r.panel(s, i), s));
  });
  flush();
  return out;
}

// a section flagged glass: true sits on the theme's glass (base.css .glass, tuned per theme)
function glass(html, s) {
  return s.glass ? html.replace(/^(\s*<[a-z]+\b[^>]*?\bclass=")/, '$1glass ') : html;
}

// the hero's opening line (Home: "From a speck of pollen to Wall Street"), set just above the theme's question line
function pre(html, s) {
  if (!s.pre) return html;
  const line = `<p class="s-pre">${esc(s.pre)}</p>`;
  const q = /<p class="(?:[a-z]+-q|am-prompt)\b/;
  return q.test(html) ? html.replace(q, m => line + m) : html.replace(/^(\s*<[a-z]+\b[^>]*>)/, `$1${line}`);
}

// puts the heading's action button first inside the theme's <header>, floated to the top right
function action(html, s) {
  if (!s.action) return html;
  const [href, label] = s.action;
  return html.replace(/^(\s*<header\b[^>]*>)/, `$1<a class="btn ghost s-act" href="${href}">${esc(label)}</a>`);
}

// the standard inside of a panel: lead paragraph, body, fine print
export const inner = s => `${s.lead ? `<p class="s-lead">${esc(s.lead)}</p>` : ''}${s.body || ''}${s.fine ? `<p class="s-fine">${esc(s.fine)}</p>` : ''}`;
