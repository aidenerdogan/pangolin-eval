from __future__ import annotations

import unittest

from pangolin_eval.models import ModelSummary, PromptResult, RunReport
from pangolin_eval.recommendations import generate_recommendations


class RecommendationsTest(unittest.TestCase):
    def test_generate_recommendations_finds_model_switch_and_fallback(self) -> None:
        report = RunReport(
            run_name="recommend",
            description="",
            results=[
                PromptResult(
                    prompt_id="case-1",
                    model_id="expensive",
                    response="ok",
                    input_tokens=10,
                    output_tokens=5,
                    latency_ms=100,
                    estimated_cost_usd=0.10,
                    quality_score=1.0,
                ),
                PromptResult(
                    prompt_id="case-1",
                    model_id="cheap",
                    response="ok",
                    input_tokens=10,
                    output_tokens=5,
                    latency_ms=90,
                    estimated_cost_usd=0.01,
                    quality_score=0.98,
                ),
            ],
            summaries=[
                ModelSummary(
                    model_id="expensive",
                    runs=1,
                    success_count=1,
                    failure_count=0,
                    success_rate=1.0,
                    avg_quality=1.0,
                    avg_latency_ms=100,
                    max_latency_ms=100,
                    total_cost_usd=0.10,
                    efficiency_score=0.5,
                    recommendation="Best quality candidate",
                ),
                ModelSummary(
                    model_id="cheap",
                    runs=1,
                    success_count=1,
                    failure_count=0,
                    success_rate=1.0,
                    avg_quality=0.98,
                    avg_latency_ms=90,
                    max_latency_ms=90,
                    total_cost_usd=0.01,
                    efficiency_score=0.9,
                    recommendation="Good baseline",
                ),
                ModelSummary(
                    model_id="flaky",
                    runs=1,
                    success_count=0,
                    failure_count=1,
                    success_rate=0,
                    avg_quality=None,
                    avg_latency_ms=0,
                    max_latency_ms=0,
                    total_cost_usd=0,
                    efficiency_score=None,
                    recommendation="Provider failures",
                ),
            ],
        )

        recommendations = generate_recommendations(report)
        categories = {recommendation.category for recommendation in recommendations}

        self.assertIn("model_switch", categories)
        self.assertIn("fallback_review", categories)

    def test_generate_recommendations_flags_large_token_usage(self) -> None:
        report = RunReport(
            run_name="recommend",
            description="",
            results=[
                PromptResult(
                    prompt_id="long-case",
                    model_id="model",
                    response="ok",
                    input_tokens=1200,
                    output_tokens=600,
                    latency_ms=100,
                    estimated_cost_usd=0.01,
                    quality_score=1.0,
                )
            ],
            summaries=[],
        )

        categories = {
            recommendation.category
            for recommendation in generate_recommendations(report)
        }

        self.assertIn("context_trimming", categories)
        self.assertIn("max_token_cap", categories)


if __name__ == "__main__":
    unittest.main()
