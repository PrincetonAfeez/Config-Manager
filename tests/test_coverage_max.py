"""Targeted tests for remaining uncovered branches."""

from unittest.mock import patch

import pytest
from config_manager import Field, Schema
from config_manager.coercion import (
    coerce_config,
    coerce_value,
    collect_coercion_issues,
)
from config_manager.dotenv import parse_dotenv
from config_manager.errors import CoercionError, ConfigError, ParseError, SchemaError
from config_manager.init_templates import generate_env_example, generate_toml_example
from config_manager.paths import get_path, set_path
from config_manager.provenance import Provenance
from config_manager.sources import _resolve_env_key
from config_manager.validation import collect_validation_issues

# --- coercion ---


def test_coerce_unsupported_field_type():
    with pytest.raises(ValueError, match="unsupported field type"):
        coerce_value("x", Field(bytes))


def test_coerce_int_non_integer_float():
    with pytest.raises(ValueError, match="non-integer float"):
        coerce_value(1.5, Field(int))


def test_coerce_float_empty_string():
    with pytest.raises(ValueError, match="empty string"):
        coerce_value("  ", Field(float))


def test_coerce_float_invalid_string():
    with pytest.raises(ValueError, match="expected float"):
        coerce_value("not-a-number", Field(float))


def test_coerce_float_invalid_type():
    with pytest.raises(ValueError, match="expected float"):
        coerce_value([], Field(float))


def test_coerce_bool_invalid_int():
    with pytest.raises(ValueError, match="expected bool, got int"):
        coerce_value(2, Field(bool))


def test_coerce_bool_empty_string():
    with pytest.raises(ValueError, match="empty string"):
        coerce_value("", Field(bool))


def test_coerce_bool_invalid_type():
    with pytest.raises(ValueError, match="expected bool"):
        coerce_value([], Field(bool))


def test_coerce_list_json_not_array():
    with patch("config_manager.coercion.json.loads", return_value={"a": 1}):
        with pytest.raises(ValueError, match="expected list"):
            coerce_value("[not-array]", Field(list))


def test_coerce_list_invalid_type():
    with pytest.raises(ValueError, match="expected list"):
        coerce_value(123, Field(list))


def test_coerce_list_item_type_failure():
    with pytest.raises(ValueError, match="invalid list item"):
        coerce_value(["a", "b"], Field(list, item_type=int))


def test_coerce_list_object_not_mapping():
    field = Field(list, item_fields={"name": Field(str)})
    with pytest.raises(ValueError, match="expected object"):
        coerce_value(["not-a-dict"], field)


def test_coerce_list_object_uses_default():
    field = Field(list, item_fields={"name": Field(str, default="default")})
    assert coerce_value([{}], field) == [{"name": "default"}]


def test_coerce_dict_json_not_object():
    with pytest.raises(ValueError, match="expected dict"):
        coerce_value("[1, 2]", Field(dict))


def test_coerce_dict_invalid_type():
    with pytest.raises(ValueError, match="expected dict"):
        coerce_value(42, Field(dict))


def test_coerce_config_success():
    schema = Schema({"n": Field(int)})
    assert coerce_config({"n": "42"}, schema) == {"n": 42}


def test_coerce_int_invalid_type():
    with pytest.raises(ValueError, match="expected int"):
        coerce_value([], Field(int))


def test_coerce_float_rejects_bool():
    with pytest.raises(ValueError, match="expected float, got bool"):
        coerce_value(True, Field(float))


def test_coerce_dict_without_value_type():
    assert coerce_value({"a": 1, "b": "x"}, Field(dict)) == {"a": 1, "b": "x"}
    schema = Schema({"n": Field(int)})
    with pytest.raises(CoercionError):
        coerce_config({"n": "bad"}, schema)


def test_collect_coercion_issues_includes_provenance():
    schema = Schema({"n": Field(int)})
    prov = {"n": Provenance("env", "N")}
    _, issues = collect_coercion_issues({"n": "bad"}, schema, provenance=prov)
    assert issues[0].source == "env"


# --- validation ---


def test_validate_nullable_allows_none():
    schema = Schema({"opt": Field(str, nullable=True)})
    issues = collect_validation_issues({"opt": None}, {"opt": None}, schema, strict=True)
    assert not issues


def test_validate_non_nullable_none():
    schema = Schema({"opt": Field(str, nullable=False)})
    issues = collect_validation_issues({"opt": None}, {"opt": None}, schema, strict=True)
    assert any("nullable" in i.message for i in issues)


def test_validate_type_mismatch():
    schema = Schema({"n": Field(int)})
    issues = collect_validation_issues({"n": "1"}, {"n": "1"}, schema, strict=True)
    assert any("expected int" in i.message for i in issues)


def test_validate_dict_max_length():
    schema = Schema({"meta": Field(dict, max_length=1)})
    issues = collect_validation_issues(
        {"meta": {"a": 1, "b": 2}}, {"meta": {"a": 1, "b": 2}}, schema, strict=True
    )
    assert any("<=" in i.message for i in issues)


def test_validate_dict_validator_rejected():
    schema = Schema({"meta": Field(dict, validator=lambda v: False)})
    issues = collect_validation_issues({"meta": {"k": "v"}}, {"meta": {}}, schema, strict=True)
    assert any("custom validator" in i.message for i in issues)


def test_validate_str_max_length():
    schema = Schema({"name": Field(str, max_length=2)})
    issues = collect_validation_issues({"name": "abc"}, {"name": "abc"}, schema, strict=True)
    assert any("<=" in i.message for i in issues)


def test_validate_list_item_not_object():
    schema = Schema({"items": Field(list, item_fields={"id": Field(int)})})
    issues = collect_validation_issues(
        {"items": ["scalar"]}, {"items": ["scalar"]}, schema, strict=True
    )
    assert any("expected object" in i.message for i in issues)


def test_validate_dict_validator_raises():
    def boom(_value: dict) -> bool:
        raise ValueError("boom")

    schema = Schema({"meta": Field(dict, validator=boom)})
    issues = collect_validation_issues({"meta": {"k": "v"}}, {"meta": {}}, schema, strict=True)
    assert any("boom" in i.message for i in issues)


def test_validate_float_type_match():
    schema = Schema({"rate": Field(float, min_value=0.0, max_value=10.0)})
    issues = collect_validation_issues({"rate": 1.5}, {"rate": 1.5}, schema, strict=True)
    assert not issues
    schema = Schema({"when": Field(str)})
    issues = collect_validation_issues({"when": 123}, {"when": 123}, schema, strict=True)
    assert any("expected str" in i.message for i in issues)
    schema = Schema({"tags": Field(list, item_type=str)})
    issues = collect_validation_issues(
        {"tags": ["a"], "tags[0]": "extra"},
        {"tags": ["a"]},
        schema,
        strict=True,
    )
    assert not any("unknown config key tags[0]" in i.message for i in issues)


# --- paths ---


def test_set_path_last_segment_not_list():
    with pytest.raises(ValueError, match="is not a list"):
        set_path({"items": "scalar"}, "items[0]", "x")


def test_get_path_missing_bracket_parent():
    assert get_path({}, "items[0].id") is None


# --- dotenv ---


def test_dotenv_trailing_continuation_buffer():
    assert parse_dotenv("KEY=value\\\n") == {"KEY": "value"}


def test_dotenv_invalid_export_syntax():
    with pytest.raises(ParseError, match="invalid export syntax"):
        parse_dotenv("export\tFOO=bar")


def test_dotenv_unterminated_single_quote():
    with pytest.raises(ParseError, match="unterminated single-quoted"):
        parse_dotenv("KEY='broken")


def test_dotenv_missing_key_before_equals():
    with pytest.raises(ParseError, match="missing key"):
        parse_dotenv("=value")


def test_dotenv_quoted_equals_in_value():
    assert parse_dotenv('KEY="a=b"')["KEY"] == "a=b"


def test_dotenv_double_quote_escape_in_key_line():
    assert parse_dotenv(r'KEY="say \"hi\""')["KEY"] == 'say "hi"'


def test_dotenv_mixed_quotes_in_key_line():
    assert parse_dotenv("KEY='a=b'")["KEY"] == "a=b"
    with pytest.raises(ParseError, match="unexpected text"):
        parse_dotenv('KEY="ok" extra')


# --- schema ---


def test_schema_unsupported_list_item_type():
    with pytest.raises(SchemaError, match="unsupported list item type"):
        Schema({"x": Field(list, item_type=list)})


def test_schema_unsupported_dict_value_type():
    with pytest.raises(SchemaError, match="unsupported dict value type"):
        Schema({"x": Field(dict, value_type=dict)})


def test_schema_duplicate_cli_name():
    with pytest.raises(SchemaError, match="duplicate CLI name"):
        Schema({"a": Field(str, cli_name="same"), "b": Field(str, cli_name="same")})


def test_schema_unsupported_object_field_in_list():
    with pytest.raises(SchemaError, match="unsupported object field type"):
        Schema({"items": Field(list, item_fields={"nested": Field(list)})})


def test_schema_docs_null_and_missing_defaults():
    schema = Schema(
        {"opt": Field(str, nullable=True, default=None), "req": Field(str, required=True)}
    )
    docs = schema.docs()
    assert "default: null" in docs
    assert "required: yes" in docs


def test_schema_format_missing_default():
    from config_manager.fields import MISSING

    assert Schema._format_value(MISSING) == ""
    schema = Schema({"a": Field(str, default="x"), "a.b": Field(str, default="y")})
    with pytest.raises(TypeError, match="cannot set nested default"):
        schema.defaults()
    schema = Schema(
        {
            "app": {
                "env": Field(
                    str,
                    choices=["dev", "prod"],
                    min_value=None,
                    max_value=None,
                    min_length=1,
                    max_length=10,
                    regex=r"^[a-z]+$",
                    nullable=True,
                    description="Environment",
                    default="dev",
                )
            }
        }
    )
    docs = schema.docs()
    assert "choices:" in docs
    assert "min_length:" in docs
    assert "max_length:" in docs
    assert "regex:" in docs
    assert "nullable:" in docs


# --- init_templates ---


def test_generate_env_list_default():
    schema = Schema({"tags": Field(list, default=["a", "b"], item_type=str)})
    text = generate_env_example(schema)
    assert "a,b" in text
    schema = Schema({"opt": Field(str, nullable=True, default=None)})
    text = generate_env_example(schema)
    assert "OPT=" in text.upper() or "opt=" in text


def test_generate_toml_nullable_none():
    schema = Schema({"opt": Field(str, nullable=True, default=None)})
    text = generate_toml_example(schema)
    assert 'opt = ""' in text


def test_generate_toml_list_nested():
    schema = Schema({"items": Field(list, default=[1, 2], item_type=int)})
    text = generate_toml_example(schema)
    assert "items = [1, 2]" in text


# --- sources ---


def test_resolve_env_key_prefixless_disabled():
    assert (
        _resolve_env_key("NAME", prefix=None, prefix_text="", env_key_map={}, require_prefix=False)
        is None
    )
    assert _resolve_env_key(
        "NAME", prefix=None, prefix_text="", env_key_map={}, require_prefix=True
    ) == (
        "name",
        "NAME",
    )


def test_resolve_env_key_empty_after_prefix():
    assert _resolve_env_key("MYAPP_", prefix="MYAPP", prefix_text="MYAPP_", env_key_map={}) is None


# --- cli ---


def test_load_schema_spec_unavailable(tmp_path):
    from config_manager.cli import _load_schema

    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\nschema = Schema({'a': Field(str)})\n",
        encoding="utf-8",
    )
    with patch("config_manager.cli.importlib.util.spec_from_file_location", return_value=None):
        with pytest.raises(ConfigError, match="could not load schema"):
            _load_schema(str(schema_file))
