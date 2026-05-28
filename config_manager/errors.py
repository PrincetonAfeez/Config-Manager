"""Custom error types for the configuration pipeline."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfigIssue:
    """One user-facing problem found during coercion or validation."""

    path: str
    message: str
    value: Any = None
    source: str | None = None
    secret: bool = False

    def format(self) -> str:
        location = self.path or "<root>"
        parts = [f"{location}: {self.message}"]
        if self.value is not None:
            if self.secret:
                parts[0] = f"{location}: {self.message} (value: ********)"
            else:
                parts[0] = f"{location}: {self.message} (value: {self.value!r})"
        if self.source:
            parts[0] = f"{parts[0]} (source: {self.source})"
        return parts[0]


class ConfigError(Exception):
    """Base class for all config-manager errors."""


class SchemaError(ConfigError):
    """A schema declaration is invalid."""


class ConfigKeyError(ConfigError, KeyError):
    """A requested config path does not exist in the resolved config."""


class SourceError(ConfigError):
    """A configured source could not be read."""


class ParseError(ConfigError):
    """A config source was malformed."""

    def __init__(
        self,
        message: str,
        *,
        path: str | None = None,
        line: int | None = None,
    ) -> None:
        self.path = path
        self.line = line
        parts = []
        if path:
            parts.append(path)
        if line is not None:
            parts.append(f"line {line}")
        prefix = ": ".join(parts)
        super().__init__(f"{prefix}: {message}" if prefix else message)


class IssueListError(ConfigError):
    """Base class for errors that aggregate multiple config issues."""

    label = "config error"

    def __init__(self, issues: Iterable[ConfigIssue]) -> None:
        self.issues = list(issues)
        count = len(self.issues)
        noun = self.label if count == 1 else f"{self.label}s"
        details = "; ".join(issue.format() for issue in self.issues)
        super().__init__(f"{count} {noun}: {details}")


class CoercionError(IssueListError):
    """Raw config values could not be converted to declared field types."""

    label = "coercion error"


class ValidationError(IssueListError):
    """Coerced config values did not satisfy the declared schema."""

    label = "validation error"


class ConfigInvalidError(IssueListError):
    """One or more coercion or validation problems were found."""

    label = "config error"


class ConfigFrozenError(ConfigError, TypeError):
    """The resolved Config object is immutable."""
