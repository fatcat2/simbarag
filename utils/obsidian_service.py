"""Obsidian headless sync service for querying and modifying vaults."""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from subprocess import run

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ObsidianService:
    """Service for interacting with Obsidian vault via obsidian-headless CLI."""

    def __init__(self):
        """Initialize Obsidian Sync client."""
        self.vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "/app/data/obsidian")

        # Create vault path if it doesn't exist
        Path(self.vault_path).mkdir(parents=True, exist_ok=True)

        # Validate vault has .md files
        self._validate_vault()

    def _validate_vault(self) -> None:
        """Validate that vault directory exists and has .md files."""
        vault_dir = Path(self.vault_path)
        if not vault_dir.exists():
            raise ValueError(
                f"Obsidian vault path '{self.vault_path}' does not exist. "
                "Please ensure the vault is synced to this location."
            )

        md_files = list(vault_dir.rglob("*.md"))
        if not md_files:
            raise ValueError(
                f"Vault at '{self.vault_path}' contains no markdown files. "
                "Please ensure the vault is synced with obsidian-headless."
            )

    def walk_vault(self) -> list[Path]:
        """Walk through vault directory and return paths to .md files.

        Returns:
            List of paths to markdown files, excluding .obsidian directory.
        """
        vault_dir = Path(self.vault_path)
        md_files = []

        # Walk vault, excluding .obsidian directory
        for md_file in vault_dir.rglob("*.md"):
            # Skip .obsidian directory and its contents
            if ".obsidian" in md_file.parts:
                continue
            md_files.append(md_file)

        return md_files

    def parse_markdown(self, content: str, filepath: Optional[Path] = None) -> dict[str, Any]:
        """Parse Obsidian markdown to extract metadata and clean content.

        Args:
            content: Raw markdown content
            filepath: Optional file path for context

        Returns:
            Dictionary containing parsed content:
                - metadata: Parsed YAML frontmatter (or empty dict if none)
                - content: Cleaned body content
                - tags: Extracted tags
                - wikilinks: List of wikilinks found
                - embeds: List of embeds found
        """
        # Split frontmatter from content
        frontmatter_pattern = r"^---\n(.*?)\n---"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        metadata = {}
        body_content = content

        if match:
            frontmatter = match.group(1)
            body_content = content[match.end():].strip()
            try:
                metadata = yaml.safe_load(frontmatter) or {}
            except yaml.YAMLError:
                # Invalid YAML, treat as empty metadata
                metadata = {}

        # Extract tags (#tag format)
        tags = re.findall(r"#(\w+)", content)
        tags = [tag for tag in tags if tag]  # Remove empty strings

        # Extract wikilinks [[wiki link]]
        wikilinks = re.findall(r"\[\[([^\]]+)\]\]", content)

        # Extract embeds [[!embed]] or [[!embed:file]]
        embeds = re.findall(r"\[\[!(.*?)\]\]", content)
        embeds = [e.split(":")[0].strip() if ":" in e else e.strip() for e in embeds]

        # Clean body content
        # Remove wikilinks [[...]] and embeds [[!...]]
        cleaned_content = re.sub(r"\[\[.*?\]\]", "", body_content)
        cleaned_content = re.sub(r"\n{3,}", "\n\n", cleaned_content).strip()

        return {
            "metadata": metadata,
            "content": cleaned_content,
            "tags": tags,
            "wikilinks": wikilinks,
            "embeds": embeds,
            "filepath": str(filepath) if filepath else None,
        }

    def read_note(self, relative_path: str) -> dict[str, Any]:
        """Read a specific note from the vault.

        Args:
            relative_path: Path to note relative to vault root (e.g., "My Notes/simba.md")

        Returns:
            Dictionary containing parsed note content and metadata.
        """
        vault_dir = Path(self.vault_path)
        note_path = vault_dir / relative_path

        if not note_path.exists():
            raise FileNotFoundError(f"Note not found at '{relative_path}'")

        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()

        parsed = self.parse_markdown(content, note_path)

        return {
            "content": parsed,
            "path": relative_path,
            "full_path": str(note_path),
        }

    def create_note(
        self,
        title: str,
        content: str,
        folder: str = "notes",
        tags: Optional[list[str]] = None,
        frontmatter: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a new note in the vault.

        Args:
            title: Note title (will be used as filename)
            content: Note body content
            folder: Folder path (default: "notes")
            tags: List of tags to add
            frontmatter: Optional custom frontmatter to merge with defaults

        Returns:
            Path to created note (relative to vault root).
        """
        vault_dir = Path(self.vault_path)
        note_folder = vault_dir / folder
        note_folder.mkdir(parents=True, exist_ok=True)

        # Sanitize title for filename
        safe_title = re.sub(r"[^a-z0-9-_]", "-", title.lower().strip())
        safe_title = re.sub(r"-+", "-", safe_title).strip("-")

        note_path = note_folder / f"{safe_title}.md"

        # Build frontmatter
        default_frontmatter = {
            "created_by": "simbarag",
            "created_at": datetime.now().isoformat(),
        }

        if frontmatter:
            default_frontmatter.update(frontmatter)

        # Add tags to frontmatter if provided
        if tags:
            default_frontmatter.setdefault("tags", []).extend(tags)

        # Write note
        frontmatter_yaml = yaml.dump(default_frontmatter, allow_unicode=True, default_flow_style=False)
        full_content = f"---\n{frontmatter_yaml}---\n\n{content}"

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return f"{folder}/{safe_title}.md"

    def create_task(
        self,
        title: str,
        content: str = "",
        folder: str = "tasks",
        due_date: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """Create a task note in the vault.

        Args:
            title: Task title
            content: Task description
            folder: Folder to place task (default: "tasks")
            due_date: Optional due date in YYYY-MM-DD format
            tags: Optional list of tags to add

        Returns:
            Path to created task note (relative to vault root).
        """
        task_content = f"# {title}\n\n{content}"

        # Add checkboxes if content is empty (simple task)
        if not content.strip():
            task_content += "\n- [ ]"

        # Add due date if provided
        if due_date:
            task_content += f"\n\n**Due**: {due_date}"

        # Add tags if provided
        if tags:
            task_content += "\n\n" + " ".join([f"#{tag}" for tag in tags])

        return self.create_note(
            title=title,
            content=task_content,
            folder=folder,
            tags=tags,
        )

    def get_daily_note_path(self, date: Optional[datetime] = None) -> str:
        """Return the relative vault path for a daily note.

        Args:
            date: Date for the note (defaults to today)

        Returns:
            Relative path like "journal/2026/2026-03-03.md"
        """
        if date is None:
            date = datetime.now()
        return f"journal/{date.strftime('%Y')}/{date.strftime('%Y-%m-%d')}.md"

    def get_daily_note(self, date: Optional[datetime] = None) -> dict[str, Any]:
        """Read a daily note from the vault.

        Args:
            date: Date for the note (defaults to today)

        Returns:
            Dictionary with found status, path, raw content, and date string.
        """
        if date is None:
            date = datetime.now()
        relative_path = self.get_daily_note_path(date)
        note_path = Path(self.vault_path) / relative_path

        if not note_path.exists():
            return {"found": False, "path": relative_path, "content": None, "date": date.strftime("%Y-%m-%d")}

        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {"found": True, "path": relative_path, "content": content, "date": date.strftime("%Y-%m-%d")}

    def get_daily_tasks(self, date: Optional[datetime] = None) -> dict[str, Any]:
        """Extract tasks from a daily note's tasks section.

        Args:
            date: Date for the note (defaults to today)

        Returns:
            Dictionary with tasks list (each has "text" and "done" keys) and metadata.
        """
        if date is None:
            date = datetime.now()
        note = self.get_daily_note(date)
        if not note["found"]:
            return {"found": False, "tasks": [], "date": note["date"], "path": note["path"]}

        tasks = []
        in_tasks = False
        for line in note["content"].split("\n"):
            if re.match(r"^###\s+tasks\s*$", line, re.IGNORECASE):
                in_tasks = True
                continue
            if in_tasks and re.match(r"^#{1,3}\s", line):
                break
            if in_tasks:
                done_match = re.match(r"^- \[x\] (.+)$", line, re.IGNORECASE)
                todo_match = re.match(r"^- \[ \] (.+)$", line)
                if done_match:
                    tasks.append({"text": done_match.group(1), "done": True})
                elif todo_match:
                    tasks.append({"text": todo_match.group(1), "done": False})

        return {"found": True, "tasks": tasks, "date": note["date"], "path": note["path"]}

    def add_task_to_daily_note(self, task_text: str, date: Optional[datetime] = None) -> dict[str, Any]:
        """Add a task checkbox to a daily note, creating the note if needed.

        Args:
            task_text: The task description text
            date: Date for the note (defaults to today)

        Returns:
            Dictionary with success status, path, and whether note was created.
        """
        if date is None:
            date = datetime.now()
        relative_path = self.get_daily_note_path(date)
        note_path = Path(self.vault_path) / relative_path

        if not note_path.exists():
            note_path.parent.mkdir(parents=True, exist_ok=True)
            content = (
                f"---\nmodified: {datetime.now().isoformat()}\n---\n"
                f"### tasks\n\n- [ ] {task_text}\n\n### log\n"
            )
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "created_note": True, "path": relative_path}

        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Insert before ### log if present, otherwise append before end
        log_match = re.search(r"\n(### log)", content, re.IGNORECASE)
        if log_match:
            insert_pos = log_match.start()
            content = content[:insert_pos] + f"\n- [ ] {task_text}" + content[insert_pos:]
        else:
            content = content.rstrip() + f"\n- [ ] {task_text}\n"

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {"success": True, "created_note": False, "path": relative_path}

    def complete_task_in_daily_note(self, task_text: str, date: Optional[datetime] = None) -> dict[str, Any]:
        """Mark a task as complete in a daily note by matching task text.

        Searches for a task matching the given text (exact or partial) and
        replaces `- [ ]` with `- [x]`.

        Args:
            task_text: The task text to search for (exact or partial match)
            date: Date for the note (defaults to today)

        Returns:
            Dictionary with success status, matched task text, and path.
        """
        if date is None:
            date = datetime.now()
        relative_path = self.get_daily_note_path(date)
        note_path = Path(self.vault_path) / relative_path

        if not note_path.exists():
            return {"success": False, "error": "Note not found", "path": relative_path}

        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try exact match first, then partial
        exact = f"- [ ] {task_text}"
        if exact in content:
            content = content.replace(exact, f"- [x] {task_text}", 1)
        else:
            match = re.search(r"- \[ \] .*" + re.escape(task_text) + r".*", content, re.IGNORECASE)
            if not match:
                return {"success": False, "error": f"Task '{task_text}' not found", "path": relative_path}
            completed = match.group(0).replace("- [ ]", "- [x]", 1)
            content = content.replace(match.group(0), completed, 1)
            task_text = match.group(0).replace("- [ ] ", "")

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {"success": True, "completed_task": task_text, "path": relative_path}

    def sync_vault(self) -> dict[str, Any]:
        """Trigger a one-time sync of the vault.

        Returns:
            Dictionary containing sync result and output.
        """
        try:
            result = run(
                ["ob", "sync"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr or "Sync failed",
                    "stdout": result.stdout,
                }

            return {
                "success": True,
                "message": "Vault synced successfully",
                "stdout": result.stdout,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def sync_status(self) -> dict[str, Any]:
        """Check sync status of the vault.

        Returns:
            Dictionary containing sync status information.
        """
        try:
            result = run(
                ["ob", "sync-status"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "success": True,
                "output": result.stdout,
                "stderr": result.stderr,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
