import tortoise.exceptions

from .models import Conversation, ConversationMessage

import blueprints.users.models


async def create_conversation(name: str = "") -> Conversation:
    conversation = await Conversation.create(name=name)
    return conversation


async def add_message_to_conversation(
    conversation: Conversation,
    message: str,
    speaker: str,
    user: blueprints.users.models.User,
) -> ConversationMessage:
    print(conversation, message, speaker)
    message = await ConversationMessage.create(
        text=message,
        speaker=speaker,
        conversation=conversation,
    )

    return message


async def get_the_only_conversation() -> Conversation:
    try:
        conversation = await Conversation.all().first()
        if conversation is None:
            conversation = await Conversation.create(name="simba_chat")
    except Exception as _e:
        conversation = await Conversation.create(name="simba_chat")

    return conversation


async def get_conversation_for_user(user: blueprints.users.models.User) -> Conversation:
    try:
        return await Conversation.get(user=user)
    except tortoise.exceptions.DoesNotExist:
        await Conversation.get_or_create(name=f"{user.username}'s chat", user=user)

        return await Conversation.get(user=user)
