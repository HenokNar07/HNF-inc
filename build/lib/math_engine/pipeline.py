"""Orchestrates the full mean-variance analysis: data -> stats -> optimize -> MVOResult.

This is the one function (`run_mvo`) the FastAPI layer will call. Everything
above it is composable on its own (useful for notebooks/tests); this module
just wires the pieces together in the right order and handles the edge cases
called out in the product spec.
"""
from __future__ import annotations

import numpy as np

from math_engine import data, optimize, stats
from math_engine.risk_free import get_risk_free_rate
from math_engine.types import AssetStats, FrontierPoint, MVOResult, PortfolioStats

DEFAULT_LOOKBACK_YEARS = 5
DEFAULT_MAX_WEIGHT = 0.40
DEFAULT_FRONTIER_POINTS = 50
MIN_ASSETS_FOR_FRONTIER = 2

# Input weights within this tolerance of summing to 1.0 (as a fraction) are
# treated as already-normalized; anything further off triggers a warning.
WEIGHT_SUM_TOLERANCE = 1e-4


class InsufficientAssetsError(ValueError):
    """Raised when there are too few assets to trace an efficient frontier."""


def _normalize_weights(weights: list[float]) -> tuple[np.ndarray, list[str]]:
    """Accept weights as fractions (sum to 1) or percentages (sum to 100).

    Anything that doesn't cleanly sum to one or the other is normalized
    proportionally, with a warning -- we'd rather produce a sensible answer
    than reject the input outright, since "my weights add up to 97%" is a
    completely normal user typo.
    """
    arr = np.array(weights, dtype=float)
    if np.any(arr < 0):
        raise ValueError("Weights cannot be negative.")

    # Heuristic: if any value is >1.5, the user is almost certainly using a
    # 0-100 percentage scale rather than a 0-1 fraction.
    if arr.max() > 1.5:
        arr = arr / 100.0

    total = arr.sum()
    if total <= 0:
        raise ValueError("Weights must sum to a positive number.")

    warnings = []
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        warnings.append(
            f"Input weights summed to {total * 100:.1f}% rather than 100%; "
            "normalized proportionally so they sum to 100%."
        )
    return arr / total, warnings


def _effective_max_weight(
    n_assets: int, max_weight: float | None
) -> tuple[float | None, list[str]]:
    """Disable the max-weight cap if it's mathematically infeasible.

    e.g. a 40% cap with only 2 assets can't sum to 100%, so we drop the cap
    for this run rather than letting the optimizer fail with an opaque error.
    """
    if max_weight is not None and max_weight * n_assets < 1.0:
        return None, [
            f"Max weight cap of {max_weight:.0%} per asset is infeasible with "
            f"only {n_assets} assets (weights must sum to 100%); cap disabled "
            "for this run."
        ]
    return max_weight, []


def _portfolio_stats(
    weights: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    tickers: list[str],
    risk_free_rate: float,
) -> PortfolioStats:
    ret = stats.portfolio_return(weights, mu)
    std = stats.portfolio_std(weights, cov)
    sharpe = stats.sharpe_ratio(ret, std, risk_free_rate)
    return PortfolioStats(
        weights={t: float(w) for t, w in zip(tickers, weights)},
        expected_return=ret,
        std_dev=std,
        sharpe_ratio=sharpe,
    )


def run_mvo(
    tickers: list[str],
    weights: list[float],
    lookback_years: float = DEFAULT_LOOKBACK_YEARS,
    max_weight: float | None = DEFAULT_MAX_WEIGHT,
    n_frontier_points: int = DEFAULT_FRONTIER_POINTS,
) -> MVOResult:
    if len(tickers) != len(weights):
        raise ValueError(
            f"tickers ({len(tickers)}) and weights ({len(weights)}) must be the same length."
        )
    if len(tickers) == 0:
        raise ValueError("At least one ticker is required.")

    tickers = [t.upper().strip() for t in tickers]
    if len(set(tickers)) != len(tickers):
        raise ValueError(f"Duplicate tickers found: {tickers}")

    if len(tickers) < MIN_ASSETS_FOR_FRONTIER:
        raise InsufficientAssetsError(
            "An efficient frontier needs at least 2 assets. It's the curve of "
            "best-possible risk/return combinations you get by mixing assets "
            "that don't move in perfect lockstep -- with a single holding "
            "there's nothing to mix, so there's no frontier to trace, only "
            "one fixed (return, risk) point equal to that asset's own stats."
        )

    norm_weights, warnings = _normalize_weights(weights)

    asset_returns, market_returns = data.fetch_monthly_returns_with_market(
        tickers, lookback_years
    )

    mu = stats.annualize_mean(asset_returns)
    cov = stats.annualize_cov(asset_returns)
    mu_arr = mu[tickers].to_numpy()
    cov_arr = cov.loc[tickers, tickers].to_numpy()

    risk_free_rate, rf_source = get_risk_free_rate()
    if rf_source == "fallback":
        warnings.append(
            f"Couldn't reach the Treasury Fiscal Data API; using a fallback "
            f"risk-free rate of {risk_free_rate:.2%} instead of a live rate."
        )

    eff_max_weight, cap_warnings = _effective_max_weight(len(tickers), max_weight)
    warnings.extend(cap_warnings)

    frontier_points, frontier_warnings = optimize.efficient_frontier(
        mu_arr, cov_arr, n_points=n_frontier_points, max_weight=eff_max_weight
    )
    warnings.extend(frontier_warnings)

    frontier = [
        FrontierPoint(
            expected_return=p["return"],
            std_dev=p["std_dev"],
            weights={t: float(w) for t, w in zip(tickers, p["weights"])},
        )
        for p in frontier_points
    ]

    max_sharpe_weights = optimize.max_sharpe_portfolio(
        mu_arr, cov_arr, risk_free_rate, eff_max_weight
    )
    min_var_weights = optimize.global_min_variance_portfolio(mu_arr, cov_arr, eff_max_weight)

    max_sharpe_stats = _portfolio_stats(max_sharpe_weights, mu_arr, cov_arr, tickers, risk_free_rate)
    min_var_stats = _portfolio_stats(min_var_weights, mu_arr, cov_arr, tickers, risk_free_rate)
    current_stats = _portfolio_stats(norm_weights, mu_arr, cov_arr, tickers, risk_free_rate)

    asset_stats_df = stats.per_asset_stats(asset_returns, market_returns)
    asset_stats = [
        AssetStats(
            ticker=t,
            mean_return=float(asset_stats_df.loc[t, "mean_return"]),
            std_dev=float(asset_stats_df.loc[t, "std_dev"]),
            beta=float(asset_stats_df.loc[t, "beta"]),
        )
        for t in tickers
    ]

    return MVOResult(
        tickers=tickers,
        lookback_years=lookback_years,
        risk_free_rate=risk_free_rate,
        risk_free_source=rf_source,
        frontier=frontier,
        max_sharpe=max_sharpe_stats,
        min_variance=min_var_stats,
        current_portfolio=current_stats,
        asset_stats=asset_stats,
        warnings=warnings,
    )
