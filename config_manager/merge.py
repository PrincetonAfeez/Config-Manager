"""Deep merge with scalar/list replacement semantics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import ParseError
from .paths import deep_copy, get_path, iter_leaf_paths
from .provenance import Provenance


def merge_layer(
    base: Mapping[str, Any],
    base_provenance: Mapping[str, Provenance],
    override: Mapping[str, Any],
    override_provenance: Mapping[str, Provenance],
) -> tuple[dict[str, Any], dict[str, Provenance]]:
    data = deep_copy(base)
    provenance = dict(base_provenance)
    _merge_into(data, override)
    for path in iter_leaf_paths(override):
        provenance[path] = override_provenance.get(
            path,
            Provenance(source="unknown", name=path, raw_value=get_path(override, path)),
        )
    return data, provenance


def merge_layers(
    layers: list[tuple[Mapping[str, Any], Mapping[str, Provenance]]],
) -> tuple[dict[str, Any], dict[str, Provenance]]:
    data: dict[str, Any] = {}
    provenance: dict[str, Provenance] = {}
    for layer, layer_provenance in layers:
        data, provenance = merge_layer(data, provenance, layer, layer_provenance)
    return data, provenance


def _merge_into(target: dict[str, Any], override: Mapping[str, Any]) -> None:
    for key, value in override.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, Mapping):
            _merge_into(target[key], value)
        else:
            replacing_dict = (
                key in target
                and isinstance(target[key], dict)
                and not isinstance(value, Mapping)
                and not isinstance(value, str)
            )
            replacing_scalar = (
                key in target and not isinstance(target[key], dict) and isinstance(value, Mapping)
            )
            if replacing_dict:
                raise ParseError(f"cannot replace nested config at {key!r} with scalar value")
            if replacing_scalar:
                raise ParseError(f"cannot replace scalar at {key!r} with nested config")
            target[key] = deep_copy(value)
