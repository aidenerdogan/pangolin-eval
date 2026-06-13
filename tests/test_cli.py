from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from pangolin_eval.cli import main


class CliTest(unittest.TestCase):
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
                    ]
                )

            payload = json.loads(
                (Path(temp_dir) / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Wrote JSON report", stdout.getvalue())
        self.assertEqual(payload["content_mode"], "metadata_only")
        self.assertIsNone(payload["results"][0]["response"])
        self.assertTrue(payload["results"][0]["metadata"]["response_content_omitted"])


if __name__ == "__main__":
    unittest.main()
