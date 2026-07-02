"""Risk-free rate lookup: FRED 3-month T-bill, with a hardcoded fallback.

The Sharpe ratio needs a risk-free rate. We use the FRED series DGS3MO
(3-Month Treasury Bill Secondary Market Rate, daily). If FRED_API_KEY isn't
set, or the request fails, we fall back to a hardcoded approximate rate
rather than failing the whole analysis -- callers should surface `source`
to the user so a stale fallback isn't mistaken for a live rate.
"""
from __future__ import annotations

import os

import requests

FRED_SERIES_ID = "DGS3MO"
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

# Approximate 3-month T-bill rate, expressed as a decimal (e.g. 0.045 = 4.5%).
# This is a fallback only -- update periodically. It exists so the app still
# functions (with a visible "fallback" label) when no FRED_API_KEY is set.
FALLBACK_RISK_FREE_RATE = 0.045

REQUEST_TIMEOUT_SECONDS = 5


def get_risk_free_rate(api_key: str | None = None) -> tuple[float, str]:
    """Return (annual_risk_free_rate, source) where source is 'fred' or 'fallback'."""
    key = api_key or os.environ.get("FRED_API_KEY")
    if not key:
        return FALLBACK_RISK_FREE_RATE, "fallback"

    params = {
        "series_id": FRED_SERIES_ID,
        "api_key": key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 5,
    }
    try:
        resp = requests.get(FRED_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        observations = resp.json().get("observations", [])
        for obs in observations:
            value = obs.get("value")
            if value not in (None, "."):  # FRED uses "." for missing data
                return round(float(value) / 100.0, 6), "fred"
        return FALLBACK_RISK_FREE_RATE, "fallback"
    except (requests.RequestException, ValueError, KeyError):
        return FALLBACK_RISK_FREE_RATE, "fallback"
