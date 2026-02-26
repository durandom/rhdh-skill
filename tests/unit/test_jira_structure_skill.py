"""Tests for jira-structure skill structure and content validation."""

import re
from pathlib import Path

import pytest
import yaml

JIRA_STRUCTURE_SKILL_DIR = Path(__file__).parent.parent.parent / "skills" / "jira-structure"


@pytest.fixture
def jira_skill_dir():
    """Return the jira-structure skill directory path."""
    return JIRA_STRUCTURE_SKILL_DIR


@pytest.fixture
def skill_md(jira_skill_dir):
    """Load jira-structure SKILL.md content."""
    skill_path = jira_skill_dir / "SKILL.md"
    return skill_path.read_text()


@pytest.fixture
def skill_frontmatter(skill_md):
    """Parse YAML frontmatter from SKILL.md."""
    match = re.match(r"^---\n(.*?)\n---", skill_md, re.DOTALL)
    if not match:
        pytest.fail("SKILL.md missing YAML frontmatter")
    return yaml.safe_load(match.group(1))


class TestJiraStructureSkillMd:
    """Test that jira-structure SKILL.md has required structure."""

    def test_skill_md_exists(self, jira_skill_dir):
        """SKILL.md must exist."""
        assert (jira_skill_dir / "SKILL.md").exists()

    def test_frontmatter_has_name(self, skill_frontmatter):
        """SKILL.md must have a name field."""
        assert "name" in skill_frontmatter
        assert skill_frontmatter["name"] == "jira-structure"

    def test_frontmatter_has_description(self, skill_frontmatter):
        """SKILL.md must have a description field with trigger phrases."""
        assert "description" in skill_frontmatter
        desc = skill_frontmatter["description"]
        assert len(desc) > 20
        assert "This skill" in desc

    def test_description_has_trigger_phrases(self, skill_frontmatter):
        """Description should include specific trigger phrases."""
        desc = skill_frontmatter["description"].lower()
        assert "jira" in desc

    def test_mentions_jira_projects(self, skill_md):
        """SKILL.md should mention the key Jira projects."""
        assert "RHIDP" in skill_md
        assert "RHDHPLAN" in skill_md
        assert "RHDHSUPP" in skill_md
        assert "RHDHBUGS" in skill_md

    def test_mentions_issue_types(self, skill_md):
        """SKILL.md should list issue types."""
        assert "Story" in skill_md
        assert "Task" in skill_md
        assert "Epic" in skill_md
        assert "Feature" in skill_md
        assert "Bug" in skill_md
