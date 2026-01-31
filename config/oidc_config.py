"""
OIDC Configuration for Authelia Integration
"""

import os
from typing import Dict, Any
from authlib.jose import jwt
from authlib.jose.errors import JoseError
import httpx


class OIDCConfig:
    """OIDC Configuration Manager"""

    def __init__(self):
        # Load from environment variables
        self.issuer = os.getenv("OIDC_ISSUER")  # e.g., https://auth.example.com
        self.client_id = os.getenv("OIDC_CLIENT_ID")
        self.client_secret = os.getenv("OIDC_CLIENT_SECRET")
        self.redirect_uri = os.getenv(
            "OIDC_REDIRECT_URI", "http://localhost:8080/api/user/oidc/callback"
        )

        # OIDC endpoints (can use discovery or manual config)
        self.use_discovery = os.getenv("OIDC_USE_DISCOVERY", "true").lower() == "true"

        # Manual endpoint configuration (fallback if discovery fails)
        self.authorization_endpoint = os.getenv("OIDC_AUTHORIZATION_ENDPOINT")
        self.token_endpoint = os.getenv("OIDC_TOKEN_ENDPOINT")
        self.userinfo_endpoint = os.getenv("OIDC_USERINFO_ENDPOINT")
        self.jwks_uri = os.getenv("OIDC_JWKS_URI")

        # Cached discovery document and JWKS
        self._discovery_doc: Dict[str, Any] | None = None
        self._jwks: Dict[str, Any] | None = None

    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        if not self.issuer or not self.client_id or not self.client_secret:
            return False
        return True

    async def get_discovery_document(self) -> Dict[str, Any]:
        """Fetch OIDC discovery document from .well-known endpoint"""
        if self._discovery_doc:
            return self._discovery_doc

        if not self.use_discovery:
            # Return manual configuration
            return {
                "issuer": self.issuer,
                "authorization_endpoint": self.authorization_endpoint,
                "token_endpoint": self.token_endpoint,
                "userinfo_endpoint": self.userinfo_endpoint,
                "jwks_uri": self.jwks_uri,
            }

        discovery_url = f"{self.issuer.rstrip('/')}/.well-known/openid-configuration"

        async with httpx.AsyncClient() as client:
            response = await client.get(discovery_url)
            response.raise_for_status()
            self._discovery_doc = response.json()
            return self._discovery_doc

    async def get_jwks(self) -> Dict[str, Any]:
        """Fetch JSON Web Key Set for token verification"""
        if self._jwks:
            return self._jwks

        discovery = await self.get_discovery_document()
        jwks_uri = discovery.get("jwks_uri")

        if not jwks_uri:
            raise ValueError("No jwks_uri found in discovery document")

        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_uri)
            response.raise_for_status()
            self._jwks = response.json()
            return self._jwks

    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify and decode ID token from OIDC provider

        Returns the decoded claims if valid
        Raises exception if invalid
        """
        jwks = await self.get_jwks()

        try:
            # Verify token signature and claims
            claims = jwt.decode(
                id_token,
                jwks,
                claims_options={
                    "iss": {"essential": True, "value": self.issuer},
                    "aud": {"essential": True, "value": self.client_id},
                    "exp": {"essential": True},
                },
            )

            # Additional validation
            claims.validate()

            return claims

        except JoseError as e:
            raise ValueError(f"Invalid ID token: {str(e)}")


# Global instance
oidc_config = OIDCConfig()
