from __future__ import annotations

import unittest

from pangolin_eval.aggregation import summarize_aggregations
from pangolin_eval.models import PromptResult


class AggregationTest(unittest.TestCase):
    def test_summarize_aggregations_groups_by_feature(self) -> None:
        aggregations = summarize_aggregations(
            [
                PromptResult(
                    prompt_id="case-1",
                    model_id="model-a",
                    response="ok",
                    input_tokens=10,
                    output_tokens=5,
                    latency_ms=100,
                    estimated_cost_usd=0.01,
                    quality_score=1.0,
                    feature="support",
                ),
                PromptResult(
                    prompt_id="case-2",
                    model_id="model-a",
                    response="ok",
                    input_tokens=10,
                    output_tokens=5,
                    latency_ms=200,
                    estimated_cost_usd=0.02,
                    quality_score=0.5,
                    feature="support",
                ),
            ]
        )

        feature_summary = next(
            summary
            for summary in aggregations
            if summary.group_by == "feature" and summary.key == "support"
        )

        self.assertEqual(feature_summary.runs, 2)
        self.assertEqual(feature_summary.total_cost_usd, 0.03)
        self.assertEqual(feature_summary.avg_quality, 0.75)
        self.assertEqual(feature_summary.avg_latency_ms, 150)


if __name__ == "__main__":
    unittest.main()
