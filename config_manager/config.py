"""Frozen Config object exposed to applications."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from types import MappingProxyType
from typing import Any

from .errors import ConfigError, ConfigFrozenError, ConfigKeyError
from .fields import MISSING
from .masking import MASK, contains_masked, mask_nested, mask_value_at_path
from .paths import deep_copy, get_path
from .provenance import Provenance
from .schema import Schema


class FrozenConfig(Mapping[str, Any]):
    """Immutable mapping with convenient attribute access for nested config."""

    def __init__(self, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_data", MappingProxyType(_freeze_nested(data)))

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        raise ConfigFrozenError("resolved config is immutable")

    def to_dict(self) -> dict[str, Any]:
        return _thaw_nested(self._data)  # type: ignore[no-any-return]


class Config(FrozenConfig):
    """Final validated config plus schema and provenance metadata."""

    def __init__(
        self,
        data: Mapping[str, Any],
        *,
        schema: Schema,
        provenance: Mapping[str, Provenance],
    ) -> None:
        super().__init__(data)
        object.__setattr__(self, "_schema", schema)
        object.__setattr__(self, "_provenance", dict(provenance))

    def get(self, path: str, default: Any = MISSING) -> Any:  # type: ignore[override]
        value = get_path(self._data, path, MISSING)
        if value is MISSING:
            if default is MISSING:
                raise ConfigKeyError(path)
            return default
        return value

    def explain(self, path: str) -> dict[str, Any]:
        field = self._schema.get_field(path)
        if field is None:
            raise ConfigError(f"{path}: not declared in schema")
        value = get_path(self._data, path, MISSING)
        if value is MISSING:
            return {
                "path": path,
                "status": "not_set",
                "value": None,
                "type": field.type_name,
                "source": None,
                "source_name": None,
                "raw_value": None,
                "secret": self._schema.path_may_contain_secrets(path),
            }
        provenance = self._provenance.get(path)
        flat_secret = self._schema.is_secret(path)
        mask_whole_value = flat_secret and not (field.type_ is list and field.item_fields is None)
        display_value = (
            MASK
            if mask_whole_value
            else mask_value_at_path(
                path,
                value,
                secret_paths=self._schema.secret_paths(),
                dict_field_paths=self._schema.dict_field_paths(),
            )
        )
        exposes_secrets = mask_whole_value or contains_masked(display_value)
        raw_value = provenance.raw_value if provenance else None
        return {
            "path": path,
            "status": "set",
            "value": display_value,
            "type": field.type_name,
            "source": provenance.source if provenance else None,
            "source_name": provenance.name if provenance else None,
            "raw_value": MASK if exposes_secrets and raw_value is not None else raw_value,
            "secret": exposes_secrets,
        }

    def provenance(self, path: str) -> Provenance | None:
        return self._provenance.get(path)  # type: ignore[no-any-return]

    def to_masked_dict(self) -> dict[str, Any]:
        return mask_nested(
            self.to_dict(),
            self._schema.secret_paths(),
            dict_field_paths=self._schema.dict_field_paths(),
        )


def _freeze_nested(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): FrozenConfig(item) if isinstance(item, Mapping) else _freeze_nested(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return tuple(_freeze_nested(item) for item in value)
    return value


def _thaw_nested(value: Any) -> Any:
    if isinstance(value, FrozenConfig):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {key: _thaw_nested(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_nested(item) for item in value]
    return deep_copy(value)
