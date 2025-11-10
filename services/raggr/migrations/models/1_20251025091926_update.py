from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- SQLite doesn't support ADD CONSTRAINT, so we need to recreate the table
        CREATE TABLE "conversations_new" (
            "id" CHAR(36) NOT NULL PRIMARY KEY,
            "name" VARCHAR(255) NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "user_id" CHAR(36),
            FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE
        );
        INSERT INTO "conversations_new" ("id", "name", "created_at", "updated_at")
        SELECT "id", "name", "created_at", "updated_at" FROM "conversations";
        DROP TABLE "conversations";
        ALTER TABLE "conversations_new" RENAME TO "conversations";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- Recreate table without user_id column
        CREATE TABLE "conversations_new" (
            "id" CHAR(36) NOT NULL PRIMARY KEY,
            "name" VARCHAR(255) NOT NULL,
            "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO "conversations_new" ("id", "name", "created_at", "updated_at")
        SELECT "id", "name", "created_at", "updated_at" FROM "conversations";
        DROP TABLE "conversations";
        ALTER TABLE "conversations_new" RENAME TO "conversations";"""


MODELS_STATE = (
    "eJztmWtP2zAUhv9KlE8gbQg6xhCaJqWlbB20ndp0F9gUuYnbWiROiJ1Bhfjvs91cnMRNKe"
    "PSon6B9vic2H5s57w+vdU934Eu2Wn4+C8MCaDIx/qRdqtj4EH2Qdn+RtNBEGSt3EDB0BUB"
    "tuQpWsCQ0BDYlDWOgEsgMzmQ2CEK4s5w5Lrc6NvMEeFxZoowuoqgRf0xpBMYsoaLP8yMsA"
    "NvIEm+BpfWCEHXyY0bObxvYbfoNBC2waB1fCI8eXdDy/bdyMOZdzClEx+n7lGEnB0ew9vG"
    "EMMQUOhI0+CjjKedmGYjZgYaRjAdqpMZHDgCkcth6B9HEbY5A030xP/sf9KXwMNQc7QIU8"
    "7i9m42q2zOwqrzrhpfjN7Wu4NtMUuf0HEoGgUR/U4EAgpmoYJrBlL8L6FsTECoRpn4F2Cy"
    "gT4EY2LIOGZ7KAGZAHoYNd0DN5YL8ZhO2Nfa+/cVGL8bPUGSeQmUPtvXs13fiZtqszaONE"
    "Noh5BP2QK0DPKYtVDkQTXMfGQBqROH7iQfVhQwm4PTxe40PgQVfM1Wu9k3jfY3PhOPkCtX"
    "IDLMJm+pCeu0YN06KCxF+hDtR8v8ovGv2nm30yzu/dTPPNf5mEBEfQv71xZwpPOaWBMwuY"
    "WNAueBC5uP3Czsiy5sPHhpXQkMreUyiBTyH2kkHtszLuLDkwZPvaNLZc7gMMrwTvwQojE+"
    "hVOBsMXGAbCtShax6BjEj1lVaJk1G0UIrlM1Im8KNjs2J0hn2dPoN4zjpi4YDoF9eQ1Cx5"
    "oD04OEgDEkZaD1OPLktAfdVJqpWcoCrj174mq+VeaxFaz8mi8xytErN3k1r2gBmM3bifvm"
    "PVXQWaCCJYj3E8OWvJAbUbzWopjCG0XKN5lVjTLxXxdRXJXKmz/NXBZPpO9W2/i5ncvkZ9"
    "3O58RdksqNs259o5Bfo5AqK2QSQHCpEgP8AtnEkVeSArnVlcJf+Ojog36zd6TxjP4b91vt"
    "unGkEeQNgX6/Jc7dMvd273HJ3Nude8fkTYUDJCea5V7zitDHfOevqYS1CwWv/5SyxfrZyl"
    "JcqGkV22VZbfuUSk7cGRTSLblLzNdq/GhvtNn6azO+jssWLeWYddFoz1C4DAAh136o2Jl1"
    "hEE4VcOUowowh1M6u/+sHs4KenUuWGW9xZjVWx2j90uteRN/eePWf5lNo4AXegC5y2zTNO"
    "Bx9ujiI/+YO3Rv936qp0r2lHXP5uLwOi8Om9L6q1jYtHJXEoCLyp6l35Efp/a5VvXkJ615"
    "GjBE9kRXaOW4pVItg8xnZeRyC88pvynVMsdc2Azxyr9ozhSV57e1vf0P+4fvDvYPmYsYSW"
    "r5UPEyaHXMBeqYHwTllXa+6pBCNto4BcmPxhIQY/f1BPg00s3HFGJFev/a73bmlqqSkALI"
    "AWYTvHCQTd9oLiL0z2piraDIZ11dVy+W0Au5mT+gripqPWch5u4f/FVgYA=="
)
