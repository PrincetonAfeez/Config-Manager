"""Hand-written .env parser."""

from __future__ import annotations

from pathlib import Path

from .errors import ParseError, SourceError


def parse_dotenv(text: str, *, path: str | None = None) -> dict[str, str]:
    result: dict[str, str] = {}
    logical_lines = _join_continuations(text.splitlines())
    for line_number, raw_line in logical_lines:
        parsed = _parse_line(raw_line, line_number, path=path)
        if parsed is None:
            continue
        key, value = parsed
        if key in result:
            raise ParseError(f"duplicate key {key!r}", path=path, line=line_number)
        result[key] = value
    return result


def load_dotenv_file(path: str | Path) -> dict[str, str]:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SourceError(f"{file_path}: file not found") from exc
    return parse_dotenv(text, path=str(file_path))


def _join_continuations(lines: list[str]) -> list[tuple[int, str]]:
    logical: list[tuple[int, str]] = []
    buffer = ""
    start_line = 0
    for index, line in enumerate(lines, start=1):
        if not buffer:
            start_line = index
            current_line = line
        else:
            current_line = line.lstrip()
        if _continues(line):
            buffer += current_line[:-1]
            continue
        buffer += current_line
        logical.append((start_line, buffer))
        buffer = ""
    if buffer:
        logical.append((start_line, buffer))
    return logical


def _continues(line: str) -> bool:
    stripped = line.rstrip()
    if not stripped.endswith("\\"):
        return False
    slash_count = 0
    for char in reversed(stripped):
        if char == "\\":
            slash_count += 1
        else:
            break
    return slash_count % 2 == 1


def _parse_line(
    raw_line: str,
    line_number: int,
    *,
    path: str | None,
) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export"):
        if line == "export":
            raise ParseError("export must be followed by KEY=VALUE", path=path, line=line_number)
        if not line.startswith("export "):
            raise ParseError("invalid export syntax", path=path, line=line_number)
        line = line[7:].lstrip()
    eq_index = _find_unquoted_equals(line)
    if eq_index < 0:
        raise ParseError("expected KEY=VALUE", path=path, line=line_number)
    key = line[:eq_index].strip()
    value_text = line[eq_index + 1 :].lstrip()
    if not key:
        raise ParseError("missing key before '='", path=path, line=line_number)
    if not _valid_key(key):
        raise ParseError(f"invalid key {key!r}", path=path, line=line_number)
    value = _parse_value(value_text, line_number, path=path)
    return key, value


def _find_unquoted_equals(line: str) -> int:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "=" and quote is None:
            return index
    return -1


def _valid_key(key: str) -> bool:
    if not (key[0].isalpha() or key[0] == "_"):
        return False
    return all(char.isalnum() or char == "_" for char in key)


def _parse_value(value_text: str, line_number: int, *, path: str | None) -> str:
    if not value_text:
        return ""
    if value_text[0] == "'":
        return _parse_single_quoted(value_text, line_number, path=path)
    if value_text[0] == '"':
        return _parse_double_quoted(value_text, line_number, path=path)
    return _strip_inline_comment(value_text).strip()


def _parse_single_quoted(value_text: str, line_number: int, *, path: str | None) -> str:
    end = value_text.find("'", 1)
    if end < 0:
        raise ParseError("unterminated single-quoted value", path=path, line=line_number)
    trailing = value_text[end + 1 :].strip()
    if trailing and not trailing.startswith("#"):
        raise ParseError("unexpected text after quoted value", path=path, line=line_number)
    return value_text[1:end]


def _parse_double_quoted(value_text: str, line_number: int, *, path: str | None) -> str:
    chars: list[str] = []
    escaped = False
    for index, char in enumerate(value_text[1:], start=1):
        if escaped:
            chars.append(_escape_char(char))
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            trailing = value_text[index + 1 :].strip()
            if trailing and not trailing.startswith("#"):
                raise ParseError("unexpected text after quoted value", path=path, line=line_number)
            return "".join(chars)
        chars.append(char)
    raise ParseError("unterminated double-quoted value", path=path, line=line_number)


def _escape_char(char: str) -> str:
    escapes = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "\\": "\\",
        '"': '"',
    }
    return escapes.get(char, char)


def _strip_inline_comment(value_text: str) -> str:
    for index, char in enumerate(value_text):
        if char == "#" and (index == 0 or value_text[index - 1].isspace()):
            return value_text[:index]
    return value_text
