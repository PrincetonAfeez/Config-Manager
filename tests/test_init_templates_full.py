"""Tests for config_manager.init_templates."""

from config_manager import Field, Schema
from config_manager.init_templates import generate_env_example, generate_toml_example


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
