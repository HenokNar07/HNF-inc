from fastapi import APIRouter

from math_engine.pipeline import run_mvo
from math_engine.types import MVOResult

from ..config import FRED_API_KEY
from ..schemas import AnalyzeRequest

router = APIRouter()


@router.post("/analyze", response_model=MVOResult)
def analyze(request: AnalyzeRequest) -> MVOResult:
    """Run the full MVO pipeline. Domain errors (bad tickers, bad weights,
    too few assets) are raised as ValueError subclasses in math_engine and
    turned into 400s by the exception handlers registered in main.py -- this
    endpoint itself has no error-handling logic, it's a thin call-through.
    """
    return run_mvo(
        tickers=request.tickers,
        weights=request.weights,
        lookback_years=request.lookback_years,
        max_weight=request.max_weight,
        n_frontier_points=request.n_frontier_points,
        fred_api_key=FRED_API_KEY,
    )
