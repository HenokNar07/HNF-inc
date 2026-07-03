"""Request models for the API layer.

Response models are math_engine.types.MVOResult directly -- no need to
duplicate that schema here, since it was designed to be JSON-ready from the
start (see math_engine/types.py's docstring).
"""
from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, StringConstraints

from math_engine.pipeline import (
    DEFAULT_FRONTIER_POINTS,
    DEFAULT_LOOKBACK_YEARS,
    DEFAULT_MAX_WEIGHT,
    DEFAULT_RETURN_MODEL,
)
from math_engine.types import MVOResult

# No real portfolio needs more than this many holdings, and an unbounded
# list lets someone force a very expensive computation (the frontier's
# covariance matrix and optimizer cost scale with the number of assets) --
# capping it here rejects that with a clean 422 before any work happens.
MAX_TICKERS = 15

TickerStr = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9.\-]{1,10}$")]


class AnalyzeRequest(BaseModel):
    tickers: list[TickerStr] = Field(
        ..., min_length=1, max_length=MAX_TICKERS, examples=[["VOO", "AAPL", "BND"]]
    )
    weights: list[float] = Field(
        ..., min_length=1, max_length=MAX_TICKERS, examples=[[40, 35, 25]]
    )
    lookback_years: float = Field(default=DEFAULT_LOOKBACK_YEARS, gt=0, le=30)
    max_weight: Optional[float] = Field(default=DEFAULT_MAX_WEIGHT, gt=0, le=1)
    n_frontier_points: int = Field(default=DEFAULT_FRONTIER_POINTS, ge=5, le=200)
    return_model: Literal["historical", "fama_french"] = Field(default=DEFAULT_RETURN_MODEL)


class ExplainRequest(BaseModel):
    """The client POSTs back exactly what /api/analyze returned."""

    result: MVOResult


class ExplainResponse(BaseModel):
    explanation: str


class ErrorResponse(BaseModel):
    detail: str
