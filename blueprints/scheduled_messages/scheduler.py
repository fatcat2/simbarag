import asyncio
import logging
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from .models import ScheduledMessage, MessageChannel, MessageStatus, Recurrence

logger = logging.getLogger(__name__)

POLL_INTERVAL = 15

RECURRENCE_DELTAS = {
    Recurrence.DAILY: relativedelta(days=1),
    Recurrence.WEEKLY: relativedelta(weeks=1),
    Recurrence.MONTHLY: relativedelta(months=1),
}


async def _schedule_next_occurrence(msg: ScheduledMessage):
    """Create the next pending occurrence for a recurring message."""
    delta = RECURRENCE_DELTAS.get(msg.recurrence)
    if not delta:
        return

    next_at = msg.scheduled_at + delta
    # If we missed several intervals, advance until we're in the future
    now = datetime.now(timezone.utc)
    while next_at <= now:
        next_at += delta

    await ScheduledMessage.create(
        recipient=msg.recipient,
        channel=msg.channel,
        content=msg.content,
        subject=msg.subject,
        scheduled_at=next_at,
        recurrence=msg.recurrence,
        created_by_id=msg.created_by_id,
    )
    logger.info(
        f"Scheduled next {msg.recurrence.value} occurrence for {msg.id} at {next_at.isoformat()}"
    )


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

                    # Schedule next occurrence for recurring messages
                    if msg.recurrence != Recurrence.NONE:
                        await _schedule_next_occurrence(msg)

                except Exception as e:
                    msg.status = MessageStatus.FAILED
                    msg.error_message = str(e)
                    await msg.save()
                    logger.error(f"Failed to send scheduled message {msg.id}: {e}")

        except Exception:
            logger.exception("Error in scheduled messages loop")

        await asyncio.sleep(POLL_INTERVAL)
