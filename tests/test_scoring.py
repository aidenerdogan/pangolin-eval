from __future__ import annotations

import unittest

from pangolin_eval.models import QualityEvaluator
from pangolin_eval.scoring import (
    estimate_cost_usd,
    estimate_message_tokens,
    estimate_tokens,
    keyword_quality_score,
    prompt_quality_score,
)


class ScoringTest(unittest.TestCase):
    def test_keyword_quality_score(self) -> None:
        score = keyword_quality_score(
            "Use the refund policy and escalate unusual cases.",
            ["refund", "policy", "escalate", "order"],
        )
        self.assertEqual(score, 0.75)

    def test_estimate_cost_usd(self) -> None:
        cost = estimate_cost_usd(
            input_tokens=1000,
            output_tokens=500,
            input_price_per_1m=1.0,
            output_price_per_1m=2.0,
        )
        self.assertEqual(cost, 0.002)

    def test_prompt_quality_score_supports_weighted_evaluators(self) -> None:
        score = prompt_quality_score(
            "Refunds are available in 30 days.",
            ["refund"],
            [
                QualityEvaluator(type="regex", value=r"\b30 days\b", weight=2),
                QualityEvaluator(type="contains", value="escalate", weight=1),
            ],
        )

        self.assertEqual(score, 0.75)

    def test_estimate_tokens_supports_configurable_counters(self) -> None:
        self.assertEqual(estimate_tokens("one two three", "whitespace"), 3)
        self.assertEqual(estimate_tokens("12345678", "char_4"), 2)
        self.assertGreater(
            estimate_message_tokens(
                [{"role": "user", "content": "one two three"}],
                "openai_chat",
            ),
            estimate_message_tokens(
                [{"role": "user", "content": "one two three"}],
                "char_4",
            ),
        )


if __name__ == "__main__":
    unittest.main()
