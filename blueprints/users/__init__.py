from quart import Blueprint, jsonify, request
from quart_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
)
from .models import User
from .oidc_service import OIDCUserService
from .decorators import admin_required
from config.oidc_config import oidc_config
import os
import secrets
import httpx
from urllib.parse import urlencode
import hashlib
import base64


user_blueprint = Blueprint("user_api", __name__, url_prefix="/api/user")

# In-memory storage for OIDC state/PKCE (production: use Redis or database)
# Format: {state: {"pkce_verifier": str, "redirect_after_login": str}}
_oidc_sessions = {}


@user_blueprint.route("/oidc/login", methods=["GET"])
async def oidc_login():
    """
    Initiate OIDC login flow
    Generates PKCE parameters and redirects to Authelia
    """
    if not oidc_config.validate_config():
        return jsonify({"error": "OIDC not configured"}), 500

    try:
        # Generate PKCE parameters
        code_verifier = secrets.token_urlsafe(64)

        # For PKCE, we need code_challenge = BASE64URL(SHA256(code_verifier))
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .decode()
            .rstrip("=")
        )

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store PKCE verifier and state for callback validation
        _oidc_sessions[state] = {
            "pkce_verifier": code_verifier,
            "redirect_after_login": request.args.get("redirect", "/"),
        }

        # Get authorization endpoint from discovery
        discovery = await oidc_config.get_discovery_document()
        auth_endpoint = discovery.get("authorization_endpoint")

        # Build authorization URL
        params = {
            "client_id": oidc_config.client_id,
            "response_type": "code",
            "redirect_uri": oidc_config.redirect_uri,
            "scope": "openid email profile groups",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = f"{auth_endpoint}?{urlencode(params)}"

        return jsonify({"auth_url": auth_url})
    except Exception as e:
        return jsonify({"error": f"OIDC login failed: {str(e)}"}), 500


@user_blueprint.route("/oidc/callback", methods=["GET"])
async def oidc_callback():
    """
    Handle OIDC callback from Authelia
    Exchanges authorization code for tokens, verifies ID token, and creates/updates user
    """
    # Get authorization code and state from callback
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if error:
        return jsonify({"error": f"OIDC error: {error}"}), 400

    if not code or not state:
        return jsonify({"error": "Missing code or state"}), 400

    # Validate state and retrieve PKCE verifier
    session = _oidc_sessions.pop(state, None)
    if not session:
        return jsonify({"error": "Invalid or expired state"}), 400

    pkce_verifier = session["pkce_verifier"]

    # Exchange authorization code for tokens
    discovery = await oidc_config.get_discovery_document()
    token_endpoint = discovery.get("token_endpoint")

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": oidc_config.redirect_uri,
        "client_id": oidc_config.client_id,
        "client_secret": oidc_config.client_secret,
        "code_verifier": pkce_verifier,
    }

    # Use client_secret_post method (credentials in POST body)
    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_endpoint, data=token_data)

        if token_response.status_code != 200:
            return jsonify(
                {"error": f"Failed to exchange code for token: {token_response.text}"}
            ), 400

        tokens = token_response.json()

    id_token = tokens.get("id_token")
    if not id_token:
        return jsonify({"error": "No ID token received"}), 400

    # Verify ID token
    try:
        claims = await oidc_config.verify_id_token(id_token)
    except Exception as e:
        return jsonify({"error": f"ID token verification failed: {str(e)}"}), 400

    # Fetch userinfo to get groups (older Authelia versions only include groups there)
    userinfo_endpoint = discovery.get("userinfo_endpoint")
    if userinfo_endpoint:
        access_token_str = tokens.get("access_token")
        if access_token_str:
            async with httpx.AsyncClient() as client:
                userinfo_response = await client.get(
                    userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token_str}"},
                )
                if userinfo_response.status_code == 200:
                    userinfo = userinfo_response.json()
                    if "groups" in userinfo and "groups" not in claims:
                        claims["groups"] = userinfo["groups"]

    # Get or create user from OIDC claims
    user = await OIDCUserService.get_or_create_user_from_oidc(claims)

    # Issue backend JWT tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    # Return tokens to frontend
    # Frontend will handle storing these and redirecting
    return jsonify(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "groups": user.ldap_groups,
            "is_admin": user.is_admin(),
        },
    )


@user_blueprint.route("/refresh", methods=["POST"])
@jwt_refresh_token_required
async def refresh():
    """Refresh access token (unchanged from original)"""
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    return jsonify(access_token=new_token)


# Legacy username/password login - kept for backward compatibility during migration
@user_blueprint.route("/login", methods=["POST"])
async def login():
    """
    Legacy username/password login
    This can be removed after full OIDC migration is complete
    """
    data = await request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = await User.filter(username=username).first()

    if not user or not user.verify_password(password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": str(user.id), "username": user.username},
    )


@user_blueprint.route("/me", methods=["GET"])
@jwt_refresh_token_required
async def me():
    user_id = get_jwt_identity()
    user = await User.get_or_none(id=user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin(),
    })


@user_blueprint.route("/admin/users", methods=["GET"])
@admin_required
async def list_users():
    from blueprints.email.helpers import get_user_email_address
    users = await User.all().order_by("username")
    mailgun_domain = os.getenv("MAILGUN_DOMAIN", "")
    return jsonify([
        {
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "whatsapp_number": u.whatsapp_number,
            "auth_provider": u.auth_provider,
            "email_enabled": u.email_enabled,
            "email_address": get_user_email_address(u.email_hmac_token, mailgun_domain) if u.email_hmac_token and u.email_enabled else None,
        }
        for u in users
    ])


@user_blueprint.route("/admin/users/<user_id>/whatsapp", methods=["PUT"])
@admin_required
async def set_whatsapp(user_id):
    data = await request.get_json()
    number = (data or {}).get("whatsapp_number", "").strip()
    if not number:
        return jsonify({"error": "whatsapp_number is required"}), 400

    user = await User.get_or_none(id=user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    conflict = await User.filter(whatsapp_number=number).exclude(id=user_id).first()
    if conflict:
        return jsonify({"error": "That WhatsApp number is already linked to another account"}), 409

    user.whatsapp_number = number
    await user.save()
    return jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "whatsapp_number": user.whatsapp_number,
        "auth_provider": user.auth_provider,
    })


@user_blueprint.route("/admin/users/<user_id>/whatsapp", methods=["DELETE"])
@admin_required
async def unlink_whatsapp(user_id):
    user = await User.get_or_none(id=user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.whatsapp_number = None
    await user.save()
    return jsonify({"ok": True})


@user_blueprint.route("/admin/users/<user_id>/email", methods=["PUT"])
@admin_required
async def toggle_email(user_id):
    """Enable email channel for a user, generating an HMAC token."""
    from blueprints.email.helpers import generate_email_token, get_user_email_address
    user = await User.get_or_none(id=user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    email_secret = os.getenv("EMAIL_HMAC_SECRET")
    if not email_secret:
        return jsonify({"error": "EMAIL_HMAC_SECRET not configured"}), 500

    mailgun_domain = os.getenv("MAILGUN_DOMAIN", "")

    if not user.email_hmac_token:
        user.email_hmac_token = generate_email_token(user.id, email_secret)
    user.email_enabled = True
    await user.save()

    return jsonify({
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "whatsapp_number": user.whatsapp_number,
        "auth_provider": user.auth_provider,
        "email_enabled": user.email_enabled,
        "email_address": get_user_email_address(user.email_hmac_token, mailgun_domain),
    })


@user_blueprint.route("/admin/users/<user_id>/email", methods=["DELETE"])
@admin_required
async def disable_email(user_id):
    """Disable email channel and clear the token."""
    user = await User.get_or_none(id=user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.email_enabled = False
    user.email_hmac_token = None
    await user.save()
    return jsonify({"ok": True})
