from quart import Blueprint, jsonify
from .models import (
    Conversation,
    PydConversation,
)

conversation_blueprint = Blueprint(
    "conversation_api", __name__, url_prefix="/api/conversation"
)


@conversation_blueprint.route("/<conversation_id>")
async def get_conversation(conversation_id: str):
    conversation = await Conversation.get(id=conversation_id)
    serialized_conversation = await PydConversation.from_tortoise_orm(conversation)

    return jsonify(serialized_conversation.model_dump_json())
