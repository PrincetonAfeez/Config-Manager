# ADR 0005: Secrets Masked, Not Encrypted

## Context

Applications need to log or print configuration without leaking credentials.
Config Manager is a loader/validator, not a secrets vault.

## Decision

Mask secrets in CLI output, error messages, and `Config.to_masked_dict()`, but
do **not** encrypt values at rest in config files or environment variables.

## Masking rules

1. **`Field(..., secret=True)`** — always masked.
2. **Inferred secrets** — leaf names such as `password`, `token`, and `api_key`
   are treated as secrets when `secret` is not set explicitly.
3. **List-of-object items** — the same rules apply to `item_fields` sub-keys.
   Masking uses pattern paths like `servers[].password` when traversing list
   items in `to_masked_dict()`.
4. **Free-form dict values** — keys inside `Field(dict, ...)` without a fixed
   schema are not scanned for inferred secret names. Use explicit `secret=True`
   on structured fields instead.

## Consequences

- Masking protects common operator workflows (`show`, logs, error output).
- Masking does not prevent access to raw values via `config.get()` or
  `config.to_dict()`.
- Callers storing config on disk must use proper secret management outside this
  library.
