"""Tests for toml loader module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from config_manager import ConfigError
from config_manager.dotenv import load_dotenv_file
from config_manager.errors import ParseError, SourceError
from config_manager.sources import normalize_prefix
from config_manager.toml_loader import load_toml_file


def test_load_valid_toml():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "app.toml"
        path.write_text('[app]\nname = "Demo"\n', encoding="utf-8")
        data = load_toml_file(path)
        assert data["app"]["name"] == "Demo"


def test_missing_file_raises_source_error():
    with pytest.raises(SourceError):
        load_toml_file(Path("does-not-exist.toml"))


def test_missing_dotenv_raises_source_error():
    with pytest.raises(SourceError):
        load_dotenv_file(Path("does-not-exist.env"))


def test_empty_prefix_raises():
    with pytest.raises(ConfigError):
        normalize_prefix("")


def test_invalid_toml_raises_parse_error():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.toml"
        path.write_text("app = [", encoding="utf-8")
        with pytest.raises(ParseError):
            load_toml_file(path)


def test_non_dict_root_raises_parse_error():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.toml"
        path.write_text("key = 1\n", encoding="utf-8")
        with patch("config_manager.toml_loader.tomllib.load", return_value=[]):
            with pytest.raises(ParseError, match="root must be a table"):
                load_toml_file(path)
