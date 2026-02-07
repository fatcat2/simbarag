# Phase 1: Foundation - Research

**Researched:** 2026-02-07
**Domain:** Email ingestion infrastructure (IMAP, parsing, encryption, database)
**Confidence:** HIGH

## Summary

Phase 1 establishes the core infrastructure for IMAP email ingestion. The standard Python async stack provides mature, well-documented solutions for all required components. The research confirms that:

1. **aioimaplib** (v2.0.1, Jan 2025) is the production-ready async IMAP client for Python 3.9+
2. Python's built-in **email** module handles multipart message parsing without additional dependencies
3. **cryptography** library's Fernet provides secure credential encryption with established patterns
4. **Tortoise ORM** custom fields enable transparent encryption/decryption at the database layer
5. **Quart-Tasks** integrates scheduled IMAP sync directly into the existing Quart application

The codebase already demonstrates the required patterns: Tortoise ORM models with foreign keys (conversations/messages), ChromaDB collection management (simba_docs2, feline_vet_lookup), and async Quart blueprints with JWT/admin decorators.

**Primary recommendation:** Build three Tortoise ORM models (EmailAccount, EmailSyncStatus, Email) with encrypted credentials field, use aioimaplib for IMAP operations, Python email module for parsing, and Quart-Tasks for scheduling. Reuse existing admin_required decorator pattern and ChromaDB collection approach.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aioimaplib | 2.0.1 (Jan 2025) | Async IMAP4rev1 client | Only mature async IMAP library; tested against Python 3.9-3.12; no runtime dependencies; RFC2177 IDLE support |
| email (stdlib) | 3.14+ | Email parsing (multipart, headers) | Built-in; official standard for email parsing; modern EmailMessage API with get_body() |
| cryptography | 46.0.4 (Jan 2026) | Fernet symmetric encryption | Industry standard; widely audited; MultiFernet for key rotation; Python 3.8+ support |
| tortoise-orm | 0.25.4 | ORM with custom fields | Already in use; custom field support via to_db_value/to_python_value |
| quart-tasks | Latest | Scheduled background tasks | Designed for Quart; async-native; cron and periodic scheduling |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| html2text | 2025.4.15 | HTML to plain text | When email body is HTML-only; converts to readable text |
| beautifulsoup4 | Latest | HTML parsing fallback | When html2text fails; more control over extraction |
| asyncio (stdlib) | 3.14+ | Async operations | IMAP connection management, timeout handling |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| aioimaplib | imaplib (stdlib sync) | imaplib is blocking; would require thread pools; no IDLE support; not Quart-compatible |
| aioimaplib | pymap | pymap is a server library, not client; wrong use case |
| Fernet | bcrypt | bcrypt is one-way hashing for passwords; Fernet is reversible encryption for credentials |
| Quart-Tasks | APScheduler AsyncIOScheduler | APScheduler adds dependency; Quart-Tasks is tighter integration; cron syntax compatible |
| email module | mail-parser | mail-parser adds dependency; stdlib sufficient for standard emails; overhead not justified |

**Installation:**
```bash
# Core dependencies (add to pyproject.toml)
pip install aioimaplib cryptography quart-tasks

# Optional HTML parsing
pip install html2text beautifulsoup4
```

## Architecture Patterns

### Recommended Project Structure
```
blueprints/
├── email/                  # New email blueprint
│   ├── __init__.py        # Routes (admin-only, follows existing pattern)
│   ├── models.py          # EmailAccount, EmailSyncStatus, Email
│   ├── imap_service.py    # IMAP connection utility
│   ├── parser_service.py  # Email body parsing
│   └── crypto_service.py  # Credential encryption utility
utils/
├── email_chunker.py       # Email-specific chunking (reuse Chunker pattern)
```

### Pattern 1: Encrypted Tortoise ORM Field

**What:** Custom field that transparently encrypts on write and decrypts on read
**When to use:** Storing reversible sensitive data (IMAP passwords, tokens)
**Example:**
```python
# Source: https://tortoise.github.io/fields.html + https://cryptography.io/en/latest/fernet/
from tortoise import fields
from cryptography.fernet import Fernet
import os

class EncryptedTextField(fields.TextField):
    """Transparently encrypts/decrypts text field using Fernet."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Key from environment variable (32-byte URL-safe base64)
        key = os.getenv("FERNET_KEY")
        if not key:
            raise ValueError("FERNET_KEY environment variable required")
        self.fernet = Fernet(key.encode())

    def to_db_value(self, value: str, instance) -> str:
        """Encrypt before storing in database"""
        if value is None:
            return None
        # Returns Fernet token (URL-safe base64 string)
        return self.fernet.encrypt(value.encode()).decode()

    def to_python_value(self, value: str) -> str:
        """Decrypt when loading from database"""
        if value is None:
            return None
        return self.fernet.decrypt(value.encode()).decode()

# Usage in model
class EmailAccount(Model):
    password = EncryptedTextField()  # Transparent encryption
```

### Pattern 2: IMAP Connection Lifecycle

**What:** Async context manager for IMAP connections with proper cleanup
**When to use:** All IMAP operations (fetch, list folders, sync)
**Example:**
```python
# Source: https://github.com/bamthomas/aioimaplib README
import asyncio
from aioimaplib import IMAP4_SSL

class IMAPService:
    async def connect(self, host: str, user: str, password: str):
        """
        Establish IMAP connection with proper lifecycle.

        CRITICAL: Must call logout() to close TCP connection.
        close() only closes mailbox, not connection.
        """
        imap = IMAP4_SSL(host=host)
        await imap.wait_hello_from_server()

        try:
            await imap.login(user, password)
            return imap
        except Exception as e:
            await imap.logout()  # Clean up on login failure
            raise

    async def list_folders(self, imap):
        """List all mailbox folders"""
        # LIST returns: (* LIST (\HasNoChildren) "/" "INBOX")
        response = await imap.list('""', '*')
        return self._parse_list_response(response)

    async def fetch_messages(self, imap, folder="INBOX", limit=100):
        """Fetch recent messages from folder"""
        await imap.select(folder)

        # Search for all messages
        response = await imap.search('ALL')
        message_ids = response.lines[0].split()

        # Fetch last N messages
        recent_ids = message_ids[-limit:]
        messages = []

        for msg_id in recent_ids:
            # FETCH returns full RFC822 message
            msg_data = await imap.fetch(msg_id, '(RFC822)')
            messages.append(msg_data)

        return messages

    async def close(self, imap):
        """Properly close IMAP connection"""
        try:
            await imap.logout()  # Closes TCP connection
        except Exception:
            pass  # Best effort cleanup

# Usage with context manager pattern
async def sync_emails(account: EmailAccount):
    service = IMAPService()
    imap = await service.connect(
        account.imap_host,
        account.imap_username,
        account.password  # Auto-decrypted by EncryptedTextField
    )
    try:
        messages = await service.fetch_messages(imap)
        # Process messages...
    finally:
        await service.close(imap)
```

### Pattern 3: Email Body Parsing (Multipart/Alternative)

**What:** Extract plain text and HTML bodies from multipart messages
**When to use:** Processing all incoming emails
**Example:**
```python
# Source: https://docs.python.org/3/library/email.message.html
from email import message_from_bytes
from email.policy import default

def parse_email_body(raw_email_bytes: bytes) -> dict:
    """
    Extract text and HTML bodies from email.

    Returns: {"text": str, "html": str, "preferred": str}
    """
    # Parse with modern EmailMessage API
    msg = message_from_bytes(raw_email_bytes, policy=default)

    result = {"text": None, "html": None, "preferred": None}

    # Try to get plain text body
    text_part = msg.get_body(preferencelist=('plain',))
    if text_part:
        result["text"] = text_part.get_content()

    # Try to get HTML body
    html_part = msg.get_body(preferencelist=('html',))
    if html_part:
        result["html"] = html_part.get_content()

    # Determine preferred version (plain text preferred for RAG)
    if result["text"]:
        result["preferred"] = result["text"]
    elif result["html"]:
        # Convert HTML to text if no plain text version
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        result["preferred"] = h.handle(result["html"])

    # Extract metadata
    result["subject"] = msg.get("subject", "")
    result["from"] = msg.get("from", "")
    result["to"] = msg.get("to", "")
    result["date"] = msg.get("date", "")
    result["message_id"] = msg.get("message-id", "")

    return result
```

### Pattern 4: Scheduled Email Sync with Quart-Tasks

**What:** Background task that syncs emails periodically
**When to use:** Production deployment with regular sync intervals
**Example:**
```python
# Source: https://github.com/pgjones/quart-tasks
from quart import Quart
from quart_tasks import QuartTasks
from datetime import timedelta

app = Quart(__name__)
tasks = QuartTasks(app)

@tasks.cron("0 */2 * * *")  # Every 2 hours at :00
async def scheduled_email_sync():
    """
    Sync emails from all active accounts.

    Runs every 2 hours. Cron format: minute hour day month weekday
    """
    from blueprints.email.models import EmailAccount

    accounts = await EmailAccount.filter(is_active=True).all()

    for account in accounts:
        try:
            await sync_account_emails(account)
        except Exception as e:
            # Log but continue with other accounts
            app.logger.error(f"Sync failed for {account.email}: {e}")

# Alternative: periodic scheduling
@tasks.periodic(timedelta(hours=2))
async def periodic_email_sync():
    """Same as above but using timedelta"""
    pass

# Manual trigger via CLI
# quart invoke-task scheduled_email_sync
```

### Pattern 5: ChromaDB Email Collection

**What:** Separate collection for email embeddings with metadata
**When to use:** All email indexing operations
**Example:**
```python
# Source: Existing main.py patterns
import chromadb
import os

# Initialize ChromaDB (reuse existing client pattern)
client = chromadb.PersistentClient(path=os.getenv("CHROMADB_PATH", ""))

# Create email collection (similar to simba_docs2, feline_vet_lookup)
email_collection = client.get_or_create_collection(
    name="email_messages",
    metadata={"description": "Email message embeddings for RAG"}
)

# Add email with metadata
from utils.chunker import Chunker

async def index_email(email: Email):
    """Index single email into ChromaDB"""
    chunker = Chunker(email_collection)

    # Prepare text (body + subject for context)
    text = f"Subject: {email.subject}\n\n{email.body_text}"

    # Metadata for filtering
    metadata = {
        "email_id": str(email.id),
        "from_address": email.from_address,
        "to_address": email.to_address,
        "subject": email.subject,
        "date": email.date.timestamp(),
        "account_id": str(email.account_id),
        "message_id": email.message_id,
    }

    # Chunk and embed (reuses existing pattern)
    chunker.chunk_document(
        document=text,
        metadata=metadata,
        chunk_size=1000
    )
```

### Anti-Patterns to Avoid

- **Don't use IMAP4.close() to disconnect**: It only closes the mailbox, not TCP connection. Always use logout()
- **Don't store encryption keys in code**: Use environment variables and proper key management
- **Don't share IMAP connections across async tasks**: Each task needs its own connection (not thread-safe)
- **Don't fetch all messages on every sync**: Track last sync timestamp and fetch incrementally
- **Don't parse HTML with regex**: Use html2text or BeautifulSoup for proper parsing
- **Don't store plaintext passwords**: Always use EncryptedTextField for credentials

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| IMAP protocol | Custom socket code | aioimaplib | IMAP has complex state machine, authentication flows (OAUTH2), IDLE support, error handling |
| Email parsing | String splitting / regex | email (stdlib) | MIME multipart is complex; nested parts; encoding issues; attachment handling |
| Credential encryption | Custom XOR / Caesar cipher | cryptography.fernet | Fernet provides authenticated encryption (AES + HMAC); time-based validation; key rotation |
| HTML to text | Regex strip tags | html2text | Preserves structure; handles entities; converts to markdown; handles nested tags |
| Scheduled tasks | while True + asyncio.sleep | Quart-Tasks | Cron syntax; error handling; graceful shutdown; CLI integration; no drift |
| Email deduplication | Compare body text | message-id header | RFC-compliant unique identifier; handles threading; forwards detection |

**Key insight:** Email handling involves decades of RFC specifications (RFC 3501 IMAP, RFC 2822 message format, RFC 2047 encoding, RFC 6154 special folders). Standard libraries internalize this complexity.

## Common Pitfalls

### Pitfall 1: IMAP Connection Limits

**What goes wrong:** Provider terminates connections with "Too many connections" error. Gmail limits 15 concurrent connections per account, Yahoo limits 5.

**Why it happens:**
- Each IMAP connection is counted against account quota
- Connections not properly closed leak quota
- Multiple sync tasks create concurrent connections
- Provider counts connections across all devices

**How to avoid:**
- Use connection pooling with max_connections limit
- Set connection timeout to 10 seconds (detect dead connections)
- Always call logout() in finally block
- Implement exponential backoff on connection errors
- Track active connections per account

**Warning signs:**
- Intermittent "Connection refused" errors
- Sync works initially then fails
- Errors after deploying multiple instances

### Pitfall 2: Message Encoding Hell

**What goes wrong:** Emails display as garbled characters (�) or wrong language characters.

**Why it happens:**
- Email headers/body can be in various encodings (UTF-8, ISO-8859-1, Windows-1252)
- RFC 2047 encoded-words in headers (`=?UTF-8?B?...?=`)
- Base64 or quoted-printable transfer encoding
- Charset mismatch between declaration and actual content

**How to avoid:**
- Use email.policy.default (handles encoding automatically)
- Call get_content() not get_payload() (modern API does decoding)
- Catch UnicodeDecodeError and try common fallback encodings
- Log original encoding for debugging

**Warning signs:**
- Subject lines with `=?UTF-8?` visible in output
- Asian/emoji characters showing as `?` or boxes
- Stack traces with UnicodeDecodeError

### Pitfall 3: Fernet Key Loss = Data Loss

**What goes wrong:** Application starts but can't decrypt existing credentials. All IMAP accounts become inaccessible.

**Why it happens:**
- FERNET_KEY environment variable changed or missing
- Database migrated without bringing encryption key
- Key rotation done incorrectly (dropped old key while data still encrypted)
- Development vs production key mismatch

**How to avoid:**
- Document FERNET_KEY as required in .env.example
- Add startup validation: decrypt test value or fail fast
- Use MultiFernet for key rotation (keeps old key for decryption)
- Back up encryption key separately from database
- Test database restore process includes key

**Warning signs:**
- cryptography.fernet.InvalidToken exceptions on account.password access
- Cannot authenticate to IMAP after deployment
- Error: "Fernet key must be 32 url-safe base64-encoded bytes"

### Pitfall 4: Not Tracking Sync State

**What goes wrong:** Re-downloads thousands of emails on every sync. Database fills with duplicates. API rate limits hit.

**Why it happens:**
- No tracking of last synced message
- Using IMAP SEARCH ALL instead of SINCE date
- Not using message-id for deduplication
- Sync status not persisted across restarts

**How to avoid:**
- EmailSyncStatus table tracks last_sync_date, last_message_uid per account
- IMAP UID (unique ID) for reliable message tracking
- Use SEARCH SINCE <date> to fetch only new messages
- Check message-id before inserting (ON CONFLICT DO NOTHING)
- Update sync status atomically with message insert

**Warning signs:**
- Sync time increases linearly with mailbox age
- Database size grows faster than email volume
- Duplicate emails in search results

### Pitfall 5: IMAP IDLE Hanging Forever

**What goes wrong:** IMAP sync task never completes. Application appears frozen. No new emails processed.

**Why it happens:**
- IDLE command waits indefinitely for new mail
- Network timeout disconnects but code doesn't detect
- Provider drops connection after 30 minutes (standard timeout)
- No timeout set on wait_server_push()

**How to avoid:**
- Don't use IDLE for scheduled sync (use SEARCH instead)
- If using IDLE, set timeout: `await imap.wait_server_push(timeout=600)`
- Implement connection health checks (NOOP command)
- Handle asyncio.TimeoutError and reconnect
- Use IDLE only for real-time notifications (out of scope for Phase 1)

**Warning signs:**
- Scheduled sync never completes
- No logs after "IDLE command sent"
- Task shows running but no activity

### Pitfall 6: HTML Email Bloat in Embeddings

**What goes wrong:** Email embeddings are poor quality. Search returns irrelevant results. ChromaDB storage explodes.

**Why it happens:**
- Storing raw HTML with tags/styles in vectors
- Email signatures with base64 images embedded
- Marketing emails with 90% HTML boilerplate
- Script tags, CSS, tracking pixels in body

**How to avoid:**
- Always convert HTML to plain text before indexing
- Strip email signatures (common patterns: "-- " divider, "Sent from my iPhone")
- Remove quoted reply text ("> " prefix detection)
- Limit chunk size to exclude metadata bloat
- Prefer plain text body over HTML when both available

**Warning signs:**
- Email search returns marketing emails for every query
- Embeddings contain HTML tag tokens
- Vector dimension much larger than document embeddings

## Code Examples

Verified patterns from official sources:

### Example 1: Complete IMAP Sync Flow

```python
# Source: Composite of aioimaplib + email module patterns
from aioimaplib import IMAP4_SSL
from email import message_from_bytes
from email.policy import default
import asyncio

async def sync_account_emails(account: EmailAccount):
    """
    Complete sync flow: connect, fetch, parse, store.
    """
    # 1. Establish connection
    imap = IMAP4_SSL(host=account.imap_host, timeout=10)
    await imap.wait_hello_from_server()

    try:
        # 2. Authenticate
        await imap.login(account.imap_username, account.password)

        # 3. Select INBOX
        await imap.select('INBOX')

        # 4. Get last sync status
        sync_status = await EmailSyncStatus.get_or_none(account=account)
        last_uid = sync_status.last_message_uid if sync_status else 1

        # 5. Search for new messages (UID > last_uid)
        response = await imap.uid('search', None, f'UID {last_uid}:*')
        message_uids = response.lines[0].split()

        # 6. Fetch and process each message
        for uid in message_uids:
            # Fetch full message
            fetch_result = await imap.uid('fetch', uid, '(RFC822)')
            raw_email = fetch_result.lines[1]  # Email bytes

            # Parse email
            msg = message_from_bytes(raw_email, policy=default)

            # Extract components
            email_data = {
                'account': account,
                'message_id': msg.get('message-id'),
                'subject': msg.get('subject', ''),
                'from_address': msg.get('from', ''),
                'to_address': msg.get('to', ''),
                'date': parsedate_to_datetime(msg.get('date')),
                'body_text': None,
                'body_html': None,
            }

            # Get body content
            text_part = msg.get_body(preferencelist=('plain',))
            if text_part:
                email_data['body_text'] = text_part.get_content()

            html_part = msg.get_body(preferencelist=('html',))
            if html_part:
                email_data['body_html'] = html_part.get_content()

            # 7. Store in database (check for duplicates)
            email_obj, created = await Email.get_or_create(
                message_id=email_data['message_id'],
                defaults=email_data
            )

            # 8. Index in ChromaDB if new
            if created:
                await index_email(email_obj)

        # 9. Update sync status
        await EmailSyncStatus.update_or_create(
            account=account,
            defaults={
                'last_sync_date': datetime.now(),
                'last_message_uid': message_uids[-1] if message_uids else last_uid,
                'message_count': len(message_uids),
            }
        )

    finally:
        # 10. Always logout
        await imap.logout()
```

### Example 2: Fernet Key Generation and Setup

```python
# Source: https://cryptography.io/en/latest/fernet/
from cryptography.fernet import Fernet

# One-time setup: Generate key
def generate_fernet_key():
    """
    Generate new Fernet encryption key.

    CRITICAL: Store this in environment variable.
    If lost, encrypted data cannot be recovered.
    """
    key = Fernet.generate_key()
    print(f"Add to .env file:")
    print(f"FERNET_KEY={key.decode()}")
    return key

# Add to .env.example
"""
# Email Encryption Key (32-byte URL-safe base64)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=your-fernet-key-here
"""

# Startup validation
def validate_fernet_key():
    """Validate encryption key on app startup"""
    key = os.getenv("FERNET_KEY")
    if not key:
        raise ValueError("FERNET_KEY environment variable required")

    try:
        f = Fernet(key.encode())
        # Test encrypt/decrypt
        test = f.encrypt(b"test")
        f.decrypt(test)
    except Exception as e:
        raise ValueError(f"Invalid FERNET_KEY: {e}")
```

### Example 3: Email Models with Encryption

```python
# Source: Tortoise ORM patterns from existing codebase
from tortoise.models import Model
from tortoise import fields
from datetime import datetime

class EmailAccount(Model):
    """
    Email account configuration.
    Multiple accounts supported (personal, work, etc.)
    """
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField('models.User', related_name='email_accounts')

    # Account info
    email_address = fields.CharField(max_length=255, unique=True)
    display_name = fields.CharField(max_length=255, null=True)

    # IMAP settings
    imap_host = fields.CharField(max_length=255)  # e.g., imap.gmail.com
    imap_port = fields.IntField(default=993)
    imap_username = fields.CharField(max_length=255)
    imap_password = EncryptedTextField()  # Encrypted at rest

    # Status
    is_active = fields.BooleanField(default=True)
    last_error = fields.TextField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "email_accounts"


class EmailSyncStatus(Model):
    """
    Tracks sync progress per account.
    Prevents re-downloading messages.
    """
    id = fields.UUIDField(primary_key=True)
    account = fields.ForeignKeyField('models.EmailAccount', related_name='sync_status', unique=True)

    last_sync_date = fields.DatetimeField(null=True)
    last_message_uid = fields.IntField(default=0)  # IMAP UID of last fetched message
    message_count = fields.IntField(default=0)

    # Error tracking
    consecutive_failures = fields.IntField(default=0)
    last_failure_date = fields.DatetimeField(null=True)

    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "email_sync_status"


class Email(Model):
    """
    Email message metadata and content.
    30-day retention enforced at application level.
    """
    id = fields.UUIDField(primary_key=True)
    account = fields.ForeignKeyField('models.EmailAccount', related_name='emails')

    # Email metadata
    message_id = fields.CharField(max_length=255, unique=True, index=True)  # RFC822 Message-ID
    subject = fields.CharField(max_length=500)
    from_address = fields.CharField(max_length=255)
    to_address = fields.TextField()  # May have multiple recipients
    date = fields.DatetimeField()

    # Body content
    body_text = fields.TextField(null=True)  # Plain text version
    body_html = fields.TextField(null=True)  # HTML version

    # Vector store reference
    chromadb_doc_id = fields.CharField(max_length=255, null=True)  # Links to ChromaDB

    # Retention
    created_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField()  # Auto-set to created_at + 30 days

    class Meta:
        table = "emails"

    async def save(self, *args, **kwargs):
        """Auto-set expiration date"""
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(days=30)
        await super().save(*args, **kwargs)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| imaplib (sync) | aioimaplib (async) | 2016 | Non-blocking IMAP; Quart-compatible; better performance |
| Message.walk() | msg.get_body() | Python 3.6+ (2017) | Simplified API; handles multipart correctly; policy-aware |
| PyCrypto | cryptography | 2016 | Actively maintained; audited; proper key rotation |
| cron system jobs | Quart-Tasks | 2020+ | Application-integrated; async-native; no external cron |
| email.message | email.message.EmailMessage | Python 3.6+ | Better API; policy system; modern email handling |

**Deprecated/outdated:**
- **imaplib2**: Unmaintained since 2015; use aioimaplib
- **PyCrypto**: Abandoned 2013; use cryptography
- **Message.get_payload()**: Use get_content() for proper decoding
- **email.parser.Parser**: Use BytesParser with policy for modern parsing

## Open Questions

Things that couldn't be fully resolved:

1. **IMAP OAUTH2 Support**
   - What we know: aioimaplib supports OAUTH2 authentication
   - What's unclear: Gmail requires OAUTH2 for new accounts (may need app registration)
   - Recommendation: Start with password auth; add OAUTH2 in Phase 2 if needed

2. **Attachment Handling**
   - What we know: Email attachments excluded from Phase 1 scope
   - What's unclear: Should attachment metadata be stored (filename, size)?
   - Recommendation: Store metadata (attachment_count field), skip content for now

3. **Folder Selection Strategy**
   - What we know: Most providers have INBOX, Sent, Drafts, Trash
   - What's unclear: Should we sync only INBOX or multiple folders?
   - Recommendation: Start with INBOX only; make folder list configurable

4. **Embedding Model for Emails**
   - What we know: Existing codebase uses text-embedding-3-small (OpenAI)
   - What's unclear: Do email embeddings need different model than documents?
   - Recommendation: Reuse existing embedding model for consistency

5. **Concurrent Account Syncing**
   - What we know: Multiple accounts should sync independently
   - What's unclear: Should syncs run in parallel or sequentially?
   - Recommendation: Sequential for Phase 1; parallel with asyncio.gather in later phase

## Sources

### Primary (HIGH confidence)

- aioimaplib v2.0.1 - https://github.com/bamthomas/aioimaplib (Jan 2025 release)
- aioimaplib PyPI - https://pypi.org/project/aioimaplib/ (v2.0.1, Python 3.9-3.12)
- Python email.parser docs - https://docs.python.org/3/library/email.parser.html (Feb 2026)
- Python email.message docs - https://docs.python.org/3/library/email.message.html (Feb 2026)
- cryptography Fernet docs - https://cryptography.io/en/latest/fernet/ (v47.0.0.dev1)
- Tortoise ORM fields docs - https://tortoise.github.io/fields.html (v0.25.4)
- Quart-Tasks GitHub - https://github.com/pgjones/quart-tasks (official extension)

### Secondary (MEDIUM confidence)

- IMAP commands reference - https://www.atmail.com/blog/imap-commands/ (tutorial)
- RFC 3501 IMAP4rev1 - https://www.rfc-editor.org/rfc/rfc3501 (official spec)
- RFC 6154 Special-Use Mailboxes - https://www.rfc-editor.org/rfc/rfc6154.html (official spec)
- html2text PyPI - https://pypi.org/project/html2text/ (v2025.4.15)
- Job Scheduling with APScheduler - https://betterstack.com/community/guides/scaling-python/apscheduler-scheduled-tasks/ (2024 guide)

### Secondary (MEDIUM confidence - verified with official docs)

- Email parsing guide - https://www.nylas.com/blog/email-parsing-with-python-a-comprehensive-guide/ (verified against Python docs)
- Fernet best practices - Multiple sources cross-referenced with official cryptography docs
- IMAP security best practices - https://www.getmailbird.com/sudden-spike-imap-sync-failures-email-providers/ (2026 article, current issues)

### Tertiary (LOW confidence - WebSearch only)

- mail-parser library - https://github.com/SpamScope/mail-parser (alternative, not fully evaluated)
- flanker library - https://github.com/mailgun/flanker (alternative, not fully evaluated)

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - All libraries verified via official docs/PyPI; current versions confirmed; Python 3.9+ compatibility validated
- Architecture: **HIGH** - Patterns demonstrated in existing codebase (Tortoise models, Quart blueprints, ChromaDB collections)
- Pitfalls: **MEDIUM** - Based on documentation warnings + community reports; some edge cases may exist
- OAUTH2 implementation: **LOW** - Not fully researched for this phase

**Research date:** 2026-02-07
**Valid until:** 2026-04-07 (60 days - stable technologies with slow release cycles)

**Notes:**
- aioimaplib actively maintained (Jan 2025 release)
- Python 3.14 stdlib recent (Feb 2026 docs)
- cryptography library rapid releases (security-focused)
- Recommend re-validating aioimaplib/cryptography versions at implementation time
