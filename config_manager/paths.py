"""Small helpers for nested dotted paths."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .errors import ParseError

_SEGMENT = re.compile(r"^([^[]+)(?:\[(\d+)\])?$")


def set_path(target: dict[str, Any], path: str, value: Any) -> None:
    parts = _split_path(path)
    if not parts:
        raise ValueError("path cannot be empty")
    current = target
    for key, index in parts[:-1]:
        if index is None:
            next_value = current.setdefault(key, {})
            if not isinstance(next_value, dict):
                raise ValueError(f"cannot set {path}: {key} is already a scalar")
            current = next_value
        else:
            items = current.setdefault(key, [])
            if not isinstance(items, list):
                raise ValueError(f"cannot set {path}: {key} is not a list")
            while len(items) <= index:
                items.append({})
            if not isinstance(items[index], dict):
                raise ValueError(f"cannot set {path}: {key}[{index}] is already a scalar")
            current = items[index]
    last_key, last_index = parts[-1]
    if last_index is None:
        if (
            last_key in current
            and isinstance(current[last_key], dict)
            and not isinstance(value, Mapping)
        ):
            raise ValueError(f"cannot replace nested config at {last_key!r} with scalar value")
        if (
            last_key in current
            and not isinstance(current[last_key], dict)
            and isinstance(value, Mapping)
        ):
            raise ValueError(f"cannot replace scalar at {last_key!r} with nested config")
        current[last_key] = value
    else:
        items = current.setdefault(last_key, [])
        if not isinstance(items, list):
            raise ValueError(f"cannot set {path}: {last_key} is not a list")
        while len(items) <= last_index:
            items.append(None)
        items[last_index] = value


def safe_set_path(target: dict[str, Any], path: str, value: Any) -> None:
    try:
        set_path(target, path, value)
    except ValueError as exc:
        raise ParseError(str(exc)) from exc


def get_path(data: Mapping[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for key, index in _split_path(path):
        if index is None:
            if not isinstance(current, Mapping) or key not in current:
                return default
            current = current[key]
        else:
            if not isinstance(current, Mapping) or key not in current:
                return default
            current = current[key]
            if not isinstance(current, list) or index >= len(current):
                return default
            current = current[index]
    return current


def has_path(data: Mapping[str, Any], path: str) -> bool:
    marker = object()
    return get_path(data, path, marker) is not marker


def iter_leaf_paths(data: Mapping[str, Any], prefix: str = "") -> list[str]:
    paths: list[str] = []
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            paths.extend(iter_leaf_paths(value, path))
        elif isinstance(value, list):
            paths.extend(_iter_list_paths(value, path))
        else:
            paths.append(path)
    return paths


def _split_path(path: str) -> list[tuple[str, int | None]]:
    parts: list[tuple[str, int | None]] = []
    for segment in path.split("."):
        if not segment:
            continue
        match = _SEGMENT.match(segment)
        if not match:
            parts.append((segment, None))
            continue
        key, index_text = match.group(1), match.group(2)
        parts.append((key, int(index_text) if index_text is not None else None))
    return parts


def _iter_list_paths(items: list[Any], path: str) -> list[str]:
    if not items:
        return [path]
    paths: list[str] = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if isinstance(item, Mapping):
            paths.extend(iter_leaf_paths(item, item_path))
        else:
            paths.append(item_path)
    return paths


def deep_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [deep_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(deep_copy(item) for item in value)
    return value
