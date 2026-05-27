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
    __version__,
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

`examples/basic_schema.py` re-exports the same schema as `config_manager.example_schema`
(the CLI default when `--schema` is omitted).

### Methods

| Method | Description |
|--------|-------------|
| `schema.fields` | Flat `dict[str, Field]` keyed by dotted path |
| `schema.defaults()` | Nested dict of default values |
| `schema.docs()` | Human-readable schema documentation |
| `schema.is_secret(path)` | Whether a path is secret (flat paths or `list[].key` patterns) |
| `schema.secret_paths()` | Paths masked by `to_masked_dict()` |
| `schema.path_may_contain_secrets(path)` | Whether operator output for a flat path may include secrets (used by `explain()`) |
| `schema.dict_field_paths()` | Flat paths declared as `Field(dict, ...)` |
| `schema.env_name_for(path, prefix=None)` | Environment variable name |
| `schema.get_field(path)` | `Field` or `None` for flat schema paths |

### Secret detection

- `Field(..., secret=True)` always masks.
- Leaf names such as `password`, `token`, and `api_key` are **inferred** as secrets when `secret` is not set.
- For `Field(list, item_fields={...})`, inference applies to item sub-fields; masked paths look like `servers[].password`.
- For `Field(list, item_type=..., secret=True)` (homogeneous lists), each item is masked; pattern `tags[]`.
- For `Field(dict, ...)` without a fixed sub-schema, dict **keys** matching inferred secret names are masked in output.

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
| `validator` | `Callable[[Any], bool]` | Custom validation; must return truthy to accept |
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
    strict=True,                  # reject unknown top-level leaves
    allow_prefixless_env=False,   # load unprefixed env vars (local dev)
)
```

Returns a frozen `Config`. Raises **`ConfigInvalidError`** on coercion or
validation failure (not `CoercionError` / `ValidationError` — those are used by
lower-level helpers).

### `strict` vs `lenient`

- **`strict=True` (default):** Unknown leaves in the merged raw config fail validation. Keys inside declared `dict` fields and list-of-object items are **not** unknown keys.
- **`strict=False`:** Unknown leaves are ignored; they are omitted from the resolved config.

## `Config`

| Method | Description |
|--------|-------------|
| `config.get(path, default=MISSING)` | Dotted path lookup; raises `ConfigKeyError` if missing |
| `config.explain(path)` | Value, type, source, provenance for one **flat schema path** |
| `config.provenance(path)` | `Provenance` or `None` for flat schema paths |
| `config.to_dict()` | Mutable nested dict (unfrozen copy) |
| `config.to_masked_dict()` | Dict with secrets replaced by `********` |
| `config.app.name` | Attribute access on nested sections |

List fields are stored as **immutable tuples** after freeze.

### `explain()` scope

`explain("database.port")` works. `explain("servers[0].host")` raises
`ConfigError` because indexed paths are not flat schema fields. For list and
dict fields, `explain()` returns a **masked** display value when nested secrets
are present; `raw_value` is redacted in that case.

### Provenance `name` field

| Source | `Provenance.name` |
|--------|-------------------|
| TOML / defaults | Dotted path |
| `.env` / environment | Original variable name (e.g. `MYAPP_DATABASE__PORT`) |
| CLI | The `--set` key |

## Error types

| Exception | When |
|-----------|------|
| `ConfigInvalidError` | **`load()`** — combined coercion + validation issues |
| `CoercionError` | `coerce_config()` only |
| `ValidationError` | `validate_config()` only |
| `SchemaError` | Invalid schema declaration |
| `ParseError` | Malformed source, merge conflict, duplicate `.env` key |
| `SourceError` | Missing config file |
| `ConfigKeyError` | Missing path on resolved config |
| `ConfigError` | General config errors (`explain`, schema load) |
| `ConfigFrozenError` | Mutation of resolved config |

Each issue in `ConfigInvalidError.issues` is a `ConfigIssue` with `path`,
`message`, optional `source`, and secret redaction in `format()`.

## Lower-level helpers

```python
from config_manager.coercion import coerce_config, collect_coercion_issues
from config_manager.validation import validate_config, collect_validation_issues
```

Use these when building custom pipelines. Prefer `load()` for applications.

## Typing

The package ships a [PEP 561](https://peps.python.org/pep-0561/) marker
(`py.typed`). Import `__version__` for the installed package version.
