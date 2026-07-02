import numpy as np
import pytest

from math_engine.optimize import (
    efficient_frontier,
    global_min_variance_portfolio,
    max_sharpe_portfolio,
    min_variance_for_target_return,
)
from math_engine.stats import portfolio_return, portfolio_std, sharpe_ratio

WEIGHT_TOL = 1e-4


def test_min_variance_weights_sum_to_one(three_asset_mu, three_asset_cov):
    weights = global_min_variance_portfolio(three_asset_mu, three_asset_cov)
    assert weights.sum() == pytest.approx(1.0, abs=WEIGHT_TOL)


def test_min_variance_weights_are_long_only(three_asset_mu, three_asset_cov):
    weights = global_min_variance_portfolio(three_asset_mu, three_asset_cov)
    assert np.all(weights >= -WEIGHT_TOL)


def test_max_sharpe_weights_sum_to_one_and_respect_cap(
    three_asset_mu, three_asset_cov, risk_free_rate
):
    max_weight = 0.6
    weights = max_sharpe_portfolio(three_asset_mu, three_asset_cov, risk_free_rate, max_weight)
    assert weights.sum() == pytest.approx(1.0, abs=WEIGHT_TOL)
    assert np.all(weights >= -WEIGHT_TOL)
    assert np.all(weights <= max_weight + WEIGHT_TOL)


def test_two_asset_min_variance_matches_closed_form():
    # For two assets there's a closed-form for the weight that minimizes
    # variance at a given target return: from w1*mu1 + (1-w1)*mu2 = target,
    # w1 = (target - mu2) / (mu1 - mu2). Cross-check the numerical solver
    # against this directly, independent of the frontier machinery.
    mu = np.array([0.12, 0.05])
    cov = np.array([[0.04, 0.01], [0.01, 0.02]])
    target = 0.09

    expected_w1 = (target - mu[1]) / (mu[0] - mu[1])
    expected = np.array([expected_w1, 1 - expected_w1])

    weights = min_variance_for_target_return(mu, cov, target)
    assert weights == pytest.approx(expected, abs=1e-3)


def test_max_sharpe_portfolio_has_best_sharpe_on_frontier(
    three_asset_mu, three_asset_cov, risk_free_rate
):
    # The defining property of the max-Sharpe (tangency) portfolio: no other
    # point on the efficient frontier has a higher Sharpe ratio. This is the
    # "max Sharpe portfolio lies on the frontier" check from the spec, stated
    # as the actual optimality condition rather than just "it's a point on the curve."
    max_sharpe_w = max_sharpe_portfolio(three_asset_mu, three_asset_cov, risk_free_rate)
    max_sharpe_ratio = sharpe_ratio(
        portfolio_return(max_sharpe_w, three_asset_mu),
        portfolio_std(max_sharpe_w, three_asset_cov),
        risk_free_rate,
    )

    frontier_points, warnings = efficient_frontier(three_asset_mu, three_asset_cov, n_points=50)
    assert len(frontier_points) > 40  # most/all of 50 points should converge

    for point in frontier_points:
        point_sharpe = sharpe_ratio(point["return"], point["std_dev"], risk_free_rate)
        assert point_sharpe <= max_sharpe_ratio + 1e-3


def test_global_min_variance_has_lowest_std_on_frontier(three_asset_mu, three_asset_cov):
    min_var_w = global_min_variance_portfolio(three_asset_mu, three_asset_cov)
    min_var_std = portfolio_std(min_var_w, three_asset_cov)

    frontier_points, _ = efficient_frontier(three_asset_mu, three_asset_cov, n_points=50)
    for point in frontier_points:
        assert point["std_dev"] >= min_var_std - 1e-3


def test_efficient_frontier_weights_sum_to_one(three_asset_mu, three_asset_cov):
    frontier_points, _ = efficient_frontier(three_asset_mu, three_asset_cov, n_points=25)
    for point in frontier_points:
        assert point["weights"].sum() == pytest.approx(1.0, abs=WEIGHT_TOL)


def test_efficient_frontier_spans_target_return_range(three_asset_mu, three_asset_cov):
    frontier_points, _ = efficient_frontier(three_asset_mu, three_asset_cov, n_points=50)
    returns = [p["return"] for p in frontier_points]
    assert min(returns) == pytest.approx(three_asset_mu.min(), abs=1e-3)
    assert max(returns) == pytest.approx(three_asset_mu.max(), abs=1e-3)
