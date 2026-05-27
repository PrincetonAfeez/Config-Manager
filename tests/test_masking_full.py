"""Tests for config_manager.masking."""

from config_manager import Field, Schema, load
from config_manager.masking import MASK, mask_nested, masked_value


def test_masked_value():
    assert masked_value("secret") == MASK


def test_mask_nested_secret_path():
    data = {"app": {"name": "Demo"}, "database": {"password": "pw"}}
    masked = mask_nested(data, {"database.password"})
    assert masked["database"]["password"] == MASK
    assert masked["app"]["name"] == "Demo"


def test_mask_nested_list_object_secret():
    schema = Schema(
        {
            "servers": Field(
                list,
                item_fields={"host": Field(str), "password": Field(str)},
            )
        }
    )
    config = load(
        schema,
        cli_overrides={"servers": '[{"host":"a","password":"secret"}]'},
    )
    masked = config.to_masked_dict()
    assert masked["servers"][0]["host"] == "a"
    assert masked["servers"][0]["password"] == MASK


def test_mask_nested_no_secrets():
    data = {"app": {"name": "Demo"}}
    assert mask_nested(data, set()) == data


def test_mask_nested_preserves_non_mapping():
    data = {"tags": ("a", "b")}
    assert mask_nested(data, set())["tags"] == ("a", "b")
