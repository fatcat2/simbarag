import logging
from datetime import datetime, timezone

from quart import Blueprint, request, jsonify

from blueprints.users.decorators import admin_required
from .models import ScheduledMessage, MessageChannel, MessageStatus

scheduled_messages_blueprint = Blueprint(
    "scheduled_messages_api", __name__, url_prefix="/api/scheduled-messages"
)

logger = logging.getLogger(__name__)


def _serialize(msg: ScheduledMessage) -> dict:
    return {
        "id": str(msg.id),
        "recipient": msg.recipient,
        "channel": msg.channel.value,
        "content": msg.content,
        "subject": msg.subject,
        "scheduled_at": msg.scheduled_at.isoformat(),
        "status": msg.status.value,
        "error_message": msg.error_message,
        "created_at": msg.created_at.isoformat(),
        "updated_at": msg.updated_at.isoformat(),
    }


@scheduled_messages_blueprint.route("/", methods=["GET"])
@admin_required
async def list_messages():
    messages = await ScheduledMessage.all().order_by("-scheduled_at")
    return jsonify([_serialize(m) for m in messages])


@scheduled_messages_blueprint.route("/", methods=["POST"])
@admin_required
async def create_message():
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    recipient = (data.get("recipient") or "").strip()
    channel = data.get("channel")
    content = (data.get("content") or "").strip()
    subject = (data.get("subject") or "").strip() or None
    scheduled_at_str = data.get("scheduled_at")

    if not recipient or not channel or not content or not scheduled_at_str:
        return jsonify(
            {"error": "recipient, channel, content, and scheduled_at are required"}
        ), 400

    try:
        channel_enum = MessageChannel(channel)
    except ValueError:
        return jsonify(
            {"error": f"Invalid channel: {channel}. Must be 'imessage' or 'email'"}
        ), 400

    if channel_enum == MessageChannel.EMAIL and not subject:
        return jsonify({"error": "subject is required for email messages"}), 400

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str)
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    except ValueError:
        return jsonify({"error": "Invalid scheduled_at format"}), 400

    if scheduled_at <= datetime.now(timezone.utc):
        return jsonify({"error": "scheduled_at must be in the future"}), 400

    from quart_jwt_extended import get_jwt_identity

    user_id = get_jwt_identity()

    msg = await ScheduledMessage.create(
        recipient=recipient,
        channel=channel_enum,
        content=content,
        subject=subject,
        scheduled_at=scheduled_at,
        created_by_id=user_id,
    )
    return jsonify(_serialize(msg)), 201


@scheduled_messages_blueprint.route("/<msg_id>", methods=["PUT"])
@admin_required
async def update_message(msg_id: str):
    msg = await ScheduledMessage.get_or_none(id=msg_id)
    if not msg:
        return jsonify({"error": "Not found"}), 404

    if msg.status != MessageStatus.PENDING:
        return jsonify({"error": "Can only update pending messages"}), 400

    data = await request.get_json()
    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    if "recipient" in data:
        msg.recipient = data["recipient"].strip()
    if "channel" in data:
        try:
            msg.channel = MessageChannel(data["channel"])
        except ValueError:
            return jsonify({"error": f"Invalid channel: {data['channel']}"}), 400
    if "content" in data:
        msg.content = data["content"].strip()
    if "subject" in data:
        msg.subject = data["subject"].strip() or None
    if "scheduled_at" in data:
        try:
            scheduled_at = datetime.fromisoformat(data["scheduled_at"])
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            if scheduled_at <= datetime.now(timezone.utc):
                return jsonify({"error": "scheduled_at must be in the future"}), 400
            msg.scheduled_at = scheduled_at
        except ValueError:
            return jsonify({"error": "Invalid scheduled_at format"}), 400
    if "status" in data and data["status"] == "cancelled":
        msg.status = MessageStatus.CANCELLED

    if msg.channel == MessageChannel.EMAIL and not msg.subject:
        return jsonify({"error": "subject is required for email messages"}), 400

    await msg.save()
    return jsonify(_serialize(msg))


@scheduled_messages_blueprint.route("/<msg_id>", methods=["DELETE"])
@admin_required
async def delete_message(msg_id: str):
    msg = await ScheduledMessage.get_or_none(id=msg_id)
    if not msg:
        return jsonify({"error": "Not found"}), 404

    if msg.status not in (MessageStatus.PENDING, MessageStatus.CANCELLED):
        return jsonify({"error": "Can only delete pending or cancelled messages"}), 400

    await msg.delete()
    return jsonify({"status": "deleted"})
