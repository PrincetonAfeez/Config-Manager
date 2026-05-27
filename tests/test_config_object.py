""" Tests for ConfigObject module """

import unittest

from config_manager import ConfigFrozenError, Field, Schema, load
from config_manager.errors import ParseError
from config_manager.sources import dotenv_source, environment_source


class ConfigObjectTests(unittest.TestCase):
    def test_list_values_are_immutable(self):
        schema = Schema({"features": Field(list, default=[], item_type=str)})
        config = load(schema, env={"MYAPP_FEATURES": "a,b"}, prefix="MYAPP")
        features = config.get("features")
        self.assertIsInstance(features, tuple)
        with self.assertRaises((TypeError, AttributeError)):
            features.append("z")  # type: ignore[attr-defined]

    def test_assignment_raises(self):
        schema = Schema({"app": {"name": Field(str, default="demo")}})
        config = load(schema)
        with self.assertRaises(ConfigFrozenError):
            config.app = "other"  # type: ignore[misc]

    def test_get_raises_config_key_error(self):
        schema = Schema({"app": {"name": Field(str, default="demo")}})
        config = load(schema)
        with self.assertRaises(KeyError):
            config.get("missing.path")


class SourcesTests(unittest.TestCase):
    def test_dotenv_skips_unprefixed_keys(self):
        schema = Schema({"app": {"name": Field(str)}})
        env = {"MYAPP_APP__NAME": "ok", "OTHER": "bad"}
        data, _ = dotenv_source(_write_env(env), prefix="MYAPP", schema=schema)
        self.assertEqual(data, {"app": {"name": "ok"}})

    def test_environment_matches_dotenv_prefix_rules(self):
        schema = Schema({"app": {"name": Field(str)}})
        env = {"MYAPP_APP__NAME": "ok", "OTHER": "bad"}
        data, _ = environment_source(env, prefix="MYAPP", schema=schema)
        self.assertEqual(data, {"app": {"name": "ok"}})

    def test_env_name_override(self):
        schema = Schema(
            {
                "api": {
                    "token": Field(str, env_name="API_TOKEN"),
                }
            }
        )
        env = {"MYAPP_API_TOKEN": "secret"}
        data, _ = environment_source(env, prefix="MYAPP", schema=schema)
        self.assertEqual(data["api"]["token"], "secret")

    def test_cli_name_override(self):
        schema = Schema({"database": {"port": Field(int, cli_name="db-port")}})
        from config_manager.sources import cli_overrides_source

        data, prov = cli_overrides_source({"db-port": "5432"}, schema=schema)
        self.assertEqual(data["database"]["port"], "5432")
        self.assertIn("database.port", prov)

    def test_environment_provenance_uses_dotted_path(self):
        schema = Schema({"database": {"port": Field(int)}})
        _, prov = environment_source(
            {"MYAPP_DATABASE__PORT": "5432"}, prefix="MYAPP", schema=schema
        )
        self.assertEqual(prov["database.port"].name, "database.port")

    def test_merge_conflict_raises_parse_error(self):
        schema = Schema({"database": {"port": Field(int)}})
        with self.assertRaises(ParseError):
            load(
                schema,
                env={"MYAPP_DATABASE": "localhost", "MYAPP_DATABASE__PORT": "5432"},
                prefix="MYAPP",
            )


def _write_env(values: dict[str, str]):
    import tempfile
    from pathlib import Path

    tmp = tempfile.mkdtemp()
    path = Path(tmp) / ".env"
    path.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
