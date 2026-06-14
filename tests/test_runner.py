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
                    model_group="small",
                    pricing_source="example_catalog",
                )
            ],
            prompts=[
                PromptCase(
                    id="case-1",
                    messages=[{"role": "user", "content": "What should support do?"}],
                    expected_keywords=["refund", "policy", "order", "escalate"],
                    feature="support",
                    workflow="refund",
                    environment="test",
                    prompt_version="v1",
                )
            ],
        )

        self.assertEqual(len(report.results), 1)
        self.assertEqual(len(report.summaries), 1)
        self.assertEqual(report.schema_version, REPORT_SCHEMA_VERSION)
        self.assertEqual(report.content_mode, "full")
        self.assertEqual(report.summaries[0].avg_quality, 1.0)
        self.assertEqual(report.summaries[0].success_rate, 1.0)
        self.assertEqual(report.summaries[0].recommendation, "Best quality candidate")
        self.assertEqual(report.results[0].feature, "support")
        self.assertEqual(report.results[0].workflow, "refund")
        self.assertEqual(report.results[0].model_group, "small")
        self.assertEqual(report.results[0].pricing_source, "example_catalog")
        self.assertTrue(
            any(
                aggregation.group_by == "feature" and aggregation.key == "support"
                for aggregation in report.aggregations
            )
        )

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

    def test_mock_provider_preserves_empty_response(self) -> None:
        report = run_comparison(
            run_name="test",
            description="",
            models=[
                ModelTarget(
                    id="mock-model",
                    provider="mock",
                    input_price_per_1m=0.1,
                    output_price_per_1m=0.2,
                    mock_response="fallback",
                    extra={"mock_responses": {"case-1": ""}},
                )
            ],
            prompts=[PromptCase(id="case-1", messages=[{"role": "user", "content": "Hi"}])],
        )

        self.assertEqual(report.results[0].response, "")
        self.assertEqual(report.results[0].output_tokens, 0)

    def test_provider_failure_is_reported_without_aborting_run(self) -> None:
        report = run_comparison(
            run_name="test",
            description="",
            models=[
                ModelTarget(
                    id="missing-key-model",
                    provider="openai_compatible",
                    input_price_per_1m=0.1,
                    output_price_per_1m=0.2,
                    base_url="https://api.example.test/v1",
                    api_key_env="PANGOLIN_EVAL_TEST_MISSING_KEY",
                    max_retries=1,
                ),
                ModelTarget(
                    id="mock-model",
                    provider="mock",
                    input_price_per_1m=0.1,
                    output_price_per_1m=0.2,
                    mock_response="refund policy order escalate",
                    mock_latency_ms=100,
                ),
            ],
            prompts=[
                PromptCase(
                    id="case-1",
                    messages=[{"role": "user", "content": "What should support do?"}],
                    expected_keywords=["refund", "policy", "order", "escalate"],
                )
            ],
        )

        failed = next(
            result for result in report.results if result.model_id == "missing-key-model"
        )
        succeeded = next(
            result for result in report.results if result.model_id == "mock-model"
        )

        self.assertFalse(failed.success)
        self.assertEqual(failed.status, "error")
        self.assertEqual(failed.retry_count, 1)
        self.assertIn("Environment variable", failed.error or "")
        self.assertTrue(succeeded.success)
        self.assertEqual(succeeded.quality_score, 1.0)

        failed_summary = next(
            summary for summary in report.summaries if summary.model_id == "missing-key-model"
        )
        self.assertEqual(failed_summary.success_count, 0)
        self.assertEqual(failed_summary.failure_count, 1)
        self.assertEqual(failed_summary.success_rate, 0)
        self.assertEqual(failed_summary.recommendation, "Provider failures")


if __name__ == "__main__":
    unittest.main()
