"""Provenance metadata for resolved values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Provenance:
    source: str
    name: str | None = None
    raw_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "name": self.name,
            "raw_value": self.raw_value,
        }
