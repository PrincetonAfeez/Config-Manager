"""Tests for the CLI module"""

import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from config_manager.cli import main

SCHEMA_TEXT = """
from config_manager import Field, Schema

schema = Schema({
    "app": {
        "name": Field(str, required=True),
        "debug": Field(bool, default=False),
    },
    "database": {
        "port": Field(int, default=5432),
        "password": Field(str, required=True, secret=True),
    },
})
"""


class CliTests(unittest.TestCase):
    def run_cli(self, args):
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_validate_show_explain_and_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schema_path = root / "schema.py"
            config_path = root / "app.toml"
            env_path = root / ".env"
            schema_path.write_text(SCHEMA_TEXT, encoding="utf-8")
            config_path.write_text('[app]\nname = "Demo"\n', encoding="utf-8")
            env_path.write_text("MYAPP_DATABASE__PASSWORD=secret\n", encoding="utf-8")

            common = [
                "--schema",
                str(schema_path),
                "--config",
                str(config_path),
                "--env-file",
                str(env_path),
                "--prefix",
                "MYAPP",
            ]
            self.assertEqual(self.run_cli(["validate", *common])[0], 0)
            self.assertEqual(self.run_cli(["show", *common])[0], 0)
            self.assertEqual(self.run_cli(["explain", "database.port", *common])[0], 0)
            self.assertEqual(self.run_cli(["schema", "--schema", str(schema_path)])[0], 0)
            self.assertEqual(
                self.run_cli(
                    ["init", "--schema", str(schema_path), "--format", "env", "--prefix", "MYAPP"]
                )[0],
                0,
            )
            self.assertEqual(
                self.run_cli(["init", "--schema", str(schema_path), "--format", "toml"])[0],
                0,
            )

    def test_invalid_config_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.py"
            schema_path.write_text(SCHEMA_TEXT, encoding="utf-8")
            code, _, stderr = self.run_cli(
                ["validate", "--schema", str(schema_path), "--set", "app.name=Demo"]
            )
            self.assertEqual(code, 1)
            self.assertIn("Config invalid", stderr)

    def test_explain_missing_key_returns_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.py"
            schema_path.write_text(SCHEMA_TEXT, encoding="utf-8")
            code, _, stderr = self.run_cli(
                [
                    "explain",
                    "database.missing",
                    "--schema",
                    str(schema_path),
                    "--set",
                    "app.name=Demo",
                    "--set",
                    "database.password=secret",
                ]
            )
            self.assertEqual(code, 3)
            self.assertIn("not declared in schema", stderr)

    def test_explain_unset_optional_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.py"
            schema_path.write_text(
                """
from config_manager import Field, Schema
schema = Schema({
    "app": {"name": Field(str, required=True)},
    "extra": {"note": Field(str)},
})
""",
                encoding="utf-8",
            )
            code, stdout, _ = self.run_cli(
                [
                    "explain",
                    "extra.note",
                    "--schema",
                    str(schema_path),
                    "--set",
                    "app.name=Demo",
                ]
            )
            self.assertEqual(code, 0)
            self.assertIn("status: not set", stdout)

    def test_missing_toml_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.py"
            schema_path.write_text(SCHEMA_TEXT, encoding="utf-8")
            code, _, stderr = self.run_cli(
                [
                    "validate",
                    "--schema",
                    str(schema_path),
                    "--config",
                    str(Path(tmp) / "missing.toml"),
                ]
            )
            self.assertEqual(code, 2)
            self.assertIn("file not found", stderr)

    def test_bad_schema_returns_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.py"
            schema_path.write_text("this is not valid python\n", encoding="utf-8")
            code, _, stderr = self.run_cli(["validate", "--schema", str(schema_path)])
            self.assertEqual(code, 3)
            self.assertIn("could not load schema", stderr)


if __name__ == "__main__":
    unittest.main()
