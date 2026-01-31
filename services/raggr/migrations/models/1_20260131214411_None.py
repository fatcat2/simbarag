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
    "ldap_groups" JSONB NOT NULL,
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
    "eJztmm1v4jgQx78Kyquu1KtatnRX1emkQOkttwuceNinXhWZ2ICviZ1NnG1R1e9+tkmIkz"
    "gUKFDY401bxh5s/zzO/Mfpo+FSiJzgpEbJT+QHgGFKjMvSo0GAi/gf2vbjkgE8L2kVBgYG"
    "jnSwlZ6yBQwC5gOb8cYhcALETRAFto+9aDASOo4wUpt3xGSUmEKCf4TIYnSE2Bj5vOHmlp"
    "sxgegBBfFH784aYuTA1LwxFGNLu8UmnrT1+42ra9lTDDewbOqELkl6exM2pmTWPQwxPBE+"
    "om2ECPIBQ1BZhphltOzYNJ0xNzA/RLOpwsQA0RCEjoBh/D4MiS0YlORI4sf5H8YSeDhqgR"
    "YTJlg8Pk1XlaxZWg0xVO2D2Tl6e/FGrpIGbOTLRknEeJKOgIGpq+SagJS/cyhrY+DrUcb9"
    "MzD5RFfBGBsSjkkMxSBjQKtRM1zwYDmIjNiYfyxXKnMwfjY7kiTvJVFSHtfTqG9FTeVpm0"
    "CaILR9JJZsAZYHecVbGHaRHmbaM4MURq4n8R87CpivAbaJM4kOwRy+vUaz3u2Zzb/FStwg"
    "+OFIRGavLlrK0jrJWI8uMlsx+5LSl0bvQ0l8LH1vt+rZ2J/16303xJxAyKhF6L0FoHJeY2"
    "sMJrWxoQdX3Ni052FjX3Vjo8kr+xog31ougyguL0gj0dy2uImrJw2Reod32pwhYOThXVMf"
    "4RH5iCYSYYPPAxBblywi0dGPvmZXoSXWZBY+uJ+pETUo+Or4mhCbZk+zWzOv6oZkOAD23T"
    "3woVUA00VBAEYoyAOtRp7XHzvImUkzPUtVwDWn37ibT5UitpIVLVOFUYpevsktu1kLIHzd"
    "MBpbjDSHzjMqWIG4mBi21I08iOK9FsUMPWhSfo9b9Sjj/vsiiuel8vrXXiqLx9L3qGl+fZ"
    "PK5J/arT/j7opUrn1qVw8K+VcUUnmFHHgI3OnEgCgg6yR0c1IgtbuK+ysfHaPfrXcuSyKj"
    "/0O6jWbVvCwF2B0AY7EtTlWZZ6cLFJlnp4U1pmjKHCA10Sz3mNe4rvOZv6cS1s5ceL1Qym"
    "bvz3aW4rOaVhMuy2rbTSo5WTNopFtcSxRrNXG0D9ps/7WZ2MdlLy1Vn33RaFu4uPRAENxT"
    "XxOZVUyAP9HDVL0yMAcTNq1/drWk18GrCr2qyi2OrNpomZ1veskb91fjtvqtVzczdJELsL"
    "NMlM4c1hOiz5/4dQbo2eliomee6snJHoqhbQXh4F9kayqHYpJZv5WAZoN0uzw3cuC5lh9b"
    "nk9/Ylgk2vVAc47be4oaDrWB84I0lOZaWSRMK8VRWskFqQOBZ418GnqaO7y/uu2WHmnGLQ"
    "O0T/gqbyC22XHJwQG73Rjem9vNpHix8vkXCdk7g8wzVXzB4SLhf3KRcHjV9kts7OwmP1cQ"
    "PvcaJPd/Jet5F7LLYnS770BM5GN7bGhq56jleF71DJI+O1M+N0jBdby2ehaYM8EQ7fyrim"
    "j5Juq38tn5u/P3by/O3/MuciYzy7s5D4NGq/dMtSwOgvaKq1jrKS6HWjmRzvxoLCOYp933"
    "E+BGajk+IkNEk96LJbLi8lryeGO3DmuTx0tk2/Wnl6f/AHvgrXs="
)
