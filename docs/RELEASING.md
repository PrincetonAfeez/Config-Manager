# Releasing

This document describes how to cut a new **config-manager** release.

## Prerequisites

- All CI checks pass on `main` (Ruff, Ruff format, mypy, pytest with coverage)
- `CHANGELOG.md` updated under `[Unreleased]` and version section dated
- `pyproject.toml` `version` bumped to match the tag

## Version numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** — incompatible API changes
- **MINOR** — backward-compatible features
- **PATCH** — backward-compatible bug fixes

## Release checklist

1. Move `[Unreleased]` entries in `CHANGELOG.md` into a new `## [X.Y.Z] - YYYY-MM-DD` section
2. Update compare/release links at the bottom of `CHANGELOG.md`
3. Set `version = "X.Y.Z"` in `pyproject.toml`
4. Commit: `Release X.Y.Z`
5. Tag: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
6. Push branch and tag: `git push origin main --tags`

Pushing a `v*` tag triggers the [Release workflow](../.github/workflows/release.yml), which builds
sdist/wheel artifacts and attaches them to the GitHub Release.

## Build locally

```powershell
pip install build
python -m build
```

Artifacts appear in `dist/`:

- `config_manager-X.Y.Z.tar.gz`
- `config_manager-X.Y.Z-py3-none-any.whl`

Verify the wheel installs:

```powershell
pip install dist/config_manager-X.Y.Z-py3-none-any.whl
config-manager --help
pytest  # from a clean checkout with dev deps
```

## PyPI (optional)

When publishing to PyPI for the first time:

1. Create accounts on [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/)
2. Configure trusted publishing or API tokens in GitHub repository secrets
3. Uncomment the PyPI upload step in `.github/workflows/release.yml`
4. Dry-run against TestPyPI before production

## Project URLs

Update `[project.urls]` in `pyproject.toml` if the repository moves:

```toml
[project.urls]
Homepage = "https://github.com/princ/config-manager"
Documentation = "https://github.com/princ/config-manager#readme"
Repository = "https://github.com/princ/config-manager"
Changelog = "https://github.com/princ/config-manager/blob/main/CHANGELOG.md"
Issues = "https://github.com/princ/config-manager/issues"
```
