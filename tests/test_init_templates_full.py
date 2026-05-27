"""Tests for config_manager.init_templates."""

import json
import tomllib
from io import BytesIO

from config_manager import Field, Schema
from config_manager.init_templates import generate_env_example, generate_toml_example


def _parse_toml(text: str) -> dict:
    return tomllib.load(BytesIO(text.encode("utf-8")))


def test_generate_env_example_includes_prefix():
    schema = Schema({"app": {"name": Field(str, required=True, description="Name")}})
    text = generate_env_example(schema, prefix="MYAPP")
    assert "MYAPP_APP__NAME=" in text
    assert "# Name" in text
    assert "# required" in text


def test_generate_env_example_bool_default():
    schema = Schema({"app": {"debug": Field(bool, default=True)}})
    text = generate_env_example(schema)
    assert "debug=true" in text.lower() or "DEBUG=true" in text


def test_generate_env_example_dict_default_json():
    schema = Schema({"flags": Field(dict, value_type=bool, default={"beta_ui": False})})
    text = generate_env_example(schema)
    assert "FLAGS=" in text.upper()
    assert json.loads(text.split("=", 1)[1].strip()) == {"beta_ui": False}


def test_generate_env_example_list_of_objects_json():
    schema = Schema(
        {
            "servers": Field(
                list,
                item_fields={
                    "host": Field(str, required=True),
                    "port": Field(int, default=8080),
                },
            )
        }
    )
    text = generate_env_example(schema)
    line = next(line for line in text.splitlines() if line.startswith("SERVERS="))
    payload = json.loads(line.split("=", 1)[1])
    assert payload == [{"host": "", "port": 8080}]


def test_generate_toml_example_sections():
    schema = Schema(
        {
            "root_key": Field(str, default="x", description="Root"),
            "app": {"name": Field(str, default="Demo", description="App name")},
        }
    )
    text = generate_toml_example(schema)
    assert "[app]" in text
    assert 'root_key = "x"' in text
    assert "name" in text


def test_generate_toml_example_list_default():
    schema = Schema({"tags": Field(list, default=["a", "b"], item_type=str)})
    text = generate_toml_example(schema)
    assert "tags" in text
    assert "a" in text


def test_generate_toml_example_dict_inline_table():
    schema = Schema({"flags": Field(dict, value_type=bool, default={"beta_ui": False})})
    text = generate_toml_example(schema)
    assert "beta_ui = false" in text
    _parse_toml(text)


def test_generate_toml_example_list_of_objects_array_of_tables():
    schema = Schema(
        {
            "servers": Field(
                list,
                item_fields={
                    "host": Field(str, required=True),
                    "port": Field(int, default=8080),
                },
            )
        }
    )
    text = generate_toml_example(schema)
    assert "[[servers]]" in text
    assert 'host = ""' in text
    assert "port = 8080" in text
    _parse_toml(text)


def test_generate_env_example_nullable_default():
    schema = Schema({"opt": Field(str, nullable=True, default=None)})
    text = generate_env_example(schema)
    assert "OPT=" in text.upper()


def test_generate_toml_required_list_of_objects_comment():
    schema = Schema(
        {
            "servers": Field(
                list,
                required=True,
                item_fields={"host": Field(str, required=True)},
            )
        }
    )
    text = generate_toml_example(schema)
    assert "# required" in text
    assert "[[servers]]" in text
    _parse_toml(text)


def test_generate_env_example_empty_dict_default():
    schema = Schema({"meta": Field(dict, default={})})
    text = generate_env_example(schema)
    assert "META={}" in text.upper() or "meta={}" in text
