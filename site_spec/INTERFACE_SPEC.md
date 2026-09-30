# Interface spec — Double Heston site (Vercel rebuild)

The screens for everything below are on the design canvas, page **"Site — amber"**:
https://claude.ai/artifact/FUnKgXnWeTrJiMhjqhQZDQ (private until shared from its Share
menu). The visual source of truth is the board **"C × D · Instrument, amber,
Schibsted"**. Where this spec and a screen disagree, this spec wins on behaviour and the
screen wins on look.

## 1. What the site is

A site about one model — **Double Heston** — and one finding: it fits option prices
almost perfectly, yet its ten parameters can't be recovered from those prices.
Black–Scholes and Heston appear only as lineage in the introduction. Live market data
from Upstox shows the model against today's real prices.

## 2. Pages

Navigation, on every page: `rw/ws instrument` · `[01] market` · `[02] the model` ·
`[03] the finding` · `[04] about` · status chip (section 4). The current page's nav
item uses the accent colour and `aria-current="page"`.

### Home
- **Live ticker banner**, pinned above the nav. Each item: symbol, last price, change %
  with ▲ or ▼. Direction is never shown by colour alone. Scrolls continuously; pauses on
  hover and keyboard focus; becomes a static, horizontally scrollable row under
  `prefers-reduced-motion`. Each item links to that symbol on `[01] market`.
- Hero: `$ query` → "Does letting volatility move like a physical random process price
  options better?" → "Yes. Then it stops being able to tell you why." → buttons *run the
  model*, *read the finding*, *live market*.
- Four readouts: Lineage 2009 · Factor S κ 0.5 · Factor F κ 5.0 · Params 10.
- Smile chart: Double Heston vs constant volatility at the starting values, 30 days.
  **Static and labelled as an illustration** — Double Heston is never fitted live.
- Finding strip: 1.80 · 99% · 4.64×.

### [01] Market — live equity
- **Watchlist** (all universe symbols, section 3): symbol, last, change %, sparkline;
  search box; selected row highlighted.
- **Chart panel** for the selected symbol: last price and change; `line | candles`
  toggle; intervals `1m | 5m | 15m` (today) and `1D` (6 months); OHLC readout for the
  hovered candle; volume bars (indices publish no volume — say so, don't draw zeros).
  Candles: hollow = closed higher, filled accent = closed lower (shape, not just colour).
- **Stats row**: open, high, low, previous close, and a link to price its options on
  `[02]`.
- Equity only. Option quotes live on `[02]`.

### [02] The model — Double Heston with live options
Top to bottom:
1. **Inputs**: underlying (universe list), expiry (only real listed expiries),
   strike (step = the contract's strike interval), call or put.
2. **Three results**: *Double Heston price* (formula) with the Monte Carlo check
   underneath ("20,000 paths: ₹x ± y"); *market mid · live* (from bid and ask);
   *gap* = model − market, in ₹ and %.
3. **Live contract**: bid, ask, last traded, volume, open interest, updated time.
4. **Option chain around the money**: ±5 strikes; call last, call IV, strike, put IV,
   put last; the chosen strike highlighted.
5. **Smile chart**: Double Heston curve against live market implied volatilities —
   filled dots for bid/ask mids, hollow for last trades — with the chosen strike marked.
6. **Ten sliders** in two groups (Factor S · slow, Factor F · fast), each with its
   current value, and a per-factor Feller readout ("Feller fails: 2κθ 0.02 < ξ² 0.09").
   Ranges from `HESTON_BOUNDS`. *Reset to starting values*.
7. **Greeks**: delta, gamma, vega (per vol point), theta (per calendar day), rho (per
   rate point) — Black–Scholes Greeks at the volatility implied by the Double Heston
   price, as the old site did.
8. One line: no calibrate button, and why, linking to `[03]`.

Starting values (the old Pricing page's Double Heston defaults): each factor starts
with half of today's variance and half of the long-run variance; κ = 5.0 / 0.5,
ξ = 0.5 / 0.3, ρ = −0.7 in both. At typical values **both factors fail Feller**; the
simulator's full-truncation scheme keeps prices valid, and the page says so.

### [03] The finding
1. `fit(prices) ≈ exact` / `recover(parameters) = no`, one-paragraph summary.
2. **Proof 1, simulated surfaces**: price match 9.16e-08 · recovery skill 1.80 ·
   tightest 49 fits 1.85 · neural network 0.80 (fits prices worse, recovers better).
3. **Proof 2, real NSE surfaces**: 99% · 4.64× · 40 stocks × 60 days, 16 starts each;
   the dispersion histogram (n = 2,379, with the 1.0 "unrelated stocks" line and the
   median).
4. **One stock** (select any of 210): price error by date beside the ten standardised
   parameters by date; market rank; fitted-parameter table folded below.
5. **Held-out check**: network 17.4% · best possible 4.3% · gap +10.8 points.
6. Folded: "Three bugs we found and fixed before trusting any of this".

Every number here must come from the exported research files (section 6), never typed in.

### [04] About
Method and data · limits · the NotebookLM video (poster frame with a real `<button>`) ·
also explored: volatility forecasting · team · references · GitHub link.

## 3. The universe

One list drives the banner, the Market watchlist and the model's underlyings, so
anything with an implied volatility on the site also has live equity and option
prices: **NIFTY 50, NIFTY BANK, and the 40 most liquid F&O stocks from the ambiguity
study** (`outputs/ambiguity/ambiguity_surfaces.csv`, column `ticker`).

Upstox instrument keys: indices are `NSE_INDEX|Nifty 50` and `NSE_INDEX|Nifty Bank`
(already in `legacy_streamlit_site/utils.py`). Stocks need their `NSE_EQ|<ISIN>` keys,
and options their F&O keys, from Upstox's instrument master file — build the map once
at deploy time, not per request.

## 4. Data states

Designed on the "Data states" board. Every live element must handle all five.

| State | When | Chip | Banner |
|---|---|---|---|
| Live | market open, feed healthy | ■ "Live, updated 09:42:15" | normal, updating |
| Market closed | outside 09:15–15:30 IST, weekends, NSE holidays | □ "Market closed, last close 30 Sep 15:30" | last close, "close" instead of change |
| Saved snapshot | feed or token failure, or visitor chose it | ■ grey "Saved snapshot, 30 Sep 09:05" | "snapshot" tag, no change arrows |
| No market data | no feed and no snapshot | □ "No market data" | one line: prices will appear when the feed reconnects |
| Loading | first fetch only | — | skeleton bars, no spinners over numbers |

Rules: never show `nan`, `NaN`, `undefined`, or a bare dash where a sentence belongs.
The model still prices from the visitor's inputs when there is no market data. A
snapshot is never labelled live. Market status and holidays should come from Upstox's
Market Information APIs, not a hard-coded calendar.

This fixes a real risk in the old site: its home page fitted Heston with no
minimum-quote check, and with an empty chain the headline would have read "nan× closer".

## 5. API contract (Python functions on Vercel)

All Upstox calls happen on the server. The browser only calls our own endpoints.

| Endpoint | Upstox source | CDN cache (`s-maxage`) |
|---|---|---|
| `GET /api/ticker` | Market Quote, **all universe symbols in one batched request** (full quote: last price, change, OHLC, volume) | 5 s |
| `GET /api/quote?symbol=` | served from the `/api/ticker` cache — no extra Upstox call | 5 s |
| `GET /api/candles?symbol=&interval=` | Historical Data v3: intraday `/historical-candle/intraday/{key}/minutes/{1,5,15}` (today) and historical `…/days/1` (6 months) | 60 s intraday, 1 h daily |
| `GET /api/expiries?underlying=` | Option contracts | 1 h |
| `GET /api/chain?underlying=&expiry=` | Option Chain | 15 s |
| `GET /api/price?…` | project pricer (section 7), no Upstox call | none |

Responses use `Cache-Control: public, s-maxage=N, stale-while-revalidate=2N`, so every
visitor shares one upstream request per window — visitor count does not multiply
Upstox calls.

**Rate budget** (Upstox standard limits: 50/s, 500/min, **2,000 per 30 min**), per
30 minutes:
- ticker: 1 request / 5 s = **360**
- chain: 1 / 15 s = 120 per active (underlying, expiry); assume 3 active = **360**
- candles: 1 / 60 s = 30 per active (symbol, interval); assume 10 active = **300**
- expiries and daily candles: negligible
- **Total ≈ 1,020 — about half the 30-minute limit.** Check the per-request instrument
  limit in the Market Quote docs; 42 symbols per batch is well within typical limits.

**Streaming**: not used. Vercel functions can't hold WebSocket connections, and
per-visitor sockets would also run into Upstox's per-user connection limit. Polling
through the cache above is enough for a price banner.

## 6. Research data (static, exported at build time)

| File | Feeds |
|---|---|
| `outputs/consolidated_results.json` | [03] proof 1, held-out check |
| `outputs/ambiguity/ambiguity_summary.json` | [03] proof 2 headline numbers |
| `outputs/ambiguity/ambiguity_surfaces.csv` | [03] histogram (use rows with `price_equivalent_count > 1`, n = 2,379), universe list |
| `outputs/market_wide/market_wide_surfaces.csv` | [03] one-stock panels; pre-aggregate per ticker (the raw file is 3.4 MB) |

Do **not** use `web_outputs*/` — those are exports from before the three bug fixes.

## 7. Reuse — don't rewrite the maths

- **Pricing**: `legacy_streamlit_site/models.py` — `double_heston_price`,
  `double_heston_paths`, `price_from_paths`, `implied_vol`, `greeks`,
  `feller_condition`, `HESTON_BOUNDS`. Guarded by `legacy_streamlit_site/tests/test_models.py`
  (28 passing) and `video_report/demo_risk_check.py` (0 issues across every reachable
  input). Keep pandas out of the pricing function if the bundle gets tight.
- **Upstox access**: `legacy_streamlit_site/utils.py` — `_upstox_get`,
  `_upstox_chain_to_frame` (already survives empty far-out-of-the-money legs),
  `market_implied_vols` (out-of-the-money quotes only, ₹0.05 floor, bid/ask mid
  preferred over last trade).
- **Snapshot**: `legacy_streamlit_site/snapshot.py` — same capture logic, written as JSON
  instead of pickle. Recapture it the morning of the exhibition.
- Rate: 5.3324% (RBI 91-day T-bill, 2026-07-15), the same rate the research uses.

## 8. Token

Use Upstox's **Analytics Token**: free, read-only (GET only, can't place orders), valid
**one year**, and it covers Market Quote, Historical Data, Option Chain and Market
Information. Generate it from the Analytics tab of the Upstox developer console and
store it as the Vercel environment variable `UPSTOX_ACCESS_TOKEN` — server-side only,
never sent to the browser. Write its expiry date on the team calendar the day it is
created. (A normal Upstox token expires at 3:30 AM every day and would need a login each
morning.)

## 9. Design tokens

| Token | Value |
|---|---|
| Background | `#0F100E` |
| Raised surface / inputs | `#151612`, selected row `#1A1B17` |
| Hairline | `#2A2B27`, faint grid `#1E1F1B` |
| Text | `#E9E6DD`; secondary `#8F8C83`; body on dark `#B8B5AC` |
| Accent (one) | `#F0B24A` |
| Up / down | `#6FCF97` ▲ / `#EB7A6F` ▼ — always with the glyph |
| Typeface | Schibsted Grotesk (Google Fonts) 400/500/700/900; tabular figures everywhere numbers align |
| Type | hero 70/1.02 w700 −0.035em; page title 48 w700; big numerals 56–80 w900 −0.04em; section label 13 w700 uppercase; body 15–20 |
| Layout | 1440 desktop, 64 px side padding, 12-column grid, square hairline panels, no rounded corners |

## 10. Accessibility and responsiveness

- Real `<button>`, `<a href>`, `<select>`, `<input>` with `<label>` everywhere.
- Visible focus rings; the banner pauses on focus.
- `prefers-reduced-motion`: no scrolling banner, no animated number changes.
- Charts get an `aria-label` describing the shape, and each has a table view.
- Text contrast ≥ 4.5:1 (secondary `#8F8C83` on `#0F100E` passes).
- Desktop is the exhibition target; below 1024 px, panels stack to one column and the
  banner becomes a scrollable row.

## 11. Risks

- **Market-data redistribution.** Showing real-time NSE prices on a public website may
  breach Upstox's and NSE's terms. Check before making the site public; options include
  restricting access to the exhibition or showing clearly delayed data.
- **Vercel Python bundle size** (250 MB unzipped limit) with numpy and scipy — measure
  early.
- **Exhibition outside market hours**: visitors will see the "market closed" state;
  recapture the snapshot that morning so it's recent.
- **Token expiry** after one year.
