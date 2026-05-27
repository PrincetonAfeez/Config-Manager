"""Tests for dotenv parser module."""

import pytest
from config_manager.dotenv import parse_dotenv
from config_manager.errors import ParseError


def test_parse_supported_syntax():
    parsed = parse_dotenv(
        """
        # comment
        APP_NAME=Demo
        export DEBUG=true # inline
        PASSWORD="abc#123"
        SINGLE='quoted value'
        MULTI=hello\\
        world
        """
    )
    assert parsed["APP_NAME"] == "Demo"
    assert parsed["DEBUG"] == "true"
    assert parsed["PASSWORD"] == "abc#123"
    assert parsed["SINGLE"] == "quoted value"
    assert parsed["MULTI"] == "helloworld"


def test_malformed_line_has_parse_error():
    with pytest.raises(ParseError, match="line 1"):
        parse_dotenv("DATABASE_PORT")


def test_duplicate_key_raises():
    with pytest.raises(ParseError, match="duplicate key"):
        parse_dotenv("APP_NAME=one\nAPP_NAME=two\n")
