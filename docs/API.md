# API Reference 

## Public exports

```python
from config_manager import (
    Config,
    ConfigInvalidError,
    ConfigKeyError,
    Field,
    MISSING,
    Schema,
    load,
)
```

## `Schema`

```python
schema = Schema({
    "app": {
        "name": Field(str, required=True, description="Application name"),
        "debug": Field(bool, default=False),
    },
    "tags": Field(list, default=[], item_type=str),
    "servers": Field(
        list,
        item_fields={
            "host": Field(str, required=True),
            "port": Field(int, default=8080),
        },
    ),
    "labels": Field(dict, value_type=str, default={}),
})
```

### Methods

| Method | Description |
|--------|-------------|
| `schema.fields` | Flat `dict[str, Field]` keyed by dotted path |
| `schema.defaults()` | Nested dict of default values |
| `schema.docs()` | Human-readable schema documentation |
| `schema.is_secret(path)` | Whether a path is treated as secret |
| `schema.env_name_for(path, prefix=None)` | Environment variable name |
| `schema.get_field(path)` | `Field` or `None` |

## `Field`

| Parameter | Type | Description |
|-----------|------|-------------|
| `type_` | `type` | `str`, `int`, `float`, `bool`, `list`, or `dict` |
| `required` | `bool` | Must be present in merged raw config |
| `default` | any | Default when not provided |
| `choices` | sequence | Allowed values |
| `min_value` / `max_value` | number | Numeric bounds |
| `min_length` / `max_length` | int | String, list, or dict length |
| `regex` | `str` | Full-string regex (`re.fullmatch`) |
| `secret` | `bool` | Mask in output |
| `nullable` | `bool` | Allow `None` |
| `item_type` | `type` | Scalar type for homogeneous lists |
| `item_fields` | `dict[str, Field]` | Schema for list-of-object items |
| `value_type` | `type` | Value type for `dict` fields |
| `validator` | callable | Custom validation; falsy = reject |
| `env_name` | `str` | Override env var name |
| `cli_name` | `str` | Override CLI `--set` key |
| `description` | `str` | Documentation text |

## `load()`

```python
config = load(
    schema,
    config_file="app.toml",       # optional TOML path
    env_file=".env",              # optional .env path
    env={"MYAPP_APP__NAME": "x"}, # optional env mapping
    cli_overrides={"app.name": "y"},
    prefix="MYAPP",
    strict=True,                  # reject unknown keys
    allow_prefixless_env=False,   # load unprefixed env vars
)
```

Returns a frozen `Config`. Raises `ConfigInvalidError` on coercion or
validation failure.

## `Config`

| Method | Description |
|--------|-------------|
| `config.get(path, default=MISSING)` | Dotted path lookup; raises `ConfigKeyError` if missing |
| `config.explain(path)` | Value, type, source, provenance for one key |
| `config.provenance(path)` | `Provenance` object or `None` |
| `config.to_dict()` | Mutable nested dict (unfrozen copy) |
| `config.to_masked_dict()` | Dict with secrets replaced by `********` |
| `config.app.name` | Attribute access on nested sections |

List fields are stored as **immutable tuples** after freeze.

## Error types

| Exception | When |
|-----------|------|
| `ConfigInvalidError` | `load()` — combined coercion + validation issues |
| `CoercionError` | `coerce_config()` failure |
| `ValidationError` | `validate_config()` failure |
| `SchemaError` | Invalid schema declaration |
| `ParseError` | Malformed source, merge conflict, duplicate `.env` key |
| `SourceError` | Missing config file |
| `ConfigKeyError` | Missing path on resolved config |
| `ConfigError` | General config errors (`explain`, schema load) |
| `ConfigFrozenError` | Mutation of resolved config |

Each issue in `ConfigInvalidError.issues` is a `ConfigIssue` with `path`,
`message`, optional `source`, and secret redaction.

## Lower-level helpers

```python
from config_manager.coercion import coerce_config, collect_coercion_issues
from config_manager.validation import validate_config, collect_validation_issues
```

Use these when building custom pipelines. Prefer `load()` for applications.
