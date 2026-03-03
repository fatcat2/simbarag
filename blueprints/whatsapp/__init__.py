import os
import logging
import asyncio
import functools
import time
from collections import defaultdict
from quart import Blueprint, request, jsonify, abort
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from blueprints.users.models import User
from blueprints.conversation.logic import (
    get_conversation_for_user,
    add_message_to_conversation,
    get_conversation_transcript,
)
from blueprints.conversation.agents import main_agent

whatsapp_blueprint = Blueprint("whatsapp_api", __name__, url_prefix="/api/whatsapp")

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting: per-number message timestamps
# Format: {phone_number: [timestamp1, timestamp2, ...]}
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

# Configurable via env: max messages per window (default: 10 per 60s)
RATE_LIMIT_MAX = int(os.getenv("WHATSAPP_RATE_LIMIT_MAX", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("WHATSAPP_RATE_LIMIT_WINDOW", "60"))

# Max message length to process (WhatsApp max is 4096, but we cap for LLM sanity)
MAX_MESSAGE_LENGTH = 2000


def _twiml_response(text: str) -> tuple[str, int]:
    """Helper to return a TwiML MessagingResponse."""
    resp = MessagingResponse()
    resp.message(text)
    return str(resp), 200


def _check_rate_limit(phone_number: str) -> bool:
    """Check if a phone number has exceeded the rate limit.

    Returns True if the request is allowed, False if rate-limited.
    Also cleans up expired entries.
    """
    now = time.monotonic()
    cutoff = now - RATE_LIMIT_WINDOW

    # Remove expired timestamps
    timestamps = _rate_limit_store[phone_number]
    _rate_limit_store[phone_number] = [t for t in timestamps if t > cutoff]

    if len(_rate_limit_store[phone_number]) >= RATE_LIMIT_MAX:
        return False

    _rate_limit_store[phone_number].append(now)
    return True


def validate_twilio_request(f):
    """Decorator to validate that the request comes from Twilio.

    Validates the X-Twilio-Signature header using the TWILIO_AUTH_TOKEN.
    Set TWILIO_WEBHOOK_URL if behind a reverse proxy (e.g., ngrok, Caddy)
    so the validated URL matches what Twilio signed against.
    Set TWILIO_SIGNATURE_VALIDATION=false to disable in development.
    """
    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        if os.getenv("TWILIO_SIGNATURE_VALIDATION", "true").lower() == "false":
            return await f(*args, **kwargs)

        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not auth_token:
            logger.error("TWILIO_AUTH_TOKEN not set — rejecting request")
            abort(403)

        twilio_signature = request.headers.get("X-Twilio-Signature")
        if not twilio_signature:
            logger.warning("Missing X-Twilio-Signature header")
            abort(403)

        # Use configured webhook URL if behind a proxy, otherwise use request URL
        url = os.getenv("TWILIO_WEBHOOK_URL") or request.url
        form_data = await request.form

        validator = RequestValidator(auth_token)
        if not validator.validate(url, form_data, twilio_signature):
            logger.warning(f"Invalid Twilio signature for URL: {url}")
            abort(403)

        return await f(*args, **kwargs)
    return decorated_function


@whatsapp_blueprint.route("/webhook", methods=["POST"])
@validate_twilio_request
async def webhook():
    """
    Handle incoming WhatsApp messages from Twilio.
    """
    form_data = await request.form
    from_number = form_data.get("From") # e.g., "whatsapp:+1234567890"
    body = form_data.get("Body")

    if not from_number or not body:
        return _twiml_response("Invalid message received.") if from_number else ("Missing From or Body", 400)

    # Strip whitespace and check for empty body
    body = body.strip()
    if not body:
        return _twiml_response("I received an empty message. Please send some text!")

    # Rate limiting
    if not _check_rate_limit(from_number):
        logger.warning(f"Rate limit exceeded for {from_number}")
        return _twiml_response("You're sending messages too quickly. Please wait a moment and try again.")

    # Truncate overly long messages
    if len(body) > MAX_MESSAGE_LENGTH:
        body = body[:MAX_MESSAGE_LENGTH]
        logger.info(f"Truncated long message from {from_number} to {MAX_MESSAGE_LENGTH} chars")

    logger.info(f"Received WhatsApp message from {from_number}: {body[:100]}")

    # Identify or create user
    user = await User.filter(whatsapp_number=from_number).first()

    if not user:
        # Check if number is in allowlist
        allowed_numbers = os.getenv("ALLOWED_WHATSAPP_NUMBERS", "").split(",")
        if from_number not in allowed_numbers and "*" not in allowed_numbers:
            return _twiml_response("Sorry, you are not authorized to use this service.")

        # Create a new user for this WhatsApp number
        username = f"wa_{from_number.split(':')[-1]}"
        try:
            user = await User.create(
                username=username,
                email=f"{username}@whatsapp.simbarag.local",
                whatsapp_number=from_number,
                auth_provider="whatsapp"
            )
            logger.info(f"Created new user for WhatsApp: {username}")
        except Exception as e:
            logger.error(f"Failed to create user for {from_number}: {e}")
            return _twiml_response("Sorry, something went wrong setting up your account. Please try again later.")

    # Get or create a conversation for this user
    try:
        conversation = await get_conversation_for_user(user=user)
        await conversation.fetch_related("messages")
    except Exception as e:
        logger.error(f"Failed to get conversation for user {user.username}: {e}")
        return _twiml_response("Sorry, something went wrong. Please try again later.")

    # Add user message to conversation
    await add_message_to_conversation(
        conversation=conversation,
        message=body,
        speaker="user",
        user=user,
    )

    # Get transcript for context
    transcript = await get_conversation_transcript(user=user, conversation=conversation)

    # Build messages payload for LangChain agent with system prompt and conversation history
    try:
        # System prompt with Simba's facts and medical information
        system_prompt = """You are a helpful cat assistant named Simba that understands veterinary terms. When there are questions to you specifically, they are referring to Simba the cat. Answer the user in as if you were a cat named Simba. Don't act too catlike. Be assertive.

SIMBA FACTS (as of January 2026):
- Name: Simba
- Species: Feline (Domestic Short Hair / American Short Hair)
- Sex: Male, Neutered
- Date of Birth: August 8, 2016 (approximately 9 years 5 months old)
- Color: Orange
- Current Weight: 16 lbs (as of 1/8/2026)
- Owner: Ryan Chen
- Location: Long Island City, NY
- Veterinarian: Court Square Animal Hospital

Medical Conditions:
- Hypertrophic Cardiomyopathy (HCM): Diagnosed 12/11/2025. Concentric left ventricular hypertrophy with no left atrial dilation. Grade II-III/VI systolic heart murmur. No cardiac medications currently needed. Must avoid Domitor, acepromazine, and ketamine during anesthesia.
- Dental Issues: Prior extraction of teeth 307 and 407 due to resorption. Tooth 107 extracted on 1/8/2026. Early resorption lesions present on teeth 207, 309, and 409.

Recent Medical Events:
- 1/8/2026: Dental cleaning and tooth 107 extraction. Prescribed Onsior for 3 days. Oravet sealant applied.
- 12/11/2025: Echocardiogram confirming HCM diagnosis. Pre-op bloodwork was normal.
- 12/1/2025: Visited for decreased appetite/nausea. Received subcutaneous fluids and Cerenia.

Diet & Lifestyle:
- Diet: Hill's I/D wet and dry food
- Supplements: Plaque Off
- Indoor only cat, only pet in the household

Upcoming Appointments:
- Rabies Vaccine: Due 2/19/2026
- Routine Examination: Due 6/1/2026
- FVRCP-3yr Vaccine: Due 10/2/2026

IMPORTANT: When users ask factual questions about Simba's health, medical history, veterinary visits, medications, weight, or any information that would be in documents, you MUST use the simba_search tool to retrieve accurate information before answering. Do not rely on general knowledge - always search the documents for factual questions.

BUDGET & FINANCE (YNAB Integration):
You have access to Ryan's budget data through YNAB (You Need A Budget). When users ask about financial matters, use the appropriate YNAB tools:
- Use ynab_budget_summary for overall budget health and status questions
- Use ynab_search_transactions to find specific purchases or spending at particular stores
- Use ynab_category_spending to analyze spending by category for a month
- Use ynab_insights to provide spending trends, patterns, and recommendations
Always use these tools when asked about budgets, spending, transactions, or financial health."""

        # Get last 10 messages for conversation history
        messages = await conversation.messages.all()
        recent_messages = list(messages)[-10:]

        # Build messages payload
        messages_payload = [{"role": "system", "content": system_prompt}]

        # Add recent conversation history (exclude the message we just added)
        for msg in recent_messages[:-1]:
            role = "user" if msg.speaker == "user" else "assistant"
            messages_payload.append({"role": role, "content": msg.text})

        # Add current query
        messages_payload.append({"role": "user", "content": body})

        # Invoke LangChain agent
        logger.info(f"Invoking LangChain agent with {len(messages_payload)} messages")
        response = await main_agent.ainvoke({"messages": messages_payload})
        response_text = response.get("messages", [])[-1].content

        # Log YNAB availability
        if os.getenv("YNAB_ACCESS_TOKEN"):
            logger.info("YNAB integration is available for this conversation")
        else:
            logger.info("YNAB integration is not configured")

    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        response_text = "Sorry, I'm having trouble thinking right now. 😿"

    # Add Simba's response to conversation
    await add_message_to_conversation(
        conversation=conversation,
        message=response_text,
        speaker="simba",
        user=user,
    )

    return _twiml_response(response_text)
