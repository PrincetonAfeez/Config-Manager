"""Field declarations used by Schema."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


class _Missing:
    def __repr__(self) -> str:
        return "MISSING"


MISSING = _Missing()

Validator = Callable[[Any], bool]


@dataclass(frozen=True)
class Field:
    """One declared config value and the rules that apply to it."""

    type_: type
    required: bool = False
    default: Any = MISSING
    choices: list[Any] | tuple[Any, ...] | set[Any] | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None
    regex: str | None = None
    secret: bool = False
    nullable: bool = False
    item_type: type | None = None
    item_fields: Mapping[str, Field] | None = None
    value_type: type | None = None
    validator: Validator | None = None
    description: str = ""
    env_name: str | None = None
    cli_name: str | None = None

    @property
    def has_default(self) -> bool:
        return self.default is not MISSING

    @property
    def type_name(self) -> str:
        if self.type_ is list and self.item_fields:
            inner = ", ".join(
                f"{key}: {field.type_name}" for key, field in self.item_fields.items()
            )
            return f"list[{{{inner}}}]"
        if self.type_ is list and self.item_type is not None:
            return f"list[{self.item_type.__name__}]"
        if self.type_ is dict and self.value_type is not None:
            return f"dict[str, {self.value_type.__name__}]"
        return self.type_.__name__
