"""Efficient frontier, max Sharpe, and min variance portfolios via scipy.optimize.

Deliberately hand-rolled with scipy.optimize.minimize (SLSQP) instead of a
black-box library like PyPortfolioOpt, so the Markowitz math is visible and
auditable: each function below is the textbook constrained QP, just solved
numerically instead of in closed form.

Guardrails against the well-known instability of naive mean-variance
optimization (a few basis points of estimated-return noise can flip weights
between 0% and 100%):
  - long-only (weights >= 0) by default
  - optional per-asset max weight cap (`max_weight`, e.g. 0.40)
A natural next step here (not implemented) would be to replace the sample
covariance matrix with a shrinkage estimator (Ledoit-Wolf) or blend expected
returns with a market-implied prior (Black-Litterman) -- both reduce the
sensitivity to estimation error without changing the optimization code below,
just the mu/cov inputs it receives.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog, minimize

from math_engine.stats import portfolio_return, portfolio_std, portfolio_variance, sharpe_ratio


class OptimizationError(RuntimeError):
    """Raised when a constrained optimization fails to converge."""


def _bounds(n_assets: int, max_weight: float | None) -> list[tuple[float, float]]:
    upper = max_weight if max_weight is not None else 1.0
    return [(0.0, upper)] * n_assets


def _sum_to_one(w: np.ndarray) -> float:
    return float(np.sum(w) - 1.0)


def _solve(
    objective,
    n_assets: int,
    max_weight: float | None,
    extra_constraints: list[dict] | None = None,
) -> np.ndarray:
    """Shared SLSQP driver: equal-weight start, sum-to-one + caller constraints.

    Retries once from a random feasible-ish start if the equal-weight start
    doesn't converge -- SLSQP occasionally reports non-convergence from a
    symmetric starting point on nearly-degenerate problems (e.g. a target
    return very close to a single asset's return).
    """
    constraints = [{"type": "eq", "fun": _sum_to_one}]
    if extra_constraints:
        constraints.extend(extra_constraints)
    bounds = _bounds(n_assets, max_weight)

    starts = [np.full(n_assets, 1.0 / n_assets)]
    rng = np.random.default_rng(seed=42)
    random_start = rng.dirichlet(np.ones(n_assets))
    starts.append(random_start)

    last_result = None
    for x0 in starts:
        result = minimize(
            objective, x0, method="SLSQP", bounds=bounds, constraints=constraints,
            options={"maxiter": 500, "ftol": 1e-10},
        )
        last_result = result
        if result.success:
            return np.clip(result.x, 0, None) / np.sum(np.clip(result.x, 0, None))

    raise OptimizationError(f"SLSQP failed to converge: {last_result.message}")


def global_min_variance_portfolio(
    mu: np.ndarray, cov: np.ndarray, max_weight: float | None = None
) -> np.ndarray:
    n = len(mu)
    return _solve(lambda w: portfolio_variance(w, cov), n, max_weight)


def min_variance_for_target_return(
    mu: np.ndarray, cov: np.ndarray, target_return: float, max_weight: float | None = None
) -> np.ndarray:
    n = len(mu)
    return_constraint = {"type": "eq", "fun": lambda w: portfolio_return(w, mu) - target_return}
    return _solve(lambda w: portfolio_variance(w, cov), n, max_weight, [return_constraint])


def max_sharpe_portfolio(
    mu: np.ndarray, cov: np.ndarray, risk_free_rate: float, max_weight: float | None = None
) -> np.ndarray:
    n = len(mu)

    def neg_sharpe(w: np.ndarray) -> float:
        ret = portfolio_return(w, mu)
        std = portfolio_std(w, cov)
        return -sharpe_ratio(ret, std, risk_free_rate)

    return _solve(neg_sharpe, n, max_weight)


def _achievable_return_range(mu: np.ndarray, max_weight: float | None) -> tuple[float, float]:
    """The true min/max portfolio return reachable under long-only + cap constraints.

    Without a max-weight cap, that's just [min(mu), max(mu)] (100% in the
    worst/best single asset). *With* a cap, those extremes are infeasible --
    you can't put 100% into one asset if no asset may exceed e.g. 40%. Solved
    as a tiny LP (linear objective, linear constraints) rather than guessed,
    since asking min_variance_for_target_return to hit an infeasible target
    just returns a solver failure with no clue why.
    """
    if max_weight is None:
        return float(mu.min()), float(mu.max())

    n = len(mu)
    bounds = _bounds(n, max_weight)
    a_eq = [np.ones(n)]
    b_eq = [1.0]

    min_result = linprog(c=mu, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method="highs")
    max_result = linprog(c=-mu, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if not (min_result.success and max_result.success):
        raise OptimizationError("Could not determine achievable return range under the weight cap.")

    return float(min_result.fun), float(-max_result.fun)


def efficient_frontier(
    mu: np.ndarray,
    cov: np.ndarray,
    n_points: int = 50,
    max_weight: float | None = None,
) -> tuple[list[dict], list[str]]:
    """Trace the frontier by solving min-variance at `n_points` target returns.

    Target returns span the achievable range under the long-only + cap
    constraints (see `_achievable_return_range`), not just [min(mu), max(mu)],
    since a max-weight cap makes the single-asset extremes infeasible. Points
    that still fail to converge are skipped and reported as warnings rather
    than crashing the whole request.
    """
    min_return, max_return = _achievable_return_range(mu, max_weight)
    target_returns = np.linspace(min_return, max_return, n_points)
    points: list[dict] = []
    warnings: list[str] = []

    for target in target_returns:
        try:
            weights = min_variance_for_target_return(mu, cov, target, max_weight)
        except OptimizationError:
            warnings.append(f"Frontier point at target return {target:.4f} did not converge; skipped.")
            continue
        points.append(
            {
                "target_return": float(target),
                "return": portfolio_return(weights, mu),
                "std_dev": portfolio_std(weights, cov),
                "weights": weights,
            }
        )

    return points, warnings
