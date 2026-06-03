"""Link an iMessage phone number to an existing user account.

Usage:
  python scripts/link_imessage.py <username_or_email> <phone_number>
  python scripts/link_imessage.py ryan +15551234567

Run inside Docker:
  docker compose exec raggr python scripts/link_imessage.py ryan +15551234567
"""

import os
import sys
import asyncio

from dotenv import load_dotenv
from tortoise import Tortoise

from blueprints.users.models import User

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://database/raggr.db")


async def link_imessage(identifier: str, phone_number: str):
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={
            "models": [
                "blueprints.users.models",
                "blueprints.conversation.models",
            ]
        },
    )

    try:
        user = await User.filter(username=identifier).first()
        if not user:
            user = await User.filter(email=identifier).first()
        if not user:
            print(f"Error: No user found with username or email '{identifier}'")
            return False

        conflict = (
            await User.filter(imessage_number=phone_number).exclude(id=user.id).first()
        )
        if conflict:
            print(
                f"Error: {phone_number} is already linked to user '{conflict.username}'"
            )
            return False

        user.imessage_number = phone_number
        await user.save()
        print(f"Linked {phone_number} to user '{user.username}' ({user.email})")
        return True

    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python scripts/link_imessage.py <username_or_email> <phone_number>"
        )
        sys.exit(1)

    success = asyncio.run(link_imessage(sys.argv[1], sys.argv[2]))
    sys.exit(0 if success else 1)
