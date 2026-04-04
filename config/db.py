import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgres://raggr:raggr_dev_password@localhost:5432/raggr"
)

TORTOISE_CONFIG = {
    "connections": {"default": DATABASE_URL},
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
