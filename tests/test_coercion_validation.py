"""Tests for coercion and validation modules."""

import pytest
from config_manager import ConfigInvalidError, Field, Schema, load
from config_manager.coercion import coerce_value
from config_manager.validation import collect_validation_issues


def test_bool_from_int():
    assert coerce_value(1, Field(bool)) is True
    assert coerce_value(0, Field(bool)) is False


def test_int_from_whole_float():
    assert coerce_value(5432.0, Field(int)) == 5432


def test_combined_coercion_and_validation_errors():
    schema = Schema(
        {
            "app": {
                "name": Field(str, required=True),
                "port": Field(int),
            }
        }
    )
    with pytest.raises(ConfigInvalidError) as exc:
        load(
            schema,
            env={"MYAPP_APP__NAME": "Demo", "MYAPP_APP__PORT": "bad"},
            prefix="MYAPP",
        )
    paths = {issue.path for issue in exc.value.issues}
    assert "app.port" in paths


def test_regex_uses_fullmatch():
    schema = Schema({"app": {"code": Field(str, regex=r"^[a-z]+$")}})
    issues = collect_validation_issues(
        {"app": {"code": "abc123"}},
        {"app": {"code": "abc123"}},
        schema,
        strict=True,
    )
    assert issues


def test_validator_rejects_falsy():
    schema = Schema({"app": {"name": Field(str, validator=lambda v: len(v) > 2)}})
    issues = collect_validation_issues(
        {"app": {"name": "ab"}},
        {"app": {"name": "ab"}},
        schema,
        strict=True,
    )
    assert issues


def test_secret_values_redacted_in_issue_format():
    schema = Schema({"database": {"password": Field(str, secret=True, min_length=8)}})
    issues = collect_validation_issues(
        {"database": {"password": "short"}},
        {"database": {"password": "short"}},
        schema,
        strict=True,
    )
    assert len(issues) == 1
    assert "********" in issues[0].format()
    assert "short" not in issues[0].format()
