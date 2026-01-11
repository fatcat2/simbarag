import datetime

from quart import Blueprint, jsonify, request
from quart_jwt_extended import (
    get_jwt_identity,
    jwt_refresh_token_required,
)

import blueprints.users.models

from .agents import main_agent
from .logic import (
    add_message_to_conversation,
    get_conversation_by_id,
    rename_conversation,
)
from .models import (
    Conversation,
    PydConversation,
    PydListConversation,
)

conversation_blueprint = Blueprint(
    "conversation_api", __name__, url_prefix="/api/conversation"
)


@conversation_blueprint.post("/query")
@jwt_refresh_token_required
async def query():
    current_user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=current_user_uuid)
    data = await request.get_json()
    query = data.get("query")
    conversation_id = data.get("conversation_id")
    conversation = await get_conversation_by_id(conversation_id)
    await conversation.fetch_related("messages")
    await add_message_to_conversation(
        conversation=conversation,
        message=query,
        speaker="user",
        user=user,
    )

    # Build conversation history from recent messages (last 10 for context)
    recent_messages = (
        conversation.messages[-10:]
        if len(conversation.messages) > 10
        else conversation.messages
    )

    messages_payload = [
        {
            "role": "system",
            "content": "You are a helpful cat assistant named Simba that understands veterinary terms. When there are questions to you specifically, they are referring to Simba the cat. Answer the user in as if you were a cat named Simba. Don't act too catlike. Be assertive.\n\nIMPORTANT: When users ask factual questions about Simba's health, medical history, veterinary visits, medications, weight, or any information that would be in documents, you MUST use the simba_search tool to retrieve accurate information before answering. Do not rely on general knowledge - always search the documents for factual questions.",
        }
    ]

    # Add recent conversation history
    for msg in recent_messages[:-1]:  # Exclude the message we just added
        role = "user" if msg.speaker == "user" else "assistant"
        messages_payload.append({"role": role, "content": msg.text})

    # Add current query
    messages_payload.append({"role": "user", "content": query})

    payload = {"messages": messages_payload}

    response = await main_agent.ainvoke(payload)
    message = response.get("messages", [])[-1].content
    await add_message_to_conversation(
        conversation=conversation,
        message=message,
        speaker="simba",
        user=user,
    )
    return jsonify({"response": message})


@conversation_blueprint.route("/<conversation_id>")
@jwt_refresh_token_required
async def get_conversation(conversation_id: str):
    conversation = await Conversation.get(id=conversation_id)
    current_user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=current_user_uuid)
    await conversation.fetch_related("messages")

    # Manually serialize the conversation with messages
    messages = []
    for msg in conversation.messages:
        messages.append(
            {
                "id": str(msg.id),
                "text": msg.text,
                "speaker": msg.speaker.value,
                "created_at": msg.created_at.isoformat(),
            }
        )
    name = conversation.name
    if len(messages) > 8 and "datetime" in name.lower():
        name = await rename_conversation(
            user=user,
            conversation=conversation,
        )
        print(name)

    return jsonify(
        {
            "id": str(conversation.id),
            "name": name,
            "messages": messages,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
    )


@conversation_blueprint.post("/")
@jwt_refresh_token_required
async def create_conversation():
    user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=user_uuid)
    conversation = await Conversation.create(
        name=f"{user.username} {datetime.datetime.now().timestamp}",
        user=user,
    )

    serialized_conversation = await PydConversation.from_tortoise_orm(conversation)
    return jsonify(serialized_conversation.model_dump())


@conversation_blueprint.get("/")
@jwt_refresh_token_required
async def get_all_conversations():
    user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=user_uuid)
    conversations = Conversation.filter(user=user)
    serialized_conversations = await PydListConversation.from_queryset(conversations)

    return jsonify(serialized_conversations.model_dump())
