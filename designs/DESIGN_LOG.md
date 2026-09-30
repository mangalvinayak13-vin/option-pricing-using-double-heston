# Design log — 20 whole-site designs for the Double Heston site

Status: **PLAN, awaiting approval** (step 1 of the brief). Nothing below is built yet.

## Pages (every design builds all six)

| # | Page | What it holds |
|---|------|---------------|
| 1 | Home | Live-price banner, the question, the smile, the two factors, the finding in one line, links |
| 2 | Market | Watchlist of the 42-stock universe, daily candlesticks (green up / red down), volume, OHLC |
| 3 | The model | Pricer (underlying, expiry, strike, call/put, ten settings), Double Heston price vs market, option chain, smile vs market IVs, Greeks |
| 4 | How it works | The maths: the two variance SDEs, Feller condition, characteristic-function pricing, Monte Carlo check, lineage (1973 / 1993 / 2009) |
| 5 | The finding | 99% of 2,400 surfaces ambiguous, 3.9× random, per-parameter bars, histogram, pick-a-stock by day, synthetic 1.80, held-out 17.4% vs 4.3% |
| 6 | About | Explainer-video slot (MP4 later), method and data, limits, team, references, source link |

Data states (live, market closed, snapshot, no data, loading) live inside each page, not as a page.

## Shared pieces (designs/shared/)

- `magnet-nav.js/.css`: the ferrofluid rail. Canvas sized to the rail only, rAF loop runs only while the pointer is within range, keyboard focus opens it, touch gets a tap handle, reduced motion becomes a fade. Themed per design with CSS custom properties.
- `glass-switch.js/.css`: the iOS 26 Liquid Glass light/dark switch, top-right on every page. Real `role="switch"`, Space/Enter, focus ring, drag + click, lens refraction via SVG displacement filter (Chrome) with a backdrop-blur + specular fallback (Safari), no-flash theme boot script in `<head>`.
- `model.js`: one helper for all model numbers. It calls the local server, which imports `legacy_streamlit_site/models.py` unchanged; sliders are debounced; results are cached so recolouring never re-runs the model.
- `data/*.json`: exported once from verified outputs (`outputs/ambiguity/*`, `outputs/consolidated_results.json`, `outputs/g8/*`) and from the NSE bhavcopy files (62 trading days, 1 Jul–25 Sep 2026: real daily OHLC and real option chains).
- `serve.py`: static files + `/api/price`, `/api/smile`, `/api/paths` (Python stdlib server; uses the numpy/scipy already installed). One command: `python3 designs/serve.py`.

## The 20 concepts

Colours are light theme / dark theme (bg, ink, accent). Full palettes are in each design's section once approved.

| # | Name | Source | One-line concept | Light (bg / ink / accent) | Dark (bg / ink / accent) | Type |
|---|------|--------|------------------|---------------------------|--------------------------|------|
| 01 | Amber Instrument | sample: chosen board + Site screens | A precision instrument: bracketed readouts, `$ query` hero, hairline panels | #F3F2EE / #16170F / #A8680A | #0F100E / #E9E6DD / #F0B24A | Schibsted Grotesk |
| 02 | Front Panel | sample: Home layout 1 | Chart-led editorial: question left, the smile as a big figure right | #F4F5F0 / #111311 / #1B6B50 | #0F1311 / #E9EEEA / #4FD1A5 | Bricolage Grotesque + Geist |
| 03 | Trading Desk | sample: Home layout 2 | A broker terminal: price and candles as hero, option ticket and chain beside it | #F5F6F8 / #14171A / #6A4DFF | #0B0E11 / #EAECEF / #9B87FF | Barlow + Barlow Condensed |
| 04 | Springboard | sample: Home layout 3 | iPhone home screen: widgets of mixed sizes, squircle app icons as navigation | #F2F2F7 / #1C1C1E / #FF9500 | #000000 / #F5F5F7 / #FF9F0A | Figtree |
| 05 | Sidebar | sample: Home layout 4 | A macOS app: coloured-squircle sidebar, watchlist, grouped settings lists | #FFFFFF / #1D1D1F / #D70F44 | #1E1E20 / #E8E8ED / #FF375F | Manrope |
| 06 | Long Read | sample: Home layout 5 | An essay with margin notes; live numbers woven into sentences | #FFFFFF / #1A1A1A / #9E1B32 | #121412 / #E6E8E3 / #FF6B81 | Newsreader + Public Sans |
| 07 | Journal | sample: B · Journal | A physics paper: numbered figures and equations, two-column abstract | #FAF8F3 / #1F1D19 / #2D3A87 | #16151A / #ECE8DF / #9AA6FF | Source Serif 4 |
| 08 | Apothecary | sample: A · Apothecary (+ phone) | Skincare-label calm: one quiet figure per screen, lots of air | #ECEDE8 / #22251F / #6E7F5E | #1B1D19 / #E4E6DF / #9DB08A | Hanken Grotesk |
| 09 | Oscilloscope | sample: C · Instrument, blue | Lab instrument: trace grid, phosphor lines, knob-like controls | #F4F7FA / #0F1419 / #1F6FB8 | #0F1419 / #E4E9EE / #7FB2E5 | IBM Plex Sans + Plex Mono |
| 10 | Swiss | sample: D · Swiss grid | Strict 12-column grid, giant numerals, one red | #FFFFFF / #121212 / #D9401A | #111111 / #F2F2F2 / #FF5A2E | Instrument Sans |
| 11 | Glass | samples: all six Apple-inspired boards | Apple product page: huge type, frosted panels, one scroll-driven reveal of the two factors | #FFFFFF / #1D1D1F / #0071E3 | #000000 / #F5F5F7 / #2997FF | Albert Sans |
| 12 | Two Clocks | new | The slow and fast factors as two dials; half-lives shown as clock hands | #EDEFF7 / #141B34 / #E63946 | #0B1024 / #E8ECFA / #FF6B6B | Unbounded + Karla |
| 13 | Brownian | new | Randomness as the visual language: a fan of real simulated paths from the model's Monte Carlo | #FFFFFF / #121212 / #C2187A | #0D0B14 / #EDEBF5 / #FF5CB8 | Syne + Work Sans |
| 14 | Blueprint | new | Engineering drawing: linework, dimension callouts, equations as annotations | #F4F8FF / #0A2A66 / #1F5FD1 | #0A2A66 / #E8F0FF / #FFD54A | Archivo + Archivo Narrow |
| 15 | Ferro | new | Chrome and glossy black liquid everywhere, echoing the magnet nav; monochrome | #E9EBEE / #0A0A0A / #0A0A0A | #050505 / #F2F2F2 / #D9DCE1 | Sora + Epilogue |
| 16 | Surface | new | The implied-volatility surface (strike × maturity) as a heat grid is the hero and colour system | #F7F7F5 / #1B1B1B / viridis ramp | #0E0E12 / #EDEDED / viridis ramp | Outfit |
| 17 | Lab Notebook | new | Graph paper, red-pen annotations on every chart, equations centre stage | #FDFDF8 / #1C2A39 / #D1495B | #10151C / #DCE6F0 / #FF7A8A | Crimson Pro + Caveat |
| 18 | Order Book | new | Options-market microstructure: the page is a bid/ask ladder, the chain is the hero | #FFFFFF / #111418 / #111418 (+ green/red) | #111418 / #E8E8E8 / #FFFFFF (+ green/red) | Chivo + Chivo Mono |
| 19 | Probability | new | The model's price distribution (fat left tail) as the hero; sliders reshape it | #FAFAFA / #202124 / #0F8F9B | #121016 / #ECE6F5 / #4DD8E3 | Gabarito + Rethink Sans |
| 20 | Exhibition Poster | new | Built for the projector: one idea per screen, giant type, full-bleed colour blocks | #FFE14D / #111111 / #1D3FE0 | #111111 / #FFE14D / #4D6BFF | Big Shoulders Display + Rubik |

Up/down colours are standard green/red in every design (tuned per theme for contrast); candles are always green up, red down.

## Generic-look budget (at most one design each)

- Cream + serif: 07 Journal only (indigo accent, not terracotta; its concept is a physics paper).
- Near-black + one bright accent: 01 Amber Instrument only (the look you chose).
- Hairline newspaper grid: 10 Swiss only.
- Rounded cards: 04 Springboard only (widgets are the concept).
- Monospace labels: 09 Oscilloscope only (18 uses mono for price digits in the ladder, not labels).
- No ALL-CAPS eyebrow labels anywhere.
