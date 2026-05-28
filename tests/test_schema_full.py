"""Exhaustive tests for config_manager.schema."""

import pytest
from config_manager import Field, Schema
from config_manager.errors import SchemaError


def test_schema_tree_and_fields(basic_schema):
    assert "app" in basic_schema.tree
    assert "app.name" in basic_schema.fields


def test_schema_defaults(basic_schema):
    defaults = basic_schema.defaults()
    assert defaults["app"]["debug"] is False


def test_schema_docs(basic_schema):
    docs = basic_schema.docs()
    assert "app.name" in docs
    assert "type: str" in docs


def test_schema_env_name_for(basic_schema):
    assert basic_schema.env_name_for("app.name", prefix="MYAPP") == "MYAPP_APP__NAME"


def test_schema_env_name_custom():
    schema = Schema({"api": {"key": Field(str, env_name="API_KEY")}})
    assert schema.env_name_for("api.key", prefix="X") == "X_API_KEY"


def test_schema_cli_key_map(basic_schema):
    mapping = basic_schema.cli_key_map()
    assert mapping["app.name"] == "app.name"


def test_schema_is_secret_explicit():
    schema = Schema({"x": Field(str, secret=True)})
    assert schema.is_secret("x") is True


def test_schema_is_secret_inferred():
    schema = Schema({"db": {"password": Field(str)}})
    assert schema.is_secret("db.password") is True


def test_schema_secret_paths(basic_schema):
    paths = basic_schema.secret_paths()
    assert "database.password" in paths


def test_schema_invalid_key_type():
    with pytest.raises(SchemaError, match="Schema keys must be non-empty strings"):
        Schema({123: Field(str)})  # type: ignore[dict-item]


def test_schema_invalid_empty_key():
    with pytest.raises(SchemaError, match="Schema keys must be non-empty strings"):
        Schema({"": Field(str)})


def test_schema_invalid_nested_value():
    with pytest.raises(SchemaError, match="schema values must be Field or mapping"):
        Schema({"app": "not a field"})


def test_schema_duplicate_env_name():
    with pytest.raises(SchemaError, match="duplicate environment"):
        Schema({"a": Field(str, env_name="SAME"), "b": Field(str, env_name="SAME")})


def test_schema_item_type_and_item_fields_exclusive():
    with pytest.raises(SchemaError, match="item_type or item_fields"):
        Schema({"x": Field(list, item_type=str, item_fields={"a": Field(str)})})


def test_schema_env_key_map(basic_schema):
    keys = basic_schema.env_key_map(prefix="MYAPP")
    assert keys["MYAPP_APP__NAME"] == "app.name"
