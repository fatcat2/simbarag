from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "email_accounts" (
    "id" UUID NOT NULL PRIMARY KEY,
    "email_address" VARCHAR(255) NOT NULL UNIQUE,
    "display_name" VARCHAR(255),
    "imap_host" VARCHAR(255) NOT NULL,
    "imap_port" INT NOT NULL DEFAULT 993,
    "imap_username" VARCHAR(255) NOT NULL,
    "imap_password" TEXT NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT TRUE,
    "last_error" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "email_sync_status" (
    "id" UUID NOT NULL PRIMARY KEY,
    "last_sync_date" TIMESTAMPTZ,
    "last_message_uid" INT NOT NULL DEFAULT 0,
    "message_count" INT NOT NULL DEFAULT 0,
    "consecutive_failures" INT NOT NULL DEFAULT 0,
    "last_failure_date" TIMESTAMPTZ,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "account_id" UUID NOT NULL UNIQUE REFERENCES "email_accounts" ("id") ON DELETE CASCADE
);
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
CREATE INDEX IF NOT EXISTS "idx_emails_message_9e3c0c" ON "emails" ("message_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "emails";
        DROP TABLE IF EXISTS "email_sync_status";
        DROP TABLE IF EXISTS "email_accounts";"""


MODELS_STATE = ""
