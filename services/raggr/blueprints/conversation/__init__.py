import datetime

from quart_jwt_extended import (
    jwt_refresh_token_required,
    get_jwt_identity,
)

from quart import Blueprint, jsonify
from .models import (
    Conversation,
    PydConversation,
    PydListConversation,
)

import blueprints.users.models

conversation_blueprint = Blueprint(
    "conversation_api", __name__, url_prefix="/api/conversation"
)


@conversation_blueprint.route("/<conversation_id>")
async def get_conversation(conversation_id: str):
    conversation = await Conversation.get(id=conversation_id)
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

    return jsonify(
        {
            "id": str(conversation.id),
            "name": conversation.name,
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
