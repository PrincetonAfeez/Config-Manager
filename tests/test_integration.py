""" Tests for integration of the CLI with the schema and config modules """

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReadmeIntegrationTests(unittest.TestCase):
    def test_readme_validate_example(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "config_manager.cli",
                "validate",
                "--schema",
                str(ROOT / "examples" / "basic_schema.py"),
                "--config",
                str(ROOT / "examples" / "app.toml"),
                "--env-file",
                str(ROOT / "examples" / ".env.example"),
                "--prefix",
                "MYAPP",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Config valid.", result.stdout)

    def test_rich_schema_validate_example(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "config_manager.cli",
                "validate",
                "--schema",
                str(ROOT / "examples" / "rich_schema.py"),
                "--config",
                str(ROOT / "examples" / "servers.toml"),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
