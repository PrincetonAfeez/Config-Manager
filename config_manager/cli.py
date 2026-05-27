"""argparse command-line interface."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from .errors import (
    CoercionError,
    ConfigError,
    ConfigInvalidError,
    ConfigKeyError,
    IssueListError,
    ParseError,
    SchemaError,
    SourceError,
    ValidationError,
)
from .example_schema import schema as default_schema
from .init_templates import generate_env_example, generate_toml_example
from .loader import load
from .schema import Schema
from .sources import normalize_prefix, parse_cli_set


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        schema = _load_schema(args.schema)
        overrides = parse_cli_set(args.set_values)
        if args.command == "schema":
            print(schema.docs())
            return 0
        if args.command == "init":
            if args.prefix is not None:
                normalize_prefix(args.prefix)
            if args.format == "env":
                print(generate_env_example(schema, prefix=args.prefix), end="")
            else:
                print(generate_toml_example(schema), end="")
            return 0

        config = load(
            schema,
            config_file=args.config,
            env_file=args.env_file,
            cli_overrides=overrides,
            prefix=args.prefix,
            strict=args.strict,
            allow_prefixless_env=args.allow_prefixless_env,
        )
        if args.command == "validate":
            print("Config valid.")
            return 0
        if args.command == "show":
            print(_format_nested(config.to_masked_dict()))
            return 0
        if args.command == "explain":
            print(_format_explain(config.explain(args.key)))
            return 0
        parser.error("missing command")
        return 3
    except (CoercionError, ValidationError, ConfigInvalidError) as exc:
        _print_issue_error("Config invalid", exc)
        return 1
    except (ParseError, SourceError) as exc:
        print(f"Config parse error: {exc}", file=sys.stderr)
        return 2
    except (ConfigError, ConfigKeyError, SchemaError) as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 3


def build_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--schema", help="Python schema file, optionally path.py:object")
    parent.add_argument("--config", help="TOML config file")
    parent.add_argument("--env-file", help=".env file")
    parent.add_argument("--prefix", help="environment variable prefix, such as MYAPP")
    parent.add_argument(
        "--allow-prefixless-env",
        action="store_true",
        help="load real environment variables without a prefix (local dev only)",
    )
    parent.add_argument(
        "--set", dest="set_values", action="append", default=[], metavar="KEY=VALUE"
    )
    mode = parent.add_mutually_exclusive_group()
    mode.add_argument("--strict", dest="strict", action="store_true", default=True)
    mode.add_argument("--lenient", dest="strict", action="store_false")

    parser = argparse.ArgumentParser(prog="config-manager")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", parents=[parent], help="validate resolved config")
    subcommands.add_parser(
        "show", parents=[parent], help="show resolved config with secrets masked"
    )
    explain = subcommands.add_parser("explain", parents=[parent], help="explain one dotted key")
    explain.add_argument("key")
    subcommands.add_parser("schema", parents=[parent], help="print schema documentation")
    init = subcommands.add_parser("init", parents=[parent], help="scaffold starter config")
    init.add_argument("--format", choices=["env", "toml"], default="env")
    return parser


def _load_schema(spec: str | None) -> Schema:
    if spec is None:
        return default_schema
    path_text, object_name = _split_schema_spec(spec)
    path = Path(path_text)
    digest = hashlib.sha256(str(path.resolve()).encode()).hexdigest()
    module_name = f"_config_manager_schema_{digest}"
    module_spec = importlib.util.spec_from_file_location(module_name, path)
    if module_spec is None or module_spec.loader is None:
        raise ConfigError(f"could not load schema from {path}")
    module = importlib.util.module_from_spec(module_spec)
    try:
        module_spec.loader.exec_module(module)
    except Exception as exc:
        raise ConfigError(f"could not load schema from {path}: {exc}") from exc
    schema = getattr(module, object_name, None)
    if not isinstance(schema, Schema):
        raise ConfigError(f"{spec}: expected {object_name} to be a config_manager.Schema")
    return schema


def _split_schema_spec(spec: str) -> tuple[str, str]:
    path = Path(spec)
    if path.exists():
        return spec, "schema"
    if ":" in spec:
        path_text, object_name = spec.rsplit(":", 1)
        if path_text and object_name and Path(path_text).exists():
            return path_text, object_name
    return spec, "schema"


def _print_issue_error(title: str, exc: IssueListError) -> None:
    print(f"{title}:", file=sys.stderr)
    for issue in exc.issues:
        print(f"- {issue.format()}", file=sys.stderr)


def _format_nested(data: dict[str, Any], indent: int = 0) -> str:
    lines: list[str] = []
    pad = "  " * indent
    for key in sorted(data):
        value = data[key]
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines.append(_format_nested(value, indent + 1))
        else:
            lines.append(f"{pad}{key}: {_format_scalar(value)}")
    return "\n".join(line for line in lines if line != "")


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _format_explain(info: dict[str, Any]) -> str:
    lines = [info["path"], f"  type: {info['type']}"]
    if info.get("status") == "not_set":
        lines.append("  status: not set")
        return "\n".join(lines)
    lines.extend(
        [
            f"  value: {_format_scalar(info['value'])}",
            f"  source: {info['source']}",
        ]
    )
    if info.get("source_name"):
        lines.append(f"  source name: {info['source_name']}")
    lines.append(f"  raw value: {_format_scalar(info['raw_value'])}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
