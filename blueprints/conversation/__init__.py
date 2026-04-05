import datetime
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
    get_conversation_by_id,
    rename_conversation,
)
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


def _build_messages_payload(
    conversation, query_text: str, image_description: str | None = None
) -> list:
    recent_messages = (
        conversation.messages[-10:]
        if len(conversation.messages) > 10
        else conversation.messages
    )
    messages_payload = [{"role": "system", "content": _SYSTEM_PROMPT}]
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
    conversation = await get_conversation_by_id(conversation_id)
    await conversation.fetch_related("messages")
    await add_message_to_conversation(
        conversation=conversation,
        message=query,
        speaker="user",
        user=user,
    )

    messages_payload = _build_messages_payload(conversation, query)
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
    conversation = await get_conversation_by_id(conversation_id)
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

    messages_payload = _build_messages_payload(
        conversation, query_text or "", image_description
    )
    payload = {"messages": messages_payload}

    async def event_generator():
        final_message = None
        try:
            async for event in main_agent.astream_events(payload, version="v2"):
                event_type = event.get("event")

                if event_type == "on_tool_start":
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"

                elif event_type == "on_tool_end":
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

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
                "image_key": msg.image_key,
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
    conversations = Conversation.filter(user=user).order_by("-updated_at")
    serialized_conversations = await PydListConversation.from_queryset(conversations)

    return jsonify(serialized_conversations.model_dump())
