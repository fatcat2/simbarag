"""
Email blueprint for IMAP email ingestion.

Provides API endpoints for managing email accounts and querying email content.
Admin-only access enforced via lldap_admin group membership.
"""

from quart import Blueprint

# Import models for Tortoise ORM registration
from . import models  # noqa: F401

# Create blueprint
email_blueprint = Blueprint("email", __name__, url_prefix="/api/email")

# Routes will be added in Phase 2
