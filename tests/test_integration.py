"""Integration tests for the CLI with examples."""

import subprocess
import sys
import tomllib
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_validate_example():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "config_manager.cli",
            "validate",
            "--schema",
            str(ROOT / "examples" / "basic_schema.py"),
            "--config",
            str(ROOT / "examples" / "app.toml"),
            "--env-file",
            str(ROOT / "examples" / ".env.example"),
            "--prefix",
            "MYAPP",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Config valid." in result.stdout


def test_rich_schema_validate_example():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "config_manager.cli",
            "validate",
            "--schema",
            str(ROOT / "examples" / "rich_schema.py"),
            "--config",
            str(ROOT / "examples" / "servers.toml"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_rich_schema_init_toml_is_valid():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "config_manager.cli",
            "init",
            "--schema",
            str(ROOT / "examples" / "rich_schema.py"),
            "--format",
            "toml",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    tomllib.load(BytesIO(result.stdout.encode("utf-8")))
