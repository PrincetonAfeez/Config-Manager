"""Tests for paths module."""

from config_manager.paths import get_path, has_path, iter_leaf_paths


def test_get_path_supports_bracket_segments():
    data = {"items": [{"extra": "x", "id": 1}]}
    assert get_path(data, "items[0].extra") == "x"
    assert get_path(data, "items[0].id") == 1


def test_get_path_bracket_out_of_range():
    data = {"items": [{"extra": "x"}]}
    assert get_path(data, "items[1].extra") is None


def test_has_path_with_brackets():
    data = {"items": [{"extra": "x"}]}
    assert has_path(data, "items[0].extra")
    assert not has_path(data, "items[0].missing")


def test_iter_leaf_paths_value_available_via_get_path():
    data = {"items": [{"extra": "surprise"}]}
    for path in iter_leaf_paths(data):
        assert get_path(data, path) is not None


def test_scalar_list_paths():
    assert iter_leaf_paths({"features": ["a", "b"]}) == ["features[0]", "features[1]"]
