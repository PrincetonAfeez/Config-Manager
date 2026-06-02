"""Reusable schemas for the Config-Manager project.

Import schemas directly from their modules when you need a specific contract:

    from Schema.basic_schema import schema
"""

from .basic_schema import schema as basic_schema
from .service_schema import schema as service_schema
from .worker_schema import schema as worker_schema

__all__ = ["basic_schema", "service_schema", "worker_schema"]
