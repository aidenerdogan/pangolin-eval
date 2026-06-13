from __future__ import annotations

import unittest

from pangolin_eval.gates import evaluate_gates, gates_passed
from pangolin_eval.models import ModelSummary, PromptResult, RunReport


def report() -> RunReport:
    return RunReport(
        run_name="gated",
        description="",
        results=[
            PromptResult(
                prompt_id="case-1",
                model_id="mock-model",
                response="refund policy",
                input_tokens=10,
                output_tokens=4,
                latency_ms=100,
                estimated_cost_usd=0.00001,
                quality_score=1.0,
            ),
            PromptResult(
                prompt_id="case-2",
                model_id="mock-model",
                response=None,
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                estimated_cost_usd=0,
                quality_score=None,
                success=False,
                status="error",
                error="RuntimeError: provider failed",
            ),
        ],
        summaries=[
            ModelSummary(
                model_id="mock-model",
                runs=2,
                success_count=1,
                failure_count=1,
                success_rate=0.5,
                avg_quality=1.0,
                avg_latency_ms=100,
                max_latency_ms=100,
                total_cost_usd=0.00001,
                efficiency_score=0.9,
                recommendation="Review reliability",
            )
        ],
    )


class GatesTest(unittest.TestCase):
    def test_evaluate_gates_passes_when_thresholds_are_met(self) -> None:
        gate_results = evaluate_gates(
            report(),
            {
                "max_total_cost_usd": 0.001,
                "min_avg_quality": 0.9,
                "min_success_rate": 0.5,
            },
        )

        self.assertTrue(gates_passed(gate_results))
        self.assertEqual(len(gate_results), 3)

    def test_evaluate_gates_fails_when_thresholds_are_missed(self) -> None:
        gate_results = evaluate_gates(
            report(),
            {
                "max_latency_ms": 50,
                "min_success_rate": 1.0,
            },
        )

        self.assertFalse(gates_passed(gate_results))
        self.assertEqual([result.passed for result in gate_results], [False, False])


if __name__ == "__main__":
    unittest.main()
