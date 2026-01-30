"""Tests for CLAUDE.md structure and content."""

import pytest


class TestClaudeMdStructure:
    """Test that CLAUDE.md has required structure."""

    @pytest.fixture
    def claude_md(self, skill_root):
        """Load CLAUDE.md content."""
        claude_path = skill_root / "CLAUDE.md"
        assert claude_path.exists(), "CLAUDE.md must exist at project root"
        return claude_path.read_text()

    def test_claude_md_exists(self, skill_root):
        """CLAUDE.md must exist at project root."""
        assert (skill_root / "CLAUDE.md").exists()

    def test_has_tdd_rule(self, claude_md):
        """CLAUDE.md must mention TDD-first development."""
        assert "TDD" in claude_md
        assert "test" in claude_md.lower()

    def test_references_test_file(self, claude_md):
        """CLAUDE.md should reference test examples."""
        assert "test_skill_structure.py" in claude_md

    def test_has_project_structure(self, claude_md):
        """CLAUDE.md should document project structure."""
        assert "rhdh/" in claude_md
        assert "skills/" in claude_md
        assert "tests/" in claude_md

    def test_has_cli_section(self, claude_md):
        """CLAUDE.md should document CLI usage."""
        assert "rhdh" in claude_md
        assert "uv run" in claude_md

    def test_documents_output_format(self, claude_md):
        """CLAUDE.md should explain JSON/human output detection."""
        assert "JSON" in claude_md
        assert "TTY" in claude_md or "human" in claude_md.lower()
