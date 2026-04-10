from .models import UserMemory


async def get_memories_for_user(user_id: str) -> list[str]:
    """Return all memory content strings for a user, ordered by most recently updated."""
    memories = await UserMemory.filter(user_id=user_id).order_by("-updated_at")
    return [m.content for m in memories]


async def save_memory(user_id: str, content: str) -> str:
    """Save a new memory or touch an existing one (exact-match dedup)."""
    existing = await UserMemory.filter(user_id=user_id, content=content).first()
    if existing:
        existing.updated_at = None  # auto_now=True will refresh it on save
        await existing.save(update_fields=["updated_at"])
        return "Memory already exists (refreshed)."

    await UserMemory.create(user_id=user_id, content=content)
    return "Memory saved."
