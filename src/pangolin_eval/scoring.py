from __future__ import annotations


def keyword_quality_score(response: str, expected_keywords: list[str]) -> float | None:
    if not expected_keywords:
        return None

    response_lower = response.lower()
    matches = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
    return matches / len(expected_keywords)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def estimate_message_tokens(messages: list[dict[str, str]]) -> int:
    content = "\n".join(message.get("content", "") for message in messages)
    return estimate_tokens(content)


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> float:
    input_cost = (input_tokens / 1_000_000) * input_price_per_1m
    output_cost = (output_tokens / 1_000_000) * output_price_per_1m
    return input_cost + output_cost
