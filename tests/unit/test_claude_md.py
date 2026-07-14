"""Tests for AGENTS.md (and CLAUDE.md symlink) structure and content."""

import pytest


class TestAgentsMdStructure:
    """Test that AGENTS.md has required structure."""

    @pytest.fixture
    def agents_md(self, skill_root):
        """Load AGENTS.md content."""
        agents_path = skill_root / "AGENTS.md"
        assert agents_path.exists(), "AGENTS.md must exist at project root"
        return agents_path.read_text()

    def test_agents_md_exists(self, skill_root):
        """AGENTS.md must exist at project root."""
        assert (skill_root / "AGENTS.md").exists()

    def test_claude_md_exists(self, skill_root):
        """CLAUDE.md must exist at project root."""
        claude_path = skill_root / "CLAUDE.md"
        assert claude_path.exists(), "CLAUDE.md must exist at project root"

    def test_claude_md_points_to_agents(self, skill_root):
        """CLAUDE.md should use @AGENTS.md directive."""
        content = (skill_root / "CLAUDE.md").read_text().strip()
        assert content == "@AGENTS.md", f"CLAUDE.md should contain '@AGENTS.md', got: {content!r}"

    def test_has_think_before_coding_rule(self, agents_md):
        """AGENTS.md must mention think before coding."""
        assert "Think Before Coding" in agents_md

    def test_has_simplicity_rule(self, agents_md):
        """AGENTS.md must mention simplicity first."""
        assert "Simplicity First" in agents_md

    def test_has_surgical_changes_rule(self, agents_md):
        """AGENTS.md must mention surgical changes."""
        assert "Surgical Changes" in agents_md

    def test_has_goal_driven_rule(self, agents_md):
        """AGENTS.md must mention goal-driven execution."""
        assert "Goal-Driven Execution" in agents_md

    def test_has_verification_command(self, agents_md):
        """AGENTS.md should reference test verification."""
        assert "uv run pytest" in agents_md

    def test_has_versioning_section(self, agents_md):
        """AGENTS.md should document versioning."""
        assert "## Versioning" in agents_md
        assert "git tag" in agents_md

    def test_has_agent_skills_section(self, agents_md):
        """AGENTS.md should have agent skills config section."""
        assert "## Agent skills" in agents_md
        assert "issue-tracker.md" in agents_md
        assert "triage-labels.md" in agents_md
        assert "domain.md" in agents_md
