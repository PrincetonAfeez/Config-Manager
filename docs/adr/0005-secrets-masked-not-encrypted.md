# ADR 0005: Secrets Masked, Not Encrypted

## Context

Applications need to log or print configuration without leaking credentials.
Config Manager is a loader/validator, not a secrets vault.

## Decision

Mask secrets in CLI output, error messages, `Config.to_masked_dict()`, and
`Config.explain()`, but do **not** encrypt values at rest in config files or
environment variables.

## Masking rules

1. **`Field(..., secret=True)`** — always masked.
2. **Inferred secrets** — leaf names such as `password`, `token`, and `api_key`
   are treated as secrets when `secret` is not set explicitly.
3. **List-of-object items** — the same rules apply to `item_fields` sub-keys.
   Masking uses pattern paths like `servers[].password` when traversing list
   items.
4. **Homogeneous lists** — `Field(list, item_type=..., secret=True)` masks
   every scalar item (`tags[]` pattern).
5. **Free-form dict values** — for `Field(dict, ...)` without fixed sub-schema,
   keys whose names match inferred secret leaf names are masked in output
   (e.g. `flags.password` inside a dict value).
6. **`explain()`** — returns masked display values when the field itself is
   secret or when nested list/dict content contains masked values; `raw_value`
   is redacted when `path_may_contain_secrets()` applies and secrets are present.

## Consequences

- Masking protects common operator workflows (`show`, `explain`, logs, error output).
- Masking does not prevent access to raw values via `config.get()` or
  `config.to_dict()`.
- Callers storing config on disk must use proper secret management outside this
  library.
