from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pangolin_eval.exports import OTEL_EXPORT_SCHEMA_VERSION, export_otel_artifact, write_otel_export


class ExportsTest(unittest.TestCase):
    def test_export_report_to_otel_spans(self) -> None:
        export = export_otel_artifact(
            {
                "schema_version": "pangolin-eval.report.v4",
                "results": [
                    {
                        "model_id": "mock-model",
                        "prompt_id": "case-1",
                        "status": "success",
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "estimated_cost_usd": 0.01,
                        "quality_score": 1.0,
                        "success": True,
                    }
                ],
            }
        )

        self.assertEqual(export["schema_version"], OTEL_EXPORT_SCHEMA_VERSION)
        self.assertEqual(export["spans"][0]["kind"], "llm")
        self.assertEqual(export["spans"][0]["attributes"]["pangolin.model_id"], "mock-model")

    def test_write_otel_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "otel.json"

            write_otel_export(
                {
                    "schema_version": "pangolin-eval.tracecards.v1",
                    "tracecards": [
                        {
                            "task_id": "task-1",
                            "events": [
                                {
                                    "id": "e1",
                                    "event_type": "tool_call",
                                    "name": "lookup",
                                    "success": True,
                                }
                            ],
                        }
                    ],
                },
                out_path,
            )

            payload = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["schema_version"], OTEL_EXPORT_SCHEMA_VERSION)
        self.assertEqual(payload["spans"][0]["kind"], "tool_call")


if __name__ == "__main__":
    unittest.main()
