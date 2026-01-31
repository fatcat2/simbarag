"""
Authentication decorators for role-based access control.
"""

from functools import wraps
from quart import jsonify
from quart_jwt_extended import jwt_refresh_token_required, get_jwt_identity
from .models import User


def admin_required(fn):
    """
    Decorator that requires the user to be an admin (member of lldap_admin group).
    Must be used on async route handlers.
    """

    @wraps(fn)
    @jwt_refresh_token_required
    async def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = await User.get_or_none(id=user_id)
        if not user or not user.is_admin():
            return jsonify({"error": "Admin access required"}), 403
        return await fn(*args, **kwargs)

    return wrapper
