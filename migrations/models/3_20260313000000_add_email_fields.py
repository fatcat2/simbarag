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


MODELS_STATE = (
    "eJztmm1v4jgQx78Kyquu1KtaKN1VdTopUHrLbYEThX3qVZFJXMg1sbOJsxRV/e5nm4Q4jg"
    "OEAoU93rRl7CH2z2PP35M+ay62oBOc1DH6Cf0AEBsj7bL0rCHgQvqHsv24pAHPS1qZgYCB"
    "wx1MoSdvAYOA+MAktPEBOAGkJgsGpm970cNQ6DjMiE3a0UbDxBQi+0cIDYKHkIygTxvu7q"
    "nZRhZ8gkH80Xs0HmzoWKlx2xZ7NrcbZOJxW7/fvLrmPdnjBoaJndBFSW9vQkYYzbqHoW2d"
    "MB/WNoQI+oBAS5gGG2U07dg0HTE1ED+Es6FaicGCDyB0GAzt94cQmYxBiT+J/Tj/QyuAh6"
    "JmaG1EGIvnl+mskjlzq8YeVf+od48qF+/4LHFAhj5v5ES0F+4ICJi6cq4JSP47g7I+Ar4a"
    "ZdxfgkkHugrG2JBwTGIoBhkDWo2a5oInw4FoSEb0Y7lanYPxs97lJGkvjhLTuJ5GfTtqKk"
    "/bGNIEoelDNmUDkCzIK9pCbBeqYaY9JaRW5HoS/7GjgOkcrA5yJtEmmMO312w1bnt66282"
    "EzcIfjgckd5rsJYyt04k69GFtBSzLyl9afY+ltjH0vdOuyHH/qxf77vGxgRCgg2ExwawhP"
    "0aW2MwqYUNPWvFhU17Hhb2TRc2GrywrgH0jWIZRHB5RRqJxrbFRVw9abDU+/CozBkMRhbe"
    "NfahPUSf4IQjbNJxAGSqkkUkOvrR1+wqtMSajMIH45kaEYOCzo7OCZJp9tRv6/pVQ+MMB8"
    "B8HAPfMnJgujAIwBAGWaC1yPP6Uxc6M2mmZikKuNb0G3fzVMljy1nhMhYYpehlm9yyK1sA"
    "ovO2omezJ82hs0AFCxCXE8OGuJAHUbzXopjAJ0XK71GrGmXcf19E8bxU3vjaS2XxWPoetf"
    "Sv71KZ/KbT/jPuLkjl+k2ndlDIv6KQyirkwIPgUSUG2AWygUI3IwVSqyu4v/HW0fq3je5l"
    "iWX0f9Bts1XTL0uB7Q6AttwSp26ZZ6dLXDLPTnPvmKxJ2kBioil2zCtc13nm76mENaWC1y"
    "ulrFw/21mKCzWtIlyKattNKjl+Z1BIt/guka/V2NY+aLP912ZsHYsWLUWffdFoWyhceiAI"
    "xthXRGbNRsCfqGGKXhLMwYRM7z+7eqVXwasxvSrKLYqs1mzr3W9qyRv3F+O29q3X0CW60A"
    "W2UyRKZw7rCdHFO36dAXp2upzomad6MrJnPAIkoEe6QZXkIE9mqmEqXFfCKofqdqlWloFa"
    "yWdaySDlQWZAxKan2vgYOxCgOQEq+srbnzpv6jAtmqoL7P9O5ya1/2tN+Urbb9UaNHg5Zt"
    "rJnkqhZrunhDtygUk1wiNUKMsFu1/y3cOIPbtY5hiQr6zCKXAhRyy2LdMIwsG/0FSUD/KB"
    "yn57CHMjWZ9e6EeG5+OftlXsSM04bk9KaQ42gfMKLZrmWl3mWK3mH6vVzLHqWMAzhj4OPU"
    "Uh/6/bTluNVHKTgPYRneWdZZvkuOTYAbnfGN67+83ofDbz+dVEuXAoCSv2BYdq4v+kmnh4"
    "3/5LLOzsdV6mKrToXWjmn8vW80J0l2+k230RqkPfNkeaooAWtRzPK6GBpM/O1NCaKOednL"
    "KExjBLwRCt/JvepPnr6N/KZ+fvzz9ULs4/0C58JDPL+zmHQXwNyS+ZsY2grHPnaz3B5VAw"
    "S6Qz3RpFBPO0+34C3EhBhz6RQKRI7/kSWXB5K3m8sdLj2uRxgWy7/vTy8h9Mf/k3"
)
