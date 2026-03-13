from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "email_enabled" BOOL NOT NULL DEFAULT FALSE;
        ALTER TABLE "users" ADD "email_hmac_token" VARCHAR(16) UNIQUE;
        CREATE INDEX "idx_users_email_h_a1b2c3" ON "users" ("email_hmac_token");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_users_email_h_a1b2c3";
        ALTER TABLE "users" DROP COLUMN "email_hmac_token";
        ALTER TABLE "users" DROP COLUMN "email_enabled";"""
