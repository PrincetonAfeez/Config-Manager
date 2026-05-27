"""Tests for the pipeline module"""

import tempfile
import unittest
from pathlib import Path

from config_manager import ConfigInvalidError, ConfigKeyError, Field, Schema, load


def make_schema():
    return Schema(
        {
            "app": {
                "name": Field(str, required=True),
                "debug": Field(bool, default=False),
                "environment": Field(str, default="dev", choices=["dev", "test", "prod"]),
            },
            "database": {
                "host": Field(str, default="localhost"),
                "port": Field(int, default=5432, min_value=1, max_value=65535),
                "password": Field(str, required=True, secret=True),
            },
            "features": Field(list, default=[], item_type=str),
        }
    )


class PipelineTests(unittest.TestCase):
    def test_precedence_coercion_masking_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "app.toml"
            env_path = Path(tmp) / ".env"
            config_path.write_text(
                """
                [app]
                name = "Demo"

                [database]
                port = 5433
                """,
                encoding="utf-8",
            )
            env_path.write_text(
                "MYAPP_DATABASE__PORT=5434\nMYAPP_DATABASE__PASSWORD=from-env-file\n",
                encoding="utf-8",
            )
            config = load(
                make_schema(),
                config_file=config_path,
                env_file=env_path,
                env={"MYAPP_DATABASE__PORT": "5435"},
                prefix="MYAPP",
                cli_overrides={"database.port": "5436", "features": "a,b"},
            )
        self.assertEqual(config.get("database.port"), 5436)
        self.assertEqual(config.database.port, 5436)
        self.assertEqual(config["database"]["port"], 5436)
        self.assertEqual(config.get("features"), ("a", "b"))
        self.assertEqual(config.explain("database.port")["source"], "cli")
        self.assertEqual(config.to_masked_dict()["database"]["password"], "********")

    def test_unknown_key_strict_vs_lenient(self):
        schema = make_schema()
        with self.assertRaises(ConfigInvalidError):
            load(
                schema,
                env={"MYAPP_APP__NAME": "Demo", "MYAPP_DATABASE__PASSWORD": "pw", "MYAPP_BAD": "x"},
                prefix="MYAPP",
            )
        config = load(
            schema,
            env={"MYAPP_APP__NAME": "Demo", "MYAPP_DATABASE__PASSWORD": "pw", "MYAPP_BAD": "x"},
            prefix="MYAPP",
            strict=False,
        )
        self.assertEqual(config.get("app.name"), "Demo")
        with self.assertRaises(ConfigKeyError):
            config.get("bad")

    def test_coercion_error(self):
        with self.assertRaises(ConfigInvalidError) as ctx:
            load(
                make_schema(),
                env={
                    "MYAPP_APP__NAME": "Demo",
                    "MYAPP_DATABASE__PASSWORD": "pw",
                    "MYAPP_DATABASE__PORT": "abc",
                },
                prefix="MYAPP",
            )
        self.assertTrue(any("database.port" in issue.path for issue in ctx.exception.issues))


if __name__ == "__main__":
    unittest.main()
