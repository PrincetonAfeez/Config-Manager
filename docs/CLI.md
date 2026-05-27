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
| `explain KEY` | Explain one dotted key (or report `not set`) |
| `schema` | Print schema documentation |
| `init` | Scaffold starter `.env` or TOML from schema |

## Shared options

| Flag | Description |
|------|-------------|
| `--schema PATH` | Python file with `schema` object (`path.py:object` supported) |
| `--config PATH` | TOML config file |
| `--env-file PATH` | `.env` file |
| `--prefix NAME` | Env var prefix (e.g. `MYAPP`) |
| `--set KEY=VALUE` | CLI override (repeatable) |
| `--strict` | Reject unknown keys (default) |
| `--lenient` | Ignore unknown keys |
| `--allow-prefixless-env` | Load unprefixed real env vars (local dev) |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Invalid config (coercion/validation) |
| `2` | Parse or source error |
| `3` | Config error (schema load, bad explain key) |

## Examples

```powershell
# Validate README example
python -m config_manager.cli validate `
  --schema examples/basic_schema.py `
  --config examples/app.toml `
  --env-file examples/.env.example `
  --prefix MYAPP

# Rich schema with list-of-objects
python -m config_manager.cli validate `
  --schema examples/rich_schema.py `
  --config examples/servers.toml

# Explain one key
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
```

See [API Reference](API.md) for Python usage.
