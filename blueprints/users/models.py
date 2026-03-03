from tortoise.models import Model
from tortoise import fields


import bcrypt


class User(Model):
    id = fields.UUIDField(primary_key=True)
    username = fields.CharField(max_length=255)
    password = fields.BinaryField(null=True)  # Hashed - nullable for OIDC users
    email = fields.CharField(max_length=100, unique=True)
    whatsapp_number = fields.CharField(max_length=30, unique=True, null=True, index=True)

    # OIDC fields
    oidc_subject = fields.CharField(
        max_length=255, unique=True, null=True, index=True
    )  # "sub" claim from OIDC
    auth_provider = fields.CharField(
        max_length=50, default="local"
    )  # "local" or "oidc"
    ldap_groups = fields.JSONField(default=[])  # LDAP groups from OIDC claims

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def has_group(self, group: str) -> bool:
        """Check if user belongs to a specific LDAP group."""
        return group in (self.ldap_groups or [])

    def is_admin(self) -> bool:
        """Check if user is an admin (member of lldap_admin group)."""
        return self.has_group("lldap_admin")

    def set_password(self, plain_password: str):
        self.password = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(),
        )

    def verify_password(self, plain_password: str):
        if not self.password:
            return False
        return bcrypt.checkpw(plain_password.encode("utf-8"), self.password)
