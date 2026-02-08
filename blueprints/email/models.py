"""
Database models for email ingestion.

Provides EmailAccount, EmailSyncStatus, and Email models for storing
IMAP account configuration, sync tracking, and email metadata.
"""

from datetime import datetime, timedelta
from tortoise.models import Model
from tortoise import fields

from .crypto_service import EncryptedTextField


class EmailAccount(Model):
    """
    Email account configuration for IMAP connections.

    Stores account credentials with encrypted password, connection settings,
    and account status. Supports multiple accounts per user.
    """

    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="email_accounts")

    # Account identification
    email_address = fields.CharField(max_length=255, unique=True)
    display_name = fields.CharField(max_length=255, null=True)

    # IMAP connection settings
    imap_host = fields.CharField(max_length=255)  # e.g., imap.gmail.com
    imap_port = fields.IntField(default=993)
    imap_username = fields.CharField(max_length=255)
    imap_password = EncryptedTextField()  # Transparently encrypted

    # Account status
    is_active = fields.BooleanField(default=True)
    last_error = fields.TextField(null=True)

    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "email_accounts"


class EmailSyncStatus(Model):
    """
    Tracks sync progress and state per email account.

    Maintains last sync timestamp, last processed message UID,
    and failure tracking to support incremental sync and error handling.
    """

    id = fields.UUIDField(primary_key=True)
    account = fields.ForeignKeyField(
        "models.EmailAccount", related_name="sync_status", unique=True
    )

    # Sync state tracking
    last_sync_date = fields.DatetimeField(null=True)
    last_message_uid = fields.IntField(default=0)  # IMAP UID of last fetched message
    message_count = fields.IntField(default=0)  # Messages fetched in last sync

    # Error tracking
    consecutive_failures = fields.IntField(default=0)
    last_failure_date = fields.DatetimeField(null=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "email_sync_status"


class Email(Model):
    """
    Email message metadata and content.

    Stores parsed email data with 30-day retention. Links to ChromaDB
    for vector search capabilities.
    """

    id = fields.UUIDField(primary_key=True)
    account = fields.ForeignKeyField("models.EmailAccount", related_name="emails")

    # Email metadata (RFC822 headers)
    message_id = fields.CharField(
        max_length=255, unique=True, index=True
    )  # RFC822 Message-ID
    subject = fields.CharField(max_length=500)
    from_address = fields.CharField(max_length=255)
    to_address = fields.TextField()  # May contain multiple recipients
    date = fields.DatetimeField()

    # Email body content
    body_text = fields.TextField(null=True)  # Plain text version
    body_html = fields.TextField(null=True)  # HTML version

    # Vector store integration
    chromadb_doc_id = fields.CharField(
        max_length=255, null=True
    )  # Reference to ChromaDB document

    # Retention management
    created_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()  # Auto-set to created_at + 30 days

    class Meta:
        table = "emails"

    async def save(self, *args, **kwargs):
        """Override save to auto-set expiration date if not provided."""
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(days=30)
        await super().save(*args, **kwargs)
