"""Tests for Config object and source helpers."""

import tempfile
from pathlib import Path

import pytest
from config_manager import ConfigFrozenError, Field, Schema, load
from config_manager.errors import ParseError
from config_manager.sources import cli_overrides_source, dotenv_source, environment_source


def test_list_values_are_immutable():
    schema = Schema({"features": Field(list, default=[], item_type=str)})
    config = load(schema, env={"MYAPP_FEATURES": "a,b"}, prefix="MYAPP")
    features = config.get("features")
    assert isinstance(features, tuple)
    with pytest.raises((TypeError, AttributeError)):
        features.append("z")  # type: ignore[attr-defined]


def test_assignment_raises():
    schema = Schema({"app": {"name": Field(str, default="demo")}})
    config = load(schema)
    with pytest.raises(ConfigFrozenError):
        config.app = "other"  # type: ignore[misc]


def test_get_raises_config_key_error():
    schema = Schema({"app": {"name": Field(str, default="demo")}})
    config = load(schema)
    with pytest.raises(KeyError):
        config.get("missing.path")


def test_dotenv_skips_unprefixed_keys():
    schema = Schema({"app": {"name": Field(str)}})
    env = {"MYAPP_APP__NAME": "ok", "OTHER": "bad"}
    data, _ = dotenv_source(_write_env(env), prefix="MYAPP", schema=schema)
    assert data == {"app": {"name": "ok"}}


def test_environment_matches_dotenv_prefix_rules():
    schema = Schema({"app": {"name": Field(str)}})
    env = {"MYAPP_APP__NAME": "ok", "OTHER": "bad"}
    data, _ = environment_source(env, prefix="MYAPP", schema=schema)
    assert data == {"app": {"name": "ok"}}


def test_env_name_override():
    schema = Schema({"api": {"token": Field(str, env_name="API_TOKEN")}})
    env = {"MYAPP_API_TOKEN": "secret"}
    data, _ = environment_source(env, prefix="MYAPP", schema=schema)
    assert data["api"]["token"] == "secret"


def test_cli_name_override():
    schema = Schema({"database": {"port": Field(int, cli_name="db-port")}})
    data, prov = cli_overrides_source({"db-port": "5432"}, schema=schema)
    assert data["database"]["port"] == "5432"
    assert "database.port" in prov


def test_environment_provenance_uses_original_env_name():
    schema = Schema({"database": {"port": Field(int)}})
    _, prov = environment_source({"MYAPP_DATABASE__PORT": "5432"}, prefix="MYAPP", schema=schema)
    assert prov["database.port"].name == "MYAPP_DATABASE__PORT"


def test_merge_conflict_raises_parse_error():
    schema = Schema({"database": {"port": Field(int)}})
    with pytest.raises(ParseError):
        load(
            schema,
            env={"MYAPP_DATABASE": "localhost", "MYAPP_DATABASE__PORT": "5432"},
            prefix="MYAPP",
        )


def _write_env(values: dict[str, str]) -> Path:
    tmp = tempfile.mkdtemp()
    path = Path(tmp) / ".env"
    path.write_text("\n".join(f"{k}={v}" for k, v in values.items()) + "\n", encoding="utf-8")
    return path
