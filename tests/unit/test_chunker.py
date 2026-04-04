"""Tests for text preprocessing functions in utils/chunker.py."""

from utils.chunker import (
    remove_headers_footers,
    remove_special_characters,
    remove_repeated_substrings,
    remove_extra_spaces,
    preprocess_text,
)


class TestRemoveHeadersFooters:
    def test_removes_default_header(self):
        text = "Header Line\nActual content here"
        result = remove_headers_footers(text)
        assert "Header" not in result
        assert "Actual content here" in result

    def test_removes_default_footer(self):
        text = "Actual content\nFooter Line"
        result = remove_headers_footers(text)
        assert "Footer" not in result
        assert "Actual content" in result

    def test_custom_patterns(self):
        text = "PAGE 1\nContent\nCopyright 2024"
        result = remove_headers_footers(
            text,
            header_patterns=[r"^PAGE \d+$"],
            footer_patterns=[r"^Copyright.*$"],
        )
        assert "PAGE 1" not in result
        assert "Copyright" not in result
        assert "Content" in result

    def test_no_match_preserves_text(self):
        text = "Just normal content"
        result = remove_headers_footers(text)
        assert result == "Just normal content"

    def test_empty_string(self):
        assert remove_headers_footers("") == ""


class TestRemoveSpecialCharacters:
    def test_removes_special_chars(self):
        text = "Hello @world #test $100"
        result = remove_special_characters(text)
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_preserves_allowed_chars(self):
        text = "Hello, world! How's it going? Yes-no."
        result = remove_special_characters(text)
        assert "," in result
        assert "!" in result
        assert "'" in result
        assert "?" in result
        assert "-" in result
        assert "." in result

    def test_custom_pattern(self):
        text = "keep @this but not #that"
        result = remove_special_characters(text, special_chars=r"[#]")
        assert "@this" in result
        assert "#" not in result

    def test_empty_string(self):
        assert remove_special_characters("") == ""


class TestRemoveRepeatedSubstrings:
    def test_collapses_dots(self):
        text = "Item.....Value"
        result = remove_repeated_substrings(text)
        assert result == "Item.Value"

    def test_single_dot_preserved(self):
        text = "End of sentence."
        result = remove_repeated_substrings(text)
        assert result == "End of sentence."

    def test_custom_pattern(self):
        text = "hello---world"
        result = remove_repeated_substrings(text, pattern=r"-{2,}")
        # Function always replaces matched pattern with "."
        assert result == "hello.world"

    def test_empty_string(self):
        assert remove_repeated_substrings("") == ""


class TestRemoveExtraSpaces:
    def test_collapses_multiple_blank_lines(self):
        text = "Line 1\n\n\n\nLine 2"
        result = remove_extra_spaces(text)
        # After collapsing newlines to \n\n, then \s+ collapses everything to single spaces
        assert "\n\n\n" not in result

    def test_collapses_multiple_spaces(self):
        text = "Hello    world"
        result = remove_extra_spaces(text)
        assert result == "Hello world"

    def test_strips_whitespace(self):
        text = "  Hello world  "
        result = remove_extra_spaces(text)
        assert result == "Hello world"

    def test_empty_string(self):
        assert remove_extra_spaces("") == ""


class TestPreprocessText:
    def test_full_pipeline(self):
        text = "Header Info\nHello @world...  with   spaces\nFooter Info"
        result = preprocess_text(text)
        assert "Header" not in result
        assert "Footer" not in result
        assert "@" not in result
        assert "..." not in result
        assert "   " not in result

    def test_preserves_meaningful_content(self):
        text = "The cat weighs 10 pounds."
        result = preprocess_text(text)
        assert "cat" in result
        assert "10" in result
        assert "pounds" in result

    def test_empty_string(self):
        assert preprocess_text("") == ""

    def test_already_clean(self):
        text = "Simple clean text here."
        result = preprocess_text(text)
        assert "Simple" in result
        assert "clean" in result
