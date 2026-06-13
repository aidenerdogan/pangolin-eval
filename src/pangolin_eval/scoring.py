from __future__ import annotations

import re

from pangolin_eval.models import (
    SUPPORTED_EVALUATOR_TYPES,
    SUPPORTED_TOKEN_COUNTERS,
    QualityEvaluator,
)


def keyword_quality_score(response: str, expected_keywords: list[str]) -> float | None:
    if not expected_keywords:
        return None

    response_lower = response.lower()
    matches = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
    return matches / len(expected_keywords)


def evaluator_quality_score(
    response: str,
    evaluators: list[QualityEvaluator],
) -> float | None:
    if not evaluators:
        return None

    total_weight = sum(evaluator.weight for evaluator in evaluators)
    if total_weight <= 0:
        return None

    weighted_matches = sum(
        evaluator.weight
        for evaluator in evaluators
        if evaluator_matches(response, evaluator)
    )
    return weighted_matches / total_weight


def prompt_quality_score(
    response: str,
    expected_keywords: list[str],
    evaluators: list[QualityEvaluator] | None = None,
) -> float | None:
    checks = [
        QualityEvaluator(type="keyword", value=keyword)
        for keyword in expected_keywords
    ]
    checks.extend(evaluators or [])
    return evaluator_quality_score(response, checks)


def evaluator_matches(response: str, evaluator: QualityEvaluator) -> bool:
    if evaluator.type not in SUPPORTED_EVALUATOR_TYPES:
        raise ValueError(f"Unsupported evaluator type '{evaluator.type}'.")

    if evaluator.type == "regex":
        flags = 0 if evaluator.case_sensitive else re.IGNORECASE
        return re.search(evaluator.value, response, flags=flags) is not None

    response_text = response if evaluator.case_sensitive else response.lower()
    expected = evaluator.value if evaluator.case_sensitive else evaluator.value.lower()
    if evaluator.type in {"keyword", "contains"}:
        return expected in response_text
    if evaluator.type == "exact":
        return response_text.strip() == expected.strip()
    return False


def estimate_tokens(text: str, token_counter: str = "char_4") -> int:
    if token_counter not in SUPPORTED_TOKEN_COUNTERS:
        supported = ", ".join(sorted(SUPPORTED_TOKEN_COUNTERS))
        raise ValueError(
            f"Unsupported token counter '{token_counter}'. Supported counters: {supported}."
        )
    if not text:
        return 0
    if token_counter == "whitespace":
        return max(1, len(text.split()))
    return max(1, round(len(text) / 4))


def estimate_message_tokens(
    messages: list[dict[str, str]],
    token_counter: str = "char_4",
) -> int:
    if token_counter == "openai_chat":
        if not messages:
            return 0
        per_message_overhead = 4
        reply_overhead = 3
        return (
            sum(
                per_message_overhead
                + estimate_tokens(message.get("content", ""), "char_4")
                for message in messages
            )
            + reply_overhead
        )
    content = "\n".join(message.get("content", "") for message in messages)
    return estimate_tokens(content, token_counter)


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> float:
    input_cost = (input_tokens / 1_000_000) * input_price_per_1m
    output_cost = (output_tokens / 1_000_000) * output_price_per_1m
    return input_cost + output_cost
