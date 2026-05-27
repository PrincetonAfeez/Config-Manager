""" Tests for low priority gaps in the library """

import tempfile
import unittest
from pathlib import Path

from config_manager import ConfigInvalidError, Field, Schema, load
from config_manager.paths import iter_leaf_paths
from config_manager.sources import toml_source


class SchemaSecretInferenceTests(unittest.TestCase):
    def test_inferred_secret_by_leaf_name(self):
        schema = Schema({"database": {"password": Field(str, required=True)}})
        self.assertTrue(schema.is_secret("database.password"))
        self.assertIn("database.password", schema.secret_paths())

    def test_explicit_secret_still_works(self):
        schema = Schema({"api": {"value": Field(str, secret=True)}})
        self.assertTrue(schema.is_secret("api.value"))

    def test_non_secret_field_not_inferred(self):
        schema = Schema({"app": {"name": Field(str)}})
        self.assertFalse(schema.is_secret("app.name"))

    def test_inferred_secret_masked_on_show(self):
        schema = Schema(
            {
                "app": {"name": Field(str, default="demo")},
                "database": {"password": Field(str, required=True)},
            }
        )
        config = load(
            schema,
            env={"MYAPP_DATABASE__PASSWORD": "secret-value"},
            prefix="MYAPP",
        )
        self.assertEqual(config.to_masked_dict()["database"]["password"], "********")

    def test_docs_marks_inferred_secret(self):
        schema = Schema({"database": {"token": Field(str)}})
        docs = schema.docs()
        self.assertIn("secret: inferred", docs)


class PathsListTraversalTests(unittest.TestCase):
    def test_scalar_list_is_single_leaf(self):
        paths = iter_leaf_paths({"features": ["a", "b"]})
        self.assertEqual(paths, ["features[0]", "features[1]"])

    def test_empty_list_is_single_leaf(self):
        paths = iter_leaf_paths({"features": []})
        self.assertEqual(paths, ["features"])

    def test_list_of_mappings_traversed_for_strict_checks(self):
        paths = iter_leaf_paths({"items": [{"id": 1, "extra": "x"}]})
        self.assertIn("items[0].id", paths)
        self.assertIn("items[0].extra", paths)

    def test_unknown_nested_list_key_caught_in_strict_mode(self):
        schema = Schema({"app": {"name": Field(str, default="demo")}})
        with self.assertRaises(ConfigInvalidError):
            load(
                schema,
                cli_overrides={"items[0].extra": "surprise"},
                strict=True,
            )


class TomlProvenanceTests(unittest.TestCase):
    def test_toml_provenance_uses_dotted_path_as_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.toml"
            path.write_text("[database]\nport = 5432\n", encoding="utf-8")
            _, provenance = toml_source(path)
        self.assertEqual(provenance["database.port"].name, "database.port")
        self.assertEqual(provenance["database.port"].source, "config_file")


if __name__ == "__main__":
    unittest.main()
