import tortoise.exceptions

import blueprints.users.models

from .models import Conversation, ConversationMessage


async def create_conversation(name: str = "") -> Conversation:
    conversation = await Conversation.create(name=name)
    return conversation


async def add_message_to_conversation(
    conversation: Conversation,
    message: str,
    speaker: str,
    user: blueprints.users.models.User,
    image_key: str | None = None,
) -> ConversationMessage:
    print(conversation, message, speaker)

    # Name the conversation after the first user message
    if speaker == "user" and not await conversation.messages.all().exists():
        conversation.name = message[:100]
        await conversation.save()

    message = await ConversationMessage.create(
        text=message,
        speaker=speaker,
        conversation=conversation,
        image_key=image_key,
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
        conversation = await Conversation.get(user=user)
    except tortoise.exceptions.MultipleObjectsReturned:
        conversation = (
            await Conversation.filter(user=user).order_by("created_at").first()
        )
    except tortoise.exceptions.DoesNotExist:
        conversation = await Conversation.create(
            name=f"{user.username}'s chat", user=user
        )
    return conversation


async def get_conversation_for_channel(
    user: blueprints.users.models.User, channel: str
) -> Conversation:
    conversation = await Conversation.filter(user=user, channel=channel).first()
    if conversation is None:
        conversation = await Conversation.create(
            name=f"{user.username}'s {channel} chat", user=user, channel=channel
        )
    return conversation


async def get_conversation_by_id(id: str) -> Conversation:
    return await Conversation.get(id=id)


async def get_conversation_transcript(
    user: blueprints.users.models.User, conversation: Conversation
) -> str:
    messages = []
    for message in conversation.messages:
        messages.append(f"{message.speaker} at {message.created_at}: {message.text}")

    return "\n".join(messages)
