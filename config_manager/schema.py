"""Declarative schema support."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import SchemaError
from .fields import MISSING, Field

SchemaNode = dict[str, "SchemaNode | Field"]

_SUPPORTED_FIELD_TYPES = (str, bool, int, float, list, dict)
_SCALAR_FIELD_TYPES = (str, bool, int, float)

# Leaf key names treated as secrets when Field.secret is not set explicitly.
_INFERRED_SECRET_NAMES = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "access_key",
        "auth_token",
        "client_secret",
    }
)


class Schema:
    """Source of truth for config shape, defaults, docs, and secret metadata."""

    def __init__(self, fields: Mapping[str, Any]) -> None:
        self._tree = self._normalize_node(fields, path="")
        self._flat = self._flatten(self._tree)
        self._validate()

    def _validate(self) -> None:
        for path, field in self._flat.items():
            if field.type_ not in _SUPPORTED_FIELD_TYPES:
                raise SchemaError(f"{path}: unsupported field type {field.type_!r}")
            if field.item_type is not None and field.item_fields is not None:
                raise SchemaError(f"{path}: use either item_type or item_fields, not both")
            if field.type_ is list and field.item_type is not None:
                if field.item_type not in _SCALAR_FIELD_TYPES:
                    raise SchemaError(f"{path}: unsupported list item type {field.item_type!r}")
            if field.type_ is list and field.item_fields is not None:
                self._validate_item_fields(path, field.item_fields)
            if field.type_ is dict and field.value_type is not None:
                if field.value_type not in _SCALAR_FIELD_TYPES:
                    raise SchemaError(f"{path}: unsupported dict value type {field.value_type!r}")

        env_names: dict[str, str] = {}
        for path in self._flat:
            env_name = self._base_env_name(path).upper()
            if env_name in env_names:
                raise SchemaError(
                    f"duplicate environment name {env_name!r} for {path!r} "
                    f"and {env_names[env_name]!r}"
                )
            env_names[env_name] = path

        cli_names: dict[str, str] = {}
        for path, field in self._flat.items():
            cli_name = field.cli_name if field.cli_name else path
            if cli_name in cli_names:
                raise SchemaError(
                    f"duplicate CLI name {cli_name!r} for {path!r} and {cli_names[cli_name]!r}"
                )
            cli_names[cli_name] = path

    @staticmethod
    def _validate_item_fields(path: str, item_fields: Mapping[str, Field]) -> None:
        for key, field in item_fields.items():
            item_path = f"{path}[].{key}"
            if field.type_ not in _SCALAR_FIELD_TYPES:
                raise SchemaError(f"{item_path}: unsupported object field type {field.type_!r}")

    @property
    def tree(self) -> SchemaNode:
        return self._tree

    @property
    def fields(self) -> dict[str, Field]:
        return dict(self._flat)

    def get_field(self, path: str) -> Field | None:
        return self._flat.get(path)

    def is_secret(self, path: str) -> bool:
        field = self.get_field(path)
        if field is not None:
            return self._field_is_secret(field, path)
        if "[]." in path:
            parent_path, item_key = path.split("[].", 1)
            parent = self.get_field(parent_path)
            if parent is None or parent.type_ is not list or parent.item_fields is None:
                return False
            item_field = parent.item_fields.get(item_key)
            if item_field is None:
                return False
            return self._field_is_secret(item_field, f"{parent_path}[].{item_key}")
        return False

    def secret_paths(self) -> set[str]:
        paths: set[str] = set()
        for path, field in self._flat.items():
            if field.type_ is list:
                if field.item_fields is None and self._field_is_secret(field, path):
                    paths.add(f"{path}[]")
                continue
            if self._field_is_secret(field, path):
                paths.add(path)
        for path, field in self._flat.items():
            if field.type_ is list and field.item_fields:
                for key, item_field in field.item_fields.items():
                    item_path = f"{path}[].{key}"
                    if self._field_is_secret(item_field, item_path):
                        paths.add(item_path)
        return paths

    def dict_field_paths(self) -> set[str]:
        return {path for path, field in self._flat.items() if field.type_ is dict}

    def path_may_contain_secrets(self, path: str) -> bool:
        """Whether operator output for this path may include secret material."""
        if self.is_secret(path):
            return True
        field = self.get_field(path)
        if field is None:
            return False
        if field.type_ is dict:
            return True
        if field.type_ is list and field.item_fields is None:
            return self._field_is_secret(field, path)
        if field.type_ is list and field.item_fields:
            return any(self.is_secret(f"{path}[].{key}") for key in field.item_fields)
        return False

    @staticmethod
    def inferred_secret_leaf(name: str) -> bool:
        normalized = name.lower().replace("-", "_")
        return normalized in _INFERRED_SECRET_NAMES

    @staticmethod
    def _field_is_secret(field: Field, path: str) -> bool:
        if field.secret:
            return True
        if "[]." in path:
            leaf = path.split("[].", 1)[1].lower().replace("-", "_")
        else:
            leaf = path.rsplit(".", 1)[-1].lower().replace("-", "_")
        return leaf in _INFERRED_SECRET_NAMES

    def defaults(self) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for path, field in self._flat.items():
            if field.has_default:
                self._set_path(output, path, field.default)
        return output

    def docs(self) -> str:
        lines: list[str] = []
        for path in sorted(self._flat):
            field = self._flat[path]
            lines.append(path)
            lines.append(f"  type: {field.type_name}")
            lines.append(f"  required: {'yes' if field.required else 'no'}")
            if field.has_default:
                lines.append(f"  default: {self._format_value(field.default)}")
            if field.choices:
                choices = ", ".join(str(choice) for choice in field.choices)
                lines.append(f"  choices: {choices}")
            if field.min_value is not None:
                lines.append(f"  min: {field.min_value}")
            if field.max_value is not None:
                lines.append(f"  max: {field.max_value}")
            if field.min_length is not None:
                lines.append(f"  min_length: {field.min_length}")
            if field.max_length is not None:
                lines.append(f"  max_length: {field.max_length}")
            if field.regex is not None:
                lines.append(f"  regex: {field.regex}")
            if field.secret:
                lines.append("  secret: yes")
            elif self.is_secret(path):
                lines.append("  secret: inferred")
            if field.nullable:
                lines.append("  nullable: yes")
            if field.description:
                lines.append(f"  description: {field.description}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def env_name_for(self, path: str, prefix: str | None = None) -> str:
        name = self._base_env_name(path)
        if prefix:
            return f"{prefix.upper()}_{name}"
        return name

    def _base_env_name(self, path: str) -> str:
        field = self._flat[path]
        if field.env_name:
            return field.env_name.upper()
        return path.upper().replace(".", "__")

    def env_key_map(self, prefix: str | None = None) -> dict[str, str]:
        return {self.env_name_for(path, prefix=prefix).upper(): path for path in self._flat}

    def cli_key_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for path, field in self._flat.items():
            cli_key = field.cli_name if field.cli_name else path
            mapping[cli_key] = path
        return mapping

    @staticmethod
    def _normalize_node(node: Mapping[str, Any], *, path: str) -> SchemaNode:
        normalized: SchemaNode = {}
        for key, value in node.items():
            if not isinstance(key, str) or not key:
                raise TypeError("Schema keys must be non-empty strings")
            current = f"{path}.{key}" if path else key
            if isinstance(value, Field):
                normalized[key] = value
            elif isinstance(value, Mapping):
                normalized[key] = Schema._normalize_node(value, path=current)
            else:
                raise TypeError(f"{current}: schema values must be Field or mapping")
        return normalized

    @staticmethod
    def _flatten(tree: SchemaNode, prefix: str = "") -> dict[str, Field]:
        flat: dict[str, Field] = {}
        for key, value in tree.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, Field):
                flat[path] = value
            else:
                flat.update(Schema._flatten(value, path))
        return flat

    @staticmethod
    def _set_path(target: dict[str, Any], path: str, value: Any) -> None:
        parts = path.split(".")
        current = target
        for part in parts[:-1]:
            next_value = current.setdefault(part, {})
            if not isinstance(next_value, dict):
                raise TypeError(f"{path}: cannot set nested default under scalar")
            current = next_value
        current[parts[-1]] = value

    @staticmethod
    def _format_value(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return value
        if value is MISSING:
            return ""
        return str(value)
