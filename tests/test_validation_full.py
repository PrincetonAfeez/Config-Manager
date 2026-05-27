"""Exhaustive tests for config_manager.validation."""

import pytest
from config_manager import Field, Schema
from config_manager.errors import ValidationError
from config_manager.validation import (
    collect_validation_issues,
    filter_to_schema,
    validate_config,
)


def test_validate_required_missing():
    schema = Schema({"app": {"name": Field(str, required=True)}})
    issues = collect_validation_issues({}, {}, schema, strict=True)
    assert any("required" in i.message for i in issues)


def test_validate_choices():
    schema = Schema({"app": {"env": Field(str, choices=["dev", "prod"])}})
    issues = collect_validation_issues(
        {"app": {"env": "staging"}}, {"app": {"env": "staging"}}, schema, strict=True
    )
    assert any("must be one of" in i.message for i in issues)


def test_validate_min_max_value():
    schema = Schema({"app": {"port": Field(int, min_value=1, max_value=10)}})
    issues = collect_validation_issues(
        {"app": {"port": 99}}, {"app": {"port": "99"}}, schema, strict=True
    )
    assert any("<=" in i.message for i in issues)


def test_validate_regex_fullmatch():
    schema = Schema({"app": {"code": Field(str, regex=r"^[a-z]+$")}})
    issues = collect_validation_issues(
        {"app": {"code": "abc123"}}, {"app": {"code": "abc123"}}, schema, strict=True
    )
    assert len(issues) == 1


def test_validate_custom_validator_falsy():
    schema = Schema({"app": {"name": Field(str, validator=lambda v: len(v) > 2)}})
    issues = collect_validation_issues(
        {"app": {"name": "ab"}}, {"app": {"name": "ab"}}, schema, strict=True
    )
    assert len(issues) == 1


def test_validate_custom_validator_raises():
    def reject(_value: str) -> bool:
        raise ValueError("nope")

    schema = Schema({"app": {"name": Field(str, validator=reject)}})
    issues = collect_validation_issues(
        {"app": {"name": "x"}}, {"app": {"name": "x"}}, schema, strict=True
    )
    assert any("nope" in i.message for i in issues)


def test_validate_unknown_key_strict():
    schema = Schema({"app": {"name": Field(str)}})
    issues = collect_validation_issues(
        {"extra": "x", "app": {"name": "a"}},
        {"extra": "x", "app": {"name": "a"}},
        schema,
        strict=True,
    )
    assert any("unknown config key" in i.message for i in issues)


def test_validate_unknown_key_lenient():
    schema = Schema({"app": {"name": Field(str)}})
    issues = collect_validation_issues(
        {"extra": "x", "app": {"name": "a"}},
        {"extra": "x", "app": {"name": "a"}},
        schema,
        strict=False,
    )
    assert not any("unknown" in i.message for i in issues)


def test_validate_list_object_items():
    schema = Schema(
        {
            "servers": Field(
                list,
                item_fields={"host": Field(str, required=True), "port": Field(int, min_value=1)},
            )
        }
    )
    issues = collect_validation_issues(
        {"servers": [{"port": 0}]},
        {"servers": [{"port": 0}]},
        schema,
        strict=True,
    )
    assert any("required" in i.message or ">=" in i.message for i in issues)


def test_validate_dict_length():
    schema = Schema({"meta": Field(dict, min_length=1)})
    issues = collect_validation_issues({"meta": {}}, {"meta": {}}, schema, strict=True)
    assert any("length" in i.message for i in issues)


def test_validate_config_raises():
    schema = Schema({"app": {"name": Field(str, required=True)}})
    with pytest.raises(ValidationError):
        validate_config({}, {}, schema, strict=True)


def test_filter_to_schema():
    schema = Schema({"app": {"name": Field(str), "extra": Field(str)}})
    data = {"app": {"name": "Demo", "extra": "x", "unknown": "y"}}
    filtered = filter_to_schema(data, schema)
    assert filtered == {"app": {"name": "Demo", "extra": "x"}}
    assert "unknown" not in filtered["app"]
