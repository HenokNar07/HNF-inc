"""Plain-English narration of already-computed MVO results -- template-based,
no external API call.

Hard boundary unchanged from the original design: this module only turns
numbers into words. It never computes, estimates, or alters a financial
number itself -- every figure used here was produced deterministically by
math_engine. The difference from an LLM-backed version is just the
mechanism: fixed prose templates filled in with those numbers, instead of
a model call. That means zero marginal cost, no external API dependency,
and no risk of the model saying something it wasn't supposed to.
"""
from __future__ import annotations

from math_engine.types import MVOResult

# Rough, deliberately coarse buckets for describing a Sharpe ratio gap in
# words. A 0.1 difference in Sharpe ratio is a meaningfully better
# risk-adjusted return in practice; boundaries are a narration aid, not a
# statistical claim.
_SHARPE_GAP_NEAR = 0.02
_SHARPE_GAP_MODEST = 0.10
_SHARPE_GAP_MEANINGFUL = 0.25

# Weight differences smaller than this are treated as "unchanged" rather
# than narrated as a shift -- avoids narrating noise-level rebalancing.
_WEIGHT_CHANGE_THRESHOLD = 0.005


def _describe_sharpe_gap(gap: float) -> str:
    if gap <= _SHARPE_GAP_NEAR:
        return (
            "That's a very small gap -- your allocation is already close to the "
            "mathematically optimal one for the assets you picked."
        )
    if gap <= _SHARPE_GAP_MODEST:
        return "That's a modest gap -- a real but not dramatic difference in efficiency."
    if gap <= _SHARPE_GAP_MEANINGFUL:
        return (
            "That's a meaningful gap -- the optimal mix earns noticeably more "
            "return for the same amount of risk."
        )
    return (
        "That's a substantial gap -- the optimal mix is considerably more "
        "efficient at turning risk into return than your current allocation."
    )


def _describe_risk_return_position(current, optimal) -> str:
    more_risk = current.std_dev > optimal.std_dev
    more_return = current.expected_return > optimal.expected_return
    if more_risk and not more_return:
        return (
            "You're carrying more risk than the optimal allocation while earning "
            "a lower expected return -- the least efficient combination of the two."
        )
    if not more_risk and more_return:
        return (
            "You're earning a higher expected return than the optimal allocation "
            "while also taking on less risk -- an unusual combination, worth "
            "double-checking your inputs if it looks surprising."
        )
    if more_risk and more_return:
        return (
            "You're taking on more risk than the optimal allocation, but also "
            "earning a higher expected return for it."
        )
    return (
        "You're taking on less risk than the optimal allocation, which also "
        "means accepting a lower expected return."
    )


def _join_naturally(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _format_weight_changes(current: dict[str, float], optimal: dict[str, float], tickers: list[str]) -> str:
    changes: list[str] = []
    unchanged: list[str] = []
    for ticker in tickers:
        cur = current.get(ticker, 0.0)
        opt = optimal.get(ticker, 0.0)
        delta = opt - cur
        if abs(delta) < _WEIGHT_CHANGE_THRESHOLD:
            unchanged.append(ticker)
            continue
        direction = "increase" if delta > 0 else "decrease"
        changes.append(f"{direction} {ticker} from {cur:.0%} to {opt:.0%} ({delta:+.0%})")

    if not changes:
        return "It would keep every position essentially where it already is."

    changes_text = _join_naturally(changes)
    if unchanged:
        unchanged_text = _join_naturally(unchanged)
        return f"It would {changes_text}, while leaving {unchanged_text} roughly unchanged."
    return f"It would {changes_text}."


def generate_explanation(result: MVOResult) -> str:
    current = result.current_portfolio
    optimal = result.max_sharpe

    sharpe_gap = optimal.sharpe_ratio - current.sharpe_ratio

    paragraph_1 = (
        f"Your portfolio has an expected annual return of {current.expected_return:.1%} "
        f"with volatility (a measure of how much its value tends to swing around that "
        f"average) of {current.std_dev:.1%}. The mathematically optimal allocation for "
        f"these same assets -- the point on the efficient frontier with the best "
        f"risk-adjusted return -- targets {optimal.expected_return:.1%} return at "
        f"{optimal.std_dev:.1%} volatility. {_describe_risk_return_position(current, optimal)}"
    )

    paragraph_2 = (
        f"The Sharpe ratio measures how much return you're earning per unit of risk "
        f"taken -- higher means more efficient. Yours is {current.sharpe_ratio:.2f}; "
        f"the optimal allocation reaches {optimal.sharpe_ratio:.2f}. "
        f"{_describe_sharpe_gap(sharpe_gap)}"
    )

    weight_change_text = _format_weight_changes(current.weights, optimal.weights, result.tickers)
    return_model_note = (
        " Expected returns here come from a Fama-French 3-factor regression "
        "(market, size, and value exposure) rather than each asset's raw "
        "historical average -- a way of estimating return from risk exposure "
        "instead of from noisy past performance alone."
        if result.return_model == "fama_french"
        else ""
    )
    paragraph_3 = (
        f"Compared to your current weights, the mathematically optimal allocation "
        f"under Markowitz assumptions differs like this: {weight_change_text} This "
        f"isn't a recommendation to buy or sell anything -- it's what the math says "
        f"would have maximized risk-adjusted return over the lookback period you "
        f"selected, based on historical patterns that may not repeat.{return_model_note}"
    )

    return "\n\n".join([paragraph_1, paragraph_2, paragraph_3])
