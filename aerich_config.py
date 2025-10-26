import os

TORTOISE_ORM = {
    "connections": {"default": os.getenv("DATABASE_URL", "sqlite:///app/database/raggr.db")},
    "apps": {
        "models": {
            "models": [
                "blueprints.conversation.models",
                "blueprints.users.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
