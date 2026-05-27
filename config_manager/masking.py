"""Secret masking helpers."""

from __future__ import annotations

from collections.abc import Mapping
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
        else:
            output[key] = value
    return output
