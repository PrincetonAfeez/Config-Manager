"""Generate starter config files from a schema."""

from __future__ import annotations

from typing import Any

from .fields import MISSING
from .schema import Schema


def generate_env_example(schema: Schema, *, prefix: str | None = None) -> str:
    lines: list[str] = []
    for path in sorted(schema.fields):
        field = schema.fields[path]
        if field.description:
            lines.append(f"# {field.description}")
        if field.required and not field.has_default:
            lines.append("# required")
        name = schema.env_name_for(path, prefix=prefix)
        value = "" if field.default is MISSING else _format_env_value(field.default)
        lines.append(f"{name}={value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_toml_example(schema: Schema) -> str:
    sections: dict[str, list[tuple[str, Any, str]]] = {}
    root_values: list[tuple[str, Any, str]] = []
    for path in sorted(schema.fields):
        field = schema.fields[path]
        parts = path.split(".")
        key = parts[-1]
        section = ".".join(parts[:-1])
        value = "" if field.default is MISSING else field.default
        entry = (key, value, field.description)
        if section:
            sections.setdefault(section, []).append(entry)
        else:
            root_values.append(entry)

    lines: list[str] = []
    for key, value, description in root_values:
        if description:
            lines.append(f"# {description}")
        lines.append(f"{key} = {_format_toml_value(value)}")
    if root_values and sections:
        lines.append("")
    for section in sorted(sections):
        lines.append(f"[{section}]")
        for key, value, description in sections[section]:
            if description:
                lines.append(f"# {description}")
            lines.append(f"{key} = {_format_toml_value(value)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _format_toml_value(value: Any) -> str:
    if value == "":
        return '""'
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(_format_toml_value(item) for item in value) + "]"
    if value is None:
        return '""'
    return str(value)
