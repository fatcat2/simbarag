import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration with environment variable support
# Use DATABASE_PATH for relative paths or DATABASE_URL for full connection strings
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/raggr.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite://{DATABASE_PATH}")

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "blueprints.conversation.models",
                "blueprints.users.models",
                "blueprints.email.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
