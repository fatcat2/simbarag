import enum

from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import (
    pydantic_queryset_creator,
    pydantic_model_creator,
)


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

    class Meta:
        table = "conversation_messages"


PydConversationMessage = pydantic_model_creator(ConversationMessage)
PydConversation = pydantic_model_creator(Conversation, name="Conversation")
PydListConversationMessage = pydantic_queryset_creator(ConversationMessage)
