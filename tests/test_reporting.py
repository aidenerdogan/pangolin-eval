from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pangolin_eval.models import ModelSummary, PromptResult, RunReport
from pangolin_eval.reporting import render_markdown, write_reports


def sample_report() -> RunReport:
    return RunReport(
        run_name="sample",
        description="A compact comparison.",
        results=[
            PromptResult(
                prompt_id="case-1",
                model_id="mock-model",
                response="Use the refund policy.",
                input_tokens=10,
                output_tokens=6,
                latency_ms=123,
                estimated_cost_usd=0.0000012,
                quality_score=1.0,
            )
        ],
        summaries=[
            ModelSummary(
                model_id="mock-model",
                runs=1,
                avg_quality=1.0,
                avg_latency_ms=123,
                total_cost_usd=0.0000012,
                efficiency_score=0.89,
                recommendation="Best quality candidate",
            )
        ],
    )


class ReportingTest(unittest.TestCase):
    def test_render_markdown_includes_summary_and_prompt_result(self) -> None:
        markdown = render_markdown(sample_report())

        self.assertIn("# sample", markdown)
        self.assertIn("| mock-model | 1 | 1.00 | 123 | 0.00000120 | 0.89 |", markdown)
        self.assertIn("### mock-model / case-1", markdown)
        self.assertIn("Use the refund policy.", markdown)

    def test_write_reports_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path, markdown_path = write_reports(sample_report(), temp_dir)

            self.assertEqual(json_path, Path(temp_dir) / "report.json")
            self.assertEqual(markdown_path, Path(temp_dir) / "report.md")
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_name"], "sample")
            self.assertIn("## Model Summary", markdown_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
