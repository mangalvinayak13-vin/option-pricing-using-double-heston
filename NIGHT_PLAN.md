# Night build plan: the Double Heston website

Branch `night-build`. The safe point before tonight is commit `ae9dd2c` on `worktree-complete-training`.
Nothing is pushed, merged, deployed or published. The model's maths (`legacy_streamlit_site/models.py`, `src/`) and `designs/` are not edited.

## What gets built

- **One site with six themes**, listed in this order: Springboard, Glass, Ferro, Amber, Instrument, Trading. Each theme has light and dark modes.
- **Eight pages:** Home, Market, The model, How it works, The finding, About, Team, References.
- **Folder:** `website/`.
- **One command:** `python3 website/serve.py`, then open http://localhost:8765.

## Architecture

| Piece | Where | Notes |
|---|---|---|
| Model connection | `website/serve.py` (stdlib only) | Imports `legacy_streamlit_site/models.py` unchanged and serves the static site plus `/api/price`. One reprice (price, IV, Greeks, a 17-strike smile, the chain, Feller, Monte Carlo) takes about 15 ms. |
| In-browser side | `assets/js/core/model-worker.js` | The Web Worker debounces requests, cancels stale ones, caches by parameters and shapes the chart data, so the page thread never waits. |
| Data | `assets/data/site.json`, `ferro_pair.json` | Snapshots of the real data: NSE bhavcopy, verified research outputs and the pricer's outputs. `website/tools/export.py` rebuilds them. |
| Content | `assets/data/content.json` | One source for all copy and numbers. `website/tools/content.py` is copied from the design generator and adjusted there, not in `designs/`. |
| Theme system | `assets/js/core/state.js` + an inline head script | `data-theme` and `data-mode` are set on `<html>` before the CSS loads, so there's no flash. They are stored in localStorage, the URL `?theme=&mode=` overrides them, and the first visit follows the system's light/dark setting. |
| Switch and theme menu | `assets/js/core/switch.js` | The Liquid Glass switch: click toggles; holding for 500 ms swells the lens and opens the menu, and the switch doesn't flip. Right-click and ArrowDown also open the menu. It is a `role=menu` with `menuitemradio` items, arrow keys and Enter, closed by Esc or a click outside. |
| Theme change | `assets/js/app.js` | The page is re-rendered in place with the View Transitions API, falling back to a crossfade. Inputs live in a shared store, so anything typed survives. The scroll is re-anchored to the same section. |
| Magnetic dashes nav | `assets/js/core/nav-dashes.js` | One shared component for five themes. DOM dashes are moved by transform only; spring physics runs only while the cursor is near or the springs are still settling. It works by keyboard (focus opens it) and touch (tap opens it). |
| Ferrofluid nav | `assets/js/core/nav-ferro.js` | Ferro only. Drawn on a canvas and animated only while the cursor is near. |
| Motion | `assets/js/core/motion.js` | Spring easing through CSS `linear()` curves. Charts reveal via an IntersectionObserver: lines draw through a clip scaled by transform, surfaces rise and numbers count up. Everything pauses off-screen or in a hidden tab, and reduced motion shows the end state. |
| Charts | `assets/js/core/charts.js` | SVG painted from theme tokens. Candles are always green up and red down, with the price axis on the right. |
| Icons | `assets/js/core/icons.js` | Original glyphs on layered squircles (a base gradient, an inner highlight, a soft shadow), with dark-mode versions. They are not Apple's icons or SF Symbols. |
| Themes | `assets/js/themes/<name>.js` + `assets/css/themes/<name>.css` | Each theme has its own layouts built on the shared blocks and tokens. |

## Decisions made without you (also listed in MORNING_REPORT.md)

1. **The pricer runs in Python behind a local server, not inside the browser.** Running it in the browser would mean either rewriting it in JS or downloading about 30 MB of Pyodide (numpy, scipy and pandas) on every load. The Worker still keeps pricing off the page thread. This matches the earlier Vercel plan of a Python function.
2. **"Instrument" is design 09, Oscilloscope.** The design log calls it "Instrument, blue". "Amber" is design 01.
3. **Springboard and Glass use the system font** (SF Pro on the Mac), with fallbacks. The other themes use their design fonts, saved into `website/assets/fonts` so the demo works offline.
4. **Trading's purple is replaced by a steel blue**, chosen when that theme is built and recorded in PROGRESS.
5. **Line-draw animations use a clip rectangle scaled by `transform`**, not `stroke-dashoffset`, to keep to transform and opacity.

## Order

1. The plan and PROGRESS file.
2. The foundation: server, data export, shell, state, switch and menu, both navs, motion, model worker, charts and blocks, icons.
3. Springboard, Glass, then Ferro, each finished and checked in light and dark before moving on.
4. Amber, then Instrument and Trading.
5. Polish, then MORNING_REPORT.md.

Each theme is checked by screenshots of every page in light and dark at 1440 and 1280×720, with a console check, a link check and an fps probe in Chrome. Safari can't be automated here, so the code sticks to features Safari supports (`-webkit-backdrop-filter`, View Transitions with a fallback).
