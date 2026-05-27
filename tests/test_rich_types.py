"""Tests for rich types module."""

import tempfile
from pathlib import Path

import pytest
from config_manager import ConfigInvalidError, Field, Schema, load
from config_manager.errors import SchemaError


def test_list_of_objects_from_toml():
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
    assert isinstance(servers, tuple)
    assert servers[0]["host"] == "a"
    assert servers[0]["port"] == 9090


def test_dict_with_value_type():
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
    assert config.get("flags") == {"beta": True, "legacy": False}


def test_list_of_objects_missing_required_field():
    schema = Schema(
        {
            "servers": Field(
                list,
                item_fields={"host": Field(str, required=True)},
            )
        }
    )
    with pytest.raises(ConfigInvalidError):
        load(schema, cli_overrides={"servers": '[{"port": 1}]'})


def test_item_type_and_item_fields_mutually_exclusive():
    with pytest.raises(SchemaError):
        Schema({"tags": Field(list, item_type=str, item_fields={"x": Field(str)})})
