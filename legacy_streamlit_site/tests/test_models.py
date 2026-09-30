"""
tests/test_models.py
====================
Correctness checks for models.py. Run with:  python3 tests/test_models.py   (or pytest).

The two headline checks are:
  * GBM Monte Carlo at 50,000 paths lands within 2 standard errors of Black-Scholes.
  * Heston with xi = 0 (no randomness in the variance) reproduces Black-Scholes.
Everything else guards the pieces those two rely on.
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import models as m

S, K, T, R, SIGMA = 100.0, 100.0, 0.5, 0.04, 0.25
N_PATHS = 50_000


# --- Black-Scholes --------------------------------------------------------

def test_black_scholes_known_value():
    # Textbook value: S=K=100, T=1, r=5%, sigma=20% -> call = 10.4506
    assert abs(m.black_scholes(100, 100, 1.0, 0.05, 0.2, "call") - 10.4506) < 1e-3


def test_put_call_parity():
    for k in (80.0, 100.0, 125.0):
        c = m.black_scholes(S, k, T, R, SIGMA, "call")
        p = m.black_scholes(S, k, T, R, SIGMA, "put")
        assert abs((c - p) - (S - k * np.exp(-R * T))) < 1e-10


def test_implied_vol_round_trip():
    for kind in ("call", "put"):
        for k in (85.0, 100.0, 115.0):
            price = m.black_scholes(S, k, T, R, 0.31, kind)
            assert abs(m.implied_vol(price, S, k, T, R, kind) - 0.31) < 1e-7


def test_implied_vol_impossible_price_is_nan():
    assert np.isnan(m.implied_vol(0.0, S, K, T, R, "call"))          # worthless call
    assert np.isnan(m.implied_vol(S + 1.0, S, K, T, R, "call"))      # call worth more than the stock
    assert np.isnan(m.implied_vol(5.0, S, K, 0.0, R, "call"))        # already expired


def test_greeks_match_finite_differences():
    for kind in ("call", "put"):
        g = m.greeks(S, K, T, R, SIGMA, kind)
        bs = lambda s=S, t=T, r=R, sig=SIGMA: m.black_scholes(s, K, t, r, sig, kind)
        h = 1e-3
        assert abs(g["delta"] - (bs(s=S + h) - bs(s=S - h)) / (2 * h)) < 1e-6
        assert abs(g["gamma"] - (bs(s=S + h) - 2 * bs() + bs(s=S - h)) / h**2) < 1e-4
        assert abs(g["vega"] - (bs(sig=SIGMA + h) - bs(sig=SIGMA - h)) / (2 * h) / 100) < 1e-6
        assert abs(g["rho"] - (bs(r=R + h) - bs(r=R - h)) / (2 * h) / 100) < 1e-6
        assert abs(g["theta"] - (-(bs(t=T + h) - bs(t=T - h)) / (2 * h) / 365)) < 1e-6


# --- Monte Carlo: GBM -----------------------------------------------------

def test_gbm_monte_carlo_converges_to_black_scholes():
    """HEADLINE CHECK 1: within 2 standard errors at 50,000 paths."""
    for kind, k in (("call", 100.0), ("put", 100.0), ("call", 110.0), ("put", 90.0)):
        paths = m.gbm_paths(S, R, SIGMA, T, N_PATHS, n_steps=10, seed=42)
        mc, se = m.price_from_paths(paths, k, R, T, kind)
        bs = m.black_scholes(S, k, T, R, SIGMA, kind)
        assert abs(mc - bs) < 2 * se, f"{kind} K={k}: MC {mc:.4f} vs BS {bs:.4f} (SE {se:.4f})"


def test_same_seed_same_paths_and_different_seed_differs():
    a = m.gbm_paths(S, R, SIGMA, T, 1000, 5, seed=1)
    assert np.array_equal(a, m.gbm_paths(S, R, SIGMA, T, 1000, 5, seed=1))
    assert not np.array_equal(a, m.gbm_paths(S, R, SIGMA, T, 1000, 5, seed=2))


def test_antithetic_reduces_standard_error():
    plain = m.gbm_paths(S, R, SIGMA, T, N_PATHS, 1, seed=7, antithetic=False)
    anti = m.gbm_paths(S, R, SIGMA, T, N_PATHS, 1, seed=7, antithetic=True)
    _, se_plain = m.price_from_paths(plain, K, R, T, "call", antithetic=False)
    _, se_anti = m.price_from_paths(anti, K, R, T, "call", antithetic=True)
    assert se_anti < se_plain


def test_odd_path_count_is_rounded_up_to_even():
    assert m.gbm_paths(S, R, SIGMA, T, 1001, 3, seed=0).shape == (1002, 4)


# --- Heston ---------------------------------------------------------------

def test_heston_with_zero_vol_of_vol_reproduces_black_scholes():
    """HEADLINE CHECK 2: xi = 0 with v0 = theta = sigma^2 means variance never moves."""
    v = SIGMA**2
    for kind in ("call", "put"):
        paths = m.heston_paths(S, R, T, v0=v, kappa=2.0, theta=v, xi=0.0, rho=-0.7,
                               n_paths=N_PATHS, n_steps=50, seed=42)
        mc, se = m.price_from_paths(paths, K, R, T, kind)
        bs = m.black_scholes(S, K, T, R, SIGMA, kind)
        assert abs(mc - bs) < 2 * se, f"{kind}: MC {mc:.4f} vs BS {bs:.4f} (SE {se:.4f})"


def test_heston_formula_with_tiny_vol_of_vol_reproduces_black_scholes():
    v = SIGMA**2
    for kind in ("call", "put"):
        h = m.heston_price(S, K, T, R, v0=v, kappa=2.0, theta=v, xi=1e-3, rho=-0.7, kind=kind)
        assert abs(h - m.black_scholes(S, K, T, R, SIGMA, kind)) < 1e-4


HESTON = dict(v0=0.04, kappa=2.0, theta=0.04, xi=0.5, rho=-0.7)


def test_heston_formula_agrees_with_monte_carlo():
    for kind, k in (("call", 100.0), ("put", 90.0), ("call", 115.0)):
        paths = m.heston_paths(S, R, T, n_paths=N_PATHS, n_steps=100, seed=3, **HESTON)
        mc, se = m.price_from_paths(paths, k, R, T, kind)
        exact = m.heston_price(S, k, T, R, kind=kind, **HESTON)
        assert abs(mc - exact) < 3 * se, f"{kind} K={k}: MC {mc:.4f} vs formula {exact:.4f} (SE {se:.4f})"


def test_heston_put_call_parity():
    c = m.heston_price(S, K, T, R, kind="call", **HESTON)
    p = m.heston_price(S, K, T, R, kind="put", **HESTON)
    assert abs((c - p) - (S - K * np.exp(-R * T))) < 1e-8


def test_full_truncation_survives_a_feller_violation():
    # 2*kappa*theta = 0.16 << xi^2 = 2.0, so the raw variance will go negative often.
    assert not m.feller_condition(kappa=2.0, theta=0.04, xi=1.4142)
    paths = m.heston_paths(S, R, T, v0=0.04, kappa=2.0, theta=0.04, xi=1.4142, rho=-0.5,
                           n_paths=5000, n_steps=100, seed=0)
    assert np.isfinite(paths).all() and (paths > 0).all()


def test_feller_condition():
    assert m.feller_condition(kappa=2.0, theta=0.04, xi=0.3)
    assert not m.feller_condition(kappa=2.0, theta=0.04, xi=0.5)


def test_negative_rho_tilts_the_smile_into_a_skew():
    ks = np.array([85.0, 100.0, 115.0])

    def smile(rho):
        prices = m.heston_price(S, ks, 0.25, R, v0=0.04, kappa=2.0, theta=0.04, xi=0.6, rho=rho)
        return [m.implied_vol(p, S, k, 0.25, R, "call") for p, k in zip(prices, ks)]

    skew = smile(-0.7)
    assert skew[0] > skew[1] > skew[2]            # low strikes more expensive: downward skew
    flat_bs = [m.implied_vol(m.black_scholes(S, k, 0.25, R, 0.2), S, k, 0.25, R) for k in ks]
    assert max(flat_bs) - min(flat_bs) < 1e-6     # Black-Scholes is flat by construction
    assert smile(0.0)[0] > smile(0.0)[1] < smile(0.0)[2]   # rho = 0 gives a symmetric smile, not a skew


# --- Double Heston --------------------------------------------------------

def test_double_heston_with_empty_second_factor_equals_heston():
    dh = m.double_heston_price(S, K, T, R, v0_1=0.04, kappa1=2.0, theta1=0.04, xi1=0.5, rho1=-0.7,
                               v0_2=0.0, kappa2=1.0, theta2=0.0, xi2=0.1, rho2=0.0)
    assert abs(dh - m.heston_price(S, K, T, R, kind="call", **HESTON)) < 1e-6


def test_double_heston_formula_agrees_with_monte_carlo():
    p = dict(v0_1=0.03, kappa1=4.0, theta1=0.03, xi1=0.6, rho1=-0.7,
             v0_2=0.02, kappa2=0.5, theta2=0.02, xi2=0.3, rho2=-0.5)
    paths = m.double_heston_paths(S, R, T, n_paths=N_PATHS, n_steps=100, seed=5, **p)
    mc, se = m.price_from_paths(paths, K, R, T, "call")
    exact = m.double_heston_price(S, K, T, R, kind="call", **p)
    assert abs(mc - exact) < 3 * se, f"MC {mc:.4f} vs formula {exact:.4f} (SE {se:.4f})"


# --- Calibration ----------------------------------------------------------

def _synthetic_chain(params, maturities=(0.08, 0.25, 0.75), n_strikes=9):
    """Prices generated BY the model, so a correct calibrator must recover `params` exactly."""
    strikes, mats, kinds, prices, ivs = [], [], [], [], []
    for T in maturities:
        for k in np.linspace(0.85 * S, 1.15 * S, n_strikes):
            kind = "put" if k < S else "call"
            p = m.heston_price(S, k, T, R, *params, kind=kind)
            if p < 0.05:
                continue
            strikes.append(k); mats.append(T); kinds.append(kind); prices.append(p)
            ivs.append(m.implied_vol(p, S, k, T, R, kind))
    return np.array(strikes), np.array(mats), kinds, np.array(prices), np.array(ivs)


TRUE_PARAMS = (0.04, 2.5, 0.05, 0.6, -0.7)


def test_calibration_recovers_known_parameters():
    """Ground-truth check: fitting model-generated prices must return the generating parameters."""
    strikes, mats, kinds, prices, _ = _synthetic_chain(TRUE_PARAMS)
    start = (0.06, 1.0, 0.03, 0.4, -0.3)          # deliberately wrong starting point
    fit = m.calibrate_heston(S, R, strikes, mats, kinds, prices, x0=start)
    assert fit["converged"]
    assert fit["rmse"] < 1e-3, f"fit error {fit['rmse']}"
    for name, got, true in zip(m.HESTON_BOUNDS, fit["params"], TRUE_PARAMS):
        assert abs(got - true) < 0.05 * max(abs(true), 0.1), f"{name}: got {got}, true {true}"


def test_vega_weighted_calibration_also_recovers_parameters():
    strikes, mats, kinds, prices, ivs = _synthetic_chain(TRUE_PARAMS)
    w = m.vega_weights(S, R, strikes, mats, kinds, ivs)
    assert (w > 0).all()
    fit = m.calibrate_heston(S, R, strikes, mats, kinds, prices, x0=(0.06, 1.0, 0.03, 0.4, -0.3), weights=w)
    assert fit["converged"]
    for got, true in zip(fit["params"], TRUE_PARAMS):
        assert abs(got - true) < 0.05 * max(abs(true), 0.1)


def test_vega_weighting_favours_the_wings():
    """The point of vega weighting: a cheap wing must not be drowned out by an expensive ATM quote."""
    strikes, mats, kinds, prices, ivs = _synthetic_chain(TRUE_PARAMS, maturities=(0.25,))
    w = m.vega_weights(S, R, strikes, mats, kinds, ivs)
    atm = int(np.argmin(np.abs(strikes - S)))
    wing = int(np.argmin(strikes))
    assert prices[atm] > prices[wing]           # ATM is the expensive one
    assert w[atm] > w[wing]                     # so it is divided by MORE, shrinking its weight
    assert prices[atm] / prices[wing] > w[atm] / w[wing]


def test_implied_vol_rmse_is_zero_for_a_perfect_fit_and_positive_otherwise():
    strikes, mats, kinds, prices, ivs = _synthetic_chain(TRUE_PARAMS)
    exact, used = m.implied_vol_rmse(S, R, strikes, mats, kinds, ivs, prices)
    assert exact < 1e-6 and used == 1.0
    worse, _ = m.implied_vol_rmse(S, R, strikes, mats, kinds, ivs, prices * 1.1)
    assert worse > 0.5


def test_calibration_reports_a_parameter_pinned_to_its_bound():
    """A chain generated with kappa far above the allowed range must come back flagged."""
    over = (0.04, 40.0, 0.05, 0.6, -0.7)        # kappa well outside HESTON_BOUNDS
    strikes, mats, kinds, prices, _ = _synthetic_chain(over)
    fit = m.calibrate_heston(S, R, strikes, mats, kinds, prices, x0=(0.04, 5.0, 0.05, 0.6, -0.7))
    assert "kappa" in fit["at_bounds"]


def test_flat_vol_calibration_recovers_a_flat_vol_chain():
    strikes, mats, kinds, prices = [], [], [], []
    for T in (0.1, 0.5):
        for k in np.linspace(0.9 * S, 1.1 * S, 7):
            kind = "put" if k < S else "call"
            strikes.append(k); mats.append(T); kinds.append(kind)
            prices.append(m.black_scholes(S, k, T, R, 0.23, kind))
    sigma, rmse = m.calibrate_black_scholes(S, R, strikes, mats, kinds, prices)
    assert abs(sigma - 0.23) < 1e-4 and rmse < 1e-4


# --- Volatility forecasting -----------------------------------------------

def _fake_returns(n=1500, daily_vol=0.01, seed=0):
    return pd.Series(np.random.default_rng(seed).normal(0.0, daily_vol, n),
                     index=pd.bdate_range("2018-01-01", periods=n))


def test_forecasts_never_use_future_returns():
    r = _fake_returns()
    tampered = r.copy()
    tampered.iloc[1000:] = 0.5                       # wreck everything after day 1000
    for fn in (m.naive_vol, m.ewma_vol):
        a, b = fn(r), fn(tampered)
        assert np.allclose(a.iloc[:1000], b.iloc[:1000], equal_nan=True)
    g1, _ = m.garch_vol(r, n_train=800)
    g2, _ = m.garch_vol(tampered, n_train=800)
    assert np.allclose(g1.iloc[:1000], g2.iloc[:1000], equal_nan=True)


def test_ewma_and_naive_track_constant_volatility():
    r = _fake_returns(daily_vol=0.01)
    for fn in (m.naive_vol, m.ewma_vol):
        assert abs(fn(r).iloc[200:].mean() - 0.01) < 0.001


def test_garch_recovers_long_run_volatility_of_constant_vol_data():
    r = _fake_returns(n=3000, daily_vol=0.01)
    _, info = m.garch_vol(r)
    assert info["converged"]
    assert abs(np.sqrt(info["long_run_var_daily"]) - 0.01) < 0.002


def test_forward_realised_vol_is_aligned_to_the_days_after_origin():
    r = pd.Series([0.0] * 5 + [0.1] * 3 + [0.0] * 5)
    fwd = m.forward_realised_vol(r, horizon=3)
    assert fwd.iloc[4] > 0.09 and fwd.iloc[3] < 0.09    # origin day 4: next 3 days (5,6,7) are the moves
    assert fwd.iloc[-3:].isna().all()


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[OK]   {name}")
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {name}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
