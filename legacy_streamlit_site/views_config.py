"""
Shared calibration settings.

These live outside the page files because the frozen snapshot has to sample the same
expiries the live page does. If the two drift apart, the fallback draws a visibly
different smile from the thing it stands in for, which is worse than having no
fallback at all.
"""

# Target maturities in days. The calibration picks the listed expiry nearest each one,
# so the fit sees the whole term structure rather than clustering at the front month.
CALIB_DAYS = [21, 45, 90, 150, 250, 360]

# Quotes closer to the money than this are the ones that carry the smile; further out
# they are mostly rounding noise once inverted to an implied volatility.
MONEYNESS_BAND = (0.8, 1.2)
