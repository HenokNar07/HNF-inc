import numpy as np
import pandas as pd
import pytest

from math_engine.stats import (
    annualize_cov,
    annualize_mean,
    compute_beta,
    portfolio_return,
    portfolio_std,
    portfolio_variance,
    sharpe_ratio,
)


def test_two_asset_variance_matches_closed_form():
    # Var(p) = w1^2*v1 + w2^2*v2 + 2*w1*w2*cov12 -- the textbook two-asset
    # portfolio variance formula, checked independently of the matrix form
    # (weights @ cov @ weights) used internally.
    v1, v2, cov12 = 0.04, 0.09, 0.015
    cov = np.array([[v1, cov12], [cov12, v2]])
    w1, w2 = 0.6, 0.4

    expected = w1**2 * v1 + w2**2 * v2 + 2 * w1 * w2 * cov12
    actual = portfolio_variance(np.array([w1, w2]), cov)

    assert actual == pytest.approx(expected)


def test_portfolio_return_is_weighted_average():
    mu = np.array([0.10, 0.05, 0.02])
    weights = np.array([0.5, 0.3, 0.2])
    expected = 0.5 * 0.10 + 0.3 * 0.05 + 0.2 * 0.02
    assert portfolio_return(weights, mu) == pytest.approx(expected)


def test_portfolio_std_is_sqrt_of_variance():
    cov = np.array([[0.04, 0.0], [0.0, 0.09]])
    weights = np.array([0.5, 0.5])
    var = portfolio_variance(weights, cov)
    assert portfolio_std(weights, cov) == pytest.approx(np.sqrt(var))


def test_sharpe_ratio_basic():
    assert sharpe_ratio(port_return=0.10, port_std=0.20, risk_free_rate=0.03) == pytest.approx(
        (0.10 - 0.03) / 0.20
    )


def test_sharpe_ratio_zero_std_returns_zero():
    assert sharpe_ratio(port_return=0.10, port_std=0.0, risk_free_rate=0.03) == 0.0


def test_annualize_mean_and_cov_scale_by_twelve():
    monthly = pd.DataFrame({"A": [0.01] * 12, "B": [0.02] * 12})
    mean = annualize_mean(monthly)
    assert mean["A"] == pytest.approx(0.12)
    assert mean["B"] == pytest.approx(0.24)

    # cov of a constant series is 0, so use a series with real variance instead
    monthly_var = pd.DataFrame({"A": [0.01, -0.01, 0.02, -0.02] * 3})
    monthly_cov = monthly_var["A"].var()
    annual_cov = annualize_cov(monthly_var)
    assert annual_cov.loc["A", "A"] == pytest.approx(monthly_cov * 12)


def test_compute_beta_recovers_known_beta():
    # Construct an asset whose returns are exactly 2x the market's, every
    # period -- beta should come back as exactly 2.0 (no noise to average out).
    market = pd.Series([0.01, -0.02, 0.03, 0.00, 0.015, -0.01, 0.02, 0.005])
    asset = 2.0 * market
    beta = compute_beta(asset, market)
    assert beta == pytest.approx(2.0, abs=1e-9)


def test_compute_beta_zero_market_variance_is_nan():
    market = pd.Series([0.01] * 10)  # constant -> zero variance
    asset = pd.Series(np.linspace(0.01, 0.02, 10))
    assert np.isnan(compute_beta(asset, market))
