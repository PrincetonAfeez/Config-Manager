"""Public load() pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .coercion import collect_coercion_issues
from .config import Config
from .errors import ConfigInvalidError
from .merge import merge_layers
from .provenance import Provenance
from .schema import Schema
from .sources import (
    cli_overrides_source,
    defaults_source,
    dotenv_source,
    environment_source,
    normalize_prefix,
    toml_source,
)
from .validation import collect_validation_issues, filter_to_schema


def load(
    schema: Schema,
    config_file: str | Path | None = None,
    env_file: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    cli_overrides: Mapping[str, str] | None = None,
    prefix: str | None = None,
    strict: bool = True,
    allow_prefixless_env: bool = False,
) -> Config:
    """Load, merge, coerce, validate, freeze, and return Config."""

    prefix = normalize_prefix(prefix)
    layer_list: list[tuple[Mapping[str, Any], Mapping[str, Provenance]]] = [
        defaults_source(schema),
        toml_source(config_file),
        dotenv_source(env_file, prefix=prefix, schema=schema),
        environment_source(
            env,
            prefix=prefix,
            allow_prefixless=allow_prefixless_env,
            schema=schema,
        ),
        cli_overrides_source(cli_overrides, schema=schema),
    ]
    raw_data, provenance = merge_layers(layer_list)
    coerced, coercion_issues = collect_coercion_issues(raw_data, schema, provenance=provenance)
    validation_issues = collect_validation_issues(
        coerced,
        raw_data,
        schema,
        strict=strict,
        provenance=provenance,
    )
    all_issues = coercion_issues + validation_issues
    if all_issues:
        raise ConfigInvalidError(all_issues)

    final_data = filter_to_schema(coerced, schema)
    final_provenance = {path: value for path, value in provenance.items() if path in schema.fields}
    return Config(final_data, schema=schema, provenance=final_provenance)
