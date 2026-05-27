"""Source adapters that load raw values and provenance."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .dotenv import load_dotenv_file
from .errors import ConfigError, ParseError
from .paths import safe_set_path
from .provenance import Provenance
from .schema import Schema
from .toml_loader import load_toml_file

SourceResult = tuple[dict[str, Any], dict[str, Provenance]]


def normalize_prefix(prefix: str | None) -> str | None:
    if prefix is None:
        return None
    if prefix == "":
        raise ConfigError("prefix cannot be an empty string")
    return prefix


def defaults_source(schema: Schema) -> SourceResult:
    data = schema.defaults()
    provenance = {
        path: Provenance(source="default", name=path, raw_value=field.default)
        for path, field in schema.fields.items()
        if field.has_default
    }
    return data, provenance


def toml_source(path: str | Path | None) -> SourceResult:
    if path is None:
        return {}, {}
    data = load_toml_file(path)
    provenance = _provenance_for_nested(data, source="config_file", source_name=str(path))
    return data, provenance


def dotenv_source(
    path: str | Path | None,
    *,
    prefix: str | None = None,
    schema: Schema | None = None,
) -> SourceResult:
    if path is None:
        return {}, {}
    flat = load_dotenv_file(path)
    env_key_map = schema.env_key_map(prefix=prefix) if schema else {}
    data: dict[str, Any] = {}
    provenance: dict[str, Provenance] = {}
    prefix_text = f"{prefix.upper()}_" if prefix else ""
    for key, value in flat.items():
        resolved = _resolve_env_key(
            key, prefix=prefix, prefix_text=prefix_text, env_key_map=env_key_map
        )
        if resolved is None:
            continue
        dotted, _ = resolved
        safe_set_path(data, dotted, value)
        provenance[dotted] = Provenance(source="env_file", name=dotted, raw_value=value)
    return data, provenance


def environment_source(
    env: Mapping[str, str] | None = None,
    *,
    prefix: str | None = None,
    allow_prefixless: bool = False,
    schema: Schema | None = None,
) -> SourceResult:
    if env is None:
        env = os.environ
    if prefix is None and not allow_prefixless:
        return {}, {}

    data: dict[str, Any] = {}
    provenance: dict[str, Provenance] = {}
    env_key_map = schema.env_key_map(prefix=prefix) if schema else {}
    prefix_text = f"{prefix.upper()}_" if prefix else ""
    for name, value in env.items():
        resolved = _resolve_env_key(
            name,
            prefix=prefix,
            prefix_text=prefix_text,
            env_key_map=env_key_map,
            require_prefix=prefix is not None or allow_prefixless,
        )
        if resolved is None:
            continue
        dotted, _ = resolved
        safe_set_path(data, dotted, value)
        provenance[dotted] = Provenance(source="environment", name=dotted, raw_value=value)
    return data, provenance


def cli_overrides_source(
    overrides: Mapping[str, str] | None = None,
    *,
    schema: Schema | None = None,
) -> SourceResult:
    data: dict[str, Any] = {}
    provenance: dict[str, Provenance] = {}
    if not overrides:
        return data, provenance
    cli_key_map = schema.cli_key_map() if schema else {}
    for key, value in overrides.items():
        path = cli_key_map.get(key, key)
        if not path or any(not part for part in path.split(".")):
            raise ParseError(f"invalid CLI override key {key!r}")
        safe_set_path(data, path, value)
        provenance[path] = Provenance(source="cli", name=key, raw_value=value)
    return data, provenance


def parse_cli_set(values: list[str] | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not values:
        return parsed
    for item in values:
        if "=" not in item:
            raise ParseError(f"--set must use key=value syntax, got {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ParseError("--set key cannot be empty")
        parsed[key] = value
    return parsed


def _resolve_env_key(
    name: str,
    *,
    prefix: str | None,
    prefix_text: str,
    env_key_map: dict[str, str],
    require_prefix: bool = True,
) -> tuple[str, str] | None:
    upper_name = name.upper()
    if upper_name in env_key_map:
        return env_key_map[upper_name], name

    if prefix_text:
        if not upper_name.startswith(prefix_text):
            return None
        raw_key = name[len(prefix_text) :]
    elif prefix is not None or require_prefix:
        raw_key = name
    else:
        return None

    if not raw_key:
        return None
    return _key_to_dotted(raw_key), raw_key


def _key_to_dotted(name: str) -> str:
    return ".".join(part.lower() for part in name.split("__") if part)


def _provenance_for_nested(
    data: Mapping[str, Any],
    *,
    source: str,
    source_name: str,
    prefix: str = "",
) -> dict[str, Provenance]:
    provenance: dict[str, Provenance] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            provenance.update(
                _provenance_for_nested(
                    value,
                    source=source,
                    source_name=source_name,
                    prefix=path,
                )
            )
        else:
            provenance[path] = Provenance(source=source, name=path, raw_value=value)
    return provenance
