# Schema Folder

This folder contains simple reusable schema files for the `Config-Manager` project.

Each file exposes a top-level variable named `schema`, which is the convention expected by the CLI and examples.

## Files

- `basic_schema.py` — small app/database/cache schema for local demos.
- `service_schema.py` — common web/API service configuration.
- `worker_schema.py` — background worker and queue configuration.
- `__init__.py` — optional imports for Python users.

## CLI examples

```bash
python -m config_manager.cli validate \
  --schema Schema/basic_schema.py \
  --config examples/app.toml \
  --env-file examples/.env.example \
  --prefix MYAPP
```

```bash
python -m config_manager.cli docs --schema Schema/service_schema.py
```

## Python example

```python
from config_manager import load
from Schema.basic_schema import schema

config = load(schema, env={"MYAPP_APP__NAME": "Demo"}, prefix="MYAPP")
print(config.get("app.name"))
```
