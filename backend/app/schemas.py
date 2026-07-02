"""Request models for the API layer.

Response models are math_engine.types.MVOResult directly -- no need to
duplicate that schema here, since it was designed to be JSON-ready from the
start (see math_engine/types.py's docstring).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from math_engine.pipeline import (
    DEFAULT_FRONTIER_POINTS,
    DEFAULT_LOOKBACK_YEARS,
    DEFAULT_MAX_WEIGHT,
)
from math_engine.types import MVOResult


class AnalyzeRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=1, examples=[["VOO", "AAPL", "BND"]])
    weights: list[float] = Field(..., min_length=1, examples=[[40, 35, 25]])
    lookback_years: float = Field(default=DEFAULT_LOOKBACK_YEARS, gt=0, le=30)
    max_weight: Optional[float] = Field(default=DEFAULT_MAX_WEIGHT, gt=0, le=1)
    n_frontier_points: int = Field(default=DEFAULT_FRONTIER_POINTS, ge=5, le=200)


class ExplainRequest(BaseModel):
    """The client POSTs back exactly what /api/analyze returned."""

    result: MVOResult


class ExplainResponse(BaseModel):
    explanation: str


class ErrorResponse(BaseModel):
    detail: str
