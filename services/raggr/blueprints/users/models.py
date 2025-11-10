from tortoise.models import Model
from tortoise import fields


import bcrypt


class User(Model):
    id = fields.UUIDField(primary_key=True)
    username = fields.CharField(max_length=255)
    password = fields.BinaryField()  # Hashed
    email = fields.CharField(max_length=100, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def set_password(self, plain_password: str):
        self.password = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(),
        )

    def verify_password(self, plain_password: str):
        return bcrypt.checkpw(plain_password.encode("utf-8"), self.password)
