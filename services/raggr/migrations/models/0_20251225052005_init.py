from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" UUID NOT NULL PRIMARY KEY,
    "username" VARCHAR(255) NOT NULL,
    "password" BYTEA,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "oidc_subject" VARCHAR(255) UNIQUE,
    "auth_provider" VARCHAR(50) NOT NULL DEFAULT 'local',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_users_oidc_su_5aec5a" ON "users" ("oidc_subject");
CREATE TABLE IF NOT EXISTS "conversations" (
    "id" UUID NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" UUID REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "conversation_messages" (
    "id" UUID NOT NULL PRIMARY KEY,
    "text" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "speaker" VARCHAR(10) NOT NULL,
    "conversation_id" UUID NOT NULL REFERENCES "conversations" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "conversation_messages"."speaker" IS 'USER: user\nSIMBA: simba';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztmmtP4zgUhv9KlE+MxCLoUGaEViulpex0Z9qO2nR3LjuK3MRtvSROJnYGKsR/X9u5J0"
    "56AUqL+gXosU9sPz7OeY/Lveq4FrTJSdvFv6BPAEUuVi+VexUDB7I/pO3Higo8L23lBgom"
    "tnAwMz1FC5gQ6gOTssYpsAlkJgsS00deNBgObJsbXZN1RHiWmgKMfgbQoO4M0jn0WcP3H8"
    "yMsAXvIIk/ejfGFEHbys0bWXxsYTfowhO28bh7dS168uEmhunagYPT3t6Czl2cdA8CZJ1w"
    "H942gxj6gEIrsww+y2jZsSmcMTNQP4DJVK3UYMEpCGwOQ/19GmCTM1DESPzH+R/qGngYao"
    "4WYcpZ3D+Eq0rXLKwqH6r9QRsevb14I1bpEjrzRaMgoj4IR0BB6Cq4piDF7xLK9hz4cpRx"
    "/wJMNtFNMMaGlGMaQzHIGNBm1FQH3Bk2xDM6Zx8bzWYNxr+1oSDJegmULovrMOr7UVMjbO"
    "NIU4SmD/mSDUDLIK9YC0UOlMPMexaQWpHrSfzHjgJma7AG2F5Eh6CGr97tdUa61vvMV+IQ"
    "8tMWiDS9w1sawrooWI8uCluRPET5p6t/UPhH5dug3ynGftJP/6byOYGAugZ2bw1gZc5rbI"
    "3B5DY28KwNNzbvedjYF93YaPKZfSXQN9bLIBmXR6SRaG5b3MTNkwZPvdMbac7gMMrwrl0f"
    "ohn+CBcCYZfNA2BTliwi0TGOHrOr0FJrOgsf3CZqJBsUbHVsTZCG2VMbtbWrjioYToB5cw"
    "t8y6iA6UBCwAySMtBW5Hn9cQjtRJrJWWYFXC984m6+VarYClZuw80wytErNzkNp2gBmK3b"
    "isbmI9XQWaKCMxBXE8NGdiMPonivRTGFd5KUrzOrHGXcf19EcV0q73zRc1k8lr5HPe3Lm1"
    "wm/zTo/xl3z0jl9qdB66CQX6OQKitk4kFwIxMDvIDs4MApSYHc7mbcX/joqONRZ3ip8Iz+"
    "Lx51ey3tUiHImQB1tS3OVZlnpysUmWenlTUmbyocoGyiWe81L3F9ynf+nkpYs3Dh9UgpW7"
    "w/21mKSzWtJFzW1bbPqeREzSCRbnEtUa3V+NE+aLP912Z8H9e9tMz67ItG28LFpQcIuXV9"
    "SWS2EAb+Qg4z61WAOVnQsP7Z1ZJeBq/F9WpWbjFkrW5fG36VS964fzZuW1/1jlagCx2A7H"
    "WiNHF4mhBdfuKfMkDPTlcTPXWqpyR7XGSZBgkm/0FTUjlUkyz6bQS0GKTb5fksB55p+bnh"
    "+e4vZFWJdjnQkuP23qKq7ZrAfkQaynNtrhKmzeoobZa1+aG4fZ3F7eHrn1exscntcqlIWX"
    "Y1X/pfh6e5n99lgbTde3kN+sicq5J6Lmo5rqvoQNpnZ0q6Lq64IpZWdBxzIRiinX9RYSe+"
    "HfmtcXb+7vz924vz96yLmElieVfzMuj29SUVHD8I0muXav2RcTnUb6mcY0djHREXdt9PgM"
    "9SX7ARKcSS9P7XaNCvvE6NXQogx5gt8LuFTHqs2IjQH7uJtYYiX3X9dz/Fr3kKuZk/oCW7"
    "eN3mZeHD/9BpOYI="
)
