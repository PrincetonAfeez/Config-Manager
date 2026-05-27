"""TOML loading isolated behind a small adapter."""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import ParseError, SourceError


def load_toml_file(path: str | Path) -> dict:
    file_path = Path(path)
    try:
        with file_path.open("rb") as file:
            loaded = tomllib.load(file)
    except FileNotFoundError as exc:
        raise SourceError(f"{file_path}: file not found") from exc
    except tomllib.TOMLDecodeError as exc:
        line = getattr(exc, "lineno", None)
        raise ParseError(str(exc), path=str(file_path), line=line) from exc
    if not isinstance(loaded, dict):
        raise ParseError("TOML root must be a table", path=str(file_path))
    return loaded
