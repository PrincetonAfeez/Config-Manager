# Contributing

Thank you for contributing to Config Manager. This is an academic project;
keep changes focused and well tested.

## Development setup

```powershell
git clone https://github.com/princ/config-manager.git
cd config-manager
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Quality checks

Run the same checks as CI before submitting:

```powershell
ruff check .
ruff format --check .
mypy config_manager
pytest
pytest --cov=config_manager --cov-report=term-missing
```

## Project layout

```
config_manager/   # Library source
tests/            # pytest suite (legacy unittest modules still run)
examples/         # Sample schemas and config files
docs/             # Architecture, API, CLI, ADRs, releasing
```

## Guidelines

1. **Match existing style** — 4-space indent, type hints on public APIs.
2. **Test behavior** — add pytest tests in `tests/` for new features and bug fixes.
3. **Update docs** — README, `docs/API.md`, `docs/ARCHITECTURE.md` (including [Limitations](docs/ARCHITECTURE.md#limitations)), `CHANGELOG.md`, or ADRs when behavior changes.
4. **Keep scope academic** — stdlib-only runtime; no heavy dependencies.
5. **One concern per change** — small, reviewable diffs.

## Adding a field type

1. Update `Field` in `fields.py`
2. Extend `Schema._validate()`
3. Add coercion in `coercion.py`
4. Add validation in `validation.py`
5. Document in `docs/API.md` and `docs/ARCHITECTURE.md`
6. Add tests

## Architecture decisions

Significant design changes should include a new ADR in `docs/adr/` using the
existing numbered format.

## Pull request checklist

- [ ] Tests pass locally
- [ ] Ruff and mypy pass
- [ ] Documentation updated if needed
- [ ] `CHANGELOG.md` updated under `[Unreleased]` for user-visible changes
- [ ] No secrets or `.env` files committed

## Releasing

Maintainers only — see [docs/RELEASING.md](docs/RELEASING.md).
