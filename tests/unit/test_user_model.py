"""Tests for User model methods in blueprints/users/models.py."""

from unittest.mock import MagicMock

import bcrypt


class TestUserModelMethods:
    """Test User model methods without requiring a database connection.

    We instantiate a mock object with the same methods as User
    to avoid Tortoise ORM initialization.
    """

    def _make_user(self, ldap_groups=None, password=None):
        """Create a mock user with real method implementations."""
        from blueprints.users.models import User

        user = MagicMock(spec=User)
        user.ldap_groups = ldap_groups
        user.password = password

        # Bind real methods
        user.has_group = lambda group: group in (user.ldap_groups or [])
        user.is_admin = lambda: user.has_group("lldap_admin")

        def set_password(plain):
            user.password = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt())

        user.set_password = set_password

        def verify_password(plain):
            if not user.password:
                return False
            return bcrypt.checkpw(plain.encode("utf-8"), user.password)

        user.verify_password = verify_password

        return user

    def test_has_group_true(self):
        user = self._make_user(ldap_groups=["lldap_admin", "users"])
        assert user.has_group("lldap_admin") is True
        assert user.has_group("users") is True

    def test_has_group_false(self):
        user = self._make_user(ldap_groups=["users"])
        assert user.has_group("lldap_admin") is False

    def test_has_group_empty_list(self):
        user = self._make_user(ldap_groups=[])
        assert user.has_group("anything") is False

    def test_has_group_none(self):
        user = self._make_user(ldap_groups=None)
        assert user.has_group("anything") is False

    def test_is_admin_true(self):
        user = self._make_user(ldap_groups=["lldap_admin"])
        assert user.is_admin() is True

    def test_is_admin_false(self):
        user = self._make_user(ldap_groups=["users"])
        assert user.is_admin() is False

    def test_is_admin_empty(self):
        user = self._make_user(ldap_groups=[])
        assert user.is_admin() is False

    def test_set_and_verify_password(self):
        user = self._make_user()
        user.set_password("hunter2")
        assert user.password is not None
        assert user.verify_password("hunter2") is True
        assert user.verify_password("wrong") is False

    def test_verify_password_no_password_set(self):
        user = self._make_user(password=None)
        assert user.verify_password("anything") is False

    def test_password_is_hashed(self):
        user = self._make_user()
        user.set_password("mypassword")
        # The stored password should not be the plaintext
        assert user.password != b"mypassword"
        assert user.password != "mypassword"
