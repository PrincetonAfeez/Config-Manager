"""Tests for config_manager.fields."""

from dataclasses import FrozenInstanceError

import pytest
from config_manager.fields import MISSING, Field


def test_missing_repr():
    assert repr(MISSING) == "MISSING"


def test_field_has_default_false():
    assert Field(str).has_default is False


def test_field_has_default_true():
    assert Field(str, default="x").has_default is True


@pytest.mark.parametrize(
    "field,expected",
    [
        (Field(str), "str"),
        (Field(int), "int"),
        (Field(list, item_type=str), "list[str]"),
        (
            Field(list, item_fields={"id": Field(int), "name": Field(str)}),
            "list[{id: int, name: str}]",
        ),
        (Field(dict, value_type=bool), "dict[str, bool]"),
        (Field(dict), "dict"),
    ],
)
def test_field_type_name(field, expected):
    assert field.type_name == expected


def test_field_frozen():
    field = Field(str, default="a")
    with pytest.raises(FrozenInstanceError):
        field.default = "b"  # type: ignore[misc]
