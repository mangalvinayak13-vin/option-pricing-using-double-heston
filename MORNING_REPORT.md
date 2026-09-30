# Morning report: the Double Heston website

## Run it (one command)

```
python3 website/serve.py
```

Then open **http://localhost:8765**. Run the command from the project folder (the `complete-training` worktree), on branch `night-build`.

- It uses the Python you already have: numpy, scipy and pandas are already needed by the pricer. Nothing new is installed.
- Keep the terminal open while presenting. The model page reprices through this server.
- To open any theme directly: `http://localhost:8765/?theme=ferro&mode=dark`. The themes are springboard, glass, ferro, amber, instrument and trading, and the modes are light and dark. Any page works, for example `model.html?theme=glass&mode=light`.

## What to look at first

1. **Ferro, light mode, Home.** This is what first-time visitors get.
   - Scroll to "Two factors, live": two pools of clear water turn into black spiking ferrofluid.
   - Move your cursor to the right edge to see the ferrofluid nav reach toward it.
2. **Theme menu.** Hold the switch at the top right for half a second, or right-click it. Pick another theme and the page changes in place.
3. **The model page** (`model.html`). Move a slider and the price, Greeks, option chain and smile reprice live. The numbers come from the project's own pricer.
   - In Ferro, each slider group has a pool that reacts to κ and ξ as you move them.
4. **The finding page in Ferro.**
   - "Same surface, different magnets" uses a real Bharti Airtel surface fitted twice.
   - Two equally good fits disagree about the one-year option by 11.7 volatility points.
5. **Glass in dark mode, then Springboard in light mode.**

## Which theme to open the presentation with: Ferro

Ferro's visuals show the model itself:

- **The two factors:** each is a pool of ferrofluid driven by its real settings. The fast one (κ 5) reacts and settles quickly, the slow one drifts, and a bigger ξ gives bigger spikes.
- **The finding:** shown literally, as one surface raised by very different "magnets". The data is real, not illustrative.
- **The projector:** in light mode its near-black type on light grey keeps strong contrast.

Glass is the most polished Apple look and a great second screen, but it could be any product page. Springboard is the friendliest, and good for a walk-through of the site's pages.

## What's finished

All six themes have all eight pages (Home, Market, The model, How it works, The finding, About, Team, References), in light and dark. Every theme shows exactly the same information and links. That was your request during the night, and it's enforced by one shared content file, `website/assets/js/core/pages.js`.

| Theme | Its look | Checked |
|---|---|---|
| **Springboard** | iPhone home screen: widgets with continuous corners, layered Apple-style icons with proper dark versions, an app grid, a frosted dock that magnifies under the cursor | 8 pages × 2 modes, interactions, fps |
| **Glass** | Apple product page: huge centred headlines, frosted tiles over soft coloured light, a glowing curve that bends from flat Black–Scholes into the smile | same |
| **Ferro** | Chrome and liquid black: brushed-chrome hero with one light sweep, 3D ferrofluid spikes, the ferrofluid side nav, factor pools tied to κ and ξ, quiet dividers | same |
| **Amber** | Precision instrument: a `$` query prompt answered by two large readouts, square channel panels, heavy Schibsted numerals | same |
| **Instrument** | Lab oscilloscope: every chart in a dark scope screen with phosphor traces, modules with status lights, a live scope in the hero | same |
| **Trading** | Broker terminal: dense panes on 1-px seams, condensed numerals, azure accent (the purple is gone) | same |

**Shared by every theme**

- **Switch:** the macOS-style light/dark switch at the top right.
  - Click it to toggle light and dark.
  - Hold it for about half a second and the knob swells into a glass lens, then an Apple-style menu of the six themes opens without flipping the switch. Right-click or ArrowDown also open it, the menu works with arrow keys and Enter, and Esc or a click outside closes it.
- **Remembered choices:** the theme and mode are remembered across pages and visits. The first visit follows the Mac's light/dark setting, and there's no flash of the wrong theme.
- **Side nav:** magnetic dashes in five themes, the ferrofluid nav in Ferro. They animate only while the cursor is near, and work with the keyboard (Tab) and on touch.
- **Motion:**
  - Charts draw in when scrolled into view and numbers count up.
  - The flat line bends into the smile.
  - The fast factor jitters while the slow one drifts; this is the model's own variance equation, simulated live.
  - Buttons press, cards lift, and a light follows the cursor.
  - With reduced motion on, everything shows its end state.
- **Speed:** nothing animates off-screen or in a hidden tab, the ticker included.
- **Ticker:** a seamless loop of NSE closes plus the model's own outputs: the ₹600.40 model price, the Monte Carlo check and the half-lives.
- **Real data only:** NSE bhavcopy, the verified research outputs and the project's pricer. There's no lorem ipsum and no invented numbers.

**Checks run on the final build (all pass)**

- **Interaction test** (`sh website/tools/test_all.sh`): 22 checks per theme with real mouse and key events in Chrome. It covers:
  - the switch, the hold menu and the keyboard theme pick;
  - that a theme change keeps a slider value;
  - live repricing and the side nav;
  - no console errors;
  - 60 fps while the nav animates, at rest and while scrolling.
- **Parity** (`python3 website/tools/parity.py`): the same sections, numbers, charts and links in all six themes, on all eight pages.
- **Console sweep** (`sh website/tools/console_all.sh`): all 48 page-and-theme combinations render with no console messages.
- **Overflow** (`node website/tools/overflow.mjs 390`, then `1280`): no page overflows sideways at phone width or at projector width.
- **Projector:** the top three themes fit their headline and buttons on the first 1280×720 screen.
- **Model numbers:** the server reproduces the published ₹600.40, IV 19.87%, delta 0.583 and Monte Carlo ₹597.10 ± 3.56.

## Decisions I made without you

1. **Pricing runs your Python pricer, unchanged, behind a small local server, not inside the browser.** `legacy_streamlit_site/models.py` needs numpy, scipy and pandas. In the browser that means either rewriting it in JavaScript, which you ruled out, or loading about 30 MB of Pyodide on every visit. The browser side still uses a Web Worker that debounces, cancels stale requests and caches. A full reprice with Monte Carlo takes about 30 ms, which also matches the earlier Vercel plan of a Python function.
2. **"Amber" is design 01, and "Instrument" is design 09 (Oscilloscope),** which the design log calls "Instrument, blue".
3. **Trading's new colour is azure,** #2F6FE0 in light and #4C8DF6 in dark. It reads as a trading desk (Kite and TradingView use it), leaves green and red for up and down, and doesn't clash with Amber's gold.
4. **Springboard and Glass use the Mac's system font (SF Pro).** The other themes' Google Fonts (open licence) were **downloaded** into `website/assets/fonts/`: 29 files, 475 KB. The demo therefore works offline. Nothing was installed.
5. **Ferro is the first-visit theme** (see above).
6. **The Bharti Airtel "fitted twice" example comes from re-running the research's own multi-start fit on one surface,** without changing any research code. It reproduced the saved result exactly: 6 equally good fits, dispersion 4.636. That's the median of all surfaces, so it's the typical case. Fit B's two speeds sit at the fit's search limit, and the page says so.
7. **Content corrections made along the way:**
   - The surface caption wrongly said short-dated options far from today's price carry the most volatility. Low strikes do, with the tilt steepest at short expiries, and the caption now says that.
   - I removed "pinned/loose" labels I had added to the six-fits chart, because they came from my own threshold rather than from the research.
   - References are now numbered 1 to 13 across groups.
8. **The equations are typeset with MathML,** which Safari and Chrome render natively.
9. **Motion exceptions to "transform and opacity only":** SVG line-draws use `stroke-dashoffset`, and count-ups change text. Both are cheap and measured at 60 fps. Glass's glowing curve fades in after the bend settles rather than re-blurring on every frame.
10. **Model page scope:** the data covers the NIFTY 27 Oct 2026 expiry, so the underlying and expiry are shown as fixed. The strike and call/put are selectable across the real chain.
11. **Safety commit:** the design canvases and the small research scratch outputs were committed. The big generated screenshots and PDFs are git-ignored and still on disk.

## Your requests during the night (all done)

- **Dark mode control like macOS:** a macOS-style switch, blue when on. You then said to keep the toggle.
- **The same information in every theme:** one shared content file plus the parity check.
- **Remove your GitHub link:** removed from the footer, About and the content.
- **Ferro spikes with no 3D:** every spike is now shaded like a glossy cone lit from one side, with a specular streak, a bright tip and a contact shadow.
- **Ferro dividers too loud:** they're now a hairline with a small shaded bead.

## Unfinished, or worth knowing

- **Team page:** it still has the placeholders from the content file ("[Name]", "[Role …]", "[Event] at [College]"). Real names are needed.
- **Explainer video:** the slot is ready. Put the file in `website/assets/video/`, set `VIDEO_SRC` in `website/tools/content.py`, and run `python3 website/tools/export.py`. Until then, clicking the slot explains this.
- **Safari wasn't tested automatically.** The only automated browser here is Chrome. The code sticks to features Safari supports: `-webkit-backdrop-filter`, MathML, View Transitions (Safari 18) with a crossfade fallback. Please click through once in Safari before the talk.
- **Frame rates were measured in headless Chrome,** which draws in software. A real MacBook Air uses its GPU and should do at least as well. The only slow frames seen, 33–50 ms, were one-offs as charts first appear.
- **Squircle card corners** use `corner-shape`, which only newer Chrome supports. Safari shows ordinary rounded corners.
- **No live Upstox data yet:** the site shows NSE closes from 25 Sep 2026 and says so. The ticker reads "Close 25 Sep 2026", and the header status in Ferro, Amber and Trading says "Market closed". Wiring Upstox, with the token server-side, is still to do.
- **Not changed or published:** the model's maths and `designs/` are untouched. Nothing was pushed, merged, deployed or published.

## How to get back to the old version

- The website is a new folder, `website/`, and NIGHT_PLAN.md, PROGRESS.md and this report are the only new top-level files. Nothing that existed before was edited except `.gitignore`, which gained a few lines for generated screenshots and PDFs.
- Everything from tonight is on branch `night-build`. The state before tonight is commit `ae9dd2c` on `worktree-complete-training`. To go back: `git switch worktree-complete-training`.
- To see everything tonight changed: `git diff ae9dd2c night-build --stat`.

## Files

- `website/serve.py` is the one command. It runs the static site plus `/api/price`, backed by the unchanged pricer.
- `website/assets/js/core/pages.js` is what every page says, shared by all themes.
- `website/assets/js/themes/*.js` and `website/assets/css/themes/*.css` hold each theme's own layout and look.
- `website/tools/` holds the content export, fonts, page shells and the checks: `check.py`, `shots.py`, `parity.py`, `interact.mjs`, `scrollfps.mjs`, `overflow.mjs`, `test_all.sh` and `console_all.sh`.
