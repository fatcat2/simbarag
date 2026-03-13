import hmac
import hashlib


def generate_email_token(user_id: str, secret: str) -> str:
    """Generate a 16-char hex HMAC token for a user's email address."""
    return hmac.new(
        secret.encode(), str(user_id).encode(), hashlib.sha256
    ).hexdigest()[:16]


def get_user_email_address(token: str, domain: str) -> str:
    """Return the routable email address for a given token."""
    return f"ask+{token}@{domain}"
