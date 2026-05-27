"""Exhaustive tests for config_manager.merge."""

import pytest
from config_manager.errors import ParseError
from config_manager.merge import merge_layer, merge_layers
from config_manager.provenance import Provenance


def test_merge_layers_empty():
    data, prov = merge_layers([])
    assert data == {} and prov == {}


def test_merge_layer_nested():
    base = {"app": {"name": "old", "debug": False}}
    override = {"app": {"debug": True}}
    data, _ = merge_layer(base, {}, override, {})
    assert data["app"] == {"name": "old", "debug": True}


def test_merge_layer_list_replacement():
    base = {"tags": ["a"]}
    override = {"tags": ["b", "c"]}
    data, _ = merge_layer(base, {}, override, {})
    assert data["tags"] == ["b", "c"]


def test_merge_scalar_over_dict_raises():
    with pytest.raises(ParseError):
        merge_layer({"db": {"port": 1}}, {}, {"db": 99}, {})


def test_merge_dict_over_scalar_raises():
    with pytest.raises(ParseError):
        merge_layer({"db": "host"}, {}, {"db": {"port": 1}}, {})


def test_merge_string_over_dict_allowed_for_coercion():
    """String overrides from env/CLI may replace dicts before coercion."""
    data, _ = merge_layer({"flags": {"a": True}}, {}, {"flags": '{"b": false}'}, {})
    assert data["flags"] == '{"b": false}'


def test_merge_provenance_unknown_fallback():
    override = {"items": [{"extra": "x"}]}
    _, prov = merge_layer({}, {}, override, {})
    assert "items[0].extra" in prov
    assert prov["items[0].extra"].raw_value == "x"


def test_merge_provenance_tracks_source():
    base_prov = {"app.name": Provenance(source="default", name="app.name", raw_value="old")}
    override_prov = {"app.name": Provenance(source="cli", name="app.name", raw_value="new")}
    _, prov = merge_layer(
        {"app": {"name": "old"}}, base_prov, {"app": {"name": "new"}}, override_prov
    )
    assert prov["app.name"].source == "cli"
