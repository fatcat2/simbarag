#!/usr/bin/env python3
"""
Script to show how many messages each user has written
"""

import asyncio
from tortoise import Tortoise
from blueprints.users.models import User
from blueprints.conversation.models import Speaker
import os


async def get_user_message_stats():
    """Get message count statistics per user"""

    # Initialize database connection
    database_url = os.getenv("DATABASE_URL", "sqlite://raggr.db")
    await Tortoise.init(
        db_url=database_url,
        modules={
            "models": [
                "blueprints.users.models",
                "blueprints.conversation.models",
            ]
        },
    )

    print("\n📊 User Message Statistics\n")
    print(
        f"{'Username':<20} {'Total Messages':<15} {'User Messages':<15} {'Conversations':<15}"
    )
    print("=" * 70)

    # Get all users
    users = await User.all()

    total_users = 0
    total_messages = 0

    for user in users:
        # Get all conversations for this user
        conversations = await user.conversations.all()

        if not conversations:
            continue

        total_users += 1

        # Count messages across all conversations
        user_message_count = 0
        total_message_count = 0

        for conversation in conversations:
            messages = await conversation.messages.all()
            total_message_count += len(messages)

            # Count only user messages (not assistant responses)
            user_messages = [msg for msg in messages if msg.speaker == Speaker.USER]
            user_message_count += len(user_messages)

        total_messages += user_message_count

        print(
            f"{user.username:<20} {total_message_count:<15} {user_message_count:<15} {len(conversations):<15}"
        )

    print("=" * 70)
    print("\n📈 Summary:")
    print(f"   Total active users: {total_users}")
    print(f"   Total user messages: {total_messages}")
    print(
        f"   Average messages per user: {total_messages / total_users if total_users > 0 else 0:.1f}\n"
    )

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(get_user_message_stats())
