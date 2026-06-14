from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import pangolin_eval
from pangolin_eval.cli import main


class CliTest(unittest.TestCase):
    def test_version_flag_prints_package_version(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn(pangolin_eval.__version__, stdout.getvalue())

    def test_validate_command_accepts_example_config(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "validate",
                    "--config",
                    "examples/simple_model_compare/config.json",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Config is valid", stdout.getvalue())

    def test_validate_command_reports_invalid_json_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "bad.json"
            config_path.write_text("{", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                exit_code = main(["validate", "--config", str(config_path)])

        self.assertEqual(exit_code, 2)
        self.assertIn("not valid JSON", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_run_command_supports_metadata_only_content_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run",
                        "--config",
                        "examples/simple_model_compare/config.json",
                        "--out",
                        temp_dir,
                        "--content-mode",
                        "metadata-only",
                        "--html",
                    ]
                )

            payload = json.loads(
                (Path(temp_dir) / "report.json").read_text(encoding="utf-8")
            )
            html_exists = (Path(temp_dir) / "report.html").exists()

        self.assertEqual(exit_code, 0)
        self.assertIn("Wrote JSON report", stdout.getvalue())
        self.assertEqual(payload["content_mode"], "metadata_only")
        self.assertIsNone(payload["results"][0]["response"])
        self.assertTrue(payload["results"][0]["metadata"]["response_content_omitted"])
        self.assertTrue(html_exists)

    def test_run_command_returns_nonzero_when_gates_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            out_dir = Path(temp_dir) / "reports"
            config = json.loads(
                Path("examples/simple_model_compare/config.json").read_text(
                    encoding="utf-8"
                )
            )
            config.pop("pricing_catalog", None)
            config["gates"] = {"max_total_cost_usd": 0.000001}
            config_path.write_text(json.dumps(config), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "run",
                        "--config",
                        str(config_path),
                        "--out",
                        str(out_dir),
                    ]
                )

            payload = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 3)
        self.assertIn("One or more gates failed", stderr.getvalue())
        self.assertEqual(payload["gate_results"][0]["name"], "max_total_cost_usd")
        self.assertFalse(payload["gate_results"][0]["passed"])

    def test_rag_command_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "rag",
                        "--config",
                        "examples/rag_eval/config.json",
                        "--out",
                        temp_dir,
                        "--content-mode",
                        "metadata-only",
                        "--html",
                    ]
                )

            payload = json.loads(
                (Path(temp_dir) / "rag_report.json").read_text(encoding="utf-8")
            )
            html_exists = (Path(temp_dir) / "rag_report.html").exists()

        self.assertEqual(exit_code, 0)
        self.assertIn("Wrote RAG JSON report", stdout.getvalue())
        self.assertEqual(payload["schema_version"], "pangolin-eval.rag_report.v1")
        self.assertEqual(payload["content_mode"], "metadata_only")
        self.assertIsNone(payload["results"][0]["response"])
        self.assertTrue(html_exists)

    def test_trace_command_writes_tracecards(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "trace",
                        "--input",
                        "examples/agent_trace/trace_events.json",
                        "--out",
                        temp_dir,
                        "--html",
                    ]
                )

            payload = json.loads(
                (Path(temp_dir) / "tracecards.json").read_text(encoding="utf-8")
            )
            html_exists = (Path(temp_dir) / "tracecards.html").exists()

        self.assertEqual(exit_code, 0)
        self.assertIn("Wrote TraceCard JSON report", stdout.getvalue())
        self.assertEqual(payload["schema_version"], "pangolin-eval.tracecards.v1")
        self.assertEqual(len(payload["tracecards"]), 2)
        self.assertTrue(html_exists)

    def test_export_otel_command_writes_spans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "report.json"
            output_path = Path(temp_dir) / "otel.json"
            input_path.write_text(
                json.dumps(
                    {
                        "schema_version": "pangolin-eval.report.v4",
                        "results": [
                            {
                                "model_id": "mock-model",
                                "prompt_id": "case-1",
                                "status": "success",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "export-otel",
                        "--input",
                        str(input_path),
                        "--out",
                        str(output_path),
                    ]
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertIn("Wrote OTel-style export", stdout.getvalue())
        self.assertEqual(payload["schema_version"], "pangolin-eval.otel_export.v1")
        self.assertEqual(payload["spans"][0]["kind"], "llm")


if __name__ == "__main__":
    unittest.main()
