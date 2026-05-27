"""Validation after coercion."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .errors import ConfigIssue, ValidationError
from .fields import Field
from .paths import get_path, has_path, iter_leaf_paths, set_path
from .provenance import Provenance
from .schema import Schema


def validate_config(
    data: Mapping[str, Any], raw_data: Mapping[str, Any], schema: Schema, *, strict: bool
) -> None:
    issues = collect_validation_issues(data, raw_data, schema, strict=strict)
    if issues:
        raise ValidationError(issues)


def collect_validation_issues(
    data: Mapping[str, Any],
    raw_data: Mapping[str, Any],
    schema: Schema,
    *,
    strict: bool,
    provenance: Mapping[str, Provenance] | None = None,
) -> list[ConfigIssue]:
    issues: list[ConfigIssue] = []
    schema_paths = set(schema.fields)

    for path, field in schema.fields.items():
        if not has_path(raw_data, path):
            if field.required and not field.has_default:
                issues.append(
                    _make_issue(path, "required field is missing", None, schema, provenance)
                )
            continue
        if not has_path(data, path):
            continue
        value = get_path(data, path)
        issues.extend(_validate_field(path, value, field, schema, provenance))

    unknown_paths = sorted(
        path
        for path in iter_leaf_paths(raw_data)
        if path not in schema_paths
        and not _is_nested_schema_content(path, schema)
        and not _is_list_item_path(path, schema)
    )
    if strict:
        for path in unknown_paths:
            issues.append(
                _make_issue(
                    path, "unknown config key", get_path(raw_data, path), schema, provenance
                )
            )

    return issues


def filter_to_schema(data: Mapping[str, Any], schema: Schema) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for path in schema.fields:
        if has_path(data, path):
            set_path(output, path, get_path(data, path))
    return output


def _make_issue(
    path: str,
    message: str,
    value: Any,
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


def _validate_field(
    path: str,
    value: Any,
    field: Field,
    schema: Schema,
    provenance: Mapping[str, Provenance] | None,
) -> list[ConfigIssue]:
    issues: list[ConfigIssue] = []
    if value is None:
        if not field.nullable:
            issues.append(
                _make_issue(
                    path, "None is allowed only when nullable=True", value, schema, provenance
                )
            )
        return issues

    if not _matches_type(value, field.type_):
        issues.append(
            _make_issue(
                path,
                f"expected {field.type_.__name__}, got {type(value).__name__}",
                value,
                schema,
                provenance,
            )
        )
        return issues

    if field.type_ is dict:
        if field.min_length is not None and len(value) < field.min_length:
            issues.append(
                _make_issue(
                    path, f"length must be >= {field.min_length}", value, schema, provenance
                )
            )
        if field.max_length is not None and len(value) > field.max_length:
            issues.append(
                _make_issue(
                    path, f"length must be <= {field.max_length}", value, schema, provenance
                )
            )
        if field.validator is not None:
            try:
                result = field.validator(value)
            except ValueError as exc:
                issues.append(_make_issue(path, str(exc), value, schema, provenance))
            else:
                if not result:
                    issues.append(
                        _make_issue(
                            path, "custom validator rejected value", value, schema, provenance
                        )
                    )
        return issues

    if field.choices is not None and value not in field.choices:
        choices = ", ".join(str(choice) for choice in field.choices)
        issues.append(_make_issue(path, f"must be one of {choices}", value, schema, provenance))
    if field.min_value is not None and value < field.min_value:
        issues.append(_make_issue(path, f"must be >= {field.min_value}", value, schema, provenance))
    if field.max_value is not None and value > field.max_value:
        issues.append(_make_issue(path, f"must be <= {field.max_value}", value, schema, provenance))
    if (
        field.min_length is not None
        and isinstance(value, (str, list))
        and len(value) < field.min_length
    ):
        issues.append(
            _make_issue(path, f"length must be >= {field.min_length}", value, schema, provenance)
        )
    if (
        field.max_length is not None
        and isinstance(value, (str, list))
        and len(value) > field.max_length
    ):
        issues.append(
            _make_issue(path, f"length must be <= {field.max_length}", value, schema, provenance)
        )
    if field.regex is not None and isinstance(value, str) and not re.fullmatch(field.regex, value):
        issues.append(
            _make_issue(path, f"must match regex {field.regex}", value, schema, provenance)
        )
    if field.type_ is list and field.item_fields is not None:
        issues.extend(_validate_list_objects(path, value, field, schema, provenance))
    if field.validator is not None:
        try:
            result = field.validator(value)
        except ValueError as exc:
            issues.append(_make_issue(path, str(exc), value, schema, provenance))
        else:
            if not result:
                issues.append(
                    _make_issue(path, "custom validator rejected value", value, schema, provenance)
                )
    return issues


def _is_nested_schema_content(path: str, schema: Schema) -> bool:
    """Paths inside list-of-object or dict fields are not unknown keys."""
    for schema_path, field in schema.fields.items():
        if field.type_ is list and field.item_fields and path.startswith(f"{schema_path}["):
            return True
        if field.type_ is dict and path.startswith(f"{schema_path}."):
            return True
    return False


def _is_list_item_path(path: str, schema: Schema) -> bool:
    """Scalar list items such as tags[0] belong to a list schema field."""
    for schema_path, field in schema.fields.items():
        if field.type_ is list and field.item_fields is None and path.startswith(f"{schema_path}["):
            return True
    return False


def _validate_list_objects(
    path: str,
    value: Any,
    field: Field,
    schema: Schema,
    provenance: Mapping[str, Provenance] | None,
) -> list[ConfigIssue]:
    issues: list[ConfigIssue] = []
    assert field.item_fields is not None
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, Mapping):
            issues.append(
                _make_issue(
                    item_path,
                    f"expected object, got {type(item).__name__}",
                    item,
                    schema,
                    provenance,
                )
            )
            continue
        for key, subfield in field.item_fields.items():
            subpath = f"{item_path}.{key}"
            if key not in item:
                if subfield.required and not subfield.has_default:
                    issues.append(
                        _make_issue(subpath, "required field is missing", None, schema, provenance)
                    )
                continue
            issues.extend(_validate_field(subpath, item[key], subfield, schema, provenance))
    return issues


def _matches_type(value: Any, expected: type) -> bool:
    if expected is bool:
        return isinstance(value, bool)
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected is float:
        return isinstance(value, float)
    if expected is list:
        return isinstance(value, list)
    if expected is dict:
        return isinstance(value, dict)
    return isinstance(value, expected)
