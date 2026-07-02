import numpy as np
import pytest


@pytest.fixture
def three_asset_mu():
    # Annualized expected returns, deliberately spread out so the frontier
    # and max-Sharpe solutions aren't degenerate.
    return np.array([0.12, 0.08, 0.04])


@pytest.fixture
def three_asset_cov():
    # Annualized covariance matrix: variances on the diagonal, plausible
    # correlations off-diagonal (asset 0 and 1 correlated ~0.4, asset 2 is
    # a low-vol, low-correlation "bond-like" asset).
    std = np.array([0.20, 0.15, 0.05])
    corr = np.array(
        [
            [1.0, 0.4, 0.1],
            [0.4, 1.0, 0.0],
            [0.1, 0.0, 1.0],
        ]
    )
    return np.outer(std, std) * corr


@pytest.fixture
def risk_free_rate():
    return 0.03
