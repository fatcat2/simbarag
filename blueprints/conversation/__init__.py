import json
import logging
import uuid

from quart import Blueprint, jsonify, make_response, request
from quart_jwt_extended import (
    get_jwt_identity,
    jwt_refresh_token_required,
)

import blueprints.users.models
from utils.image_process import analyze_user_image
from utils.image_upload import ImageValidationError, process_image
from utils.s3_client import generate_presigned_url as s3_presigned_url
from utils.s3_client import get_image as s3_get_image
from utils.s3_client import upload_image as s3_upload_image

from .agents import main_agent
from .logic import (
    add_message_to_conversation,
)
from .memory import get_memories_for_user
from .models import (
    Conversation,
    PydConversation,
    PydListConversation,
)
from .prompts import SIMBA_SYSTEM_PROMPT

conversation_blueprint = Blueprint(
    "conversation_api", __name__, url_prefix="/api/conversation"
)

_SYSTEM_PROMPT = SIMBA_SYSTEM_PROMPT


async def _get_owned_conversation(conversation_id, user_id) -> Conversation | None:
    """Fetch a conversation only if it belongs to the given user."""
    return await Conversation.get_or_none(id=conversation_id, user_id=user_id)


async def _build_system_prompt_with_memories(user_id: str) -> str:
    """Append user memories to the base system prompt."""
    memories = await get_memories_for_user(user_id)
    if not memories:
        return _SYSTEM_PROMPT
    memory_block = "\n".join(f"- {m}" for m in memories)
    return f"{_SYSTEM_PROMPT}\n\nUSER MEMORIES (facts the user has asked you to remember):\n{memory_block}"


def _build_messages_payload(
    conversation,
    query_text: str,
    image_description: str | None = None,
    system_prompt: str | None = None,
) -> list:
    recent_messages = (
        conversation.messages[-10:]
        if len(conversation.messages) > 10
        else conversation.messages
    )
    messages_payload = [{"role": "system", "content": system_prompt or _SYSTEM_PROMPT}]
    for msg in recent_messages[:-1]:  # Exclude the message we just added
        role = "user" if msg.speaker == "user" else "assistant"
        text = msg.text
        if msg.image_key and role == "user":
            text = f"[User sent an image]\n{text}"
        messages_payload.append({"role": role, "content": text})

    # Build the current user message with optional image description
    if image_description:
        content = f"[Image analysis: {image_description}]"
        if query_text:
            content = f"{query_text}\n\n{content}"
    else:
        content = query_text
    messages_payload.append({"role": "user", "content": content})
    return messages_payload


@conversation_blueprint.post("/query")
@jwt_refresh_token_required
async def query():
    current_user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=current_user_uuid)
    data = await request.get_json()
    query = data.get("query")
    conversation_id = data.get("conversation_id")
    conversation = await _get_owned_conversation(conversation_id, current_user_uuid)
    if conversation is None:
        return jsonify({"error": "conversation not found"}), 404
    await conversation.fetch_related("messages")
    await add_message_to_conversation(
        conversation=conversation,
        message=query,
        speaker="user",
        user=user,
    )

    system_prompt = await _build_system_prompt_with_memories(str(user.id))
    messages_payload = _build_messages_payload(
        conversation, query, system_prompt=system_prompt
    )
    payload = {"messages": messages_payload}
    agent_config = {
        "configurable": {"user_id": str(user.id), "is_admin": user.is_admin()}
    }

    response = await main_agent.ainvoke(payload, config=agent_config)
    message = response.get("messages", [])[-1].content
    await add_message_to_conversation(
        conversation=conversation,
        message=message,
        speaker="simba",
        user=user,
    )
    return jsonify({"response": message})


@conversation_blueprint.post("/upload-image")
@jwt_refresh_token_required
async def upload_image():
    current_user_uuid = get_jwt_identity()
    await blueprints.users.models.User.get(id=current_user_uuid)

    files = await request.files
    form = await request.form
    file = files.get("file")
    conversation_id = form.get("conversation_id")

    if not file or not conversation_id:
        return jsonify({"error": "file and conversation_id are required"}), 400

    file_bytes = file.read()
    content_type = file.content_type or "image/jpeg"

    try:
        processed_bytes, output_content_type = process_image(file_bytes, content_type)
    except ImageValidationError as e:
        return jsonify({"error": str(e)}), 400

    ext = output_content_type.split("/")[-1]
    if ext == "jpeg":
        ext = "jpg"
    key = f"conversations/{conversation_id}/{uuid.uuid4()}.{ext}"

    await s3_upload_image(processed_bytes, key, output_content_type)

    return jsonify({"image_key": key})


@conversation_blueprint.get("/image/<path:image_key>")
@jwt_refresh_token_required
async def serve_image(image_key: str):
    url = await s3_presigned_url(image_key)
    return jsonify({"url": url})


@conversation_blueprint.post("/stream-query")
@jwt_refresh_token_required
async def stream_query():
    current_user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=current_user_uuid)
    data = await request.get_json()
    query_text = data.get("query")
    conversation_id = data.get("conversation_id")
    image_key = data.get("image_key")
    conversation = await _get_owned_conversation(conversation_id, current_user_uuid)
    if conversation is None:
        return jsonify({"error": "conversation not found"}), 404
    await conversation.fetch_related("messages")
    await add_message_to_conversation(
        conversation=conversation,
        message=query_text or "",
        speaker="user",
        user=user,
        image_key=image_key,
    )

    # If an image was uploaded, analyze it with the vision model
    image_description = None
    if image_key:
        try:
            image_bytes, _ = await s3_get_image(image_key)
            image_description = await analyze_user_image(image_bytes)
            logging.info(f"Image analysis complete for {image_key}")
        except Exception as e:
            logging.error(f"Failed to analyze image: {e}")
            image_description = "[Image could not be analyzed]"

    system_prompt = await _build_system_prompt_with_memories(str(user.id))
    messages_payload = _build_messages_payload(
        conversation, query_text or "", image_description, system_prompt=system_prompt
    )
    payload = {"messages": messages_payload}
    agent_config = {
        "configurable": {"user_id": str(user.id), "is_admin": user.is_admin()}
    }

    async def event_generator():
        final_message = None
        streamed = ""
        try:
            async for event in main_agent.astream_events(
                payload, version="v2", config=agent_config
            ):
                event_type = event.get("event")

                if event_type == "on_tool_start":
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"

                elif event_type == "on_tool_end":
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

                elif event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    content = getattr(chunk, "content", None)
                    if isinstance(content, str) and content:
                        streamed += content
                        yield f"data: {json.dumps({'type': 'content', 'delta': content})}\n\n"

                elif event_type == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if isinstance(output, dict):
                        msgs = output.get("messages", [])
                        if msgs:
                            last_msg = msgs[-1]
                            content = getattr(last_msg, "content", None)
                            if isinstance(content, str) and content:
                                final_message = content

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        final_message = final_message or streamed
        if final_message:
            await add_message_to_conversation(
                conversation=conversation,
                message=final_message,
                speaker="simba",
                user=user,
            )
            yield f"data: {json.dumps({'type': 'response', 'message': final_message})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No response generated'})}\n\n"

        yield "data: [DONE]\n\n"

    return await make_response(
        event_generator(),
        200,
        {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@conversation_blueprint.route("/<conversation_id>")
@jwt_refresh_token_required
async def get_conversation(conversation_id: str):
    user_uuid = get_jwt_identity()
    conversation = await _get_owned_conversation(conversation_id, user_uuid)
    if conversation is None:
        return jsonify({"error": "conversation not found"}), 404
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
                "image_key": msg.image_key,
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
        name="New Conversation",
        user=user,
    )

    serialized_conversation = await PydConversation.from_tortoise_orm(conversation)
    return jsonify(serialized_conversation.model_dump())


@conversation_blueprint.get("/")
@jwt_refresh_token_required
async def get_all_conversations():
    user_uuid = get_jwt_identity()
    user = await blueprints.users.models.User.get(id=user_uuid)

    query = Conversation.filter(user=user)

    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(name__icontains=search)

    query = query.order_by("-updated_at")

    # `limit` is optional: when omitted we return the full list (backward
    # compatible with any non-frontend callers). `offset` only applies with it.
    limit = request.args.get("limit", type=int)
    if limit is not None:
        offset = request.args.get("offset", default=0, type=int)
        query = query.offset(offset).limit(limit)

    serialized_conversations = await PydListConversation.from_queryset(query)

    return jsonify(serialized_conversations.model_dump())


@conversation_blueprint.patch("/<conversation_id>")
@jwt_refresh_token_required
async def rename_conversation(conversation_id: str):
    user_uuid = get_jwt_identity()
    body = await request.get_json()
    name = (body or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    conversation = await _get_owned_conversation(conversation_id, user_uuid)
    if conversation is None:
        return jsonify({"error": "conversation not found"}), 404

    conversation.name = name[:255]
    await conversation.save()

    serialized_conversation = await PydConversation.from_tortoise_orm(conversation)
    return jsonify(serialized_conversation.model_dump())


@conversation_blueprint.delete("/<conversation_id>")
@jwt_refresh_token_required
async def delete_conversation(conversation_id: str):
    user_uuid = get_jwt_identity()
    conversation = await _get_owned_conversation(conversation_id, user_uuid)
    if conversation is None:
        return jsonify({"error": "conversation not found"}), 404

    await conversation.delete()
    return jsonify({"success": True})
