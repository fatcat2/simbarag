from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user_memories" (
    "id" UUID NOT NULL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        CREATE TABLE IF NOT EXISTS "email_accounts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email_address" VARCHAR(255) NOT NULL UNIQUE,
    "display_name" VARCHAR(255),
    "imap_host" VARCHAR(255) NOT NULL,
    "imap_port" INT NOT NULL DEFAULT 993,
    "imap_username" VARCHAR(255) NOT NULL,
    "imap_password" TEXT NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "last_error" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "email_accounts" IS 'Email account configuration for IMAP connections.';
        CREATE TABLE IF NOT EXISTS "emails" (
    "id" UUID NOT NULL PRIMARY KEY,
    "message_id" VARCHAR(255) NOT NULL UNIQUE,
    "subject" VARCHAR(500) NOT NULL,
    "from_address" VARCHAR(255) NOT NULL,
    "to_address" TEXT NOT NULL,
    "date" TIMESTAMPTZ NOT NULL,
    "body_text" TEXT,
    "body_html" TEXT,
    "chromadb_doc_id" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "account_id" UUID NOT NULL REFERENCES "email_accounts" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_emails_message_981ddd" ON "emails" ("message_id");
COMMENT ON TABLE "emails" IS 'Email message metadata and content.';
        CREATE TABLE IF NOT EXISTS "email_sync_status" (
    "id" UUID NOT NULL PRIMARY KEY,
    "last_sync_date" TIMESTAMPTZ,
    "last_message_uid" INT NOT NULL DEFAULT 0,
    "message_count" INT NOT NULL DEFAULT 0,
    "consecutive_failures" INT NOT NULL DEFAULT 0,
    "last_failure_date" TIMESTAMPTZ,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "account_id" UUID NOT NULL REFERENCES "email_accounts" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "email_sync_status" IS 'Tracks sync progress and state per email account.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "user_memories";
        DROP TABLE IF EXISTS "email_accounts";
        DROP TABLE IF EXISTS "emails";
        DROP TABLE IF EXISTS "email_sync_status";"""


MODELS_STATE = (
    "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"
)
