""" Tests for toml loader module """

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config_manager import ConfigError
from config_manager.dotenv import load_dotenv_file
from config_manager.errors import ParseError, SourceError
from config_manager.sources import normalize_prefix
from config_manager.toml_loader import load_toml_file


class TomlLoaderTests(unittest.TestCase):
    def test_load_valid_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.toml"
            path.write_text('[app]\nname = "Demo"\n', encoding="utf-8")
            data = load_toml_file(path)
            self.assertEqual(data["app"]["name"], "Demo")

    def test_missing_file_raises_source_error(self):
        with self.assertRaises(SourceError):
            load_toml_file(Path("does-not-exist.toml"))

    def test_missing_dotenv_raises_source_error(self):
        with self.assertRaises(SourceError):
            load_dotenv_file(Path("does-not-exist.env"))

    def test_empty_prefix_raises(self):
        with self.assertRaises(ConfigError):
            normalize_prefix("")

    def test_invalid_toml_raises_parse_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.toml"
            path.write_text("app = [", encoding="utf-8")
            with self.assertRaises(ParseError):
                load_toml_file(path)

    def test_non_dict_root_raises_parse_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.toml"
            path.write_text("key = 1\n", encoding="utf-8")
            with patch("config_manager.toml_loader.tomllib.load", return_value=[]):
                with self.assertRaises(ParseError) as ctx:
                    load_toml_file(path)
                self.assertIn("root must be a table", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
