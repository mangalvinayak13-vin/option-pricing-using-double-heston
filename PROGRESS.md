# Night build progress

The site lives in `website/`. Run it with `python3 website/serve.py` and open http://localhost:8765.
Work happens on branch `night-build`; the restore point is `ae9dd2c` on `worktree-complete-training`.
NIGHT_PLAN.md has the architecture.

| Step | Status | Notes |
|---|---|---|
| Plan and progress files | done | |
| Foundation | done | `9ab2044` |
| Springboard | done, checked | `12da8a4`, `b9ae32a`; 8 pages checked in light and dark; interaction test 22/22 |
| Shared content spec | done | `core/pages.js`; `tools/parity.py` OK across 8 pages × 6 themes |
| Glass | done, checked | `0049421`; Apple product-page bands, frosted tiles, glowing bend |
| Ferro | done, checked | `1ae91f6`, `6fbc57d`; 3D ferrofluid spikes, quiet dividers, factor pools tied to κ and ξ |
| Amber | done, checked | `738d70b`; query prompt with readouts, channel panels |
| Instrument | done, checked | Committed with `6fbc57d`; oscilloscope screens with phosphor traces |
| Trading | done, checked | `fd9b8c7`; azure accent replaces purple |
| Polish and morning report | done | `c65f690`, `6cebb3f`; Ferro is the default; keyboard order; video slot; overflow check; MORNING_REPORT.md |

## Your requests during the night

- **Dark mode control like macOS:** it is now a macOS-style switch (blue when on, flatter track, hairline edge) and still has the hold-for-themes menu. You then said to leave the toggle as it is for now.
- **Same information in every theme:** all page content now comes from one file, `website/assets/js/core/pages.js`. Themes only change presentation. `python3 website/tools/parity.py` compares sections, numbers, charts and links across all six themes. Section keys are the same everywhere, so a theme switch lands on the same section.
- **GitHub link removed:** it's gone from the footer, from About and from the content file.
- **Ferro "no 3D effect in the spikes":** every spike (pools, side nav, spike charts) is now shaded as a cone lit from one side, with a specular streak, a bright tip and a contact shadow.
- **Ferro "connected spikes are loud":** the full-width spike ridges became a hairline with a small shaded bead.
- **Nav canvas bug:** the shared `canvas { max-width: 100% }` rule squeezed Ferro's nav canvas to 72 px. It's fixed, so the spikes now reach the cursor.

## Checks

- `python3 website/tools/check.py`: every page renders, with console messages printed.
- `python3 website/tools/shots.py <theme> [page] [mode] [720]`: screenshots in `website/.shots/` (git-ignored).
- `node website/tools/interact.mjs <theme>`: real pointer and key events via the DevTools protocol, covering the switch, hold menu, keyboard theme pick, repricing and the nav, plus fps and console errors.
- `python3 website/tools/parity.py`: content parity across themes.

## Log

- Saved the design canvases and outputs in commit `ae9dd2c`, then created the `night-build` branch.
- Foundation: `serve.py` wraps the unchanged pricer and reproduces ₹600.40, IV 19.87%, delta 0.583 and MC ₹597.10 ± 3.56. The theme menu, both navs, motion, the model worker, charts and icons are in place.
- Springboard review fixes:
  - Surface caption corrected: low strikes carry the most volatility, not "short-dated far from price".
  - Equations are typeset in MathML.
  - iOS-style sliders, and slider steps chosen so the default settings sit on the step grid.
  - Count-up no longer overwrites repriced values after a theme change.
  - Stocks-style watchlist.
  - The misleading "pinned/loose" labels were removed from the six-fits chart.
  - References are numbered continuously.

## If this session stops

1. Read NIGHT_PLAN.md and this table.
2. `git log --oneline night-build` shows the last milestone.
3. The next step is the first row that isn't marked done.
4. Build each remaining theme with `renderPage()` from `core/layout.js`, so the content stays identical.
