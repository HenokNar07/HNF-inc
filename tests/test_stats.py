import numpy as np
import pandas as pd
import pytest

from math_engine.stats import (
    MONTHS_PER_YEAR,
    annualize_cov,
    annualize_mean,
    compute_beta,
    estimate_factor_expected_returns,
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


def test_estimate_factor_expected_returns_recovers_known_betas():
    # Build 24 months of factor data, then construct one asset's returns
    # *exactly* from known factor exposures with zero alpha and no noise --
    # the regression should recover those exact betas, and the expected
    # return should equal risk_free + betas . mean(factor premiums),
    # annualized, since there's no alpha or noise to distort it.
    n = 24
    rng = np.random.default_rng(0)
    dates = pd.date_range("2020-01-31", periods=n, freq="ME")
    factors = pd.DataFrame(
        {
            "Mkt-RF": rng.normal(0.01, 0.04, n),
            "SMB": rng.normal(0.002, 0.02, n),
            "HML": rng.normal(0.001, 0.02, n),
            "RF": np.full(n, 0.001),
        },
        index=dates,
    )

    true_betas = {"Mkt-RF": 1.2, "SMB": 0.3, "HML": -0.4}
    excess = sum(factors[k] * v for k, v in true_betas.items())
    asset_returns = pd.DataFrame({"FAKE": factors["RF"] + excess}, index=dates)

    expected_annual, betas = estimate_factor_expected_returns(asset_returns, factors)

    for factor_name, beta in true_betas.items():
        assert betas.loc["FAKE", factor_name] == pytest.approx(beta, abs=1e-8)
    assert betas.loc["FAKE", "alpha"] == pytest.approx(0.0, abs=1e-8)

    mean_factors = factors[["Mkt-RF", "SMB", "HML"]].mean()
    expected_excess_monthly = sum(mean_factors[k] * v for k, v in true_betas.items())
    expected_monthly = expected_excess_monthly + factors["RF"].mean()
    assert expected_annual["FAKE"] == pytest.approx(expected_monthly * MONTHS_PER_YEAR)


def test_estimate_factor_expected_returns_insufficient_overlap_raises():
    dates = pd.date_range("2020-01-31", periods=5, freq="ME")
    factors = pd.DataFrame(
        {"Mkt-RF": [0.01] * 5, "SMB": [0.0] * 5, "HML": [0.0] * 5, "RF": [0.001] * 5},
        index=dates,
    )
    asset_returns = pd.DataFrame({"FAKE": [0.01] * 5}, index=dates)
    with pytest.raises(ValueError):
        estimate_factor_expected_returns(asset_returns, factors)
