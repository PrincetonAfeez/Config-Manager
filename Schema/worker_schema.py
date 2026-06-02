"""Schema for a background worker process."""

from config_manager import Field, Schema

schema = Schema(
    {
        "app": {
            "name": Field(str, required=True, description="Worker application name"),
            "environment": Field(
                str,
                default="dev",
                choices=["dev", "staging", "prod"],
            ),
        },
        "queue": {
            "url": Field(str, required=True, secret=True, description="Queue connection URL"),
            "name": Field(str, default="default", description="Queue name"),
            "prefetch": Field(int, default=10, min_value=1, description="Prefetch size"),
        },
        "worker": {
            "concurrency": Field(int, default=1, min_value=1),
            "shutdown_timeout_seconds": Field(int, default=30, min_value=1),
            "enabled_jobs": Field(
                list,
                default=["default"],
                item_type=str,
                min_length=1,
                description="Job names this worker may execute",
            ),
        },
        "retry": {
            "max_attempts": Field(int, default=3, min_value=0),
            "backoff_seconds": Field(float, default=1.5, min_value=0.0),
        },
        "logging": {
            "level": Field(
                str,
                default="INFO",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            )
        },
    }
)
