from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "users" ADD "whatsapp_number" VARCHAR(20) UNIQUE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_users_whatsap_e6b586";
        ALTER TABLE "users" DROP COLUMN "whatsapp_number";"""


MODELS_STATE = (
    "eJztmm1v4jgQx78Kyquu1KtatnRX1emkQOkttwuceNinXhWZxECuiZ2NnaWo6nc/2yTESR"
    "wgFCjs8aYtYw+2fx5n/p70SXOxBR1yVsPoJ/QJoDZG2nXpSUPAhewPZftpSQOeF7dyAwUD"
    "RziYUk/RAgaE+sCkrHEIHAKZyYLE9G0vHAwFjsON2GQdbTSKTQGyfwTQoHgE6Rj6rOHunp"
    "ltZMFHSKKP3oMxtKFjJeZtW3xsYTfo1BO2fr9xcyt68uEGhomdwEVxb29KxxjNuweBbZ1x"
    "H942ggj6gEJLWgafZbjsyDSbMTNQP4DzqVqxwYJDEDgchvb7MEAmZ1ASI/Efl39oBfAw1B"
    "ytjShn8fQ8W1W8ZmHV+FC1D3rn5O3VG7FKTOjIF42CiPYsHAEFM1fBNQYpfmdQ1sbAV6OM"
    "+qdgsomugzEyxBzjGIpARoDWo6a54NFwIBrRMftYrlQWYPysdwRJ1kugxCyuZ1HfCpvKsz"
    "aONEZo+pAv2QA0C/KGtVDbhWqYSc8UUit0PYv+2FPAbA1WGznT8BAs4NtrNOvdnt78m6/E"
    "JeSHIxDpvTpvKQvrNGU9uUptxfxLSl8avQ8l/rH0vd2qp2N/3q/3XeNzAgHFBsITA1jSeY"
    "2sEZjExgaetebGJj2PG/uqGxtOXtpXAn2jWAaRXF6QRsK57XAT108aPPUOH5Q5g8PIwrvF"
    "PrRH6COcCoQNNg+ATFWyCEVHP/yafYUWW+NZ+GAyVyNyULDVsTVBOsueerem39Q1wXAAzI"
    "cJ8C0jB6YLCQEjSLJAq6Hn7ccOdObSTM1SFnDN2Tfu51Mlj61ghctYYpSgl21yy27aAhBb"
    "txWOzUdaQGeJCpYgriaGDXkjj6L4oEUxhY+KlN9jVjXKqP+hiOJFqbz+tZfI4pH0PWnqX9"
    "8kMvmnduvPqLsklWuf2tWjQv4VhVRWIRMPggeVGOAXyDoK3IwUSOyu5P7KR0frd+ud6xLP"
    "6P+gbqNZ1a9LxHYHQFttixO3zIvzFS6ZF+e5d0zelDpAcqIp9phXuG7ymX+gEtZMFbxeKG"
    "XT9bO9pbhU0yrCpai23aaSE3cGhXSL7hL5Wo0f7aM2O3xtxvexaNFS9jkUjbaDwqUHCJlg"
    "XxGZVRsBf6qGKXulYA6mdHb/2dcrvQpeletVWW4xZNVGS+98U0veqL8ct9VvvbqeogtdYD"
    "tFonTusJkQXX7iNxmgF+eriZ5FqicjeyZjQAl7pBtMSQ7yZKYapsJ1LazpUN0t1fIqUMv5"
    "TMsZpNi2TIMEg3+hqbiM5fNM+x0izG08Q9n1aGx4Pv5pW8UCNOO4u8SkOdgEzgsye5JrZZ"
    "UgreQHaSUTpI4FPGPk48BTlEX/6rZbaqQptxTQPmKrvLNsk56WHJvQ+63hvbvfjmriK19c"
    "m0mXYVJpin/BsTbzP6nNHN9e/hIbO385krljL3uzlPlXnc28Xtpnfb/b10o69G1zrCnKEW"
    "HL6aKCBIj77E1FooFy3nAoCxIccyoYwp1/1XuJeLn3W/ni8t3l+7dXl+9ZFzGTueXdgodB"
    "o9VbUoDgB0FZNczXepLLsfwQS2d2NIoI5ln3wwS4lesxG5FCpEjv+RJZcnkteby1Qs7G5H"
    "GBbLv59PL8Hy/ZG1k="
)
