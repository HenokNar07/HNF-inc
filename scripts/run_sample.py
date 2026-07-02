#!/usr/bin/env python
"""Run the math engine on a sample portfolio and print output for manual
verification against Portfolio Visualizer's "Efficient Frontier" tool.

Usage:
    python scripts/run_sample.py
    python scripts/run_sample.py --tickers VOO,AAPL,BND --weights 40,35,25 --years 5

To compare against Portfolio Visualizer:
  1. Go to Portfolio Visualizer -> Efficient Frontier.
  2. Enter the same tickers/weights, same time period (this defaults to the
     trailing 5 years of monthly data), and use "Arithmetic Mean" returns
     (not geometric) -- that's the convention this engine uses too.
  3. Compare: per-asset arithmetic mean return & std dev, the correlation
     matrix, your portfolio's expected return/std dev/Sharpe, and the max
     Sharpe (tangency) portfolio's weights and stats.
  Small differences (~tens of bps) are expected due to data vendor
  differences and exact date-range alignment; large differences mean
  something is wrong.
"""
from __future__ import annotations

import argparse
import sys

from math_engine import data, stats
from math_engine.pipeline import run_mvo


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", default="VOO,AAPL,BND", help="Comma-separated tickers")
    parser.add_argument("--weights", default="40,35,25", help="Comma-separated weights (% or fraction)")
    parser.add_argument("--years", type=float, default=5, help="Lookback period in years")
    parser.add_argument("--max-weight", type=float, default=0.40, help="Per-asset weight cap (fraction)")
    return parser.parse_args()


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def print_header(title: str):
    print()
    print(title)
    print("-" * len(title))


def main():
    args = parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    weights = [float(w.strip()) for w in args.weights.split(",")]

    print(f"Running MVO for {tickers} @ {weights} over {args.years}y lookback...")
    result = run_mvo(tickers, weights, lookback_years=args.years, max_weight=args.max_weight)

    if result.warnings:
        print_header("Warnings")
        for w in result.warnings:
            print(f"  - {w}")

    print_header("Per-asset stats (annualized, vs. Portfolio Visualizer's asset statistics)")
    print(f"{'Ticker':<8}{'Mean Return':>14}{'Std Dev':>12}{'Beta vs SPY':>14}")
    for a in result.asset_stats:
        print(f"{a.ticker:<8}{pct(a.mean_return):>14}{pct(a.std_dev):>12}{a.beta:>14.3f}")

    print_header("Risk-free rate")
    print(f"  {pct(result.risk_free_rate)}  (source: {result.risk_free_source})")

    print_header("Your current portfolio")
    for t, w in result.current_portfolio.weights.items():
        print(f"  {t}: {pct(w)}")
    print(f"  Expected return: {pct(result.current_portfolio.expected_return)}")
    print(f"  Std dev:         {pct(result.current_portfolio.std_dev)}")
    print(f"  Sharpe ratio:    {result.current_portfolio.sharpe_ratio:.3f}")

    print_header("Max Sharpe (tangency) portfolio -- compare to PV's 'Tangency Portfolio'")
    for t, w in result.max_sharpe.weights.items():
        print(f"  {t}: {pct(w)}")
    print(f"  Expected return: {pct(result.max_sharpe.expected_return)}")
    print(f"  Std dev:         {pct(result.max_sharpe.std_dev)}")
    print(f"  Sharpe ratio:    {result.max_sharpe.sharpe_ratio:.3f}")

    print_header("Global min variance portfolio -- compare to PV's 'Minimum Variance Portfolio'")
    for t, w in result.min_variance.weights.items():
        print(f"  {t}: {pct(w)}")
    print(f"  Expected return: {pct(result.min_variance.expected_return)}")
    print(f"  Std dev:         {pct(result.min_variance.std_dev)}")
    print(f"  Sharpe ratio:    {result.min_variance.sharpe_ratio:.3f}")

    print_header(f"Efficient frontier ({len(result.frontier)} points, min -> max return)")
    print(f"{'Return':>10}{'Std Dev':>12}")
    step = max(len(result.frontier) // 10, 1)
    for p in result.frontier[::step]:
        print(f"{pct(p.expected_return):>10}{pct(p.std_dev):>12}")

    # Also print the raw annualized covariance/correlation matrix -- Portfolio
    # Visualizer shows a correlation matrix on the asset statistics page,
    # which is the easiest single number to eyeball-compare.
    asset_returns, _ = data.fetch_monthly_returns_with_market(tickers, args.years)
    corr = asset_returns.corr()
    print_header("Correlation matrix (monthly returns, vs. PV's correlation matrix)")
    print(corr.round(3).to_string())


if __name__ == "__main__":
    sys.exit(main())
