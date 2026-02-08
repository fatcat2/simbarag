"""Email body parsing service for multipart MIME messages.

Extracts text and HTML bodies from RFC822 email format, converts HTML to text
when needed, and extracts email metadata (subject, from, to, date, message-id).
"""

import logging
from email import message_from_bytes
from email.policy import default
from email.utils import parsedate_to_datetime

import html2text

# Configure logging
logger = logging.getLogger(__name__)


def parse_email_body(raw_email_bytes: bytes) -> dict:
    """
    Extract text and HTML bodies from RFC822 email bytes.

    Args:
        raw_email_bytes: Raw email message bytes from IMAP FETCH

    Returns:
        Dictionary with keys:
        - "text": Plain text body (None if not present)
        - "html": HTML body (None if not present)
        - "preferred": Best available body (text preferred, HTML converted if text missing)
        - "subject": Email subject
        - "from": Sender address
        - "to": Recipient address(es)
        - "date": Parsed datetime object (None if missing/invalid)
        - "message_id": RFC822 Message-ID header

    Note:
        Uses modern EmailMessage API with email.policy.default for proper
        encoding handling. Prefers plain text over HTML for RAG indexing.
    """
    logger.info("[EMAIL PARSER] Parsing email message")

    try:
        # Parse with modern EmailMessage API and default policy
        msg = message_from_bytes(raw_email_bytes, policy=default)

        result = {
            "text": None,
            "html": None,
            "preferred": None,
            "subject": "",
            "from": "",
            "to": "",
            "date": None,
            "message_id": "",
        }

        # Extract plain text body
        text_part = msg.get_body(preferencelist=("plain",))
        if text_part:
            # Use get_content() for proper decoding (not get_payload())
            result["text"] = text_part.get_content()
            logger.debug("[EMAIL PARSER] Found plain text body")

        # Extract HTML body
        html_part = msg.get_body(preferencelist=("html",))
        if html_part:
            result["html"] = html_part.get_content()
            logger.debug("[EMAIL PARSER] Found HTML body")

        # Determine preferred version (text preferred for RAG)
        if result["text"]:
            result["preferred"] = result["text"]
            logger.debug("[EMAIL PARSER] Using plain text as preferred")
        elif result["html"]:
            # Convert HTML to text using html2text
            h = html2text.HTML2Text()
            h.ignore_links = False  # Keep links for context
            result["preferred"] = h.handle(result["html"])
            logger.debug("[EMAIL PARSER] Converted HTML to text for preferred")
        else:
            logger.warning(
                "[EMAIL PARSER] No body content found (neither text nor HTML)"
            )

        # Extract metadata
        result["subject"] = msg.get("subject", "")
        result["from"] = msg.get("from", "")
        result["to"] = msg.get("to", "")
        result["message_id"] = msg.get("message-id", "")

        # Parse date header
        date_header = msg.get("date")
        if date_header:
            try:
                result["date"] = parsedate_to_datetime(date_header)
            except Exception as date_error:
                logger.warning(
                    f"[EMAIL PARSER] Failed to parse date header '{date_header}': {date_error}"
                )

        logger.info(
            f"[EMAIL PARSER] Successfully parsed email: subject='{result['subject']}', from='{result['from']}'"
        )
        return result

    except UnicodeDecodeError as e:
        logger.error(f"[EMAIL PARSER] Unicode decode error: {str(e)}")
        # Return partial data with error indication
        return {
            "text": None,
            "html": None,
            "preferred": None,
            "subject": "[Encoding Error]",
            "from": "",
            "to": "",
            "date": None,
            "message_id": "",
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"[EMAIL PARSER] Unexpected error: {type(e).__name__}: {str(e)}")
        logger.exception("[EMAIL PARSER] Full traceback:")
        raise
