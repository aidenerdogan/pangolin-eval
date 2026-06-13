from __future__ import annotations

import unittest

from pangolin_eval.models import REPORT_SCHEMA_VERSION, ModelTarget, PromptCase
from pangolin_eval.runner import run_comparison


class RunnerTest(unittest.TestCase):
    def test_run_comparison_summarizes_models(self) -> None:
        report = run_comparison(
            run_name="test",
            description="",
            models=[
                ModelTarget(
                    id="mock-model",
                    provider="mock",
                    input_price_per_1m=0.1,
                    output_price_per_1m=0.2,
                    mock_response="refund policy order escalate",
                    mock_latency_ms=100,
                )
            ],
            prompts=[
                PromptCase(
                    id="case-1",
                    messages=[{"role": "user", "content": "What should support do?"}],
                    expected_keywords=["refund", "policy", "order", "escalate"],
                )
            ],
        )

        self.assertEqual(len(report.results), 1)
        self.assertEqual(len(report.summaries), 1)
        self.assertEqual(report.schema_version, REPORT_SCHEMA_VERSION)
        self.assertEqual(report.content_mode, "full")
        self.assertEqual(report.summaries[0].avg_quality, 1.0)
        self.assertEqual(report.summaries[0].recommendation, "Best quality candidate")

    def test_metadata_only_mode_omits_response_content_but_keeps_score(self) -> None:
        report = run_comparison(
            run_name="test",
            description="",
            models=[
                ModelTarget(
                    id="mock-model",
                    provider="mock",
                    input_price_per_1m=0.1,
                    output_price_per_1m=0.2,
                    mock_response="refund policy order escalate",
                    mock_latency_ms=100,
                )
            ],
            prompts=[
                PromptCase(
                    id="case-1",
                    messages=[{"role": "user", "content": "What should support do?"}],
                    expected_keywords=["refund", "policy", "order", "escalate"],
                )
            ],
            content_mode="metadata_only",
        )

        self.assertEqual(report.content_mode, "metadata_only")
        self.assertIsNone(report.results[0].response)
        self.assertEqual(report.results[0].quality_score, 1.0)
        self.assertTrue(report.results[0].metadata["response_content_omitted"])


if __name__ == "__main__":
    unittest.main()
