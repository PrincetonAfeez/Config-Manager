"""Secret masking helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

MASK = "********"


def masked_value(value: Any) -> str:
    return MASK


def mask_nested(
    data: Mapping[str, Any], secret_paths: set[str], prefix: str = ""
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if path in secret_paths:
            output[key] = MASK
        elif isinstance(value, Mapping):
            output[key] = mask_nested(value, secret_paths, path)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            output[key] = _mask_sequence(value, secret_paths, path)
        else:
            output[key] = value
    return output


def _mask_sequence(
    items: Sequence[Any], secret_paths: set[str], prefix: str
) -> list[Any] | tuple[Any, ...]:
    masked: list[Any] = []
    for index, item in enumerate(items):
        item_path = f"{prefix}[{index}]"
        if item_path in secret_paths:
            masked.append(MASK)
        elif isinstance(item, Mapping):
            masked.append(_mask_mapping_item(item, secret_paths, prefix))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            masked.append(_mask_sequence(item, secret_paths, item_path))
        else:
            masked.append(item)
    return tuple(masked) if isinstance(items, tuple) else masked


def _mask_mapping_item(
    item: Mapping[str, Any], secret_paths: set[str], list_path: str
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in item.items():
        pattern_path = f"{list_path}[].{key}"
        if pattern_path in secret_paths:
            output[key] = MASK
        elif isinstance(value, Mapping):
            output[key] = mask_nested(value, secret_paths, f"{list_path}[].{key}")
        else:
            output[key] = value
    return output
