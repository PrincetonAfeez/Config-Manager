"""Exhaustive tests for config_manager.coercion."""

import pytest
from config_manager import Field
from config_manager.coercion import (
    coerce_config,
    coerce_value,
    collect_coercion_issues,
)
from config_manager.errors import CoercionError
from config_manager.schema import Schema


@pytest.mark.parametrize(
    "value,expected",
    [
        ("hello", "hello"),
        (42, "42"),
        (True, "True"),
        (3.14, "3.14"),
    ],
)
def test_coerce_str(value, expected):
    assert coerce_value(value, Field(str)) == expected


def test_coerce_str_rejects_list():
    with pytest.raises(ValueError, match="str-compatible"):
        coerce_value([], Field(str))


@pytest.mark.parametrize(
    "value,expected",
    [
        ("5432", 5432),
        (5432, 5432),
        (5432.0, 5432),
    ],
)
def test_coerce_int(value, expected):
    assert coerce_value(value, Field(int)) == expected


@pytest.mark.parametrize(
    "value",
    ["abc", True, 1.5, ""],
)
def test_coerce_int_rejects(value):
    with pytest.raises(ValueError):
        coerce_value(value, Field(int))


def test_coerce_int_rejects_bool():
    with pytest.raises(ValueError, match="bool"):
        coerce_value(True, Field(int))


@pytest.mark.parametrize(
    "value,expected",
    [
        ("3.14", 3.14),
        (2, 2.0),
        (1.5, 1.5),
    ],
)
def test_coerce_float(value, expected):
    assert coerce_value(value, Field(float)) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("no", False),
        ("on", True),
        ("off", False),
        (1, True),
        (0, False),
        (True, True),
    ],
)
def test_coerce_bool(value, expected):
    assert coerce_value(value, Field(bool)) == expected


def test_coerce_bool_rejects_invalid():
    with pytest.raises(ValueError):
        coerce_value("maybe", Field(bool))


def test_coerce_nullable():
    assert coerce_value(None, Field(str, nullable=True)) is None


def test_coerce_non_nullable_none():
    with pytest.raises(ValueError, match="nullable"):
        coerce_value(None, Field(str))


def test_coerce_list_comma_separated():
    assert coerce_value("a, b ,c", Field(list, item_type=str)) == ["a", "b", "c"]


def test_coerce_list_empty_string():
    assert coerce_value("", Field(list)) == []


def test_coerce_list_json_array():
    assert coerce_value('["x","y"]', Field(list, item_type=str)) == ["x", "y"]


def test_coerce_list_of_objects():
    field = Field(list, item_fields={"id": Field(int), "name": Field(str, required=True)})
    raw = [{"id": 1, "name": "a"}]
    assert coerce_value(raw, field) == [{"id": 1, "name": "a"}]


def test_coerce_list_object_missing_required():
    field = Field(list, item_fields={"name": Field(str, required=True)})
    with pytest.raises(ValueError, match="missing required"):
        coerce_value([{}], field)


def test_coerce_dict_from_mapping():
    assert coerce_value({"a": "1", "b": "2"}, Field(dict, value_type=int)) == {"a": 1, "b": 2}


def test_coerce_dict_from_json():
    assert coerce_value('{"x": true}', Field(dict, value_type=bool)) == {"x": True}


def test_coerce_config_raises():
    schema = Schema({"app": {"port": Field(int)}})
    with pytest.raises(CoercionError):
        coerce_config({"app": {"port": "bad"}}, schema)


def test_collect_coercion_issues_returns_partial():
    schema = Schema({"app": {"port": Field(int), "name": Field(str)}})
    output, issues = collect_coercion_issues({"app": {"port": "bad", "name": "ok"}}, schema)
    assert len(issues) == 1
    assert issues[0].path == "app.port"
    assert output["app"]["name"] == "ok"
