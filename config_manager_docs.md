# Architecture Decision Record
## App — Config Manager
**Configuration Systems Group | Document 1 of 5**
**Status: Accepted**

---

## Context

The Configuration Systems group requires a Python library and command-line tool that can load application configuration from multiple sources, apply deterministic precedence, coerce raw strings into typed Python values, validate against a declarative schema, freeze the final result, mask secrets, and explain which source won for each key.

The project is intentionally not a web framework, settings server, secrets manager, or full configuration language. It is a focused layered configuration loader for Python applications. The main design problem is safely moving from messy real-world inputs — TOML files, `.env` files, environment variables, and CLI overrides — into a validated immutable object.

The selected architecture is a pure-Python package with a thin CLI. The core public API is:

```python
from config_manager import Field, Schema, load, Config
```

The core pipeline is:

```text
Schema defaults
  → TOML file
  → .env file
  → process environment
  → CLI --set overrides
  → merge
  → coerce
  → validate
  → filter to schema
  → freeze
  → expose Config with provenance and masking
```

---

## Decisions

### Decision 1 — Schema-first configuration

**Chosen:** `Schema` and `Field` are the source of truth for configuration shape, field types, defaults, validation rules, environment names, CLI aliases, and secret metadata.

**Rejected:** Accepting arbitrary dictionaries without a schema.

**Reason:** Configuration becomes unsafe when keys and types are implicit. A schema lets the loader validate every resolved value, document expected settings, detect unknown keys, infer secret paths, and provide reliable provenance.

---

### Decision 2 — Fixed source precedence

**Chosen:** Precedence is deterministic:

```text
defaults < TOML < .env < environment < CLI --set
```

**Rejected:** User-defined arbitrary source ordering.

**Reason:** The precedence model should be simple enough to explain and stable enough to test. The chosen order matches common application expectations: defaults are weakest, CLI overrides are strongest.

---

### Decision 3 — Preserve provenance per leaf path

**Chosen:** Every source adapter returns both nested data and a mapping of dotted paths to `Provenance`.

**Rejected:** Returning only the merged config.

**Reason:** The app is not only meant to resolve config; it must explain why a value exists. Provenance powers `Config.explain()`, user-facing error messages, and debugging source precedence.

---

### Decision 4 — Coercion before validation

**Chosen:** Raw values are first coerced into declared Python types, then validated for choices, ranges, regexes, required fields, unknown keys, and custom validators.

**Rejected:** Validating raw strings directly.

**Reason:** Real inputs often arrive as strings, especially from environment variables and CLI flags. Coercion normalizes them before applying semantic validation. This keeps validation rules typed and predictable.

---

### Decision 5 — Aggregate issues instead of failing fast

**Chosen:** Coercion and validation collect all issues and raise `ConfigInvalidError` with a list of `ConfigIssue` objects.

**Rejected:** Raising on the first error.

**Reason:** Configuration errors are operational. Users benefit from seeing every problem in one run instead of fixing one issue at a time.

---

### Decision 6 — Freeze final configuration

**Chosen:** `Config` extends `FrozenConfig`, uses a mapping proxy for nested mappings, converts lists to tuples, and rejects mutation.

**Rejected:** Returning a normal mutable dictionary.

**Reason:** Once resolved, configuration should not drift at runtime. Freezing makes the config object safer and makes application behavior easier to reason about. `to_dict()` is available when a mutable copy is needed.

---

### Decision 7 — Secret masking is built in

**Chosen:** Secrets can be declared explicitly with `Field(secret=True)` and inferred from common leaf names such as `password`, `token`, `api_key`, and `client_secret`.

**Rejected:** Leaving secret redaction entirely to callers.

**Reason:** Configuration values often contain secrets. Built-in masking reduces accidental leaks in `show`, `explain`, error output, and masked dictionaries.

---

### Decision 8 — Support structured list and dict fields

**Chosen:** The schema supports scalar fields, homogeneous scalar lists, list-of-object fields, and string-keyed dictionaries with optional value types.

**Rejected:** Supporting only flat scalar settings.

**Reason:** Real application config often includes server lists, route definitions, feature maps, and metadata dictionaries. The implementation supports those structures without becoming a full schema language.

---

### Decision 9 — Hand-written `.env` parser

**Chosen:** The `.env` parser is implemented directly.

**Rejected:** Depending on python-dotenv.

**Reason:** The project aims to be small, explicit, and mostly standard-library based. A hand-written parser gives control over duplicate keys, quoting, comments, line continuations, and parse errors.

---

### Decision 10 — TOML through `tomllib`

**Chosen:** TOML loading is isolated behind a small adapter using Python's standard `tomllib`.

**Rejected:** Adding a third-party TOML parser.

**Reason:** Python 3.11+ includes `tomllib` for reading TOML. This keeps runtime dependencies low while supporting a standard configuration file format.

---

### Decision 11 — CLI as thin orchestration layer

**Chosen:** The CLI loads a schema, parses flags, delegates to `load()`, and formats the result.

**Rejected:** Reimplementing merge/coercion/validation behavior inside CLI commands.

**Reason:** CLI and library behavior must not drift. The CLI should be a wrapper over the same public pipeline application code uses.

---

### Decision 12 — Strict mode by default

**Chosen:** Unknown keys are validation issues by default, with `--lenient` available for relaxed behavior.

**Rejected:** Silently ignoring unknown keys by default.

**Reason:** Misspelled configuration keys are a common source of production bugs. Strict mode catches them early while still allowing migration or exploratory workflows.

---

## Consequences

**Positive:**
- Source precedence is easy to document.
- The library API and CLI share the same behavior.
- The schema documents config shape and generates docs/templates.
- Operators can explain individual values and see which source won.
- Secrets are masked consistently.
- Immutable config reduces runtime drift.
- `.env`, environment, TOML, and CLI overrides are supported without runtime third-party dependencies.
- Error output can show multiple issues at once.

**Negative / Trade-offs:**
- The schema API is more verbose than plain dictionaries.
- Environment and CLI mappings require dotted-path conventions.
- List-of-object support increases coercion and validation complexity.
- The hand-written `.env` parser must be maintained.
- Strict mode can reject otherwise harmless unknown keys.
- No dynamic reload/watch mode exists.
- No secrets backend integration exists.

---

## Alternatives Not Explored

- YAML source support.
- Pydantic/dataclass-based schema.
- Runtime config reload.
- Remote configuration server.
- Secrets manager integration.
- Schema migration/versioning system.
- Nested CLI override language beyond dotted `KEY=VALUE`.
- Rich JSON output for every CLI command.
- Automatic generation of application-specific argparse flags.

---

*Constitution reference: Article 1 (Python fundamentals and architectural thinking), Article 3.3 (scope discipline), Article 4 (quality proportional to scope), Article 6 (behavior verification), and Article 7 (progressive complexity).*

---


# Technical Design Document
## App — Config Manager
**Configuration Systems Group | Document 2 of 5**

---

## Overview

Config Manager is a Python package and CLI for layered configuration loading. It resolves configuration from schema defaults, TOML files, `.env` files, real environment variables, and CLI overrides. It then coerces, validates, freezes, masks, and explains the final configuration.

**Package:** `config_manager`  
**Console script:** `config-manager`  
**Python requirement:** `>=3.11`  
**Runtime dependencies:** standard library only  
**Dev tools:** pytest, pytest-cov, ruff, mypy  
**Primary public API:** `Field`, `Schema`, `load`, `Config`

---

## Data Flow

```text
User code / CLI
  │
  ▼
Schema(fields)
  │
  ├── normalize nested schema tree
  ├── flatten paths
  ├── validate supported field types
  ├── validate env/CLI alias uniqueness
  └── infer secret paths
  │
  ▼
load(schema, config_file, env_file, env, cli_overrides, prefix)
  │
  ├── defaults_source(schema)
  ├── toml_source(path)
  ├── dotenv_source(path, prefix, schema)
  ├── environment_source(env, prefix, schema)
  └── cli_overrides_source(overrides, schema)
  │
  ▼
merge_layers()
  │
  ├── deep-merge mappings
  ├── replace scalars/lists
  └── track winning provenance
  │
  ▼
collect_coercion_issues()
  │
  ├── str/int/float/bool
  ├── list item_type
  ├── list item_fields
  └── dict value_type
  │
  ▼
collect_validation_issues()
  │
  ├── required fields
  ├── type checks
  ├── choices
  ├── min/max values
  ├── min/max length
  ├── regex
  ├── custom validator
  └── unknown keys in strict mode
  │
  ▼
Config(final_data, schema, provenance)
  │
  ├── MappingProxyType
  ├── nested FrozenConfig objects
  ├── list → tuple freeze
  ├── get()
  ├── explain()
  ├── provenance()
  └── to_masked_dict()
```

---

## Module-Level Structure

```text
Config-Manager/
  config_manager/
    __init__.py
    cli.py
    coercion.py
    config.py
    dotenv.py
    errors.py
    example_schema.py
    fields.py
    init_templates.py
    loader.py
    masking.py
    merge.py
    paths.py
    provenance.py
    schema.py
    sources.py
    toml_loader.py
    validation.py
    py.typed
  docs/
    ARCHITECTURE.md
    API.md
    CLI.md
    RELEASING.md
    adr/
  examples/
    basic_schema.py
    rich_schema.py
    app.toml
    servers.toml
    .env.example
  tests/
  pyproject.toml
  requirements-dev.lock
  README.md
  CHANGELOG.md
  LICENSE
  .github/workflows/ci.yml
```

---

## Module Dependency Graph

```text
config_manager.__init__
  ├── Config
  ├── Field
  ├── Schema
  ├── load
  └── public errors

cli.py
  ├── argparse
  ├── example_schema
  ├── init_templates
  ├── loader.load
  ├── Schema dynamic import
  └── sources.parse_cli_set

loader.py
  ├── sources
  ├── merge.merge_layers
  ├── coercion.collect_coercion_issues
  ├── validation.collect_validation_issues
  ├── validation.filter_to_schema
  └── Config

schema.py
  ├── Field
  ├── SchemaError
  └── secret path inference

sources.py
  ├── dotenv.load_dotenv_file
  ├── toml_loader.load_toml_file
  ├── paths.safe_set_path
  ├── Provenance
  └── Schema maps
```

---

## Core Data Structures

### `Field`

A frozen dataclass declaring one config value.

Important attributes:
- `type_`
- `required`
- `default`
- `choices`
- `min_value`
- `max_value`
- `min_length`
- `max_length`
- `regex`
- `secret`
- `nullable`
- `item_type`
- `item_fields`
- `value_type`
- `validator`
- `description`
- `env_name`
- `cli_name`

Computed:
- `has_default`
- `type_name`

---

### `Schema`

Owns:
- nested schema tree
- flattened dotted-path map
- defaults
- secret-path discovery
- environment name mapping
- CLI key mapping
- generated docs text

Supported field types:
- `str`
- `bool`
- `int`
- `float`
- `list`
- `dict`

List support:
- scalar list through `item_type`
- list of objects through `item_fields`

Dict support:
- freeform dict
- string-keyed dict with optional scalar `value_type`

---

### `Provenance`

```python
@dataclass(frozen=True)
class Provenance:
    source: str
    name: str | None = None
    raw_value: Any = None
```

Represents the winning source for a resolved config value.

---

### `ConfigIssue`

```python
@dataclass(frozen=True)
class ConfigIssue:
    path: str
    message: str
    value: Any = None
    source: str | None = None
    secret: bool = False
```

Used by coercion and validation errors. It masks secret values when formatted.

---

### `FrozenConfig`

Immutable mapping wrapper for nested config data.

Behavior:
- mapping access
- attribute access for nested sections
- mutation rejected with `ConfigFrozenError`
- `to_dict()` returns thawed mutable copy

---

### `Config`

Extends `FrozenConfig` with:
- schema reference
- provenance map
- `get(path)`
- `explain(path)`
- `provenance(path)`
- `to_masked_dict()`

---

## Function Reference

### `load()`

```python
load(
    schema: Schema,
    config_file: str | Path | None = None,
    env_file: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    cli_overrides: Mapping[str, str] | None = None,
    prefix: str | None = None,
    strict: bool = True,
    allow_prefixless_env: bool = False,
) -> Config
```

Responsibilities:
1. Normalize prefix.
2. Build source layers.
3. Merge layers by precedence.
4. Coerce values against schema.
5. Validate coerced data.
6. Raise aggregated `ConfigInvalidError` if issues exist.
7. Filter final data to schema.
8. Return `Config`.

---

### `defaults_source(schema)`

Returns schema defaults plus `default` provenance entries.

---

### `toml_source(path)`

Loads TOML via `tomllib`, returns nested data and `config_file` provenance.

---

### `dotenv_source(path, prefix, schema)`

Parses `.env` text, resolves env keys into dotted schema paths, and returns `env_file` provenance.

---

### `environment_source(env, prefix, allow_prefixless, schema)`

Reads process environment or a supplied mapping. Prefixless real environment loading is disabled unless explicitly allowed.

---

### `cli_overrides_source(overrides, schema)`

Converts CLI `--set KEY=VALUE` values into dotted config paths, respecting `Field.cli_name`.

---

### `merge_layers(layers)`

Applies layers in order. Later values win. Nested mappings are merged. Scalars/lists replace prior values.

Protection:
- replacing a nested mapping with a non-string scalar raises `ParseError`
- replacing a scalar with a mapping raises `ParseError`

---

### `coerce_value(value, field)`

Coerces raw values into declared types.

Supported conversions:
- string-compatible values to `str`
- numeric strings to `int` / `float`
- bool strings such as `true`, `false`, `yes`, `no`, `on`, `off`
- comma-separated or JSON-array strings to lists
- JSON-object strings to dicts
- list-of-object items using `item_fields`
- dict values using `value_type`

---

### `collect_validation_issues()`

Validates:
- required values
- type match
- choices
- min/max values
- min/max lengths
- regex
- custom validators
- list-of-object fields
- unknown keys under strict mode

---

### `Config.get(path, default=MISSING)`

Returns a dotted-path config value. Raises `ConfigKeyError` when missing and no default is supplied.

---

### `Config.explain(path)`

Returns:
- path
- status
- masked display value
- type
- source
- source name
- masked raw value when needed
- secret flag

---

## Error Handling Strategy

Expected error groups:
- `SchemaError`
- `SourceError`
- `ParseError`
- `CoercionError`
- `ValidationError`
- `ConfigInvalidError`
- `ConfigKeyError`
- `ConfigFrozenError`
- `ConfigError`

CLI exit behavior:
- `0`: success
- `1`: coercion/validation/config invalid
- `2`: parse/source error
- `3`: schema/config/key error
- `64`: argparse usage error

---

## External Dependencies

### Runtime

None beyond the Python standard library.

Important standard-library dependencies:
- `argparse`
- `tomllib`
- `importlib.util`
- `MappingProxyType`
- `re`
- `json`
- `pathlib`

### Development

- pytest
- pytest-cov
- ruff
- mypy

---

## Concurrency Model

The app is synchronous and in-memory. It does not watch files, reload config automatically, spawn threads, call remote services, or perform background work. Each call to `load()` resolves one immutable `Config` snapshot.

---

## Known Limitations

- No YAML source.
- No remote config source.
- No secrets manager integration.
- No dynamic reload/watch mode.
- No automatic CLI flag generation per schema field.
- No schema migration system.
- No runtime mutation of resolved config.
- Only Python schema files are supported for schema declarations.
- TOML read support depends on Python 3.11+ `tomllib`.

---

## Design Patterns Used

- **Functional pipeline:** source → merge → coerce → validate → freeze.
- **Schema as source of truth:** one declaration drives docs, env mapping, CLI mapping, secrets, and validation.
- **Provenance tracking:** every winning value can be explained.
- **Immutable result object:** application reads stable config.
- **Error aggregation:** multiple issues reported together.
- **Adapter pattern:** TOML, `.env`, environment, CLI, and defaults each implement source adapter behavior.
- **Thin CLI over library:** avoids duplicate behavior.

---

## Verification Summary

The repo documents and configures pytest testpaths, coverage, Ruff linting, Ruff format checking, mypy checks, GitHub Actions across Python 3.11 through 3.14, and a coverage fail-under threshold in CI.

---

*Constitution reference: Article 4 (engineering quality), Article 6 (behavior verification), Article 7 (progressive complexity), and Article 8 (valid learner work).*

---


# Interface Design Specification
## App — Config Manager
**Configuration Systems Group | Document 3 of 5**

---

## Public Python Interface

### Import

```python
from config_manager import Field, Schema, load, Config
```

Other exported names include:
- `CoercionError`
- `ConfigError`
- `ConfigFrozenError`
- `ConfigInvalidError`
- `ConfigIssue`
- `ConfigKeyError`
- `MISSING`
- `ParseError`
- `SchemaError`
- `SourceError`
- `ValidationError`
- `__version__`

---

## Library Usage

```python
from config_manager import Field, Schema, load

schema = Schema(
    {
        "app": {
            "name": Field(str, required=True),
            "debug": Field(bool, default=False),
        },
        "server": {
            "port": Field(int, default=8000, min_value=1, max_value=65535),
        },
        "auth": {
            "api_key": Field(str, required=True, secret=True),
        },
    }
)

config = load(
    schema,
    config_file="app.toml",
    env_file=".env",
    prefix="MYAPP",
    cli_overrides={"server.port": "9000"},
)

print(config.get("app.name"))
print(config.server.port)
print(config.to_masked_dict())
print(config.explain("server.port"))
```

---

## `Field` Contract

```python
Field(
    type_,
    required=False,
    default=MISSING,
    choices=None,
    min_value=None,
    max_value=None,
    min_length=None,
    max_length=None,
    regex=None,
    secret=False,
    nullable=False,
    item_type=None,
    item_fields=None,
    value_type=None,
    validator=None,
    description="",
    env_name=None,
    cli_name=None,
)
```

Supported `type_` values:
- `str`
- `bool`
- `int`
- `float`
- `list`
- `dict`

---

## `Schema` Contract

```python
schema = Schema({"section": {"key": Field(str)}})
```

Important methods:
- `fields`
- `tree`
- `get_field(path)`
- `is_secret(path)`
- `secret_paths()`
- `dict_field_paths()`
- `defaults()`
- `docs()`
- `env_name_for(path, prefix=None)`
- `env_key_map(prefix=None)`
- `cli_key_map()`

---

## `load()` Contract

```python
config = load(
    schema,
    config_file=None,
    env_file=None,
    env=None,
    cli_overrides=None,
    prefix=None,
    strict=True,
    allow_prefixless_env=False,
)
```

Returns:
```python
Config
```

Raises:
- `ConfigInvalidError`
- `ParseError`
- `SourceError`
- `SchemaError`
- `ConfigError`

---

## `Config` Contract

Important methods:
- `get(path, default=MISSING)`
- `explain(path)`
- `provenance(path)`
- `to_masked_dict()`
- `to_dict()`

Access patterns:
```python
config.get("app.name")
config["app"]["name"]
config.app.name
```

Mutation:
```python
config.app.name = "new"
```

Expected:
```text
ConfigFrozenError
```

---

## Public CLI Interface

### Console script

```powershell
config-manager <command> [options]
```

### Module form

```powershell
python -m config_manager.cli <command> [options]
```

---

## CLI Commands

| Command | Description |
|---|---|
| `validate` | Resolve and validate config |
| `show` | Print resolved config with secrets masked |
| `explain <key>` | Explain one dotted config key |
| `schema` | Print schema documentation |
| `init` | Generate starter `.env` or TOML config |

---

## Shared CLI Options

| Option | Description |
|---|---|
| `--schema PATH[:object]` | Load schema from Python file; defaults to built-in demo schema |
| `--config PATH` | TOML config file |
| `--env-file PATH` | `.env` file |
| `--prefix PREFIX` | Environment variable prefix such as `MYAPP` |
| `--allow-prefixless-env` | Load real environment without a prefix |
| `--set KEY=VALUE` | CLI override; may be repeated |
| `--strict` | Reject unknown keys; default |
| `--lenient` | Ignore unknown keys |

---

## Source Precedence Contract

Lowest to highest:

```text
1. schema defaults
2. TOML config file
3. .env file
4. environment variables
5. CLI --set overrides
```

Later layers override earlier layers.

---

## Environment Variable Contract

Dotted paths convert to uppercase env names using `__` between segments:

```text
app.name → APP__NAME
server.port → SERVER__PORT
```

With prefix:

```text
MYAPP_APP__NAME
MYAPP_SERVER__PORT
```

Custom `Field(env_name=...)` overrides default env name.

---

## CLI Override Contract

Syntax:

```powershell
--set key=value
```

Examples:

```powershell
--set app.name=Demo
--set server.port=9000
```

Custom `Field(cli_name=...)` maps alternate CLI names to schema paths.

---

## `.env` Contract

Supported:
- `KEY=VALUE`
- optional `export KEY=VALUE`
- single quotes
- double quotes with escapes
- inline comments for unquoted values
- line continuations with trailing backslash
- duplicate key detection

Invalid:
- malformed `export`
- missing `=`
- invalid key
- duplicate key
- unterminated quote
- unexpected trailing text after quoted value

---

## TOML Contract

TOML files are parsed with `tomllib`.

Expected:
- TOML root must be a table
- parse errors include path/line when available

---

## Output Contract

### `validate`

Success:
```text
Config valid.
```

Failure:
```text
Config invalid:
- <path>: <message> (value: <value>) (source: <source>)
```

Secret issue values are masked.

---

### `show`

Outputs nested config with keys sorted. Secrets are masked.

---

### `schema`

Outputs field documentation:
- path
- type
- required
- default
- choices
- min/max
- regex
- secret status
- nullable
- description

---

### `explain`

Outputs:
- path
- type
- status or value
- source
- source name
- raw value

Secret raw values are masked.

---

## Exit Codes

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Config invalid: coercion or validation issues |
| `2` | Parse/source error |
| `3` | Schema/config/key error |
| `64` | CLI usage error from argparse |

---

## Side Effects

| Operation | Side Effect |
|---|---|
| `load()` | Reads configured source files and environment mapping |
| `show` | Prints masked config |
| `schema` | Prints generated schema docs |
| `init` | Prints starter config template |
| `validate` | Prints success/failure status |
| `explain` | Prints one key's resolved value/provenance |
| `Config.to_dict()` | Returns mutable copy; original config remains frozen |

The library does not write files by default.

---

## Error Types

| Error | Use |
|---|---|
| `SchemaError` | Invalid schema declaration |
| `SourceError` | Source file cannot be read |
| `ParseError` | Source syntax error |
| `CoercionError` | Raw value cannot become declared type |
| `ValidationError` | Coerced value violates schema |
| `ConfigInvalidError` | Aggregated coercion + validation issues |
| `ConfigKeyError` | Missing requested key |
| `ConfigFrozenError` | Mutation attempted on frozen config |
| `ConfigError` | General config error |

---

*Constitution reference: Article 4 (input/output boundaries), Article 6 (verification), and Article 8 (understandable and verifiable work).*

---


# Runbook
## App — Config Manager
**Configuration Systems Group | Document 4 of 5**

---

## Requirements

### Runtime

- Python 3.11 or newer
- No third-party runtime dependencies

### Development

- pytest
- pytest-cov
- ruff
- mypy

---

## Installation

### Editable install

```powershell
pip install -e .
```

### Editable install with dev tools

```powershell
pip install -e ".[dev]"
```

### Locked dev install

```powershell
pip install -r requirements-dev.lock
pip install -e . --no-deps
```

---

## Basic Smoke Test

```powershell
config-manager --version
config-manager schema
config-manager init --format env --prefix MYAPP
config-manager validate `
  --schema examples/basic_schema.py `
  --config examples/app.toml `
  --env-file examples/.env.example `
  --prefix MYAPP
```

Expected:
```text
Config valid.
```

---

## Standard Operating Procedures

### Validate a config file

```powershell
config-manager validate --schema examples/basic_schema.py --config examples/app.toml
```

---

### Include `.env`

```powershell
config-manager validate `
  --schema examples/basic_schema.py `
  --config examples/app.toml `
  --env-file examples/.env.example `
  --prefix MYAPP
```

---

### Override from CLI

```powershell
config-manager validate `
  --schema examples/basic_schema.py `
  --config examples/app.toml `
  --set app.name=Demo `
  --set server.port=9000
```

---

### Show masked resolved config

```powershell
config-manager show --schema examples/basic_schema.py --config examples/app.toml
```

---

### Explain a resolved value

```powershell
config-manager explain app.name --schema examples/basic_schema.py --config examples/app.toml
```

---

### Generate starter `.env`

```powershell
config-manager init --format env --prefix MYAPP
```

---

### Generate starter TOML

```powershell
config-manager init --format toml
```

---

## Running Tests

```powershell
pytest
```

Coverage:

```powershell
pytest --cov=config_manager --cov-report=term-missing
```

---

## Running Quality Checks

```powershell
ruff check .
ruff format --check .
mypy config_manager
```

---

## CI Parity

The GitHub Actions workflow runs:
- Python 3.11, 3.12, 3.13, 3.14
- install dev tools from `requirements-dev.lock`
- editable package install
- Ruff lint
- Ruff format check
- mypy
- pytest with coverage and `--cov-fail-under=85`

---

## Health Checks

### Import check

```powershell
python -c "from config_manager import Field, Schema, load; print('ok')"
```

Expected:
```text
ok
```

---

### CLI version

```powershell
config-manager --version
```

Expected:
```text
config-manager 0.3.0
```

---

### Schema docs

```powershell
config-manager schema
```

Expected:
- field list printed
- field types shown
- defaults/required/secret metadata shown where applicable

---

### Validation success

```powershell
config-manager validate --schema examples/basic_schema.py --config examples/app.toml
```

Expected:
```text
Config valid.
```

---

### Secret masking

```powershell
config-manager show --schema examples/basic_schema.py --config examples/app.toml
```

Expected:
- secret-like keys are printed as `********`

---

## Expected Failure Modes

### Missing source file

**Trigger:**
```powershell
config-manager validate --config missing.toml
```

Expected:
```text
Config parse error: missing.toml: file not found
```

Exit:
```text
2
```

---

### Invalid TOML

**Trigger:** malformed TOML file.

Expected:
```text
Config parse error: <path>: line <n>: ...
```

Exit:
```text
2
```

---

### Invalid `.env`

**Common causes:**
- duplicate key
- missing `=`
- invalid key
- unterminated quote
- malformed export syntax

Exit:
```text
2
```

---

### Coercion failure

**Trigger:**
```powershell
--set server.port=not-a-number
```

Expected:
```text
Config invalid:
- server.port: expected int, got 'not-a-number' ...
```

Exit:
```text
1
```

---

### Validation failure

**Common causes:**
- required field missing
- unknown key in strict mode
- value outside min/max
- value not in choices
- regex mismatch
- custom validator rejected value

Exit:
```text
1
```

---

### Unknown key

Default strict mode rejects unknown keys.

Resolution options:
- fix the key
- add it to schema
- use `--lenient` when appropriate

---

### Prefixless environment not loaded

By default, real environment variables require prefix usage unless `--allow-prefixless-env` is used.

Resolution:
```powershell
config-manager validate --allow-prefixless-env
```

Use prefixless mode carefully in local development only.

---

### Config mutation rejected

**Trigger:**
```python
config.app.name = "new"
```

Expected:
```text
ConfigFrozenError
```

Resolution:
- change source values and call `load()` again
- use `to_dict()` for a mutable copy

---

## Troubleshooting Decision Tree

```text
Config does not validate
  ├── Is the source file readable?
  │     └── Check --config / --env-file path
  ├── Is the source syntax valid?
  │     ├── Validate TOML
  │     └── Check .env KEY=VALUE syntax
  ├── Are env vars using the expected prefix?
  │     └── Check --prefix and MYAPP_SECTION__KEY names
  ├── Is a raw value coercible?
  │     └── Check bool/int/float/list/dict syntax
  ├── Is the value allowed by schema?
  │     └── Check choices, min/max, regex, required
  ├── Is strict mode rejecting unknown keys?
  │     └── Fix schema/key or use --lenient
  └── Is the schema file loadable?
        └── Check path.py:object and that object is Schema
```

---

## Recovery Procedures

### Recover from bad source path

Correct path and rerun:
```powershell
config-manager validate --config <correct-path>
```

---

### Recover from malformed `.env`

1. Remove duplicate keys.
2. Ensure every active line uses `KEY=VALUE`.
3. Quote values that include special characters.
4. Rerun validation.

---

### Recover from wrong source precedence

Use `explain`:

```powershell
config-manager explain app.name --config app.toml --env-file .env --prefix MYAPP
```

Then remove or correct the higher-precedence source.

---

### Recover from secret leak concern

Use:

```python
config.to_masked_dict()
config.explain("path")
```

Avoid printing `config.to_dict()` in logs when secrets may exist.

---

## Maintenance Notes

- Keep schema as the only source of config shape.
- Add tests before changing precedence.
- Add tests before changing `.env` parsing.
- Preserve secret masking in issue formatting and CLI output.
- Keep CLI thin over `load()`.
- Keep runtime dependencies low unless a new ADR justifies them.
- Avoid silent unknown keys in default mode.
- Keep list-of-object validation aligned with coercion.
- Keep public exports stable.
- Run Ruff, mypy, and pytest before release.

---

*Constitution reference: Article 6 (behavior verification), Article 5 (constraints and trade-offs), and Article 8 (verifiable learner work).*

---


# Lessons Learned
## App — Config Manager
**Configuration Systems Group | Document 5 of 5**

---

## Why This Design Was Chosen

This design was chosen because configuration bugs are usually boundary bugs. Values enter through files, environment variables, command-line flags, and defaults. They arrive as raw strings, nested tables, missing values, unknown keys, and secrets. The app needed a design that could make those boundaries visible and safe.

The schema-first design gives every other module something stable to use. Source adapters can map environment and CLI names to schema paths. Coercion knows the target type. Validation knows required fields and constraints. Masking knows which values are secrets. `Config.explain()` can show which source won because provenance is tracked consistently.

The core choice was to treat configuration loading as a pipeline rather than one large parser. That makes the system easier to test and easier to explain.

---

## What Was Intentionally Omitted

**YAML support:** TOML and `.env` were enough for V1.

**Remote config:** Network sources would add retries, authentication, caching, and failure modes.

**Secrets manager integration:** Secret masking is included, but secret retrieval is out of scope.

**Auto-reload:** The app produces immutable snapshots. Reloading can be implemented by calling `load()` again.

**Mutation APIs:** Runtime mutation is intentionally rejected.

**Full schema language:** The schema supports practical field metadata, but not every possible JSON Schema concept.

**Application-specific argparse generation:** CLI overrides use generic `--set KEY=VALUE`.

---

## Biggest Weakness

The biggest weakness is that schemas are Python code. This gives excellent flexibility and custom validators, but it also means schema files must be trusted and importable. A declarative schema file format would be safer for untrusted inputs, but less expressive.

The second weakness is that `.env` parsing is custom. That supports the learning goal and avoids runtime dependencies, but it means parser compatibility must be maintained by tests.

The third weakness is that the app does not solve secret storage. It can prevent accidental display of secrets, but it does not fetch, rotate, encrypt, or audit secrets.

---

## Scaling Considerations

**If source types grow:**
- create new source adapters that return `(data, provenance)`
- keep source precedence explicit
- add tests for conflict resolution

**If schema features grow:**
- keep `Field` backward compatible
- add validation and docs support together
- avoid turning the project into a full JSON Schema clone without a clear reason

**If applications use large configs:**
- keep immutable snapshots
- avoid repeated `load()` calls in hot paths
- consider caching config in the application layer

**If secret support expands:**
- add secret provider interface
- preserve masking defaults
- prevent `explain()` from revealing raw provider values

---

## What the Next Refactor Would Be

1. **Add JSON output mode to CLI** — especially for `show`, `schema`, and `explain`.

2. **Add source adapter interface** — make new sources more formal.

3. **Add optional YAML support** — only if a dependency trade-off is accepted.

4. **Add schema export** — generate machine-readable schema metadata.

5. **Improve error grouping** — group issues by source or section for long configs.

---

## What This Project Taught

- **Precedence must be explicit.** Layered config is only understandable when source ordering is documented and testable.

- **Provenance is a feature, not a debug afterthought.** Operators need to know why a value won.

- **Secrets affect every output path.** Masking must cover config display, explain output, and error formatting.

- **Coercion and validation are different steps.** Raw strings must become typed values before semantic rules are meaningful.

- **Immutability simplifies runtime behavior.** A frozen config avoids hidden mutation after startup.

- **Source adapters keep the pipeline clean.** TOML, `.env`, env vars, defaults, and CLI overrides can all feed one merge path.

- **Tests define the contract.** The important behavior is not only successful loading; it is invalid keys, parse failures, type errors, provenance, secret masking, and CLI exit codes.

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation), Article 6 (verification), and Article 7 (progressive complexity) for Config Manager.*
