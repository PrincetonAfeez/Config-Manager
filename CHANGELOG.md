# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive pytest suite (~329 tests) with ~99% coverage on `config_manager/`
- `CHANGELOG.md` and [release process](docs/RELEASING.md)

### Changed

- Test tree lint/format aligned with Ruff so CI stays green
- `CONTRIBUTING.md` documents pytest (legacy unittest modules still run)

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

[Unreleased]: https://github.com/princ/config-manager/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/princ/config-manager/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/princ/config-manager/releases/tag/v0.1.0
