"""Tests for schema module."""

import pytest
from config_manager import Field, Schema
from config_manager.errors import SchemaError


def test_duplicate_env_name_rejected():
    with pytest.raises(SchemaError, match="duplicate environment name"):
        Schema(
            {
                "a": Field(str, env_name="API_TOKEN"),
                "b": Field(str, env_name="API_TOKEN"),
            }
        )


def test_duplicate_cli_name_rejected():
    with pytest.raises(SchemaError):
        Schema(
            {
                "a": Field(str, cli_name="db-port"),
                "b": Field(int, cli_name="db-port"),
            }
        )


def test_unsupported_field_type_rejected():
    with pytest.raises(SchemaError):
        Schema({"app": {"data": Field(bytes)}})  # type: ignore[arg-type]


def test_distinct_paths_with_same_leaf_name_allowed():
    schema = Schema({"a": {"token": Field(str)}, "b": {"token": Field(str)}})
    assert schema.env_key_map(prefix="MYAPP")["MYAPP_A__TOKEN"] == "a.token"
    assert schema.env_key_map(prefix="MYAPP")["MYAPP_B__TOKEN"] == "b.token"
