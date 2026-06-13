from __future__ import annotations

import unittest

from pangolin_eval.tracecards import generate_tracecard, generate_tracecard_report


class TraceCardsTest(unittest.TestCase):
    def test_generate_tracecard_summarizes_cost_failures_and_repeated_steps(self) -> None:
        card = generate_tracecard(
            task_id="task-1",
            outcome="failed",
            raw_events=[
                {
                    "id": "e1",
                    "event_type": "llm_call",
                    "name": "plan",
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "latency_ms": 200,
                    "estimated_cost_usd": 0.01,
                },
                {
                    "id": "e2",
                    "event_type": "tool_call",
                    "name": "lookup",
                    "latency_ms": 50,
                    "success": False,
                    "retry_count": 1,
                },
                {
                    "id": "e3",
                    "event_type": "tool_call",
                    "name": "lookup",
                    "latency_ms": 50,
                    "success": False,
                },
            ],
        )

        self.assertFalse(card.success)
        self.assertEqual(card.total_cost_usd, 0.01)
        self.assertEqual(card.total_latency_ms, 300)
        self.assertEqual(card.failure_count, 2)
        self.assertEqual(card.retry_count, 1)
        self.assertEqual(card.repeated_step_count, 1)
        self.assertIsNone(card.cost_per_successful_task_usd)

    def test_generate_tracecard_report(self) -> None:
        report = generate_tracecard_report(
            {
                "run_name": "trace",
                "description": "",
                "traces": [
                    {
                        "task_id": "task-1",
                        "outcome": "success",
                        "events": [
                            {
                                "id": "e1",
                                "event_type": "cache_read",
                                "name": "cache",
                                "cache_hit": True,
                            }
                        ],
                    }
                ],
            }
        )

        self.assertEqual(report.schema_version, "pangolin-eval.tracecards.v1")
        self.assertEqual(report.tracecards[0].cache_hit_count, 1)


if __name__ == "__main__":
    unittest.main()
