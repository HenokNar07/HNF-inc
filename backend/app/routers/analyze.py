from fastapi import APIRouter, Request

from math_engine.pipeline import run_mvo
from math_engine.types import MVOResult

from ..rate_limit import ANALYZE_RATE_LIMIT, limiter
from ..schemas import AnalyzeRequest

router = APIRouter()


@router.post("/analyze", response_model=MVOResult)
@limiter.limit(ANALYZE_RATE_LIMIT)
def analyze(request: Request, body: AnalyzeRequest) -> MVOResult:
    """Run the full MVO pipeline. Domain errors (bad tickers, bad weights,
    too few assets) are raised as ValueError subclasses in math_engine and
    turned into 400s by the exception handlers registered in main.py -- this
    endpoint itself has no error-handling logic, it's a thin call-through.

    The `request` param (unused directly) is required by slowapi's rate
    limiter, which pulls the caller's IP from it.
    """
    return run_mvo(
        tickers=body.tickers,
        weights=body.weights,
        lookback_years=body.lookback_years,
        max_weight=body.max_weight,
        n_frontier_points=body.n_frontier_points,
        return_model=body.return_model,
    )
