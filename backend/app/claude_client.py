"""Plain-English narration of already-computed MVO results, via Claude.

Hard boundary: this module only turns numbers into words. It never computes,
estimates, or infers a financial number itself -- every figure that reaches
the prompt was produced deterministically by math_engine. If a number here
is wrong, the bug is in math_engine, not in this file.
"""
from __future__ import annotations

from anthropic import Anthropic

from math_engine.types import MVOResult

from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

SYSTEM_PROMPT = """\
You are explaining a mean-variance (Markowitz) portfolio analysis to someone \
with no finance background. You are given pre-computed numbers -- never \
calculate, estimate, or alter any number yourself, only explain the ones provided.

Rules:
- Plain language. If you use a finance term (Sharpe ratio, standard deviation, \
efficient frontier, beta), define it briefly in the same sentence.
- No hype, no urgency, no superlatives.
- Never phrase anything as advice or a recommendation to buy, sell, or rebalance. \
Refer to the optimizer's output as "the mathematically optimal allocation under \
Markowitz assumptions," not as what the user "should" do.
- Cover exactly three things, in this order: (1) where the user's portfolio \
sits relative to the efficient frontier, (2) what the Sharpe ratio gap between \
their portfolio and the max-Sharpe portfolio means in everyday terms, (3) what \
the optimal weights are and why they differ from the user's current weights.
- 3-4 short paragraphs. Narrate the numbers, don't just list them back.
"""


def _format_weights(weights: dict[str, float]) -> str:
    return ", ".join(f"{ticker}: {weight:.1%}" for ticker, weight in weights.items())


def build_user_prompt(result: MVOResult) -> str:
    current = result.current_portfolio
    optimal = result.max_sharpe

    lines = [
        f"Risk-free rate used: {result.risk_free_rate:.2%} (source: {result.risk_free_source}).",
        "",
        "User's current portfolio:",
        f"  Weights: {_format_weights(current.weights)}",
        f"  Expected annual return: {current.expected_return:.2%}",
        f"  Annual volatility (std dev): {current.std_dev:.2%}",
        f"  Sharpe ratio: {current.sharpe_ratio:.3f}",
        "",
        "Mathematically optimal (max Sharpe) portfolio under Markowitz assumptions:",
        f"  Weights: {_format_weights(optimal.weights)}",
        f"  Expected annual return: {optimal.expected_return:.2%}",
        f"  Annual volatility (std dev): {optimal.std_dev:.2%}",
        f"  Sharpe ratio: {optimal.sharpe_ratio:.3f}",
        "",
        "Per-asset stats:",
    ]
    for asset in result.asset_stats:
        lines.append(
            f"  {asset.ticker}: mean return {asset.mean_return:.2%}, "
            f"std dev {asset.std_dev:.2%}, beta vs S&P 500 {asset.beta:.2f}"
        )
    return "\n".join(lines)


def generate_explanation(result: MVOResult) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. AI explanations require it; portfolio "
            "analysis and charting work fine without it."
        )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(result)}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
