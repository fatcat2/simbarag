"""
OIDC User Management Service
"""

from typing import Dict, Any, Optional
from uuid import uuid4
from .models import User


class OIDCUserService:
    """Service for managing OIDC user authentication and provisioning"""

    @staticmethod
    async def get_or_create_user_from_oidc(claims: Dict[str, Any]) -> User:
        """
        Get existing user by OIDC subject, or create new user from OIDC claims

        Args:
            claims: Decoded OIDC ID token claims

        Returns:
            User object (existing or newly created)
        """
        oidc_subject = claims.get("sub")
        if not oidc_subject:
            raise ValueError("No 'sub' claim in ID token")

        # Try to find existing user by OIDC subject
        user = await User.filter(oidc_subject=oidc_subject).first()

        if user:
            # Update user info from latest claims (optional)
            user.email = claims.get("email", user.email)
            user.username = (
                claims.get("preferred_username") or claims.get("name") or user.username
            )
            # Update LDAP groups from claims
            user.ldap_groups = claims.get("groups") or []
            await user.save()
            return user

        # Check if user exists by email (migration case)
        email = claims.get("email")
        if email:
            user = await User.filter(email=email, auth_provider="local").first()
            if user:
                # Migrate existing local user to OIDC
                user.oidc_subject = oidc_subject
                user.auth_provider = "oidc"
                user.password = None  # Clear password
                user.ldap_groups = claims.get("groups") or []
                await user.save()
                return user

        # Create new user from OIDC claims
        username = (
            claims.get("preferred_username")
            or claims.get("name")
            or claims.get("email", "").split("@")[0]
            or f"user_{oidc_subject[:8]}"
        )

        # Extract LDAP groups from claims
        groups = claims.get("groups") or []

        user = await User.create(
            id=uuid4(),
            username=username,
            email=email or f"{oidc_subject}@oidc.local",  # Fallback if no email claim
            oidc_subject=oidc_subject,
            auth_provider="oidc",
            password=None,
            ldap_groups=groups,
        )

        return user

    @staticmethod
    async def find_user_by_oidc_subject(oidc_subject: str) -> Optional[User]:
        """Find user by OIDC subject ID"""
        return await User.filter(oidc_subject=oidc_subject).first()
