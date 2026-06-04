from __future__ import annotations

import unittest

from pangolin_eval.scoring import estimate_cost_usd, keyword_quality_score


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


if __name__ == "__main__":
    unittest.main()
