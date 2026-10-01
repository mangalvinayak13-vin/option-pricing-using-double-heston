# Progress — 20 whole-site designs (as design artifacts)

Format changed by the user on 2026-09-30: web **designs as artifacts**, not working web pages.
Pages per design: 8 (Home, Market, The model, How it works, The finding, About, Team, References)
plus a Components board (magnet rail states, Liquid Glass switch, icons, type, palettes).
Each design is its own Design-canvas artifact; every board has a light/dark `dark` tweak and a
working switch in Play; the magnet rail links the boards.

| # | Design | Artifact | Status |
|---|--------|----------|--------|
| 01 | Amber Instrument | https://claude.ai/artifact/FiQSei1BZiB1N7VBCHRLTX | Published, 9 boards, checked in both themes |
| 02 | Front Panel | https://claude.ai/artifact/AMMxRjAXWqqr8WGVToToqY | Published, checked |
| 03 | Trading Desk | https://claude.ai/artifact/RgTPAHRiUf7B6dMwkZB7Xk | Published, checked |
| 04 | Springboard | https://claude.ai/artifact/H5izAFpGNNccumncPHJ4rQ | Published, checked |
| 05 | Sidebar | https://claude.ai/artifact/Engv1p1JmaJo71NiSGJPLr | Published, checked |
| 06 | Long Read | https://claude.ai/artifact/4CbczVqdW9JzNt6AAraJ7R | Published, checked |
| 07 | Journal | https://claude.ai/artifact/8L5AiGZ74Ds61UeA4DiLWp | Published, checked |
| 08 | Apothecary | https://claude.ai/artifact/1DAzvLaDQBSKeQrT3RKugW | Published, checked |
| 09 | Oscilloscope | https://claude.ai/artifact/FQdcQ5g3A3JbxcszNKhyPE | Published, checked |
| 10 | Swiss | https://claude.ai/artifact/QNB2GqNn7HLy9igmrQNAso | Published, checked |
| 11 | Glass | https://claude.ai/artifact/59JAuzAHFfGymsth23UppX | Published, checked |
| 12 | Two Clocks | https://claude.ai/artifact/9CCDnSmqEUFn49oahzraXQ | Published, checked |
| 13 | Brownian | https://claude.ai/artifact/Kf4Trk48VDwuiWi1Hjtiyg | Published, checked |
| 14 | Blueprint | https://claude.ai/artifact/4nnnWAXArYNQ44dZHFgDe5 | Published, checked |
| 15 | Ferro | https://claude.ai/artifact/TEbz1xRTUcabHcDvxgN21C | Published v4: reworked as "same surface, different magnets" (Bharti Airtel 21 Aug 2026 fitted twice, `gen/ferro_pair.py`), checked both themes |

PDFs (`python3 gen/pdf.py --home` / `pdf.py` / `pdf.py --compact`): `Double-Heston-designs-home.pdf` (Home light + dark per design, 30 pages),
`Double-Heston-designs.pdf` (every board, 288 pages), `Double-Heston-designs-compact.pdf`.

## How to rebuild

```
cd designs/gen
python3 prep.py                 # real data -> site_data.json (NSE bhavcopy, verified outputs, the pricer)
python3 build.py d01 --shots    # boards -> designs/01-amber-instrument/project/, screenshots -> gen/shots/
python3 sheet.py amber-instrument t-dark   # contact sheet for review
```

## Data notes

- Market: official NSE bhavcopy, 62 trading days 1 Jul – 25 Sep 2026 (index `gen/bhav_index.json`).
- Option chain: NIFTY, 27 Oct 2026 expiry (32 days), closing prices with the research's activity filters;
  IVs on the October futures forward; rate = RBI 91-day T-bill 15 Jul observation carried forward, as the research does.
- Model numbers: `legacy_streamlit_site/models.py`, unchanged (price, Monte Carlo 20,000 paths, Greeks).
- Findings: `outputs/consolidated_results.json`, `outputs/ambiguity/*`. Networks' 0.80 is RMSE-based skill;
  compare with the optimizer's 3.00 on that basis (its 1.80 is the median-based score).

## Rules

Don't modify the model, the live site, or the original samples. Don't commit, push, deploy or install without asking.
