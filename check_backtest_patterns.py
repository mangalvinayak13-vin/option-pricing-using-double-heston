"""Ad-hoc deeper look at option_backtest_pairs.csv for write-up-worthy patterns."""
import pandas as pd
import numpy as np

p = pd.read_csv("outputs/option_backtest/option_backtest_pairs.csv")
s = p[p.in_support].copy()

print("=== does slot coverage on t+1 relate to network fit quality? ===")
for lo, hi, label in [(6, 12, "6-12"), (13, 17, "13-17"), (18, 20, "18-20")]:
    sub = s[(s.slots_t1 >= lo) & (s.slots_t1 <= hi)]
    print(f"  slots {label:6s} n={len(sub):5d}  median fresh_dh {sub.err_fresh_dh.median()*100:5.1f}%  "
          f"median flat_bs {sub.err_bs_same_day.median()*100:5.1f}%")

print()
print("=== does param_jump correlate with slot-count CHANGE between t and t+1? ===")
m = p.merge(p[['ticker', 'day_t1', 'slots_t1']].rename(columns={'day_t1': 'day_t', 'slots_t1': 'slots_t'}),
            on=['ticker', 'day_t'], how='left')
m['slot_change'] = (m.slots_t1 - m.slots_t).abs()
s2 = m[m.in_support].dropna(subset=['slot_change'])
print(f"  correlation(param_jump, |slot count change|): {np.corrcoef(s2.param_jump, s2.slot_change)[0,1]:.3f}")
print(f"  correlation(param_jump, |spot_move|): {np.corrcoef(s2.param_jump, s2.spot_move.abs())[0,1]:.3f}")

print()
print("=== per-ticker: is any stock's network fit actually GOOD (beats flat)? ===")
by_ticker = s.groupby('ticker').agg(
    n=('err_fresh_dh', 'size'),
    net=('err_fresh_dh', 'median'),
    flat=('err_bs_same_day', 'median'),
).reset_index()
by_ticker['net_beats_flat'] = by_ticker.net < by_ticker.flat
print(f"  stocks where median fresh-DH beats median flat-BS: {by_ticker.net_beats_flat.sum()} of {len(by_ticker)}")
print(by_ticker.sort_values('net').head(5).to_string(index=False))
print()
print(by_ticker.sort_values('net', ascending=False).head(5).to_string(index=False))
