# Authentication Architecture

This document describes the authentication stack for SimbaRAG: LLDAP → Authelia → OAuth2/OIDC.

## Overview

```
┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  LLDAP  │────▶│ Authelia │────▶│ OAuth2/OIDC  │────▶│ SimbaRAG │
│ (Users) │     │  (IdP)   │     │   (Flow)     │     │  (App)   │
└─────────┘     └──────────┘     └──────────────┘     └──────────┘
```

| Component | Role |
|-----------|------|
| **LLDAP** | Lightweight LDAP server storing users and groups |
| **Authelia** | Identity provider that authenticates against LLDAP and issues OIDC tokens |
| **SimbaRAG** | Relying party that consumes OIDC tokens and manages sessions |

## OIDC Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OIDC_ISSUER` | Authelia server URL | Required |
| `OIDC_CLIENT_ID` | Client ID registered in Authelia | Required |
| `OIDC_CLIENT_SECRET` | Client secret for token exchange | Required |
| `OIDC_REDIRECT_URI` | Callback URL after authentication | Required |
| `OIDC_USE_DISCOVERY` | Enable automatic discovery | `true` |
| `JWT_SECRET_KEY` | Secret for signing backend JWTs | Required |

### Discovery

When `OIDC_USE_DISCOVERY=true`, the application fetches endpoints from:

```
{OIDC_ISSUER}/.well-known/openid-configuration
```

This provides:

- Authorization endpoint
- Token endpoint
- JWKS URI for signature verification
- Supported scopes and claims

## Authentication Flow

### 1. Login Initiation

```
GET /api/user/oidc/login
```

1. Generate PKCE code verifier and challenge (S256)
2. Generate CSRF state token
3. Store state in session storage
4. Return authorization URL for frontend redirect

### 2. Authorization

User is redirected to Authelia where they:

1. Enter LDAP credentials
2. Complete MFA if configured
3. Consent to requested scopes

### 3. Callback

```
GET /api/user/oidc/callback?code=...&state=...
```

1. Validate state matches stored value (CSRF protection)
2. Exchange authorization code for tokens using PKCE verifier
3. Verify ID token signature using JWKS
4. Validate claims (issuer, audience, expiration)
5. Create or update user in database
6. Issue backend JWT tokens (access + refresh)

### 4. Token Refresh

```
POST /api/user/refresh
Authorization: Bearer <refresh_token>
```

Issues a new access token without re-authentication.

## User Model

```python
class User(Model):
    id = UUIDField(primary_key=True)
    username = CharField(max_length=255)
    password = BinaryField(null=True)  # Nullable for OIDC-only users
    email = CharField(max_length=100, unique=True)

    # OIDC fields
    oidc_subject = CharField(max_length=255, unique=True, null=True)
    auth_provider = CharField(max_length=50, default="local")  # "local" or "oidc"
    ldap_groups = JSONField(default=[])  # LDAP groups from OIDC claims

    created_at = DatetimeField(auto_now_add=True)
    updated_at = DatetimeField(auto_now=True)

    def has_group(self, group: str) -> bool:
        """Check if user belongs to a specific LDAP group."""
        return group in (self.ldap_groups or [])

    def is_admin(self) -> bool:
        """Check if user is an admin (member of lldap_admin group)."""
        return self.has_group("lldap_admin")
```

### User Provisioning

The `OIDCUserService` handles automatic user creation:

1. Extract claims from ID token (`sub`, `email`, `preferred_username`)
2. Check if user exists by `oidc_subject`
3. If not, check by email for migration from local auth
4. Create new user or update existing

## JWT Tokens

Backend issues its own JWTs after OIDC authentication:

| Token Type | Purpose | Typical Lifetime |
|------------|---------|------------------|
| Access Token | API authorization | 15 minutes |
| Refresh Token | Obtain new access tokens | 7 days |

### Claims

```json
{
  "identity": "<user-uuid>",
  "type": "access|refresh",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Protected Endpoints

All API endpoints use the `@jwt_refresh_token_required` decorator for basic authentication:

```python
@blueprint.route("/example")
@jwt_refresh_token_required
async def protected_endpoint():
    user_id = get_jwt_identity()
    # ...
```

---

## Role-Based Access Control (RBAC)

RBAC is implemented using LDAP groups passed through Authelia as OIDC claims. Users in the `lldap_admin` group have admin privileges.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        LLDAP                                │
│  Groups: lldap_admin, lldap_user                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Authelia                              │
│  Scope: groups → Claim: groups = ["lldap_admin"]           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       SimbaRAG                              │
│  1. Extract groups from ID token                            │
│  2. Store in User.ldap_groups                               │
│  3. Check membership with @admin_required decorator         │
└─────────────────────────────────────────────────────────────┘
```

### Authelia Configuration

Ensure Authelia is configured to pass the `groups` claim:

```yaml
identity_providers:
  oidc:
    clients:
      - client_id: simbarag
        scopes:
          - openid
          - profile
          - email
          - groups  # Required for RBAC
```

### Admin-Only Endpoints

The `@admin_required` decorator protects privileged endpoints:

```python
from blueprints.users.decorators import admin_required

@blueprint.post("/admin-action")
@admin_required
async def admin_only_endpoint():
    # Only users in lldap_admin group can access
    ...
```

**Protected endpoints:**

| Endpoint | Access | Description |
|----------|--------|-------------|
| `POST /api/rag/index` | Admin | Trigger document indexing |
| `POST /api/rag/reindex` | Admin | Clear and reindex all documents |
| `GET /api/rag/stats` | All users | View vector store statistics |

### User Response

The OIDC callback returns group information:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {
    "id": "uuid",
    "username": "john",
    "email": "john@example.com",
    "groups": ["lldap_admin", "lldap_user"],
    "is_admin": true
  }
}
```

---

## Security Considerations

### Current Gaps

| Issue | Risk | Mitigation |
|-------|------|------------|
| In-memory session storage | State lost on restart, not scalable | Use Redis for production |
| No token revocation | Tokens valid until expiry | Implement blacklist or short expiry |
| No audit logging | Cannot track auth events | Add event logging |
| Single JWT secret | Compromise affects all tokens | Rotate secrets, use asymmetric keys |

### Recommendations

1. **Use Redis** for OIDC state storage in production
2. **Implement logout** with token blacklisting
3. **Add audit logging** for authentication events
4. **Rotate JWT secrets** regularly
5. **Use short-lived access tokens** (15 min) with refresh

---

## File Reference

| File | Purpose |
|------|---------|
| `services/raggr/oidc_config.py` | OIDC client configuration and discovery |
| `services/raggr/blueprints/users/models.py` | User model definition with group helpers |
| `services/raggr/blueprints/users/oidc_service.py` | User provisioning from OIDC claims |
| `services/raggr/blueprints/users/__init__.py` | Auth endpoints and flow |
| `services/raggr/blueprints/users/decorators.py` | Auth decorators (`@admin_required`) |
