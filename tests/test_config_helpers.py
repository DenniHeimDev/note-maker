"""Unit tests for config_helpers module."""

from __future__ import annotations

from pathlib import Path


from config_helpers import (
    collect_preserved_lines,
    normalize_path,
    parse_env_file,
    preview_key,
    write_env_file,
)


class TestParseEnvFile:
    """Tests for parsing .env files."""

    def test_parse_env_file_with_key_value_pairs(self, tmp_path: Path) -> None:
        """Test parsing standard KEY=VALUE format."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=secret123\nHOST_PATH=/home/user\n")

        result = parse_env_file(env_file)

        assert result["API_KEY"] == "secret123"
        assert result["HOST_PATH"] == "/home/user"

    def test_parse_env_file_with_quoted_values(self, tmp_path: Path) -> None:
        """Test parsing values with quotes."""
        env_file = tmp_path / ".env"
        env_file.write_text('API_KEY="secret123"\nPATH=\'/home/user\'\n')

        result = parse_env_file(env_file)

        assert result["API_KEY"] == "secret123"
        assert result["PATH"] == "/home/user"

    def test_parse_env_file_ignores_comments(self, tmp_path: Path) -> None:
        """Test that comments are ignored."""
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nAPI_KEY=secret\n# Another comment\n")

        result = parse_env_file(env_file)

        assert "API_KEY" in result
        assert len(result) == 1

    def test_parse_env_file_ignores_empty_lines(self, tmp_path: Path) -> None:
        """Test that empty lines are ignored."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_KEY=secret\n\n\nPATH=/home\n")

        result = parse_env_file(env_file)

        assert len(result) == 2

    def test_parse_env_file_returns_empty_dict_for_missing_file(
        self, tmp_path: Path
    ) -> None:
        """Test that missing file returns empty dict."""
        env_file = tmp_path / "nonexistent.env"

        result = parse_env_file(env_file)

        assert result == {}

    def test_parse_env_file_handles_bare_api_key(self, tmp_path: Path) -> None:
        """Test parsing a file with just an API key value (no KEY=)."""
        env_file = tmp_path / ".env"
        env_file.write_text("sk-abc123xyz\n")

        result = parse_env_file(env_file)

        assert result.get("OPENAI_API_KEY") == "sk-abc123xyz"


class TestNormalizePath:
    """Tests for path normalization."""

    def test_normalize_path_expands_tilde(self) -> None:
        """Test that ~ is expanded to home directory."""
        result = normalize_path("~/Documents")
        assert "~" not in result
        assert "Documents" in result

    def test_normalize_path_resolves_relative_paths(self, tmp_path: Path) -> None:
        """Test that relative paths are resolved."""
        result = normalize_path(str(tmp_path / "subdir" / ".." / "file"))
        assert ".." not in result


class TestPreviewKey:
    """Tests for API key preview."""

    def test_preview_key_masks_middle(self) -> None:
        """Test that middle of key is masked."""
        result = preview_key("sk-1234567890abcdef")
        assert result == "sk-1...cdef"

    def test_preview_key_short_keys_unchanged(self) -> None:
        """Test that short keys are not masked."""
        result = preview_key("short")
        assert result == "short"


class TestCollectPreservedLines:
    """Tests for collecting preserved lines from env files."""

    def test_collect_preserved_lines_keeps_comments(self, tmp_path: Path) -> None:
        """Test that comments are preserved."""
        env_file = tmp_path / ".env"
        env_file.write_text("# Custom comment\nOPENAI_API_KEY=secret\nCUSTOM_VAR=value\n")

        result = collect_preserved_lines(env_file)

        assert "# Custom comment" in result
        assert "CUSTOM_VAR=value" in result

    def test_collect_preserved_lines_excludes_managed_keys(self, tmp_path: Path) -> None:
        """Test that managed keys are excluded."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "OPENAI_API_KEY=secret\nHOST_INPUT_PATH=/input\nCUSTOM_VAR=value\n"
        )

        result = collect_preserved_lines(env_file)

        # Managed keys should be excluded
        assert not any("OPENAI_API_KEY" in line for line in result)
        assert not any("HOST_INPUT_PATH" in line for line in result)
        # Custom vars should be preserved
        assert any("CUSTOM_VAR" in line for line in result)


class TestWriteEnvFile:
    """Tests for writing env files."""

    def test_write_env_file_creates_file(self, tmp_path: Path) -> None:
        """Test that env file is created with correct content."""
        env_file = tmp_path / ".env"
        values = {
            "OPENAI_API_KEY": "sk-test",
            "HOST_INPUT_PATH": "/input",
            "HOST_OUTPUT_PATH": "/output",
            "HOST_COPY_PATH": "/copy",
        }

        write_env_file(values, [], env_file)

        assert env_file.exists()
        content = env_file.read_text()
        assert 'OPENAI_API_KEY="sk-test"' in content
        assert 'HOST_INPUT_PATH="/input"' in content

    def test_write_env_file_includes_preserved_lines(self, tmp_path: Path) -> None:
        """Test that preserved lines are included."""
        env_file = tmp_path / ".env"
        values = {
            "OPENAI_API_KEY": "sk-test",
            "HOST_INPUT_PATH": "/input",
            "HOST_OUTPUT_PATH": "/output",
            "HOST_COPY_PATH": "/copy",
        }
        preserved = ["# My custom comment", "CUSTOM_VAR=myvalue"]

        write_env_file(values, preserved, env_file)

        content = env_file.read_text()
        assert "# My custom comment" in content
        assert "CUSTOM_VAR=myvalue" in content
