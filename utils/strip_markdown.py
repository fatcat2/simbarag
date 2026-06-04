import re


def strip_markdown(text: str) -> str:
    """Strip markdown formatting from text for plain-text channels like iMessage."""
    # Code blocks (fenced)
    text = re.sub(
        r"```[\s\S]*?```", lambda m: re.sub(r"```\w*\n?", "", m.group()), text
    )
    # Inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    # Links — keep the link text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Bold/italic (order matters: bold+italic first)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"___(.+?)___", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    # Headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Bullet lists — remove the bullet marker
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Numbered lists — remove the number marker
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Blockquotes
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
