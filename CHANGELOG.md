# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-05-27

### Added

- `__version__` export and PEP 561 `py.typed` marker
- Secret inference and masking for list-of-object `item_fields` (e.g. `servers[].password`)
- Inferred-secret masking for keys inside free-form `Field(dict, ...)` values
- Rich-type support in `init` scaffolding (dict inline tables, array-of-tables, JSON env values)
- Architecture/API/CLI documentation for pipeline limitations and provenance semantics
- `Schema.dict_field_paths()` and `Schema.path_may_contain_secrets()` helpers
- `explain()` masks nested secrets in list and dict field values
- Homogeneous `Field(list, item_type=..., secret=True)` masks each list item
- Release workflow builds on Python 3.14 and verifies wheel install before upload

### Changed

- `examples/basic_schema.py` re-exports `config_manager.example_schema` (single source of truth)
- Environment and `.env` provenance `name` now stores the original variable name
- Test suite fully migrated to pytest; `minimal_schema` fixture replaces ad-hoc duplicates
- CI matrix includes Python 3.14

### Fixed

- `init` no longer emits Python `repr()` for dict defaults in TOML/env output
- `to_masked_dict()` and `explain()` now mask secrets inside list-of-object items
- CI `ruff format --check` passes on the full test tree

## [0.2.0] - 2025-05-26

### Added

- Rich schema types: `Field(dict, value_type=...)` and `Field(list, item_fields={...})`
- JSON coercion for dict/list values from env and CLI strings
- Documentation: `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/CLI.md`, `CONTRIBUTING.md`
- Five architecture decision records under `docs/adr/`
- GitHub Actions CI (Ruff, mypy, pytest with coverage gate)
- Examples: `examples/rich_schema.py`, `examples/servers.toml`

### Changed

- List values are stored as immutable tuples after freeze
- `env_name` and `cli_name` on `Field` are wired through sources and CLI
- Schema module loading uses SHA-256 digests for import names
- Improved error types: `ConfigInvalidError`, bracket path support, merge guards

## [0.1.0] - 2025-05-01

### Added

- Initial release: layered config loading (defaults, TOML, `.env`, environment, CLI)
- Declarative `Schema` / `Field` with coercion and validation
- Immutable `Config` with provenance, secret masking, and `explain`
- CLI: `validate`, `show`, `explain`, `schema`, `init`
- Stdlib-only runtime (Python 3.11+, `tomllib`)

[Unreleased]: https://github.com/princ/config-manager/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/princ/config-manager/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/princ/config-manager/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/princ/config-manager/releases/tag/v0.1.0
