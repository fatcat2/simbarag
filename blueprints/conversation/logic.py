from .models import Conversation, ConversationMessage


async def create_conversation(name: str = "") -> Conversation:
    conversation = await Conversation.create(name=name)
    return conversation


async def add_message_to_conversation(
    conversation: Conversation,
    message: str,
    speaker: str,
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
