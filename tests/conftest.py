"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from config_manager import Field, Schema


@pytest.fixture
def basic_schema() -> Schema:
    """Minimal schema for unit tests (not identical to examples/basic_schema.py)."""
    return Schema(
        {
            "app": {
                "name": Field(str, required=True, description="App name"),
                "debug": Field(bool, default=False),
                "port": Field(int, default=8080, min_value=1, max_value=65535),
            },
            "database": {
                "password": Field(str, required=True, secret=True),
            },
        }
    )


@pytest.fixture
def rich_schema() -> Schema:
    return Schema(
        {
            "app": {
                "name": Field(str, required=True),
                "tags": Field(list, default=[], item_type=str),
            },
            "servers": Field(
                list,
                item_fields={
                    "host": Field(str, required=True),
                    "port": Field(int, default=8080),
                },
            ),
            "flags": Field(dict, value_type=bool, default={}),
        }
    )


@pytest.fixture
def examples_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "examples"
