from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "conversations" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "conversation_messages" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "speaker" VARCHAR(10) NOT NULL /* USER: user\nSIMBA: simba */,
    "conversation_id" CHAR(36) NOT NULL REFERENCES "conversations" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" CHAR(36) NOT NULL PRIMARY KEY,
    "username" VARCHAR(255) NOT NULL,
    "password" BLOB NOT NULL,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmG1v4jgQx79KlFddaa9q2W53VZ1OCpTecrvACcLdPtwqMskAVhMnazvboorvfrbJE4"
    "kJpWq3UPGmhRkPtn8ztv/2nRmEHvjsuBWSn0AZ4jgk5oVxZxIUgPig9b82TBRFuVcaOBr7"
    "KsAttFQeNGacIpcL5wT5DITJA+ZSHCWdkdj3pTF0RUNMprkpJvhHDA4Pp8BnQIXj23dhxs"
    "SDW2Dp1+jamWDwvZVxY0/2rewOn0fKNhp1Lq9US9nd2HFDPw5I3jqa81lIsuZxjL1jGSN9"
    "UyBAEQevMA05ymTaqWk5YmHgNIZsqF5u8GCCYl/CMH+fxMSVDAzVk/xz9oe5BR6BWqLFhE"
    "sWd4vlrPI5K6spu2p9sAZHb85fqVmGjE+pcioi5kIFIo6WoYprDlL9r6BszRDVo0zbl2CK"
    "gT4EY2rIOeY1lIJMAT2MmhmgW8cHMuUz8bXx9m0Nxn+sgSIpWimUoajrZdX3Eldj6ZNIc4"
    "QuBTllB/EqyEvh4TgAPczVyBJSLwk9Tj/sKGAxB69P/HmyCGr42p1ue2hb3b/lTALGfvgK"
    "kWW3paehrPOS9ei8lIrsR4x/O/YHQ341vvZ77XLtZ+3sr6YcE4p56JDwxkFeYb2m1hTMSm"
    "LjyHtgYlcjD4l91sSqwcuTZHJd2AKlYYzc6xtEPWfFUzgdgTE0BVZNfzOJvPo4AD87NkuJ"
    "1hyu3eUv7mbGF2kZp9YivLARrqNXdQWNoGxBRMzbS/qWPdXQ2aBQChDvJ1ScYiIPgmWvBQ"
    "uHW812bAurHmXafl8ES9022/5sr+ywqSw56lqfX63ssp/6vT/T5gUZ0/rUbx7Uy0s85Krq"
    "hUWAroHqxX2bxIHKakfgQMSFSnYL4c+8dMzRsD24MGIG9D8y7HSb1oXBcDBG5gNuAKcn97"
    "gAnJ6s1f/SVVpAxYNmu21eE/qYe/6zblYbtviKHtMDrdK8CingKfkI80r9bpZfO02xoruE"
    "maKbTEzoykV8EJMEvlzY1rBlXbbNxXpt+5RKbsSUJKpIN2Wv1WpyaR+02f5rM5nHbR+Uij"
    "H7otF+waNShBi7CammMpuYIDrXwyxGlWCO53x5/9k9nDX0mlKwFvWWYNbs9KzBF73mTdsX"
    "C7f5xW5bJbwQIOxvU6ZZwOPU6OYl/5gVenpyP9VTJ3uquudwcXiZF4fDs+eLSOy2z55PKQ"
    "0toNid6cRh4qmVhyhvszP6sEPWvDdp5aHU9KVqTxL2rIeEemr9rXF69u7s/Zvzs/eiiRpJ"
    "ZnlXU/2dnr1BDsrLivYOt/6YLYQcxGAGUi6NLSAmzfcT4NNolZBwIJrz7K9hv7f2bSYNKY"
    "EcETHBbx52+WvDx4x/302sNRTlrOsfkstvxqXDSP5AU/eK8yuPl8X/Etg7Fw=="
)
