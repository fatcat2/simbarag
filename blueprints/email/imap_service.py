"""IMAP connection service for email operations.

Provides async IMAP client for connecting to mail servers, listing folders,
and fetching messages. Uses aioimaplib for async IMAP4 operations.
"""

import logging
import re

from aioimaplib import IMAP4_SSL

# Configure logging
logger = logging.getLogger(__name__)


class IMAPService:
    """Async IMAP client for email operations."""

    async def connect(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 993,
        timeout: int = 10,
    ) -> IMAP4_SSL:
        """
        Establish IMAP connection with authentication.

        Args:
            host: IMAP server hostname (e.g., imap.gmail.com)
            username: IMAP username (usually email address)
            password: IMAP password or app-specific password
            port: IMAP port (default 993 for SSL)
            timeout: Connection timeout in seconds (default 10)

        Returns:
            Authenticated IMAP4_SSL client ready for operations

        Raises:
            Exception: On connection or authentication failure

        Note:
            Caller must call close() to properly disconnect when done.
        """
        logger.info(f"[IMAP] Connecting to {host}:{port} as {username}")

        try:
            # Create connection with timeout
            imap = IMAP4_SSL(host=host, port=port, timeout=timeout)

            # Wait for server greeting
            await imap.wait_hello_from_server()
            logger.info(f"[IMAP] Server greeting received from {host}")

            # Authenticate
            login_response = await imap.login(username, password)
            logger.info(f"[IMAP] Authentication successful: {login_response}")

            return imap

        except Exception as e:
            logger.error(
                f"[IMAP ERROR] Connection failed to {host}: {type(e).__name__}: {str(e)}"
            )
            # Best effort cleanup
            try:
                if "imap" in locals():
                    await imap.logout()
            except Exception:
                pass
            raise

    async def list_folders(self, imap: IMAP4_SSL) -> list[str]:
        """
        List all mailbox folders.

        Args:
            imap: Authenticated IMAP4_SSL client

        Returns:
            List of folder names (e.g., ["INBOX", "Sent", "Drafts"])

        Note:
            Parses IMAP LIST response format: (* LIST (...) "/" "INBOX")
        """
        logger.info("[IMAP] Listing mailbox folders")

        try:
            # LIST command: list('""', '*') lists all folders
            response = await imap.list('""', "*")
            logger.info(f"[IMAP] LIST response status: {response}")

            folders = []

            # Parse LIST response lines
            # Format: * LIST (\HasNoChildren) "/" "INBOX"
            # Or: * LIST (\HasChildren \Noselect) "/" "folder name"
            for line in response.lines:
                # Decode bytes to string if needed
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="ignore")

                # Extract folder name from response
                # Match pattern: "folder name" at end of line
                match = re.search(r'"([^"]+)"\s*$', line)
                if match:
                    folder_name = match.group(1)
                    folders.append(folder_name)
                    logger.debug(f"[IMAP] Found folder: {folder_name}")

            logger.info(f"[IMAP] Found {len(folders)} folders")
            return folders

        except Exception as e:
            logger.error(
                f"[IMAP ERROR] Failed to list folders: {type(e).__name__}: {str(e)}"
            )
            raise

    async def close(self, imap: IMAP4_SSL) -> None:
        """
        Properly close IMAP connection.

        Args:
            imap: IMAP4_SSL client to close

        Note:
            CRITICAL: Must use logout(), not close().
            close() only closes the selected mailbox, logout() closes TCP connection.
        """
        logger.info("[IMAP] Closing connection")

        try:
            # Use logout() to close TCP connection
            await imap.logout()
            logger.info("[IMAP] Connection closed successfully")
        except Exception as e:
            # Best effort cleanup - don't fail on close
            logger.warning(
                f"[IMAP] Error during logout (non-fatal): {type(e).__name__}: {str(e)}"
            )
