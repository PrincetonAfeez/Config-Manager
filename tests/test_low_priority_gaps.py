"""Tests for low priority gaps in the library."""

import tempfile
from pathlib import Path

import pytest
from config_manager import ConfigInvalidError, Field, Schema, load
from config_manager.paths import iter_leaf_paths
from config_manager.sources import toml_source


def test_inferred_secret_by_leaf_name():
    schema = Schema({"database": {"password": Field(str, required=True)}})
    assert schema.is_secret("database.password")
    assert "database.password" in schema.secret_paths()


def test_inferred_secret_in_list_item_fields():
    schema = Schema(
        {
            "servers": Field(
                list,
                item_fields={"host": Field(str), "token": Field(str)},
            )
        }
    )
    assert schema.is_secret("servers[].token")
    assert "servers[].token" in schema.secret_paths()


def test_explicit_secret_still_works():
    schema = Schema({"api": {"value": Field(str, secret=True)}})
    assert schema.is_secret("api.value")


def test_non_secret_field_not_inferred():
    schema = Schema({"app": {"name": Field(str)}})
    assert not schema.is_secret("app.name")


def test_inferred_secret_masked_on_show():
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
    assert config.to_masked_dict()["database"]["password"] == "********"


def test_docs_marks_inferred_secret():
    schema = Schema({"database": {"token": Field(str)}})
    docs = schema.docs()
    assert "secret: inferred" in docs


def test_scalar_list_is_single_leaf():
    paths = iter_leaf_paths({"features": ["a", "b"]})
    assert paths == ["features[0]", "features[1]"]


def test_empty_list_is_single_leaf():
    paths = iter_leaf_paths({"features": []})
    assert paths == ["features"]


def test_list_of_mappings_traversed_for_strict_checks():
    paths = iter_leaf_paths({"items": [{"id": 1, "extra": "x"}]})
    assert "items[0].id" in paths
    assert "items[0].extra" in paths


def test_unknown_nested_list_key_caught_in_strict_mode():
    schema = Schema({"app": {"name": Field(str, default="demo")}})
    with pytest.raises(ConfigInvalidError):
        load(
            schema,
            cli_overrides={"items[0].extra": "surprise"},
            strict=True,
        )


def test_toml_provenance_uses_dotted_path_as_name():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "app.toml"
        path.write_text("[database]\nport = 5432\n", encoding="utf-8")
        _, provenance = toml_source(path)
    assert provenance["database.port"].name == "database.port"
    assert provenance["database.port"].source == "config_file"
