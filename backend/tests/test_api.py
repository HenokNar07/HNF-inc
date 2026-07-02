import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_single_ticker_returns_400():
    resp = client.post("/api/analyze", json={"tickers": ["AAPL"], "weights": [1.0]})
    assert resp.status_code == 400
    assert "at least 2 assets" in resp.json()["detail"]


def test_analyze_mismatched_lengths_returns_400():
    resp = client.post(
        "/api/analyze", json={"tickers": ["AAPL", "MSFT"], "weights": [1.0]}
    )
    assert resp.status_code == 400


def test_analyze_missing_fields_returns_422():
    resp = client.post("/api/analyze", json={"tickers": ["AAPL", "MSFT"]})
    assert resp.status_code == 422  # pydantic request validation, not a domain error


def test_explain_without_api_key_returns_503(monkeypatch):
    monkeypatch.setattr("app.claude_client.ANTHROPIC_API_KEY", None)
    # Minimal-but-valid MVOResult payload -- shape matches math_engine.types.MVOResult.
    fake_result = {
        "tickers": ["VOO", "BND"],
        "lookback_years": 5,
        "risk_free_rate": 0.045,
        "risk_free_source": "fallback",
        "frontier": [],
        "max_sharpe": {
            "weights": {"VOO": 0.6, "BND": 0.4},
            "expected_return": 0.10,
            "std_dev": 0.12,
            "sharpe_ratio": 0.5,
        },
        "min_variance": {
            "weights": {"VOO": 0.3, "BND": 0.7},
            "expected_return": 0.06,
            "std_dev": 0.08,
            "sharpe_ratio": 0.2,
        },
        "current_portfolio": {
            "weights": {"VOO": 0.5, "BND": 0.5},
            "expected_return": 0.08,
            "std_dev": 0.10,
            "sharpe_ratio": 0.35,
        },
        "asset_stats": [
            {"ticker": "VOO", "mean_return": 0.13, "std_dev": 0.16, "beta": 1.0},
            {"ticker": "BND", "mean_return": 0.0, "std_dev": 0.06, "beta": 0.25},
        ],
        "warnings": [],
    }
    resp = client.post("/api/explain", json={"result": fake_result})
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]


@pytest.mark.network
def test_analyze_sample_portfolio_end_to_end():
    resp = client.post(
        "/api/analyze",
        json={"tickers": ["VOO", "AAPL", "BND"], "weights": [40, 35, 25], "lookback_years": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tickers"] == ["VOO", "AAPL", "BND"]
    assert len(body["frontier"]) > 40
    assert body["max_sharpe"]["sharpe_ratio"] >= body["current_portfolio"]["sharpe_ratio"]


@pytest.mark.network
def test_analyze_invalid_ticker_returns_400():
    resp = client.post(
        "/api/analyze",
        json={"tickers": ["AAPL", "NOTAREALTICKERXYZ"], "weights": [50, 50]},
    )
    assert resp.status_code == 400


@pytest.mark.network
def test_explain_end_to_end():
    analyze_resp = client.post(
        "/api/analyze",
        json={"tickers": ["VOO", "AAPL", "BND"], "weights": [40, 35, 25], "lookback_years": 5},
    )
    assert analyze_resp.status_code == 200

    explain_resp = client.post("/api/explain", json={"result": analyze_resp.json()})
    assert explain_resp.status_code == 200
    explanation = explain_resp.json()["explanation"]
    assert len(explanation) > 0
