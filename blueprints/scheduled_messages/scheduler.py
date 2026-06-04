import asyncio
import logging
from datetime import datetime, timezone

from .models import ScheduledMessage, MessageChannel, MessageStatus

logger = logging.getLogger(__name__)

POLL_INTERVAL = 15


async def scheduled_messages_loop():
    """Background loop that polls for and sends due scheduled messages."""
    logger.info(f"Scheduled messages loop started (interval={POLL_INTERVAL}s)")

    while True:
        try:
            now = datetime.now(timezone.utc)
            due = await ScheduledMessage.filter(
                status=MessageStatus.PENDING,
                scheduled_at__lte=now,
            ).all()

            for msg in due:
                try:
                    if msg.channel == MessageChannel.IMESSAGE:
                        from blueprints.imessage import send_imessage
                        from utils.strip_markdown import strip_markdown

                        await send_imessage(msg.recipient, strip_markdown(msg.content))

                    elif msg.channel == MessageChannel.EMAIL:
                        from blueprints.email import send_email_reply

                        await send_email_reply(
                            to=msg.recipient,
                            subject=msg.subject or "(no subject)",
                            body=msg.content,
                        )

                    msg.status = MessageStatus.SENT
                    msg.error_message = None
                    await msg.save()
                    logger.info(
                        f"Sent scheduled {msg.channel.value} message {msg.id} to {msg.recipient}"
                    )

                except Exception as e:
                    msg.status = MessageStatus.FAILED
                    msg.error_message = str(e)
                    await msg.save()
                    logger.error(f"Failed to send scheduled message {msg.id}: {e}")

        except Exception:
            logger.exception("Error in scheduled messages loop")

        await asyncio.sleep(POLL_INTERVAL)
