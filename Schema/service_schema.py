"""Schema for a small web/API service."""

from config_manager import Field, Schema

schema = Schema(
    {
        "app": {
            "name": Field(str, required=True, description="Service name"),
            "environment": Field(
                str,
                default="dev",
                choices=["dev", "staging", "prod"],
                description="Deployment environment",
            ),
            "debug": Field(bool, default=False, description="Enable debug output"),
        },
        "server": {
            "host": Field(str, default="127.0.0.1", description="Bind host"),
            "port": Field(
                int,
                default=8000,
                min_value=1,
                max_value=65535,
                description="Bind port",
            ),
            "workers": Field(int, default=1, min_value=1, description="Worker count"),
        },
        "database": {
            "url": Field(str, required=True, secret=True, description="Database URL"),
            "pool_size": Field(int, default=5, min_value=1, description="DB pool size"),
            "timeout_seconds": Field(float, default=30.0, min_value=0.1),
        },
        "security": {
            "api_key": Field(str, required=True, secret=True, description="Service API key"),
            "allowed_origins": Field(
                list,
                default=["http://localhost:3000"],
                item_type=str,
                description="Allowed CORS origins",
            ),
        },
        "logging": {
            "level": Field(
                str,
                default="INFO",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            ),
            "json": Field(bool, default=False, description="Emit JSON logs"),
        },
        "feature_flags": Field(
            dict,
            value_type=bool,
            default={"new_dashboard": False},
            description="Boolean feature flags",
        ),
    }
)
