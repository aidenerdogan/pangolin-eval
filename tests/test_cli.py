from __future__ import annotations

import contextlib
import io
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


if __name__ == "__main__":
    unittest.main()
