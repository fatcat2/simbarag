import enum

from tortoise import fields
from tortoise.models import Model


class MessageChannel(enum.Enum):
    IMESSAGE = "imessage"
    EMAIL = "email"


class MessageStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledMessage(Model):
    id = fields.UUIDField(primary_key=True)
    recipient = fields.CharField(max_length=255)
    channel = fields.CharEnumField(enum_type=MessageChannel, max_length=10)
    content = fields.TextField()
    subject = fields.CharField(max_length=255, null=True)
    scheduled_at = fields.DatetimeField()
    status = fields.CharEnumField(
        enum_type=MessageStatus, max_length=10, default=MessageStatus.PENDING
    )
    error_message = fields.TextField(null=True)
    created_by = fields.ForeignKeyField(
        "models.User", related_name="scheduled_messages"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "scheduled_messages"
