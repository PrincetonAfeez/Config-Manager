from config_manager import Field, Schema

schema = Schema(
    {
        "app": {
            "name": Field(str, required=True, description="Application name"),
            "tags": Field(list, default=["web"], item_type=str),
        },
        "servers": Field(
            list,
            item_fields={
                "host": Field(str, required=True),
                "port": Field(int, default=8080, min_value=1, max_value=65535),
                "enabled": Field(bool, default=True),
            },
            description="Backend servers",
        ),
        "feature_flags": Field(
            dict,
            value_type=bool,
            default={"beta_ui": False},
            description="Feature toggle map",
        ),
    }
)
