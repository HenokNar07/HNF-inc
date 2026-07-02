import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rate_limit import ANALYZE_RATE_LIMIT

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


def test_analyze_too_many_tickers_returns_422():
    # Guards against someone forcing an expensive computation with an
    # unbounded ticker list -- see MAX_TICKERS in schemas.py.
    n = 20
    resp = client.post(
        "/api/analyze",
        json={"tickers": [f"T{i}" for i in range(n)], "weights": [1] * n},
    )
    assert resp.status_code == 422


def test_analyze_invalid_ticker_format_returns_422():
    resp = client.post(
        "/api/analyze",
        json={"tickers": ["AAPL", "'; DROP TABLE--"], "weights": [50, 50]},
    )
    assert resp.status_code == 422


FAKE_MVO_RESULT = {
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


def test_explain_is_deterministic_and_needs_no_api_key():
    # No external API, so no key to set up and no 503 case -- this always works.
    resp = client.post("/api/explain", json={"result": FAKE_MVO_RESULT})
    assert resp.status_code == 200
    explanation = resp.json()["explanation"]
    assert "VOO" in explanation and "BND" in explanation
    assert "Sharpe" in explanation
    # weights differ (0.6/0.4 optimal vs 0.5/0.5 current), so the weight-change
    # paragraph should narrate a shift, not "keep every position unchanged".
    assert "unchanged" not in explanation.lower() or "roughly unchanged" in explanation.lower()


def test_explain_same_output_for_same_input():
    # Template-based, so no run-to-run variance -- unlike an LLM call.
    resp1 = client.post("/api/explain", json={"result": FAKE_MVO_RESULT})
    resp2 = client.post("/api/explain", json={"result": FAKE_MVO_RESULT})
    assert resp1.json()["explanation"] == resp2.json()["explanation"]


def test_analyze_rate_limit_returns_429():
    # Fire one more request than the configured per-minute limit, using a
    # single-ticker body so each call fails fast on validation (400) rather
    # than hitting yfinance -- we're testing the limiter, not the pipeline.
    # (The autouse _reset_rate_limiter fixture already gives this test a
    # clean bucket to start from.)
    limit = int(ANALYZE_RATE_LIMIT.split("/")[0])
    responses = [
        client.post("/api/analyze", json={"tickers": ["AAPL"], "weights": [1.0]})
        for _ in range(limit + 1)
    ]
    assert responses[-1].status_code == 429
    assert all(r.status_code == 400 for r in responses[:-1])


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
    # Syntactically valid (<=10 chars, matches the ticker pattern) but not a
    # real security -- must reach the business-logic 400, not the 422 a
    # too-long or malformed string would trigger at request validation.
    resp = client.post(
        "/api/analyze",
        json={"tickers": ["AAPL", "ZZFAKEZZ"], "weights": [50, 50]},
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
