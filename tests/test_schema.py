""" Tests for schema module """

import unittest

from config_manager import Field, Schema
from config_manager.errors import SchemaError


class SchemaValidationTests(unittest.TestCase):
    def test_duplicate_env_name_rejected(self):
        with self.assertRaises(SchemaError) as ctx:
            Schema(
                {
                    "a": Field(str, env_name="API_TOKEN"),
                    "b": Field(str, env_name="API_TOKEN"),
                }
            )
        self.assertIn("duplicate environment name", str(ctx.exception))

    def test_duplicate_cli_name_rejected(self):
        with self.assertRaises(SchemaError):
            Schema(
                {
                    "a": Field(str, cli_name="db-port"),
                    "b": Field(int, cli_name="db-port"),
                }
            )

    def test_unsupported_field_type_rejected(self):
        with self.assertRaises(SchemaError):
            Schema({"app": {"data": Field(bytes)}})  # type: ignore[arg-type]

    def test_distinct_paths_with_same_leaf_name_allowed(self):
        schema = Schema({"a": {"token": Field(str)}, "b": {"token": Field(str)}})
        self.assertEqual(schema.env_key_map(prefix="MYAPP")["MYAPP_A__TOKEN"], "a.token")
        self.assertEqual(schema.env_key_map(prefix="MYAPP")["MYAPP_B__TOKEN"], "b.token")


if __name__ == "__main__":
    unittest.main()
