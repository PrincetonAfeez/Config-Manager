"""Generate starter config files from a schema."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .fields import MISSING, Field
from .schema import Schema


def generate_env_example(schema: Schema, *, prefix: str | None = None) -> str:
    lines: list[str] = []
    for path in sorted(schema.fields):
        field = schema.fields[path]
        if field.description:
            lines.append(f"# {field.description}")
        if field.required and not field.has_default:
            lines.append("# required")
        if field.type_ is list and field.item_fields is not None:
            lines.extend(_format_env_list_objects(path, field, schema, prefix=prefix))
        else:
            name = schema.env_name_for(path, prefix=prefix)
            value = _format_env_field_value(field)
            lines.append(f"{name}={value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_toml_example(schema: Schema) -> str:
    scalar_sections: dict[str, list[tuple[str, Field, str]]] = {}
    list_object_fields: list[tuple[str, Field]] = []

    for path in sorted(schema.fields):
        field = schema.fields[path]
        if field.type_ is list and field.item_fields is not None:
            list_object_fields.append((path, field))
            continue
        parts = path.split(".")
        key = parts[-1]
        section = ".".join(parts[:-1])
        scalar_sections.setdefault(section, []).append((key, field, path))

    lines: list[str] = []
    for section in sorted(scalar_sections.keys(), key=lambda value: (value != "", value)):
        entries = scalar_sections[section]
        if section:
            lines.append(f"[{section}]")
        for key, field, _path in entries:
            if field.description:
                lines.append(f"# {field.description}")
            if field.required and not field.has_default:
                lines.append("# required")
            value = _example_scalar_value(field)
            lines.append(f"{key} = {_format_toml_value(value, field)}")
        if section and (list_object_fields or _has_following_section(section, scalar_sections)):
            lines.append("")

    for path, field in list_object_fields:
        assert field.item_fields is not None
        if field.description:
            lines.append(f"# {field.description}")
        if field.required and not field.has_default:
            lines.append("# required — add one [[...]] block per item")
        lines.append(f"[[{path}]]")
        for item_key, item_field in field.item_fields.items():
            if item_field.description:
                lines.append(f"# {item_field.description}")
            item_value = _example_scalar_value(item_field)
            lines.append(f"{item_key} = {_format_toml_value(item_value, item_field)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _has_following_section(
    section: str, scalar_sections: dict[str, list[tuple[str, Field, str]]]
) -> bool:
    keys = sorted(scalar_sections.keys(), key=lambda value: (value != "", value))
    index = keys.index(section)
    return index < len(keys) - 1


def _format_env_list_objects(
    path: str, field: Field, schema: Schema, *, prefix: str | None
) -> list[str]:
    assert field.item_fields is not None
    name = schema.env_name_for(path, prefix=prefix)
    if field.has_default and isinstance(field.default, list):
        payload = field.default
    else:
        payload = [_example_object(field.item_fields)]
    return [f"{name}={json.dumps(payload, separators=(',', ':'))}"]


def _example_object(item_fields: Mapping[str, Field]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, subfield in item_fields.items():
        if subfield.has_default:
            output[key] = subfield.default
        elif subfield.required:
            output[key] = _example_scalar_value(subfield)
        elif subfield.type_ is bool:
            output[key] = False
        elif subfield.type_ is int:
            output[key] = 0
        elif subfield.type_ is float:
            output[key] = 0.0
        else:
            output[key] = ""
    return output


def _example_scalar_value(field: Field) -> Any:
    if field.has_default:
        return field.default
    if field.type_ is bool:
        return False
    if field.type_ is int:
        return 0
    if field.type_ is float:
        return 0.0
    if field.type_ is list:
        if field.item_type is not None:
            return []
        return []
    if field.type_ is dict:
        return {}
    return ""


def _format_env_field_value(field: Field) -> str:
    if field.default is MISSING:
        if field.type_ is dict:
            return "{}"
        return ""
    value = field.default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        if field.item_type is not None:
            return ",".join(str(item) for item in value)
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    if value is None:
        return ""
    return str(value)


def _format_toml_value(value: Any, field: Field | None = None) -> str:
    if value == "" and (field is None or field.type_ is str):
        return '""'
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(_format_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = [f"{key} = {_format_toml_value(item)}" for key, item in value.items()]
        return "{ " + ", ".join(parts) + " }"
    if value is None:
        return '""'
    return str(value)
