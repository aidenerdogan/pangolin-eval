from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pangolin_eval.models import (
    REPORT_SCHEMA_VERSION,
    GateResult,
    ModelSummary,
    PromptResult,
    RagReport,
    RagResult,
    RunReport,
    TraceCard,
    TraceCardReport,
    TraceEvent,
)
from pangolin_eval.reporting import (
    render_markdown,
    render_rag_markdown,
    render_tracecard_markdown,
    write_reports,
)


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
                success_count=1,
                failure_count=0,
                success_rate=1.0,
                avg_quality=1.0,
                avg_latency_ms=123,
                max_latency_ms=123,
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
        self.assertIn(f"- Schema version: `{REPORT_SCHEMA_VERSION}`", markdown)
        self.assertIn("- Content mode: `full`", markdown)
        self.assertIn(
            "| mock-model | 1 | 1.00 | 1.00 | 123 | 123 | 0.00000120 | 0.89 |",
            markdown,
        )
        self.assertIn("### mock-model / case-1", markdown)
        self.assertIn("- Status: success", markdown)
        self.assertIn("Use the refund policy.", markdown)

    def test_render_markdown_includes_gate_results(self) -> None:
        report = RunReport(
            run_name="sample",
            description="",
            results=sample_report().results,
            summaries=sample_report().summaries,
            gate_results=[
                GateResult(
                    name="max_total_cost_usd",
                    passed=False,
                    actual=0.2,
                    threshold=0.1,
                    comparator="<=",
                )
            ],
        )

        markdown = render_markdown(report)

        self.assertIn("## Gate Results", markdown)
        self.assertIn("| max_total_cost_usd | fail | 0.200000 | 0.100000 | <= |", markdown)

    def test_render_markdown_notes_when_response_content_is_omitted(self) -> None:
        report = sample_report()
        report.results[0] = PromptResult(
            prompt_id="case-1",
            model_id="mock-model",
            response=None,
            input_tokens=10,
            output_tokens=6,
            latency_ms=123,
            estimated_cost_usd=0.0000012,
            quality_score=1.0,
        )
        report = RunReport(
            run_name=report.run_name,
            description=report.description,
            results=report.results,
            summaries=report.summaries,
            content_mode="metadata_only",
        )

        markdown = render_markdown(report)

        self.assertIn("- Content mode: `metadata_only`", markdown)
        self.assertIn("Response content omitted", markdown)
        self.assertNotIn("```text", markdown)

    def test_write_reports_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path, markdown_path = write_reports(sample_report(), temp_dir)

            self.assertEqual(json_path, Path(temp_dir) / "report.json")
            self.assertEqual(markdown_path, Path(temp_dir) / "report.md")
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_name"], "sample")
            self.assertEqual(payload["schema_version"], REPORT_SCHEMA_VERSION)
            self.assertEqual(payload["content_mode"], "full")
            self.assertIn("## Model Summary", markdown_path.read_text(encoding="utf-8"))

    def test_report_schema_file_matches_runtime_version(self) -> None:
        schema = json.loads(
            Path("schemas/report.v3.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            REPORT_SCHEMA_VERSION,
        )

    def test_render_rag_markdown_includes_metrics(self) -> None:
        report = RagReport(
            run_name="rag",
            description="",
            results=[
                RagResult(
                    question_id="case-1",
                    model_id="mock-model",
                    response="Use [doc-1].",
                    retrieved_context_tokens=10,
                    answer_tokens=4,
                    latency_ms=100,
                    estimated_cost_usd=0.001,
                    answer_coverage=1.0,
                    faithfulness_score=1.0,
                    context_efficiency=100.0,
                    unused_context_signal=0,
                    missing_citation=False,
                )
            ],
        )

        markdown = render_rag_markdown(report)

        self.assertIn("## RAG Results", markdown)
        self.assertIn("| mock-model | case-1 | 1.00 | 1.00 |", markdown)

    def test_render_tracecard_markdown_includes_summary(self) -> None:
        report = TraceCardReport(
            run_name="trace",
            description="",
            tracecards=[
                TraceCard(
                    task_id="task-1",
                    outcome="success",
                    success=True,
                    events=[
                        TraceEvent(
                            id="e1",
                            event_type="llm_call",
                            name="answer",
                            estimated_cost_usd=0.01,
                            latency_ms=100,
                        )
                    ],
                    total_cost_usd=0.01,
                    total_latency_ms=100,
                    input_tokens=10,
                    output_tokens=5,
                    retry_count=0,
                    failure_count=0,
                    cache_hit_count=0,
                    repeated_step_count=0,
                    cost_per_successful_task_usd=0.01,
                )
            ],
        )

        markdown = render_tracecard_markdown(report)

        self.assertIn("## TraceCards", markdown)
        self.assertIn("| task-1 | success | 0.01000000 |", markdown)


if __name__ == "__main__":
    unittest.main()
