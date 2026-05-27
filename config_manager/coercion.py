"""Schema-driven type coercion."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .errors import CoercionError, ConfigIssue
from .fields import Field
from .paths import get_path, has_path, set_path
from .provenance import Provenance
from .schema import Schema


def coerce_config(data: Mapping[str, Any], schema: Schema) -> dict[str, Any]:
    output, issues = collect_coercion_issues(data, schema)
    if issues:
        raise CoercionError(issues)
    return output


def collect_coercion_issues(
    data: Mapping[str, Any],
    schema: Schema,
    *,
    provenance: Mapping[str, Provenance] | None = None,
) -> tuple[dict[str, Any], list[ConfigIssue]]:
    output: dict[str, Any] = {}
    issues: list[ConfigIssue] = []
    for path, field in schema.fields.items():
        if not has_path(data, path):
            continue
        raw_value = get_path(data, path)
        try:
            value = coerce_value(raw_value, field)
        except ValueError as exc:
            issues.append(_make_issue(path, str(exc), raw_value, field, schema, provenance))
            continue
        set_path(output, path, value)
    return output, issues


def coerce_value(value: Any, field: Field) -> Any:
    if value is None:
        if field.nullable:
            return None
        raise ValueError("None is allowed only when nullable=True")

    target = field.type_
    if target is str:
        return _coerce_str(value)
    if target is bool:
        return _coerce_bool(value)
    if target is int:
        return _coerce_int(value)
    if target is float:
        return _coerce_float(value)
    if target is list:
        return _coerce_list(value, field)
    if target is dict:
        return _coerce_dict(value, field.value_type)
    raise ValueError(f"unsupported field type {target!r}")


def _make_issue(
    path: str,
    message: str,
    value: Any,
    field: Field,
    schema: Schema,
    provenance: Mapping[str, Provenance] | None,
) -> ConfigIssue:
    source = None
    if provenance and path in provenance:
        source = provenance[path].source
    return ConfigIssue(
        path,
        message,
        value,
        source=source,
        secret=schema.is_secret(path),
    )


def _coerce_str(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    raise ValueError(f"expected str-compatible value, got {type(value).__name__}")


def _coerce_int(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("expected int, got bool")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError(f"expected int, got non-integer float {value!r}")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("expected int, got empty string")
        try:
            return int(text, 10)
        except ValueError as exc:
            raise ValueError(f"expected int, got {value!r}") from exc
    raise ValueError(f"expected int, got {type(value).__name__}")


def _coerce_float(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("expected float, got bool")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("expected float, got empty string")
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"expected float, got {value!r}") from exc
    raise ValueError(f"expected float, got {type(value).__name__}")


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if value == 1:
            return True
        if value == 0:
            return False
        raise ValueError(f"expected bool, got int {value!r}")
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "y", "on"}:
            return True
        if text in {"false", "0", "no", "n", "off"}:
            return False
        if text == "":
            raise ValueError("expected bool, got empty string")
        raise ValueError(f"expected bool, got {value!r}")
    raise ValueError(f"expected bool, got {type(value).__name__}")


def _coerce_list(value: Any, field: Field) -> list[Any]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        if value.strip() == "":
            items = []
        elif value.strip().startswith("["):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"expected list or JSON array, got {value!r}") from exc
            if not isinstance(parsed, list):
                raise ValueError(f"expected list, got {type(parsed).__name__}")
            items = parsed
        else:
            items = [item.strip() for item in value.split(",")]
    else:
        raise ValueError(f"expected list, got {type(value).__name__}")

    if field.item_fields is not None:
        coerced = []
        for index, item in enumerate(items):
            try:
                coerced.append(_coerce_object(item, field.item_fields))
            except ValueError as exc:
                raise ValueError(f"invalid list item at index {index}: {exc}") from exc
        return coerced

    if field.item_type is None:
        return list(items)
    pseudo_field = Field(field.item_type)
    coerced = []
    for item in items:
        try:
            coerced.append(coerce_value(item, pseudo_field))
        except ValueError as exc:
            raise ValueError(f"invalid list item {item!r}: {exc}") from exc
    return coerced


def _coerce_object(value: Any, item_fields: Mapping[str, Field]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"expected object, got {type(value).__name__}")
    output: dict[str, Any] = {}
    for key, subfield in item_fields.items():
        if key not in value:
            if subfield.required and not subfield.has_default:
                raise ValueError(f"missing required field {key!r}")
            if subfield.has_default:
                output[key] = subfield.default
            continue
        output[key] = coerce_value(value[key], subfield)
    return output


def _coerce_dict(value: Any, value_type: type | None) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"expected dict or JSON object, got {value!r}") from exc
        value = parsed
    if not isinstance(value, Mapping):
        raise ValueError(f"expected dict, got {type(value).__name__}")
    output: dict[str, Any] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key)
        if value_type is None:
            output[key] = raw_value
        else:
            output[key] = coerce_value(raw_value, Field(value_type))
    return output
