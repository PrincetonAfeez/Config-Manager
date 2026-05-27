from config_manager import Field, Schema

schema = Schema(
    {
        "app": {
            "name": Field(str, required=True, description="Application name"),
            "debug": Field(bool, default=False, description="Enable debug mode"),
            "environment": Field(
                str,
                default="dev",
                choices=["dev", "test", "prod"],
                description="Runtime environment",
            ),
        },
        "database": {
            "host": Field(str, default="localhost", description="Database host"),
            "port": Field(int, default=5432, min_value=1, max_value=65535),
            "username": Field(str, required=True),
            "password": Field(str, required=True, secret=True),
        },
        "cache": {
            "ttl": Field(int, default=60, min_value=0, description="Cache TTL seconds"),
            "enabled": Field(bool, default=True, description="Enable cache"),
        },
    }
)
