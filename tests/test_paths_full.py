"""Exhaustive tests for config_manager.paths."""

import pytest
from config_manager.errors import ParseError
from config_manager.paths import (
    deep_copy,
    get_path,
    has_path,
    iter_leaf_paths,
    safe_set_path,
    set_path,
)


def test_set_path_nested():
    target: dict = {}
    set_path(target, "app.name", "Demo")
    assert target == {"app": {"name": "Demo"}}


def test_set_path_bracket_index():
    target: dict = {}
    set_path(target, "items[0].name", "first")
    assert target["items"][0]["name"] == "first"


def test_set_path_scalar_replace_raises():
    target = {"app": {"name": "Demo"}}
    with pytest.raises(ValueError):
        set_path(target, "app", "scalar")


def test_set_path_empty_raises():
    with pytest.raises(ValueError, match="path cannot be empty"):
        set_path({}, "", "value")


def test_set_path_intermediate_scalar_raises():
    with pytest.raises(ValueError, match="already a scalar"):
        set_path({"a": "scalar"}, "a.b", 1)


def test_set_path_intermediate_not_list_raises():
    with pytest.raises(ValueError, match="is not a list"):
        set_path({"items": "scalar"}, "items[0].x", 1)


def test_set_path_list_item_scalar_raises():
    with pytest.raises(ValueError, match="already a scalar"):
        set_path({"items": ["scalar"]}, "items[0].x", 1)


def test_set_path_scalar_to_nested_raises():
    with pytest.raises(ValueError, match="cannot replace scalar"):
        set_path({"a": 1}, "a", {"nested": True})


def test_set_path_bracket_scalar():
    target: dict = {}
    set_path(target, "items[2]", "third")
    assert target["items"][2] == "third"


def test_set_path_nested_replace_raises():
    target = {"app": {"name": "Demo"}}
    with pytest.raises(ValueError, match="cannot replace nested"):
        set_path(target, "app", "scalar")


def test_get_path_empty_segment():
    data = {"a": {"b": 1}}
    assert get_path(data, "a..b") == 1


def test_get_path_invalid_segment():
    assert get_path({"a": 1}, "a[bad") is None


def test_get_path_list_out_of_range():
    assert get_path({"items": [1]}, "items[5]", default="missing") == "missing"


def test_iter_leaf_paths_empty_list():
    assert iter_leaf_paths({"items": []}) == ["items"]


def test_safe_set_path_wraps_nested_replace():
    with pytest.raises(ParseError, match="cannot replace nested"):
        safe_set_path({"app": {"name": "Demo"}}, "app", "scalar")


def test_safe_set_path_wraps_scalar_conflict():
    with pytest.raises(ParseError, match="already a scalar"):
        safe_set_path({"a": "scalar"}, "a.b", 2)


def test_get_path_brackets():
    data = {"items": [{"id": 1}]}
    assert get_path(data, "items[0].id") == 1


def test_has_path_false():
    assert has_path({}, "missing") is False


def test_iter_leaf_paths_nested_list():
    paths = iter_leaf_paths({"items": [{"x": 1}]})
    assert "items[0].x" in paths


def test_deep_copy_nested():
    original = {"a": [1, {"b": 2}]}
    copy = deep_copy(original)
    copy["a"][1]["b"] = 99
    assert original["a"][1]["b"] == 2


def test_deep_copy_tuple():
    assert deep_copy((1, 2)) == (1, 2)
