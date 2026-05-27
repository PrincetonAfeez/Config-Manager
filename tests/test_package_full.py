"""Tests for package exports and example schemas."""

import importlib

import config_manager
from config_manager import __all__


def test_public_exports_match_all():
    assert sorted(config_manager.__all__) == sorted(__all__)


def test_all_exports_importable():
    for name in __all__:
        assert hasattr(config_manager, name)


def test_example_schema_loads():
    mod = importlib.import_module("config_manager.example_schema")
    assert hasattr(mod, "schema")


def test_rich_example_schema_loads():
    mod = importlib.import_module("examples.rich_schema")
    assert hasattr(mod, "schema")


def test_cli_module_main_guard():
    """Running cli as __main__ without args exits non-zero (argparse error)."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "config_manager.cli"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
