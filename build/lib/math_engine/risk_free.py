"""Risk-free rate lookup: U.S. Treasury Fiscal Data API, with a hardcoded fallback.

The Sharpe ratio needs a risk-free rate. We use the official U.S. Treasury
Fiscal Data API's "Average Interest Rates on U.S. Treasury Securities"
dataset, filtered to Treasury Bills -- a monthly average interest rate
across outstanding T-bills. It's a coarser cadence than a daily quote (and
an average across bill maturities rather than a single 3-month yield), but
that's more than precise enough for a Sharpe ratio input, and the upside is
real: it's free, official, and requires no API key or signup at all -- one
less thing anyone running this app needs to configure.

If the request fails for any reason, we fall back to a hardcoded
approximate rate rather than failing the whole analysis -- callers should
surface `source` to the user so a stale fallback isn't mistaken for a live
rate.
"""
from __future__ import annotations

import requests

TREASURY_API_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/"
    "accounting/od/avg_interest_rates"
)

# Approximate average T-bill interest rate, expressed as a decimal (e.g.
# 0.037 = 3.7%). This is a fallback only, used when the Treasury API is
# unreachable -- update periodically to keep it in the right ballpark.
FALLBACK_RISK_FREE_RATE = 0.037

REQUEST_TIMEOUT_SECONDS = 5


def get_risk_free_rate() -> tuple[float, str]:
    """Return (annual_risk_free_rate, source) where source is 'treasury' or 'fallback'."""
    params = {
        "filter": "security_desc:eq:Treasury Bills",
        "sort": "-record_date",
        "page[size]": 1,
    }
    try:
        resp = requests.get(TREASURY_API_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        rows = resp.json().get("data", [])
        if rows:
            rate = rows[0].get("avg_interest_rate_amt")
            if rate is not None:
                return round(float(rate) / 100.0, 6), "treasury"
        return FALLBACK_RISK_FREE_RATE, "fallback"
    except (requests.RequestException, ValueError, KeyError):
        return FALLBACK_RISK_FREE_RATE, "fallback"
