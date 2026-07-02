"""Price data fetching and return computation.

Design note: we always pull SPY alongside the user's tickers (deduped) because
per-asset beta is computed against the market portfolio proxy, and we'd rather
fetch it once here than special-case it in every caller.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import yfinance as yf

MARKET_PROXY = "SPY"

# Below this many monthly observations, covariance/beta estimates are too
# noisy to be meaningful (a 5-year lookback gives ~60; we want a hard floor
# well under that so short-but-usable histories, e.g. a recent IPO, still work).
MIN_MONTHS_REQUIRED = 12


class TickerDataError(ValueError):
    """Raised when requested tickers can't be fetched or are invalid."""


def fetch_adjusted_close(tickers: list[str], lookback_years: float = 5) -> pd.DataFrame:
    """Fetch daily adjusted close prices for the given tickers.

    Returns a DataFrame indexed by date, one column per ticker. Raises
    TickerDataError if any ticker returns no data (typically an invalid symbol).

    Uses explicit start/end dates rather than yfinance's `period=` shorthand,
    which only accepts a fixed enum ("5y", "2y", ...) and rejects anything
    else (including a perfectly reasonable float like "5.0y" or "2.5y").
    """
    end = dt.date.today()
    start = end - dt.timedelta(days=round(lookback_years * 365.25))
    raw = yf.download(
        tickers,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="column",
    )

    if raw.empty:
        raise TickerDataError(
            f"No price data returned for {tickers}. Check the ticker symbols."
        )

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        # yfinance flattens columns when only one ticker is requested.
        prices = raw[["Close"]]
        prices.columns = tickers

    missing = [t for t in tickers if t not in prices.columns or prices[t].dropna().empty]
    if missing:
        raise TickerDataError(
            f"No price data for ticker(s): {missing}. Check the symbol(s) are correct."
        )

    return prices.dropna(how="all")


def compute_monthly_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Resample daily prices to month-end and compute simple monthly returns."""
    monthly_prices = prices.resample("ME").last()
    returns = monthly_prices.pct_change().dropna(how="all")
    return returns


def fetch_monthly_returns_with_market(
    tickers: list[str], lookback_years: float = 5
) -> tuple[pd.DataFrame, pd.Series]:
    """Fetch monthly returns for `tickers` plus the market proxy (SPY) for beta.

    Returns (asset_returns, market_returns). If SPY is itself one of the
    requested tickers, market_returns is just that column, no double fetch.
    """
    fetch_list = list(dict.fromkeys(tickers + [MARKET_PROXY]))  # dedup, preserve order
    prices = fetch_adjusted_close(fetch_list, lookback_years)
    returns = compute_monthly_returns(prices)

    if len(returns) < MIN_MONTHS_REQUIRED:
        raise TickerDataError(
            f"Only {len(returns)} months of overlapping price history available "
            f"for {tickers}; need at least {MIN_MONTHS_REQUIRED}. Try a longer "
            "lookback or a different ticker (recent IPOs often lack history)."
        )

    asset_returns = returns[tickers]
    market_returns = returns[MARKET_PROXY]
    return asset_returns, market_returns
