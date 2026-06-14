from __future__ import annotations

import re
import unittest
from pathlib import Path

import pangolin_eval


class VersionTest(unittest.TestCase):
    def test_package_version_metadata_is_consistent(self) -> None:
        pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
        setup_py = Path("setup.py").read_text(encoding="utf-8")

        pyproject_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
        setup_version = re.search(r'version="([^"]+)"', setup_py)

        self.assertIsNotNone(pyproject_version)
        self.assertIsNotNone(setup_version)
        assert pyproject_version is not None
        assert setup_version is not None
        self.assertEqual(pyproject_version.group(1), "0.2.1")
        self.assertEqual(setup_version.group(1), pyproject_version.group(1))
        self.assertEqual(pangolin_eval.__version__, pyproject_version.group(1))


if __name__ == "__main__":
    unittest.main()
