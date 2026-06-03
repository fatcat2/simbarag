import os
import hmac
import logging
import functools
import time
from collections import defaultdict

import httpx
from quart import Blueprint, request, jsonify

from blueprints.users.models import User
from blueprints.conversation.logic import (
    get_conversation_for_channel,
    add_message_to_conversation,
)
from blueprints.conversation.agents import main_agent
from blueprints.conversation.prompts import SIMBA_SYSTEM_PROMPT

imessage_blueprint = Blueprint("imessage_api", __name__, url_prefix="/api/imessage")

logger = logging.getLogger(__name__)

# Rate limiting: per-number message timestamps
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

RATE_LIMIT_MAX = int(os.getenv("IMESSAGE_RATE_LIMIT_MAX", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("IMESSAGE_RATE_LIMIT_WINDOW", "60"))

MAX_MESSAGE_LENGTH = 2000

SENDBLUE_API_BASE = "https://api.sendblue.co"


def _get_sendblue_headers() -> dict[str, str]:
    return {
        "sb-api-key-id": os.getenv("SENDBLUE_API_KEY", ""),
        "sb-api-secret-key": os.getenv("SENDBLUE_API_SECRET", ""),
        "Content-Type": "application/json",
    }


def _check_rate_limit(phone_number: str) -> bool:
    """Check if a phone number has exceeded the rate limit.

    Returns True if the request is allowed, False if rate-limited.
    """
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW

    timestamps = _rate_limit_store[phone_number]
    _rate_limit_store[phone_number] = [t for t in timestamps if t > cutoff]

    if len(_rate_limit_store[phone_number]) >= RATE_LIMIT_MAX:
        return False

    _rate_limit_store[phone_number].append(now)
    return True


async def send_imessage(to_number: str, content: str) -> dict:
    """Send an iMessage via SendBlue API."""
    from_number = os.getenv("SENDBLUE_FROM_NUMBER", "")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SENDBLUE_API_BASE}/api/send-message",
            headers=_get_sendblue_headers(),
            json={
                "number": to_number,
                "from_number": from_number,
                "content": content,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


def validate_sendblue_signature(f):
    """Decorator to validate the SendBlue webhook signing secret."""

    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        if os.getenv("SENDBLUE_SIGNATURE_VALIDATION", "true").lower() == "false":
            return await f(*args, **kwargs)

        secret = os.getenv("SENDBLUE_WEBHOOK_SECRET")
        if not secret:
            logger.error("SENDBLUE_WEBHOOK_SECRET not set — rejecting request")
            return jsonify({"error": "Server misconfigured"}), 500

        sig = request.headers.get("sb-signing-secret", "")
        if not hmac.compare_digest(sig, secret):
            logger.warning("Invalid SendBlue signing secret")
            return jsonify({"error": "Unauthorized"}), 403

        return await f(*args, **kwargs)

    return decorated_function


@imessage_blueprint.route("/webhook", methods=["POST"])
@validate_sendblue_signature
async def webhook():
    """Handle incoming iMessages from SendBlue."""
    data = await request.get_json()
    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    from_number = data.get("from_number")
    content = data.get("content")
    is_outbound = data.get("is_outbound", False)

    # Ignore outbound messages (our own replies echoed back)
    if is_outbound:
        return jsonify({"status": "ignored"}), 200

    if not from_number or not content:
        return jsonify({"error": "Missing from_number or content"}), 400

    content = content.strip()
    if not content:
        await send_imessage(
            from_number, "I received an empty message. Please send some text!"
        )
        return jsonify({"status": "ok"}), 200

    # Rate limiting
    if not _check_rate_limit(from_number):
        logger.warning(f"Rate limit exceeded for {from_number}")
        await send_imessage(
            from_number,
            "You're sending messages too quickly. Please wait a moment and try again.",
        )
        return jsonify({"status": "rate_limited"}), 200

    # Truncate overly long messages
    if len(content) > MAX_MESSAGE_LENGTH:
        content = content[:MAX_MESSAGE_LENGTH]
        logger.info(
            f"Truncated long message from {from_number} to {MAX_MESSAGE_LENGTH} chars"
        )

    logger.info(f"Received iMessage from {from_number}: {content[:100]}")

    # Identify or create user
    user = await User.filter(imessage_number=from_number).first()

    if not user:
        allowed_numbers = os.getenv("ALLOWED_IMESSAGE_NUMBERS", "").split(",")
        if from_number not in allowed_numbers and "*" not in allowed_numbers:
            await send_imessage(
                from_number, "Sorry, you are not authorized to use this service."
            )
            return jsonify({"status": "unauthorized"}), 200

        username = f"im_{from_number.lstrip('+')}"
        try:
            user = await User.create(
                username=username,
                email=f"{username}@imessage.simbarag.local",
                imessage_number=from_number,
                auth_provider="imessage",
            )
            logger.info(f"Created new user for iMessage: {username}")
        except Exception as e:
            logger.error(f"Failed to create user for {from_number}: {e}")
            await send_imessage(
                from_number, "Sorry, something went wrong setting up your account."
            )
            return jsonify({"status": "error"}), 200

    # iMessage is restricted to admins
    if not user.is_admin():
        logger.warning(f"Non-admin user {user.username} attempted iMessage access")
        await send_imessage(from_number, "Sorry, this feature is restricted to admins.")
        return jsonify({"status": "forbidden"}), 200

    # Get or create conversation
    try:
        conversation = await get_conversation_for_channel(user=user, channel="imessage")
        await conversation.fetch_related("messages")
    except Exception as e:
        logger.error(f"Failed to get conversation for user {user.username}: {e}")
        await send_imessage(
            from_number, "Sorry, something went wrong. Please try again later."
        )
        return jsonify({"status": "error"}), 200

    # Add user message to conversation
    await add_message_to_conversation(
        conversation=conversation,
        message=content,
        speaker="user",
        user=user,
    )

    # Build messages payload for LangChain agent
    try:
        messages = await conversation.messages.all()
        recent_messages = list(messages)[-10:]

        messages_payload = [{"role": "system", "content": SIMBA_SYSTEM_PROMPT}]

        for msg in recent_messages[:-1]:
            role = "user" if msg.speaker == "user" else "assistant"
            messages_payload.append({"role": role, "content": msg.text})

        messages_payload.append({"role": "user", "content": content})

        logger.info(f"Invoking LangChain agent with {len(messages_payload)} messages")
        response = await main_agent.ainvoke({"messages": messages_payload})
        response_text = response.get("messages", [])[-1].content

    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        response_text = "Sorry, I'm having trouble thinking right now."

    # Save and send response
    await add_message_to_conversation(
        conversation=conversation,
        message=response_text,
        speaker="simba",
        user=user,
    )

    await send_imessage(from_number, response_text)

    return jsonify({"status": "ok"}), 200
