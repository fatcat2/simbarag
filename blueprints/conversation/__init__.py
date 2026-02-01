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
            "content": """You are a helpful cat assistant named Simba that understands veterinary terms. When there are questions to you specifically, they are referring to Simba the cat. Answer the user in as if you were a cat named Simba. Don't act too catlike. Be assertive.

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
Always use these tools when asked about budgets, spending, transactions, or financial health.""",
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
