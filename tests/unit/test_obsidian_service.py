"""Tests for ObsidianService markdown parsing and file operations."""

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Set vault path before importing so __init__ validation passes
_test_vault_dir = None


@pytest.fixture(autouse=True)
def vault_dir(tmp_path):
    """Create a temporary vault directory with a sample .md file."""
    global _test_vault_dir
    _test_vault_dir = tmp_path

    # Create a sample markdown file so vault validation passes
    sample = tmp_path / "sample.md"
    sample.write_text("# Sample\nHello world")

    with patch.dict(os.environ, {"OBSIDIAN_VAULT_PATH": str(tmp_path)}):
        yield tmp_path


@pytest.fixture
def service(vault_dir):
    from utils.obsidian_service import ObsidianService

    return ObsidianService()


class TestParseMarkdown:
    def test_extracts_frontmatter(self, service):
        content = "---\ntitle: Test Note\ntags: [cat, vet]\n---\n\nBody content"
        result = service.parse_markdown(content)
        assert result["metadata"]["title"] == "Test Note"
        assert result["metadata"]["tags"] == ["cat", "vet"]

    def test_no_frontmatter(self, service):
        content = "Just body content with no frontmatter"
        result = service.parse_markdown(content)
        assert result["metadata"] == {}
        assert "Just body content" in result["content"]

    def test_invalid_yaml_frontmatter(self, service):
        content = "---\n: invalid: yaml: [[\n---\n\nBody"
        result = service.parse_markdown(content)
        assert result["metadata"] == {}

    def test_extracts_tags(self, service):
        content = "Some text with #tag1 and #tag2 here"
        result = service.parse_markdown(content)
        assert "tag1" in result["tags"]
        assert "tag2" in result["tags"]

    def test_extracts_wikilinks(self, service):
        content = "Link to [[Other Note]] and [[Another Page]]"
        result = service.parse_markdown(content)
        assert "Other Note" in result["wikilinks"]
        assert "Another Page" in result["wikilinks"]

    def test_extracts_embeds(self, service):
        content = "An embed [[!my_embed]] here"
        result = service.parse_markdown(content)
        assert "my_embed" in result["embeds"]

    def test_cleans_wikilinks_from_content(self, service):
        content = "Text with [[link]] included"
        result = service.parse_markdown(content)
        assert "[[" not in result["content"]
        assert "]]" not in result["content"]

    def test_filepath_passed_through(self, service):
        result = service.parse_markdown("text", filepath=Path("/vault/note.md"))
        assert result["filepath"] == "/vault/note.md"

    def test_filepath_none_by_default(self, service):
        result = service.parse_markdown("text")
        assert result["filepath"] is None

    def test_empty_content(self, service):
        result = service.parse_markdown("")
        assert result["metadata"] == {}
        assert result["tags"] == []
        assert result["wikilinks"] == []
        assert result["embeds"] == []


class TestGetDailyNotePath:
    def test_formats_path_correctly(self, service):
        date = datetime(2026, 3, 15)
        path = service.get_daily_note_path(date)
        assert path == "journal/2026/2026-03-15.md"

    def test_defaults_to_today(self, service):
        path = service.get_daily_note_path()
        today = datetime.now()
        assert today.strftime("%Y-%m-%d") in path
        assert path.startswith(f"journal/{today.strftime('%Y')}/")


class TestWalkVault:
    def test_finds_markdown_files(self, service, vault_dir):
        (vault_dir / "note1.md").write_text("# Note 1")
        (vault_dir / "subdir").mkdir()
        (vault_dir / "subdir" / "note2.md").write_text("# Note 2")

        files = service.walk_vault()
        filenames = [f.name for f in files]
        assert "sample.md" in filenames
        assert "note1.md" in filenames
        assert "note2.md" in filenames

    def test_excludes_obsidian_dir(self, service, vault_dir):
        obsidian_dir = vault_dir / ".obsidian"
        obsidian_dir.mkdir()
        (obsidian_dir / "config.md").write_text("config")

        files = service.walk_vault()
        filenames = [f.name for f in files]
        assert "config.md" not in filenames

    def test_ignores_non_md_files(self, service, vault_dir):
        (vault_dir / "image.png").write_bytes(b"\x89PNG")

        files = service.walk_vault()
        filenames = [f.name for f in files]
        assert "image.png" not in filenames


class TestCreateNote:
    def test_creates_file(self, service, vault_dir):
        path = service.create_note("My Test Note", "Body content")
        full_path = vault_dir / path
        assert full_path.exists()

    def test_sanitizes_title(self, service, vault_dir):
        path = service.create_note("Hello World! @#$", "Body")
        assert "hello-world" in path
        assert "@" not in path
        assert "#" not in path

    def test_includes_frontmatter(self, service, vault_dir):
        path = service.create_note("Test", "Body", tags=["cat", "vet"])
        full_path = vault_dir / path
        content = full_path.read_text()
        assert "---" in content
        assert "created_by: simbarag" in content
        assert "cat" in content
        assert "vet" in content

    def test_custom_folder(self, service, vault_dir):
        path = service.create_note("Test", "Body", folder="custom/subfolder")
        assert path.startswith("custom/subfolder/")
        assert (vault_dir / path).exists()


class TestDailyNoteTasks:
    def test_get_tasks_from_daily_note(self, service, vault_dir):
        # Create a daily note with tasks
        date = datetime(2026, 1, 15)
        rel_path = service.get_daily_note_path(date)
        note_path = vault_dir / rel_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(
            "---\nmodified: 2026-01-15\n---\n"
            "### tasks\n\n"
            "- [ ] Feed the cat\n"
            "- [x] Clean litter box\n"
            "- [ ] Buy cat food\n\n"
            "### log\n"
        )

        result = service.get_daily_tasks(date)
        assert result["found"] is True
        assert len(result["tasks"]) == 3
        assert result["tasks"][0] == {"text": "Feed the cat", "done": False}
        assert result["tasks"][1] == {"text": "Clean litter box", "done": True}
        assert result["tasks"][2] == {"text": "Buy cat food", "done": False}

    def test_get_tasks_no_note(self, service):
        date = datetime(2099, 12, 31)
        result = service.get_daily_tasks(date)
        assert result["found"] is False
        assert result["tasks"] == []

    def test_add_task_creates_note(self, service, vault_dir):
        date = datetime(2026, 6, 1)
        result = service.add_task_to_daily_note("Walk the cat", date)
        assert result["success"] is True
        assert result["created_note"] is True

        # Verify file was created with the task
        note_path = vault_dir / result["path"]
        content = note_path.read_text()
        assert "- [ ] Walk the cat" in content

    def test_add_task_to_existing_note(self, service, vault_dir):
        date = datetime(2026, 6, 2)
        rel_path = service.get_daily_note_path(date)
        note_path = vault_dir / rel_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(
            "---\nmodified: 2026-06-02\n---\n"
            "### tasks\n\n"
            "- [ ] Existing task\n\n"
            "### log\n"
        )

        result = service.add_task_to_daily_note("New task", date)
        assert result["success"] is True
        assert result["created_note"] is False

        content = note_path.read_text()
        assert "- [ ] Existing task" in content
        assert "- [ ] New task" in content

    def test_complete_task_exact_match(self, service, vault_dir):
        date = datetime(2026, 6, 3)
        rel_path = service.get_daily_note_path(date)
        note_path = vault_dir / rel_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text("### tasks\n\n" "- [ ] Feed the cat\n" "- [ ] Buy food\n")

        result = service.complete_task_in_daily_note("Feed the cat", date)
        assert result["success"] is True

        content = note_path.read_text()
        assert "- [x] Feed the cat" in content
        assert "- [ ] Buy food" in content  # Other task unchanged

    def test_complete_task_partial_match(self, service, vault_dir):
        date = datetime(2026, 6, 4)
        rel_path = service.get_daily_note_path(date)
        note_path = vault_dir / rel_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text("### tasks\n\n- [ ] Feed the cat at 5pm\n")

        result = service.complete_task_in_daily_note("Feed the cat", date)
        assert result["success"] is True

    def test_complete_task_not_found(self, service, vault_dir):
        date = datetime(2026, 6, 5)
        rel_path = service.get_daily_note_path(date)
        note_path = vault_dir / rel_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text("### tasks\n\n- [ ] Feed the cat\n")

        result = service.complete_task_in_daily_note("Walk the dog", date)
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_complete_task_no_note(self, service):
        date = datetime(2099, 12, 31)
        result = service.complete_task_in_daily_note("Something", date)
        assert result["success"] is False
