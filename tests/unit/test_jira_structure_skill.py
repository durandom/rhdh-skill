"""Tests for jira-structure reference content validation."""

from pathlib import Path

import pytest

JIRA_STRUCTURE_REF = (
    Path(__file__).parent.parent.parent
    / "skills"
    / "rhdh"
    / "references"
    / "jira-structure.md"
)


@pytest.fixture
def jira_structure_content():
    """Load jira-structure.md reference content."""
    return JIRA_STRUCTURE_REF.read_text()


class TestJiraStructureReference:
    """Test that jira-structure.md reference has required content."""

    def test_reference_exists(self):
        """jira-structure.md must exist."""
        assert JIRA_STRUCTURE_REF.exists()

    def test_mentions_jira_projects(self, jira_structure_content):
        """Reference should mention the key Jira projects."""
        assert "RHIDP" in jira_structure_content
        assert "RHDHPLAN" in jira_structure_content
        assert "RHDHSUPP" in jira_structure_content
        assert "RHDHBUGS" in jira_structure_content


    def test_mentions_issue_types(self, jira_structure_content):
        """Reference should list issue types."""
        assert "Story" in jira_structure_content
        assert "Task" in jira_structure_content
        assert "Epic" in jira_structure_content
        assert "Feature" in jira_structure_content
        assert "Bug" in jira_structure_content

    def test_has_key_rules(self, jira_structure_content):
        """Reference should include key filing rules."""
        assert "Key Rules" in jira_structure_content

    def test_old_skill_directory_removed(self):
        """The separate rhdh-jira-structure skill directory should not exist."""
        old_skill_dir = (
            Path(__file__).parent.parent.parent / "skills" / "rhdh-jira-structure"
        )
        assert not old_skill_dir.exists(), (
            "skills/rhdh-jira-structure/ should be removed — "
            "content moved to skills/rhdh/references/jira-structure.md"
        )
