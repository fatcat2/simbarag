import enum
from dataclasses import dataclass

from tortoise import fields
from tortoise.contrib.pydantic import (
    pydantic_model_creator,
    pydantic_queryset_creator,
)
from tortoise.models import Model


@dataclass
class RenameConversationOutputSchema:
    title: str
    justification: str


class Speaker(enum.Enum):
    USER = "user"
    SIMBA = "simba"


class Conversation(Model):
    id = fields.UUIDField(primary_key=True)
    name = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User", related_name="conversations", null=True
    )

    class Meta:
        table = "conversations"


class ConversationMessage(Model):
    id = fields.UUIDField(primary_key=True)
    text = fields.TextField()
    conversation = fields.ForeignKeyField(
        "models.Conversation", related_name="messages"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    speaker = fields.CharEnumField(enum_type=Speaker, max_length=10)
    image_key = fields.CharField(max_length=512, null=True, default=None)

    class Meta:
        table = "conversation_messages"


PydConversationMessage = pydantic_model_creator(ConversationMessage)
PydConversation = pydantic_model_creator(
    Conversation, name="Conversation", allow_cycles=True, exclude=("user",)
)
PydConversationWithMessages = pydantic_model_creator(
    Conversation,
    name="ConversationWithMessages",
    allow_cycles=True,
    exclude=("user",),
    include=("messages",),
)
PydListConversation = pydantic_queryset_creator(Conversation)
PydListConversationMessage = pydantic_queryset_creator(ConversationMessage)
