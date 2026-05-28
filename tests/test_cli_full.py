"""Exhaustive tests for config_manager.cli helpers and commands."""

import sys
from io import StringIO

import pytest
from config_manager.cli import (
    _format_explain,
    _format_nested,
    _format_scalar,
    _load_schema,
    _split_schema_spec,
    build_parser,
    main,
)
from config_manager.errors import ConfigError
from config_manager.schema import Schema


def test_build_parser_subcommands():
    parser = build_parser()
    args = parser.parse_args(["validate", "--schema", "x.py"])
    assert args.command == "validate"


def test_split_schema_spec_existing_file(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text("schema = None\n", encoding="utf-8")
    path, obj = _split_schema_spec(str(schema_file))
    assert path == str(schema_file)
    assert obj == "schema"


def test_split_schema_spec_with_object(tmp_path):
    schema_file = tmp_path / "custom.py"
    schema_file.write_text("my_schema = None\n", encoding="utf-8")
    path, obj = _split_schema_spec(f"{schema_file}:my_schema")
    assert obj == "my_schema"


def test_split_schema_spec_nonexistent():
    path, obj = _split_schema_spec("missing.py")
    assert obj == "schema"


def test_load_schema_none_returns_default():
    schema = _load_schema(None)
    assert isinstance(schema, Schema)


def test_load_schema_from_file(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\n"
        "schema = Schema({'a': Field(str, default='x')})\n",
        encoding="utf-8",
    )
    schema = _load_schema(str(schema_file))
    assert schema.get_field("a") is not None


def test_load_schema_invalid_file(tmp_path):
    schema_file = tmp_path / "bad.py"
    schema_file.write_text("syntax !!!\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        _load_schema(str(schema_file))


def test_format_scalar_bool():
    assert _format_scalar(True) == "true"
    assert _format_scalar(False) == "false"


def test_format_scalar_str():
    assert _format_scalar("hello") == "hello"


def test_format_nested():
    text = _format_nested({"app": {"name": "Demo", "debug": False}})
    assert "app:" in text
    assert "name: Demo" in text
    assert "debug: false" in text


def test_format_explain_set():
    text = _format_explain(
        {
            "path": "app.name",
            "status": "set",
            "type": "str",
            "value": "Demo",
            "source": "default",
            "source_name": "app.name",
            "raw_value": "Demo",
        }
    )
    assert "app.name" in text
    assert "value: Demo" in text


def test_format_explain_not_set():
    text = _format_explain({"path": "opt.x", "type": "str", "status": "not_set"})
    assert "status: not set" in text


def test_main_validate_success(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\n"
        "schema = Schema({'app': {'name': Field(str, required=True)}})\n",
        encoding="utf-8",
    )
    code = main(["validate", "--schema", str(schema_file), "--set", "app.name=Demo"])
    assert code == 0


def test_main_schema_command(capsys, tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\nschema = Schema({'a': Field(str)})\n",
        encoding="utf-8",
    )
    code = main(["schema", "--schema", str(schema_file)])
    assert code == 0
    assert "a" in capsys.readouterr().out


def test_main_init_env(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\n"
        "schema = Schema({'a': Field(str, default='x')})\n",
        encoding="utf-8",
    )
    code = main(["init", "--schema", str(schema_file), "--format", "env", "--prefix", "APP"])
    assert code == 0


def test_main_init_empty_prefix_fails(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\nschema = Schema({'a': Field(str)})\n",
        encoding="utf-8",
    )
    code = main(["init", "--schema", str(schema_file), "--prefix", ""])
    assert code == 3


def test_main_show_command(tmp_path, capsys):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\n"
        "schema = Schema({'app': {'name': Field(str, default='demo')}})\n",
        encoding="utf-8",
    )
    code = main(["show", "--schema", str(schema_file)])
    assert code == 0
    assert "app:" in capsys.readouterr().out


def test_main_explain_command(tmp_path, capsys):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\n"
        "schema = Schema({'app': {'name': Field(str, default='demo')}})\n",
        encoding="utf-8",
    )
    code = main(["explain", "app.name", "--schema", str(schema_file)])
    assert code == 0
    assert "app.name" in capsys.readouterr().out


def test_main_invalid_schema_object(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text("schema = 'not a schema'\n", encoding="utf-8")
    assert main(["validate", "--schema", str(schema_file)]) == 3


def test_cli_usage_error_returns_sixty_four():
    with pytest.raises(SystemExit) as exc_info:
        main(["not-a-command"])
    assert exc_info.value.code == 64


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert "config-manager" in capsys.readouterr().out


def test_load_schema_wrong_object(tmp_path):
    schema_file = tmp_path / "custom.py"
    schema_file.write_text("schema = 'nope'\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        _load_schema(f"{schema_file}:schema")


def test_main_missing_config_file(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        "from config_manager import Field, Schema\nschema = Schema({'a': Field(str)})\n",
        encoding="utf-8",
    )
    stderr = StringIO()
    stdout = StringIO()
    old_err, old_out = sys.stderr, sys.stdout
    sys.stderr, sys.stdout = stderr, stdout
    try:
        code = main(
            ["validate", "--schema", str(schema_file), "--config", str(tmp_path / "nope.toml")]
        )
    finally:
        sys.stderr, sys.stdout = old_err, old_out
    assert code == 2
