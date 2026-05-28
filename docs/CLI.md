# CLI Reference

Install and invoke:

```powershell
pip install -e .
config-manager --help
python -m config_manager.cli --help
```

## Commands

| Command | Description |
|---------|-------------|
| `validate` | Load and validate; exit 0 on success |
| `show` | Print resolved config with secrets masked |
| `explain KEY` | Explain one flat schema path (or report `not set`) |
| `schema` | Print schema documentation |
| `init` | Scaffold starter `.env` or TOML from schema |

## Shared options

| Flag | Description |
|------|-------------|
| `--schema PATH` | Python file with `schema` object (`path.py:object` supported). Defaults to built-in demo schema. |
| `--config PATH` | TOML config file |
| `--env-file PATH` | `.env` file |
| `--prefix NAME` | Env var prefix (e.g. `MYAPP`). Applies to `.env` and real environment variables when provided. Real environment variables are ignored without `--prefix` unless `--allow-prefixless-env` is set. `.env` files may use schema env names with or without the prefix. |
| `--set KEY=VALUE` | CLI override (repeatable). Supports dotted paths and bracket indices (e.g. `items[0].name=x`). |
| `--strict` | Reject unknown top-level keys and unknown keys inside list-of-object items (default) |
| `--lenient` | Ignore unknown top-level keys |
| `--allow-prefixless-env` | Load unprefixed real env vars — **local dev only** |
| `--version` | Print program version and exit |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Invalid config (coercion/validation) |
| `2` | Parse or source error |
| `3` | Config error (schema load, bad explain key) |
| `64` | CLI usage error |

## Examples

```powershell
# Validate README example (examples/basic_schema.py re-exports the built-in schema)
python -m config_manager.cli validate `
  --schema examples/basic_schema.py `
  --config examples/app.toml `
  --env-file examples/.env.example `
  --prefix MYAPP

# Rich schema with list-of-objects
python -m config_manager.cli validate `
  --schema examples/rich_schema.py `
  --config examples/servers.toml

# Explain one key (flat schema path only)
python -m config_manager.cli explain database.port `
  --schema examples/basic_schema.py `
  --config examples/app.toml `
  --env-file examples/.env.example `
  --prefix MYAPP

# Generate starter env file
python -m config_manager.cli init `
  --schema examples/basic_schema.py `
  --format env `
  --prefix MYAPP

# Generate starter TOML including array-of-tables for list-of-objects
python -m config_manager.cli init `
  --schema examples/rich_schema.py `
  --format toml
```

## CLI limitations

- **`explain KEY`** accepts only flat schema paths (`database.port`, `servers`), not indexed paths like `servers[0].host`.
- **`init`** emits JSON strings in `.env` for dict/list-of-object fields and `[[table]]` blocks in TOML where appropriate. Review generated files before committing.
- **Multiple `--set` flags** targeting the same list can overwrite each other depending on order; prefer a single JSON/list override when replacing entire lists.
- **`--allow-prefixless-env`** reads unprefixed variables from the process environment — convenient locally, risky in shared CI shells.

See [API Reference](API.md) and [Architecture](ARCHITECTURE.md) for Python usage and pipeline details.
