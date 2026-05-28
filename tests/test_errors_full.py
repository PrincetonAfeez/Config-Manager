"""Tests for config_manager.errors."""

import pytest
from config_manager.errors import (
    CoercionError,
    ConfigError,
    ConfigFrozenError,
    ConfigInvalidError,
    ConfigIssue,
    ConfigKeyError,
    IssueListError,
    ParseError,
    SchemaError,
    SourceError,
    ValidationError,
)


def test_config_issue_format_plain():
    issue = ConfigIssue("app.name", "required field is missing")
    assert issue.format() == "app.name: required field is missing"


def test_config_issue_format_with_value():
    issue = ConfigIssue("app.port", "bad value", value=999)
    assert "999" in issue.format()


def test_config_issue_format_secret_redacted():
    issue = ConfigIssue("db.password", "too short", value="secret", secret=True)
    formatted = issue.format()
    assert "********" in formatted
    assert "secret" not in formatted


def test_config_issue_format_secret_missing_omits_value():
    issue = ConfigIssue("db.password", "required field is missing", secret=True)
    assert issue.format() == "db.password: required field is missing"


def test_config_issue_format_with_source():
    issue = ConfigIssue("app.name", "missing", source="environment")
    assert "(source: environment)" in issue.format()


def test_config_issue_root_path():
    issue = ConfigIssue("", "root error")
    assert issue.format().startswith("<root>")


@pytest.mark.parametrize(
    "exc_cls,label",
    [
        (CoercionError, "coercion error"),
        (ValidationError, "validation error"),
        (ConfigInvalidError, "config error"),
    ],
)
def test_issue_list_errors(exc_cls, label):
    issues = [ConfigIssue("a", "one"), ConfigIssue("b", "two")]
    exc = exc_cls(issues)
    assert len(exc.issues) == 2
    assert label in str(exc)
    assert exc.label == label


def test_issue_list_error_single_noun():
    exc = ValidationError([ConfigIssue("x", "bad")])
    assert "1 validation error:" in str(exc)


def test_parse_error_with_path_and_line():
    exc = ParseError("bad line", path=".env", line=3)
    assert exc.path == ".env"
    assert exc.line == 3
    assert ".env" in str(exc)
    assert "line 3" in str(exc)


def test_parse_error_message_only():
    exc = ParseError("oops")
    assert str(exc) == "oops"


def test_exception_hierarchy():
    assert issubclass(ConfigKeyError, (ConfigError, KeyError))
    assert issubclass(CoercionError, IssueListError)
    assert issubclass(SchemaError, ConfigError)
    assert issubclass(ConfigFrozenError, TypeError)


def test_source_error():
    exc = SourceError("file missing")
    assert isinstance(exc, ConfigError)


def test_config_key_error_is_key_error():
    with pytest.raises(KeyError):
        raise ConfigKeyError("missing.path")
