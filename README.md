# Config Manager

A small Python configuration manager that loads layered settings from schema
defaults, TOML files, `.env` files, real environment variables, and CLI
overrides. It coerces raw values into typed Python values, validates against a
declarative schema, freezes the final config, masks secrets, and explains which source won for each value.

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | Pipeline, modules, design decisions |
| [API Reference](docs/API.md) | `Schema`, `Field`, `load()`, `Config`, errors |
| [CLI Reference](docs/CLI.md) | Commands, flags, exit codes |
| [Contributing](CONTRIBUTING.md) | Dev setup, quality checks, guidelines |
| [Releasing](docs/RELEASING.md) | Version bumps, tags, and artifacts |
| [Changelog](CHANGELOG.md) | Version history |
| [ADRs](docs/adr/) | Architecture decision records |

## Quick start

```powershell
pip install -e ".[dev]"
python -m config_manager.cli validate `
  --schema examples/basic_schema.py `
  --config examples/app.toml `
  --env-file examples/.env.example `
  --prefix MYAPP
```

## Precedence

1. Schema defaults → 2. TOML → 3. `.env` → 4. Environment → 5. CLI `--set`

See [Architecture](docs/ARCHITECTURE.md) for details.

## Field types

Scalars (`str`, `int`, `float`, `bool`), nested dicts, homogeneous lists
(`item_type`), **list of objects** (`item_fields`), and **string-keyed maps**
(`dict` with optional `value_type`). See [API Reference](docs/API.md).

## Python API

```python
from config_manager import Field, Schema, load, ConfigInvalidError, __version__

config = load(schema, env={"MYAPP_APP__NAME": "Demo"}, prefix="MYAPP")
print(config.get("app.name"))
print(__version__)
```

List fields return **tuples** after freeze. `load()` raises **`ConfigInvalidError`**
on failure. See the [error matrix in docs/API.md](docs/API.md#error-types).

## Examples

| Example | Description |
|---------|-------------|
| `examples/basic_schema.py` | Re-exports built-in demo schema (same as CLI default) |
| `examples/rich_schema.py` | List-of-objects and dict fields |
| `examples/servers.toml` | TOML for rich schema |

## Tests and CI

```powershell
pip install -e ".[dev]"
pytest
pytest --cov=config_manager --cov-report=term-missing
ruff check .
mypy config_manager
```

GitHub Actions runs lint, type-check, and pytest on Python 3.11–3.13.

## License

MIT — see [LICENSE](LICENSE).

## Releases

See [CHANGELOG.md](CHANGELOG.md) for version history. Maintainers: follow
[docs/RELEASING.md](docs/RELEASING.md) to tag a release; GitHub Actions builds
and attaches wheel/sdist artifacts automatically.
