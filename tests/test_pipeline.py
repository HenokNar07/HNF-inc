import numpy as np
import pytest

from math_engine.pipeline import InsufficientAssetsError, _normalize_weights, run_mvo


# -- Edge cases that fail validation before any network call happens --


def test_single_ticker_raises_insufficient_assets():
    with pytest.raises(InsufficientAssetsError):
        run_mvo(tickers=["AAPL"], weights=[1.0])


def test_mismatched_tickers_and_weights_raises():
    with pytest.raises(ValueError):
        run_mvo(tickers=["AAPL", "MSFT"], weights=[1.0])


def test_duplicate_tickers_raises():
    with pytest.raises(ValueError):
        run_mvo(tickers=["AAPL", "AAPL"], weights=[0.5, 0.5])


def test_zero_tickers_raises():
    with pytest.raises(ValueError):
        run_mvo(tickers=[], weights=[])


# -- Weight normalization (percent vs. fraction input, off-sum warnings) --


def test_normalize_weights_percentage_scale():
    weights, warnings = _normalize_weights([40, 35, 25])
    assert weights == pytest.approx([0.40, 0.35, 0.25])
    assert warnings == []


def test_normalize_weights_fraction_scale():
    weights, warnings = _normalize_weights([0.4, 0.35, 0.25])
    assert weights == pytest.approx([0.40, 0.35, 0.25])
    assert warnings == []


def test_normalize_weights_off_sum_warns_and_normalizes():
    # Sums to 90, not 100 -- a very normal user typo.
    weights, warnings = _normalize_weights([40, 30, 20])
    assert weights.sum() == pytest.approx(1.0)
    assert weights == pytest.approx([40 / 90, 30 / 90, 20 / 90])
    assert len(warnings) == 1
    assert "90.0%" in warnings[0]


def test_normalize_weights_negative_raises():
    with pytest.raises(ValueError):
        _normalize_weights([50, -10, 60])


def test_normalize_weights_all_zero_raises():
    with pytest.raises(ValueError):
        _normalize_weights([0, 0, 0])


# -- Full pipeline integration test against real market data (opt-in) --


@pytest.mark.network
def test_run_mvo_sample_portfolio_end_to_end():
    """40% VOO / 35% AAPL / 25% BND -- the sample portfolio from the product spec.

    Run with: pytest -m network
    Requires network access (yfinance, Treasury Fiscal Data API).
    """
    result = run_mvo(
        tickers=["VOO", "AAPL", "BND"],
        weights=[40, 35, 25],
        lookback_years=5,
    )

    assert result.tickers == ["VOO", "AAPL", "BND"]
    assert sum(result.current_portfolio.weights.values()) == pytest.approx(1.0, abs=1e-6)
    assert sum(result.max_sharpe.weights.values()) == pytest.approx(1.0, abs=1e-4)
    assert sum(result.min_variance.weights.values()) == pytest.approx(1.0, abs=1e-4)

    # Max Sharpe should never be worse than an arbitrary user-chosen allocation.
    assert result.max_sharpe.sharpe_ratio >= result.current_portfolio.sharpe_ratio

    assert len(result.frontier) > 40
    assert len(result.asset_stats) == 3
    for asset in result.asset_stats:
        assert asset.ticker in result.tickers
        assert not np.isnan(asset.beta)
