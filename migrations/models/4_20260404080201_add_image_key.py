from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "conversation_messages" ADD "image_key" VARCHAR(512);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "conversation_messages" DROP COLUMN "image_key";"""


MODELS_STATE = (
    "eJztmmtv4jgUhv8KyqeO1K0KvcyoWq0UWrrDToFVC3PrVpFJXPCS2JnEGYqq/ve1TUIcx6"
    "GkBQqzfGnLsQ+xH1/Oe076aHjEgW54cE7wTxiEgCKCjbPKo4GBB9kf2vb9igF8P23lBgr6"
    "rnCwpZ6iBfRDGgCbssZ74IaQmRwY2gHy44fhyHW5kdisI8KD1BRh9COCFiUDSIcwYA23d8"
    "yMsAMfYJh89EfWPYKukxk3cvizhd2iE1/Yer3mxaXoyR/Xt2ziRh5Oe/sTOiR41j2KkHPA"
    "fXjbAGIYAAodaRp8lPG0E9N0xMxAgwjOhuqkBgfeg8jlMIzf7yNscwYV8ST+4/gPowQehp"
    "qjRZhyFo9P01mlcxZWgz/q/KN5vXd0+k7MkoR0EIhGQcR4Eo6Agqmr4JqCFL9zKM+HINCj"
    "TPorMNlAX4IxMaQc0z2UgEwAvYya4YEHy4V4QIfsY+3kZA7Gz+a1IMl6CZSE7evprm/HTb"
    "VpG0eaIrQDyKdsAZoHecFaKPKgHmbWU0HqxK4HyR8bCpjNwelgdxIfgjl8u81W46Zrtv7m"
    "M/HC8IcrEJndBm+pCetEse6dKksx+5LKl2b3Y4V/rHzvtBvq3p/16343+JhARImFydgCjn"
    "ReE2sCJrOwke+8cGGznruFfdOFjQcvrWsIA6tcBJFcXhFG4rGtcRFfHjR46L0faWMGh5GH"
    "d0kCiAb4E5wIhE02DoBtXbCIRUcv/ppNhZZa01EEYDxTI/KmYLNjc4J0Gj3Nm3PzomEIhn"
    "1gj8YgcKwCmB4MQzCAYR5oPfa8/HQN3Zk007OUBVxr+o2beasUsRWsSI1IjDL08k1ezVMt"
    "ALN5O/Gz+ZPm0HlGBUsQFxPDlryQO1G81aKYwgdNyO8yqx5l0n9bRPG8UN742s1E8UT67r"
    "XMr+8ykfyq0/4z6S5J5fOrTn2nkH9FIZVXyKEPwUgnBngC2cCRl5MCmdWV3N/46Bi9m8b1"
    "WYVH9H/wTbNVN88qIfL6wFhsiTNZZvVwgSSzeliYY/Km7AFCHoss1ghOyqTqGacX8V2/9M"
    "qCPKnWFiDJehWiFG3KZSQH7XIhU+O6zPi5pemArRQPX5kWqLXIjaX4bH6g2S5l84RVqmKR"
    "f2lkcJKXFetefk3udO7261y+jmULwLLPtujdNRSBfRCGYxJodmYdYRBM9DBlLwVmf0Knue"
    "TGxeg58Opc+8vSlSGrN9vm9Td9+pD0l/dt/Vu3YSp0oQeQW2aXzhyWs0WfP/HL3KDVw8UE"
    "5DwFmZOQ4yGgIbvSLabK+0WSXQ9T47oUObleqkeLQD0qZnqUQyo2mQUxn57u4BPiQoDnbF"
    "DZVz3+zHlVl2nZUF3i/Hc6V5nzX2+q5YFeq95gm1dgZp3QVAo1210t3KEHbKYRRlCjLJ85"
    "/YrvFu7Y6uki14Ca/ku3wKm6YwlybCuM+v9CW1OKKQaq+m0hzJVEfRDRoeUH5Cdyyl2pOc"
    "f1SSnDJTZwX6FFlRx9kWv1pPhaPcldq64DfGsQkMjXvBT566bT1iNV3BSgPcxmeesgm+5X"
    "XBTSu5Xhvb1bjc7nM59fmVWLsIqw4l+wq8z+Tyqzu/9d+CUWdvZqNFcVeu69cu4f9Zbzcn"
    "mTM9L1vlQ2YYDsoaEpoMUt+/NKaCDtszE1tCYueL+pLaFxzMpmiFf+TTNp8Wr/t1r1+P3x"
    "h6PT4w+sixjJzPJ+zmWQpCHFJTN+ELR17mKtJ7nsCmapdGZHo4xgnnbfToArKeiwJ1KINe"
    "G9WCJLLm8lj1dWelyaPC4RbZcfXp7+AzcBYwM="
)
