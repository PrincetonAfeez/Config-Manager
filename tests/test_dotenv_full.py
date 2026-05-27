"""Exhaustive tests for config_manager.dotenv."""

import pytest
from config_manager.dotenv import load_dotenv_file, parse_dotenv
from config_manager.errors import ParseError, SourceError


def test_parse_export_syntax():
    assert parse_dotenv("export FOO=bar")["FOO"] == "bar"


def test_parse_inline_comment():
    assert parse_dotenv("DEBUG=true # comment")["DEBUG"] == "true"


def test_parse_single_quoted():
    assert parse_dotenv("NAME='hello world'")["NAME"] == "hello world"


def test_parse_double_quoted_escape():
    assert parse_dotenv(r'PATH="C:\\temp"')["PATH"] == "C:\\temp"


def test_parse_continuation():
    text = "MULTI=line1\\\nline2"
    assert parse_dotenv(text)["MULTI"] == "line1line2"


def test_parse_empty_and_comment_lines():
    assert parse_dotenv("\n# comment\n\nKEY=value\n") == {"KEY": "value"}


def test_parse_duplicate_key():
    with pytest.raises(ParseError, match="duplicate"):
        parse_dotenv("A=1\nA=2\n")


def test_parse_missing_equals():
    with pytest.raises(ParseError):
        parse_dotenv("BADKEY")


def test_parse_invalid_key():
    with pytest.raises(ParseError):
        parse_dotenv("123BAD=value")


def test_parse_export_alone():
    with pytest.raises(ParseError):
        parse_dotenv("export")


def test_parse_unterminated_quote():
    with pytest.raises(ParseError, match="unterminated"):
        parse_dotenv('KEY="broken')


def test_parse_empty_value():
    assert parse_dotenv("EMPTY=")["EMPTY"] == ""


def test_load_dotenv_missing_file():
    with pytest.raises(SourceError):
        load_dotenv_file("nonexistent.env")


def test_load_dotenv_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("FOO=bar\n", encoding="utf-8")
    assert load_dotenv_file(path) == {"FOO": "bar"}
