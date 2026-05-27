"""Tests for config explain masking, path_may_contain_secrets, and list secrets."""

from config_manager import Field, Schema, load


def test_explain_masks_list_object_item_secrets():
    schema = Schema(
        {
            "servers": Field(
                list,
                item_fields={"host": Field(str), "token": Field(str)},
            )
        }
    )
    config = load(schema, cli_overrides={"servers": '[{"host":"a","token":"sec"}]'})
    info = config.explain("servers")
    assert info["secret"] is True
    assert info["raw_value"] == "********"
    assert info["value"][0]["host"] == "a"
    assert info["value"][0]["token"] == "********"


def test_to_masked_dict_masks_inferred_dict_keys():
    schema = Schema({"flags": Field(dict, default={"password": "secret"})})
    config = load(schema)
    assert config.to_masked_dict()["flags"]["password"] == "********"


def test_homogeneous_secret_list_masks_each_item():
    schema = Schema({"tokens": Field(list, item_type=str, secret=True, default=[])})
    config = load(schema, cli_overrides={"tokens": "a,b,c"})
    masked = config.to_masked_dict()
    assert masked["tokens"] == ["********", "********", "********"]
    assert config.get("tokens") == ("a", "b", "c")


def test_explain_homogeneous_secret_list():
    schema = Schema({"tokens": Field(list, item_type=str, secret=True)})
    config = load(schema, cli_overrides={"tokens": "secret1,secret2"})
    info = config.explain("tokens")
    assert info["secret"] is True
    assert info["raw_value"] == "********"
    assert info["value"] == ("********", "********")


def test_path_may_contain_secrets_for_dict_and_lists():
    schema = Schema(
        {
            "flags": Field(dict, default={}),
            "tokens": Field(list, item_type=str, secret=True),
            "servers": Field(list, item_fields={"host": Field(str), "token": Field(str)}),
            "app": {"name": Field(str)},
        }
    )
    assert schema.path_may_contain_secrets("flags")
    assert schema.path_may_contain_secrets("tokens")
    assert schema.path_may_contain_secrets("servers")
    assert not schema.path_may_contain_secrets("app.name")
    assert "tokens[]" in schema.secret_paths()


def test_explain_not_set_dict_may_contain_secrets():
    schema = Schema({"flags": Field(dict), "app": {"name": Field(str)}})
    config = load(schema, cli_overrides={"app.name": "demo"})
    assert config.explain("flags")["secret"] is True
    assert config.explain("app.name")["secret"] is False
