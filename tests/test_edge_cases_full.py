"""Additional edge-case tests to maximize coverage."""

import pytest
from config_manager import Field, Schema
from config_manager.coercion import coerce_value
from config_manager.dotenv import parse_dotenv
from config_manager.errors import ParseError
from config_manager.toml_loader import load_toml_file


def test_dotenv_unexpected_text_after_quoted():
    with pytest.raises(ParseError, match="unexpected text"):
        parse_dotenv("KEY='a' trailing")


def test_dotenv_double_quote_newline_escape():
    assert parse_dotenv('TEXT="line1\\nline2"')["TEXT"] == "line1\nline2"


def test_coerce_float_empty_string():
    with pytest.raises(ValueError):
        coerce_value("", Field(float))


def test_coerce_list_invalid_json():
    with pytest.raises(ValueError):
        coerce_value("[bad json", Field(list))


def test_coerce_dict_invalid_json():
    with pytest.raises(ValueError):
        coerce_value("{bad", Field(dict))


def test_toml_invalid_syntax(tmp_path):
    path = tmp_path / "bad.toml"
    path.write_text("key =", encoding="utf-8")
    with pytest.raises(ParseError):
        load_toml_file(path)


def test_schema_get_field_missing():
    schema = Schema({"a": Field(str)})
    assert schema.get_field("missing") is None


def test_schema_is_secret_unknown_path():
    schema = Schema({"a": Field(str)})
    assert schema.is_secret("missing") is False
