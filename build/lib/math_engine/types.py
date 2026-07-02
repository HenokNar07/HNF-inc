"""Pydantic models for the math engine's output.

These double as the FastAPI response schema later -- defining them here,
before the API layer exists, means the pipeline's output is JSON-ready from
day one and the API layer becomes a thin wrapper instead of a translation layer.
"""
from __future__ import annotations

from pydantic import BaseModel


class AssetStats(BaseModel):
    ticker: str
    mean_return: float  # annualized
    std_dev: float  # annualized
    beta: float  # vs. SPY


class PortfolioStats(BaseModel):
    weights: dict[str, float]
    expected_return: float  # annualized
    std_dev: float  # annualized
    sharpe_ratio: float


class FrontierPoint(BaseModel):
    expected_return: float
    std_dev: float
    weights: dict[str, float]


class MVOResult(BaseModel):
    tickers: list[str]
    lookback_years: float
    risk_free_rate: float
    risk_free_source: str  # "treasury" or "fallback"
    frontier: list[FrontierPoint]
    max_sharpe: PortfolioStats
    min_variance: PortfolioStats
    current_portfolio: PortfolioStats
    asset_stats: list[AssetStats]
    warnings: list[str]
