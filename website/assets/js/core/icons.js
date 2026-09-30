// Original app-style icons: a superellipse squircle with layered depth (base gradient, soft top sheen,
// an inner rim lit from above, a bold glyph with its own small shadow) and a proper dark-mode
// version (dark base, glyph in the tint colour). All glyphs are drawn here; none are Apple's.
import { uid } from './util.js';

// continuous-corner squircle, |x|^n + |y|^n = 1 with n = 5, on a 100 x 100 box
const SQ = (() => {
  const n = 5, pts = [];
  for (let i = 0; i < 96; i++) {
    const t = (i / 96) * Math.PI * 2, c = Math.cos(t), s = Math.sin(t);
    pts.push([50 + 50 * Math.sign(c) * Math.abs(c) ** (2 / n), 50 + 50 * Math.sign(s) * Math.abs(s) ** (2 / n)]);
  }
  return 'M' + pts.map(p => p.map(v => v.toFixed(2)).join(',')).join(' L') + ' Z';
})();
export const SQUIRCLE_PATH = SQ;

// [light base top, light base bottom, light glyph, dark glyph top, dark glyph bottom]
export const TINTS = {
  blue: ['#5AB0FF', '#0A5FE0', '#FFFFFF', '#6CB8FF', '#2F7BF5'],
  orange: ['#FFB547', '#FF7A0A', '#FFFFFF', '#FFBE5C', '#FF8A1F'],
  green: ['#63E083', '#1DAA4E', '#FFFFFF', '#6BE38A', '#2DBB5C'],
  red: ['#FF7A70', '#E02B3A', '#FFFFFF', '#FF8378', '#F0444F'],
  indigo: ['#8E8BFF', '#4B3FE0', '#FFFFFF', '#9C99FF', '#6A60F2'],
  teal: ['#63DDEB', '#0A9CC0', '#FFFFFF', '#6FE3F0', '#20ADCB'],
  graphite: ['#5C5F66', '#26282C', '#FFFFFF', '#E6E7EA', '#B9BCC2'],
  grey: ['#A6A7AD', '#6B6C72', '#FFFFFF', '#D5D6DA', '#A5A7AD'],
  pink: ['#FF7EB3', '#E0367C', '#FFFFFF', '#FF8DBC', '#EE4F8E'],
  yellow: ['#FFD95E', '#F2A600', '#FFFFFF', '#FFDD6E', '#F5B21A'],
  // theme sets
  chrome: ['#FAFBFC', '#C3C8CF', '#0A0A0B', '#F2F4F7', '#AEB4BC'],
  amber: ['#F7C66E', '#C9820F', '#1A1406', '#F5BE5E', '#D99527'],
  steel: ['#7FB2E5', '#2D6FAE', '#FFFFFF', '#9CC6F0', '#5E9BD8'],
  azure: ['#6FA8FF', '#2F6FE0', '#FFFFFF', '#7EB2FF', '#4C8DF6'],
};
export const PAGE_TINT = { home: 'blue', market: 'graphite', model: 'orange', maths: 'indigo', finding: 'red', about: 'grey', team: 'teal', references: 'yellow', slow: 'teal', fast: 'orange', play: 'red', video: 'red' };
export const PAGE_GLYPH = { home: 'home', market: 'market', model: 'model', maths: 'maths', finding: 'finding', about: 'about', team: 'team', references: 'refs' };

const G = {
  home: g => `<path d="M50 23 78.5 47.2c2 1.7.8 5-1.9 5H74V74a5 5 0 0 1-5 5H58.5V63.5a2.5 2.5 0 0 0-2.5-2.5H44a2.5 2.5 0 0 0-2.5 2.5V79H31a5 5 0 0 1-5-5V52.2h-2.6c-2.7 0-3.9-3.3-1.9-5Z" style="fill:${g}"/>`,
  market: () => `
    <path d="M31 22v56M50 17v50M69 30v52" style="stroke:#FFFFFF;stroke-opacity:.5;stroke-width:3.4;stroke-linecap:round"/>
    <rect x="23" y="33" width="16" height="30" rx="3.2" style="fill:#34D160"/>
    <rect x="42" y="25" width="16" height="27" rx="3.2" style="fill:#FF4D42"/>
    <rect x="61" y="44" width="16" height="30" rx="3.2" style="fill:#34D160"/>`,
  model: g => `
    <path d="M22 20v58h58" style="fill:none;stroke:${g};stroke-opacity:.42;stroke-width:5.5;stroke-linecap:round;stroke-linejoin:round"/>
    <path d="M32 29c7 22 20 34 44 36" style="fill:none;stroke:${g};stroke-width:9.5;stroke-linecap:round"/>
    <circle cx="32" cy="29" r="8" style="fill:${g}"/>`,
  maths: g => `
    <path d="M62.5 22.5c-6.5-4.2-15-1.8-15.6 8.4L45.3 70c-.7 10-8.6 12.4-14.6 8" style="fill:none;stroke:${g};stroke-width:8.6;stroke-linecap:round"/>
    <path d="M58 58h16M66 50v16" style="stroke:${g};stroke-width:6.5;stroke-linecap:round;stroke-opacity:.55"/>`,
  finding: g => `
    <path d="M20 35c10 16 22 22 30 22s20-6 30-22" style="fill:none;stroke:${g};stroke-width:8.5;stroke-linecap:round"/>
    <circle cx="27" cy="72" r="6.5" style="fill:${g}"/><circle cx="50" cy="77" r="6.5" style="fill:${g};opacity:.75"/>
    <circle cx="73" cy="70" r="6.5" style="fill:${g};opacity:.55"/>`,
  about: g => `<circle cx="50" cy="27" r="8.5" style="fill:${g}"/><rect x="43" y="42" width="14" height="37" rx="7" style="fill:${g}"/>`,
  team: g => `
    <circle cx="64" cy="37" r="11" style="fill:${g};opacity:.62"/><path d="M47 77c1.5-15 9-21 17-21s15.5 6 17 21Z" style="fill:${g};opacity:.62"/>
    <circle cx="39" cy="40" r="12.5" style="fill:${g}"/><path d="M18 80c1.6-17 10.5-24 21-24s19.4 7 21 24Z" style="fill:${g}"/>`,
  refs: g => `
    <path d="M28 20h32l14 14v42a4 4 0 0 1-4 4H28a4 4 0 0 1-4-4V24a4 4 0 0 1 4-4Z" style="fill:${g}"/>
    <path d="M60 20v11a3 3 0 0 0 3 3h11" style="fill:none;stroke:var(--ic-cut);stroke-width:3;stroke-linejoin:round;opacity:.5"/>
    <path d="M34 48h30M34 58h30M34 68h20" style="stroke:var(--ic-cut);stroke-width:5;stroke-linecap:round;opacity:.72"/>`,
  slow: g => `<path d="M14 58c10-26 26-26 36-6s26 20 36-6" style="fill:none;stroke:${g};stroke-width:9;stroke-linecap:round"/>`,
  fast: g => `<path d="M12 52l8-15 9 28 9-30 9 30 9-28 9 26 8-20 7 9" style="fill:none;stroke:${g};stroke-width:7.5;stroke-linecap:round;stroke-linejoin:round"/>`,
  play: g => `<path d="M39 27.5c0-3.3 3.6-5.3 6.4-3.6l27.4 16.9c2.7 1.7 2.7 5.6 0 7.2L45.4 65c-2.8 1.7-6.4-.3-6.4-3.6Z" transform="translate(-3 5)" style="fill:${g}"/>`,
  video: g => G.play(g),
};

export function icon(kind, { size = 60, tint, cls = '', label = '' } = {}) {
  const t = TINTS[tint || PAGE_TINT[kind] || 'blue'];
  const k = PAGE_GLYPH[kind] || kind;
  const id = uid('ic');
  const glyph = (G[k] || G.about)(`url(#${id}g)`);
  const style = `width:${size}px;height:${size}px;--l-a:${t[0]};--l-b:${t[1]};--l-g:${t[2]};--d-ga:${t[3]};--d-gb:${t[4]}`;
  const aria = label ? `role="img" aria-label="${label}"` : 'aria-hidden="true"';
  return `<span class="ico ico-${k} ${cls}" style="${style}"><svg viewBox="0 0 100 100" ${aria} focusable="false">
<defs>
  <linearGradient id="${id}b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--ic-base-a)"/><stop offset="1" style="stop-color:var(--ic-base-b)"/></linearGradient>
  <linearGradient id="${id}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--ic-glyph-a)"/><stop offset="1" style="stop-color:var(--ic-glyph-b)"/></linearGradient>
  <radialGradient id="${id}s" cx="50%" cy="0%" r="75%"><stop offset="0" style="stop-color:#fff;stop-opacity:var(--ic-sheen)"/><stop offset=".62" style="stop-color:#fff;stop-opacity:0"/></radialGradient>
  <linearGradient id="${id}r" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:#fff;stop-opacity:var(--ic-rim)"/><stop offset=".5" style="stop-color:#fff;stop-opacity:.04"/><stop offset="1" style="stop-color:#000;stop-opacity:.14"/></linearGradient>
  <clipPath id="${id}c"><path d="${SQ}"/></clipPath>
  <filter id="${id}f" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="1.6" stdDeviation="1.5" style="flood-color:#000;flood-opacity:var(--ic-gshadow)"/></filter>
</defs>
<path d="${SQ}" style="fill:url(#${id}b)"/>
<g clip-path="url(#${id}c)"><rect width="100" height="100" style="fill:url(#${id}s)"/></g>
<g filter="url(#${id}f)" style="--ic-cut:var(--ic-base-b)">${glyph}</g>
<path d="${SQ}" transform="translate(.75 .75) scale(.985)" style="fill:none;stroke:url(#${id}r);stroke-width:1.5"/>
</svg></span>`;
}
