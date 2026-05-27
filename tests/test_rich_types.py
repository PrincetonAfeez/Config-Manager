"""Tests for rich types module"""

import tempfile
import unittest
from pathlib import Path

from config_manager import ConfigInvalidError, Field, Schema, load
from config_manager.errors import SchemaError


class RichTypeTests(unittest.TestCase):
    def test_list_of_objects_from_toml(self):
        schema = Schema(
            {
                "app": {"name": Field(str, required=True)},
                "servers": Field(
                    list,
                    item_fields={
                        "host": Field(str, required=True),
                        "port": Field(int, default=8080),
                    },
                ),
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.toml"
            path.write_text(
                '[app]\nname = "Demo"\n\n[[servers]]\nhost = "a"\nport = 9090\n',
                encoding="utf-8",
            )
            config = load(schema, config_file=path)
        servers = config.get("servers")
        self.assertIsInstance(servers, tuple)
        self.assertEqual(servers[0]["host"], "a")
        self.assertEqual(servers[0]["port"], 9090)

    def test_dict_with_value_type(self):
        schema = Schema(
            {
                "app": {"name": Field(str, default="demo")},
                "flags": Field(dict, value_type=bool, default={}),
            }
        )
        config = load(
            schema,
            cli_overrides={"flags": '{"beta": true, "legacy": false}'},
        )
        self.assertEqual(config.get("flags"), {"beta": True, "legacy": False})

    def test_list_of_objects_missing_required_field(self):
        schema = Schema(
            {
                "servers": Field(
                    list,
                    item_fields={"host": Field(str, required=True)},
                )
            }
        )
        with self.assertRaises(ConfigInvalidError):
            load(schema, cli_overrides={"servers": '[{"port": 1}]'})

    def test_item_type_and_item_fields_mutually_exclusive(self):
        with self.assertRaises(SchemaError):
            Schema({"tags": Field(list, item_type=str, item_fields={"x": Field(str)})})


if __name__ == "__main__":
    unittest.main()
