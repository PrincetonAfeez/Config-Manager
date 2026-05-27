"""Tests for merge module."""

import pytest
from config_manager.errors import ParseError
from config_manager.merge import merge_layer
from config_manager.provenance import Provenance


def test_nested_merge():
    base = {"app": {"name": "old", "debug": False}}
    override = {"app": {"debug": True}}
    data, _ = merge_layer(base, {}, override, {})
    assert data == {"app": {"name": "old", "debug": True}}


def test_scalar_replaces_nested_dict_raises():
    base = {"database": {"host": "localhost", "port": 5432}}
    override = {"database": 12345}
    with pytest.raises(ParseError):
        merge_layer(base, {}, override, {})


def test_provenance_tracks_override():
    base = {"database": {"port": 5432}}
    prov = {"database.port": Provenance(source="default", name="database.port", raw_value=5432)}
    override = {"database": {"port": 5433}}
    override_prov = {
        "database.port": Provenance(source="environment", name="database.port", raw_value="5433")
    }
    _, provenance = merge_layer(base, prov, override, override_prov)
    assert provenance["database.port"].source == "environment"
