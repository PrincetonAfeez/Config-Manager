"""Validated layered configuration for Python applications."""

from importlib.metadata import PackageNotFoundError, version

from .config import Config
from .errors import (
    CoercionError,
    ConfigError,
    ConfigFrozenError,
    ConfigInvalidError,
    ConfigIssue,
    ConfigKeyError,
    ParseError,
    SchemaError,
    SourceError,
    ValidationError,
)
from .fields import MISSING, Field
from .loader import load
from .schema import Schema

try:
    __version__ = version("config-manager")
except PackageNotFoundError:
    __version__ = "0.2.0"

__all__ = [
    "CoercionError",
    "Config",
    "ConfigError",
    "ConfigFrozenError",
    "ConfigInvalidError",
    "ConfigIssue",
    "ConfigKeyError",
    "Field",
    "MISSING",
    "ParseError",
    "Schema",
    "SchemaError",
    "SourceError",
    "ValidationError",
    "__version__",
    "load",
]
