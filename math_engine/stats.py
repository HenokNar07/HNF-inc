"""Return/risk statistics: annualization, portfolio moments, Sharpe, beta.

Annualization note: we use *arithmetic* annualization (monthly mean * 12,
monthly covariance * 12) rather than compounding monthly returns
geometrically. This is the standard convention for Markowitz mean-variance
inputs -- the optimizer needs the mean and variance of the *distribution* of
returns, not a compounded growth rate. It will read a little higher than a
CAGR figure; that's expected and matches what tools like Portfolio Visualizer
report as "expected return" in the efficient frontier context.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MONTHS_PER_YEAR = 12


def annualize_mean(monthly_returns: pd.DataFrame) -> pd.Series:
    return monthly_returns.mean() * MONTHS_PER_YEAR


def annualize_cov(monthly_returns: pd.DataFrame) -> pd.DataFrame:
    return monthly_returns.cov() * MONTHS_PER_YEAR


def portfolio_return(weights: np.ndarray, mu: np.ndarray) -> float:
    return float(np.dot(weights, mu))


def portfolio_variance(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(weights @ cov @ weights)


def portfolio_std(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(max(portfolio_variance(weights, cov), 0.0)))


def sharpe_ratio(port_return: float, port_std: float, risk_free_rate: float) -> float:
    if port_std == 0:
        return 0.0
    return (port_return - risk_free_rate) / port_std


def compute_beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    """Beta of an asset vs. the market proxy, from monthly returns.

    Beta is scale-invariant to annualization (cov and var scale by the same
    factor and cancel), so we compute it directly on monthly data rather than
    annualizing first.
    """
    aligned = pd.concat([asset_returns, market_returns], axis=1).dropna()
    if len(aligned) < 2:
        return float("nan")
    asset_col, market_col = aligned.columns[0], aligned.columns[1]
    market_var = aligned[market_col].var()
    # A "zero" market variance can still land near 1e-36 due to floating-point
    # rounding in pandas' variance algorithm, even for a genuinely constant
    # series -- compare against a small epsilon rather than exact zero.
    if market_var < 1e-12:
        return float("nan")
    covariance = aligned[asset_col].cov(aligned[market_col])
    return float(covariance / market_var)


def per_asset_stats(
    monthly_returns: pd.DataFrame, market_returns: pd.Series
) -> pd.DataFrame:
    """Per-ticker annualized mean return, annualized std dev, and beta vs. market."""
    mean_annual = annualize_mean(monthly_returns)
    std_annual = monthly_returns.std() * np.sqrt(MONTHS_PER_YEAR)
    betas = {
        ticker: compute_beta(monthly_returns[ticker], market_returns)
        for ticker in monthly_returns.columns
    }
    return pd.DataFrame(
        {
            "mean_return": mean_annual,
            "std_dev": std_annual,
            "beta": pd.Series(betas),
        }
    )


# Fama-French factor columns expected in the `factors` argument below --
# imported here (rather than importing math_engine.factors, which would be
# a data-fetching module depending on a pure-stats one) to avoid a layering
# inversion; factors.py is the only place that produces a DataFrame shaped
# like this.
FACTOR_COLUMNS = ["Mkt-RF", "SMB", "HML"]

MIN_FACTOR_OBSERVATIONS = 12


def estimate_factor_expected_returns(
    monthly_returns: pd.DataFrame, factors: pd.DataFrame
) -> tuple[pd.Series, pd.DataFrame]:
    """Expected annual returns from a Fama-French 3-factor regression.

    For each asset, regresses monthly excess return (return - RF) on
    (Mkt-RF, SMB, HML) to get factor betas, then estimates expected excess
    return as beta . mean(factor premiums) -- deliberately *excluding* the
    regression's alpha term. Alpha is the asset's realized return left over
    after its factor exposures are accounted for; folding it back in would
    just reproduce the noisy historical sample mean, defeating the point of
    using a factor model in the first place. Expected return = risk-free
    rate + that factor-implied excess return.

    Returns (expected_annual_returns, betas) where betas has one row per
    ticker with columns alpha, Mkt-RF, SMB, HML (monthly, for diagnostics).

    Both inputs must be indexed by a monthly period; only overlapping months
    are used.
    """
    returns_by_period = monthly_returns.copy()
    returns_by_period.index = returns_by_period.index.to_period("M")
    factors_by_period = factors.copy()
    factors_by_period.index = factors_by_period.index.to_period("M")

    merged = returns_by_period.join(factors_by_period, how="inner")
    if len(merged) < MIN_FACTOR_OBSERVATIONS:
        raise ValueError(
            f"Only {len(merged)} overlapping months between price history and "
            f"Fama-French factor data; need at least {MIN_FACTOR_OBSERVATIONS}."
        )

    factor_values = merged[FACTOR_COLUMNS].to_numpy()
    design = np.column_stack([np.ones(len(merged)), factor_values])
    risk_free_monthly = merged["RF"].to_numpy()
    mean_factor_premiums = factor_values.mean(axis=0)
    mean_risk_free_monthly = float(risk_free_monthly.mean())

    expected_annual = {}
    betas = {}
    for ticker in monthly_returns.columns:
        excess_return = merged[ticker].to_numpy() - risk_free_monthly
        coeffs, *_ = np.linalg.lstsq(design, excess_return, rcond=None)
        alpha, *factor_betas = coeffs
        betas[ticker] = dict(zip(["alpha", *FACTOR_COLUMNS], coeffs))
        expected_excess_monthly = float(np.dot(factor_betas, mean_factor_premiums))
        expected_annual[ticker] = (
            expected_excess_monthly + mean_risk_free_monthly
        ) * MONTHS_PER_YEAR

    return pd.Series(expected_annual), pd.DataFrame(betas).T
