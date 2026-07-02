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
