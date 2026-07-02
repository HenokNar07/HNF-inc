"""FastAPI app: a thin HTTP wrapper around math_engine, plus a template-based
narration endpoint. All the actual math lives in math_engine and was verified
there before this layer existed -- nothing here recomputes or double-checks
numbers.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from math_engine.optimize import OptimizationError

from .config import CORS_ORIGINS
from .rate_limit import limiter
from .routers import analyze, explain

app = FastAPI(
    title="portfolio-frontier API",
    description="Deterministic mean-variance analysis, with a template-based narration layer.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    # Covers math_engine.pipeline.InsufficientAssetsError and
    # math_engine.data.TickerDataError too -- both subclass ValueError, so
    # every "the input was bad" case funnels through one 400 handler.
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(OptimizationError)
async def optimization_error_handler(request: Request, exc: OptimizationError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": f"Optimization failed: {exc}"})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(analyze.router, prefix="/api")
app.include_router(explain.router, prefix="/api")
