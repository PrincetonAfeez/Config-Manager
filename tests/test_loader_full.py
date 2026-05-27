"""Tests for config_manager.loader."""

import pytest
from config_manager import ConfigInvalidError, Field, Schema, load


def test_load_minimal():
    schema = Schema({"app": {"name": Field(str, default="demo")}})
    config = load(schema)
    assert config.get("app.name") == "demo"


def test_load_all_layers(tmp_path):
    schema = Schema(
        {
            "app": {"name": Field(str, required=True), "port": Field(int, default=8080)},
            "database": {"password": Field(str, required=True, secret=True)},
        }
    )
    toml = tmp_path / "app.toml"
    toml.write_text('[app]\nname = "FromToml"\n', encoding="utf-8")
    env_file = tmp_path / ".env"
    env_file.write_text("MYAPP_DATABASE__PASSWORD=fromenv\n", encoding="utf-8")
    config = load(
        schema,
        config_file=toml,
        env_file=env_file,
        env={"MYAPP_APP__PORT": "9090"},
        prefix="MYAPP",
        cli_overrides={"app.port": "9091"},
    )
    assert config.get("app.name") == "FromToml"
    assert config.get("app.port") == 9091
    assert config.get("database.password") == "fromenv"


def test_load_lenient_ignores_unknown():
    schema = Schema({"app": {"name": Field(str, default="x")}})
    config = load(
        schema,
        env={"MYAPP_APP__NAME": "Demo", "MYAPP_UNKNOWN": "y"},
        prefix="MYAPP",
        strict=False,
    )
    assert config.get("app.name") == "Demo"


def test_load_raises_config_invalid():
    schema = Schema({"app": {"port": Field(int)}})
    with pytest.raises(ConfigInvalidError):
        load(schema, cli_overrides={"app.port": "not-int"})


def test_load_allow_prefixless_env():
    schema = Schema({"name": Field(str)})
    config = load(schema, env={"NAME": "demo"}, allow_prefixless_env=True)
    assert config.get("name") == "demo"


def test_load_provenance_filtered_to_schema():
    schema = Schema({"app": {"name": Field(str, default="x")}})
    config = load(schema, cli_overrides={"app.name": "y", "extra": "z"}, strict=False)
    assert config.provenance("app.name") is not None
