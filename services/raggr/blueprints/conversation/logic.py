import tortoise.exceptions
from langchain_openai import ChatOpenAI

import blueprints.users.models

from .models import Conversation, ConversationMessage, RenameConversationOutputSchema


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


async def get_conversation_by_id(id: str) -> Conversation:
    return await Conversation.get(id=id)


async def get_conversation_transcript(
    user: blueprints.users.models.User, conversation: Conversation
) -> str:
    messages = []
    for message in conversation.messages:
        messages.append(f"{message.speaker} at {message.created_at}: {message.text}")

    return "\n".join(messages)


async def rename_conversation(
    user: blueprints.users.models.User,
    conversation: Conversation,
) -> str:
    messages: str = await get_conversation_transcript(
        user=user, conversation=conversation
    )

    llm = ChatOpenAI(model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(RenameConversationOutputSchema)

    prompt = f"Summarize the following conversation into a sassy one-liner title:\n\n{messages}"
    response = structured_llm.invoke(prompt)
    new_name: str = response.get("title")
    conversation.name = new_name
    await conversation.save()
    return new_name
