"""Tests for config_manager.provenance."""

from dataclasses import FrozenInstanceError

import pytest
from config_manager.provenance import Provenance


def test_provenance_to_dict():
    prov = Provenance(source="environment", name="app.name", raw_value="Demo")
    data = prov.to_dict()
    assert data == {"source": "environment", "name": "app.name", "raw_value": "Demo"}


def test_provenance_defaults():
    prov = Provenance(source="default")
    assert prov.name is None
    assert prov.raw_value is None


def test_provenance_frozen():
    prov = Provenance(source="cli", name="key", raw_value="1")
    with pytest.raises(FrozenInstanceError):
        prov.source = "other"  # type: ignore[misc]
