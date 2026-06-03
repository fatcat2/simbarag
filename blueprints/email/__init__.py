import os
import hmac
import hashlib
import logging
import functools
import time
from collections import defaultdict

import httpx
from quart import Blueprint, request

from blueprints.users.models import User
from blueprints.conversation.logic import (
    get_conversation_for_channel,
    add_message_to_conversation,
)
from blueprints.conversation.agents import main_agent
from blueprints.conversation.prompts import SIMBA_SYSTEM_PROMPT
from . import models  # noqa: F401 — register Tortoise ORM models
from .helpers import generate_email_token, get_user_email_address  # noqa: F401

email_blueprint = Blueprint("email_api", __name__, url_prefix="/api/email")

logger = logging.getLogger(__name__)

# Rate limiting: per-sender message timestamps
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

RATE_LIMIT_MAX = int(os.getenv("EMAIL_RATE_LIMIT_MAX", "5"))
RATE_LIMIT_WINDOW = int(os.getenv("EMAIL_RATE_LIMIT_WINDOW", "300"))

MAX_MESSAGE_LENGTH = 2000


# --- Mailgun signature validation ---


def validate_mailgun_signature(f):
    """Decorator to validate Mailgun webhook signatures."""

    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        if os.getenv("MAILGUN_SIGNATURE_VALIDATION", "true").lower() == "false":
            return await f(*args, **kwargs)

        signing_key = os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY")
        if not signing_key:
            logger.error("MAILGUN_WEBHOOK_SIGNING_KEY not set — rejecting request")
            return "", 406

        form_data = await request.form
        timestamp = form_data.get("timestamp", "")
        token = form_data.get("token", "")
        signature = form_data.get("signature", "")

        if not timestamp or not token or not signature:
            logger.warning("Missing Mailgun signature fields")
            return "", 406

        expected = hmac.new(
            signing_key.encode(),
            f"{timestamp}{token}".encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            logger.warning("Invalid Mailgun signature")
            return "", 406

        return await f(*args, **kwargs)

    return decorated_function


# --- Rate limiting ---


def _check_rate_limit(sender: str) -> bool:
    """Check if a sender has exceeded the rate limit.

    Returns True if the request is allowed, False if rate-limited.
    """
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW

    timestamps = _rate_limit_store[sender]
    _rate_limit_store[sender] = [t for t in timestamps if t > cutoff]

    if len(_rate_limit_store[sender]) >= RATE_LIMIT_MAX:
        return False

    _rate_limit_store[sender].append(now)
    return True


# --- Send reply via Mailgun API ---


async def send_email_reply(
    to: str, subject: str, body: str, in_reply_to: str | None = None
):
    """Send a reply email via the Mailgun API."""
    api_key = os.getenv("MAILGUN_API_KEY")
    domain = os.getenv("MAILGUN_DOMAIN")
    if not api_key or not domain:
        logger.error("MAILGUN_API_KEY or MAILGUN_DOMAIN not configured")
        return

    data = {
        "from": f"Simba <simba@{domain}>",
        "to": to,
        "subject": f"Re: {subject}" if not subject.startswith("Re:") else subject,
        "text": body,
    }
    if in_reply_to:
        data["h:In-Reply-To"] = in_reply_to

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data=data,
        )
        if resp.status_code != 200:
            logger.error(f"Mailgun send failed ({resp.status_code}): {resp.text}")
        else:
            logger.info(f"Sent email reply to {to}")


# --- Webhook route ---


@email_blueprint.route("/webhook", methods=["POST"])
@validate_mailgun_signature
async def webhook():
    """Handle inbound emails forwarded by Mailgun."""
    form_data = await request.form
    sender = form_data.get("sender", "")
    recipient = form_data.get("recipient", "")
    body = form_data.get("stripped-text", "")
    subject = form_data.get("subject", "(no subject)")
    message_id = form_data.get("Message-Id", "")

    # Extract token from recipient: ask+<token>@domain
    local_part = recipient.split("@")[0] if "@" in recipient else ""
    if "+" not in local_part:
        logger.info(f"Ignoring email to {recipient} — no token in address")
        return "", 200

    token = local_part.split("+", 1)[1]

    # Lookup user by token
    user = await User.filter(email_hmac_token=token, email_enabled=True).first()
    if not user:
        logger.info(f"No user found for email token {token}")
        return "", 200

    # Rate limit
    if not _check_rate_limit(sender):
        logger.warning(f"Rate limit exceeded for email sender {sender}")
        return "", 200

    # Clean up body
    body = (body or "").strip()
    if not body:
        logger.info(f"Ignoring empty email from {sender}")
        return "", 200

    if len(body) > MAX_MESSAGE_LENGTH:
        body = body[:MAX_MESSAGE_LENGTH]
        logger.info(f"Truncated long email from {sender} to {MAX_MESSAGE_LENGTH} chars")

    logger.info(
        f"Processing email from {sender} for user {user.username}: {body[:100]}"
    )

    # Get or create conversation
    try:
        conversation = await get_conversation_for_channel(user=user, channel="email")
        await conversation.fetch_related("messages")
    except Exception as e:
        logger.error(f"Failed to get conversation for user {user.username}: {e}")
        return "", 200

    # Add user message
    await add_message_to_conversation(
        conversation=conversation,
        message=body,
        speaker="user",
        user=user,
    )

    # Build messages payload
    try:
        messages = await conversation.messages.all()
        recent_messages = list(messages)[-10:]

        messages_payload = [{"role": "system", "content": SIMBA_SYSTEM_PROMPT}]
        for msg in recent_messages[:-1]:
            role = "user" if msg.speaker == "user" else "assistant"
            messages_payload.append({"role": role, "content": msg.text})
        messages_payload.append({"role": "user", "content": body})

        logger.info(f"Invoking LangChain agent with {len(messages_payload)} messages")
        response = await main_agent.ainvoke({"messages": messages_payload})
        response_text = response.get("messages", [])[-1].content
    except Exception as e:
        logger.error(f"Error invoking agent for email: {e}")
        response_text = "Sorry, I'm having trouble thinking right now."

    # Save response
    await add_message_to_conversation(
        conversation=conversation,
        message=response_text,
        speaker="simba",
        user=user,
    )

    # Send reply email
    await send_email_reply(
        to=sender,
        subject=subject,
        body=response_text,
        in_reply_to=message_id,
    )

    return "", 200
