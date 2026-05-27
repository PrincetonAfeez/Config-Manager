"""Secret masking helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

MASK = "********"


def masked_value(value: Any) -> str:
    return MASK


def contains_masked(value: Any) -> bool:
    if value == MASK:
        return True
    if isinstance(value, Mapping):
        return any(contains_masked(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(contains_masked(item) for item in value)
    return False


def mask_value_at_path(
    path: str,
    value: Any,
    *,
    secret_paths: set[str],
    dict_field_paths: set[str] | None = None,
) -> Any:
    wrapped: Any = value
    for part in reversed(path.split(".")):
        wrapped = {part: wrapped}
    masked = mask_nested(
        wrapped,
        secret_paths,
        dict_field_paths=dict_field_paths,
    )
    current = masked
    for part in path.split("."):
        current = current[part]
    return current


def mask_nested(
    data: Mapping[str, Any],
    secret_paths: set[str],
    prefix: str = "",
    *,
    dict_field_paths: set[str] | None = None,
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if path in secret_paths:
            output[key] = MASK
        elif dict_field_paths and path in dict_field_paths and isinstance(value, Mapping):
            output[key] = _mask_freeform_dict(value)
        elif isinstance(value, Mapping):
            output[key] = mask_nested(
                value,
                secret_paths,
                path,
                dict_field_paths=dict_field_paths,
            )
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            output[key] = _mask_sequence(value, secret_paths, path, dict_field_paths)
        else:
            output[key] = value
    return output


def _mask_freeform_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    from .schema import Schema

    output: dict[str, Any] = {}
    for key, value in data.items():
        if Schema.inferred_secret_leaf(str(key)):
            output[key] = MASK
        elif isinstance(value, Mapping):
            output[key] = _mask_freeform_dict(value)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            output[key] = [
                _mask_freeform_dict(item) if isinstance(item, Mapping) else item for item in value
            ]
        else:
            output[key] = value
    return output


def _mask_sequence(
    items: Sequence[Any],
    secret_paths: set[str],
    prefix: str,
    dict_field_paths: set[str] | None,
) -> list[Any] | tuple[Any, ...]:
    mask_all_scalars = f"{prefix}[]" in secret_paths
    masked: list[Any] = []
    for index, item in enumerate(items):
        item_path = f"{prefix}[{index}]"
        if item_path in secret_paths or mask_all_scalars:
            if isinstance(item, Mapping):
                masked.append(_mask_mapping_item(item, secret_paths, prefix, dict_field_paths))
            elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
                masked.append(_mask_sequence(item, secret_paths, item_path, dict_field_paths))
            else:
                masked.append(MASK)
        elif isinstance(item, Mapping):
            masked.append(_mask_mapping_item(item, secret_paths, prefix, dict_field_paths))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            masked.append(_mask_sequence(item, secret_paths, item_path, dict_field_paths))
        else:
            masked.append(item)
    return tuple(masked) if isinstance(items, tuple) else masked


def _mask_mapping_item(
    item: Mapping[str, Any],
    secret_paths: set[str],
    list_path: str,
    dict_field_paths: set[str] | None,
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in item.items():
        pattern_path = f"{list_path}[].{key}"
        if pattern_path in secret_paths:
            output[key] = MASK
        elif isinstance(value, Mapping):
            output[key] = mask_nested(
                value,
                secret_paths,
                f"{list_path}[].{key}",
                dict_field_paths=dict_field_paths,
            )
        else:
            output[key] = value
    return output
