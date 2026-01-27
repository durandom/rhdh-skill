"""Tests for SKILL.md structure and content validation."""

import re

import pytest
import yaml


class TestSkillMdStructure:
    """Test that SKILL.md has required structure."""

    @pytest.fixture
    def skill_md(self, skills_dir):
        """Load SKILL.md content."""
        skill_path = skills_dir / "SKILL.md"
        return skill_path.read_text()

    @pytest.fixture
    def skill_frontmatter(self, skill_md):
        """Parse YAML frontmatter from SKILL.md."""
        match = re.match(r"^---\n(.*?)\n---", skill_md, re.DOTALL)
        if not match:
            pytest.fail("SKILL.md missing YAML frontmatter")
        return yaml.safe_load(match.group(1))

    def test_frontmatter_has_name(self, skill_frontmatter):
        """SKILL.md must have a name field."""
        assert "name" in skill_frontmatter
        assert skill_frontmatter["name"] == "rhdh-plugin"

    def test_frontmatter_has_description(self, skill_frontmatter):
        """SKILL.md must have a description field."""
        assert "description" in skill_frontmatter
        assert len(skill_frontmatter["description"]) > 20

    def test_has_cli_setup_section(self, skill_md):
        """SKILL.md must have <cli_setup> section."""
        assert "<cli_setup>" in skill_md
        assert "</cli_setup>" in skill_md
        assert "CLAUDE_PLUGIN_ROOT" in skill_md

    def test_has_essential_principles(self, skill_md):
        """SKILL.md must have <essential_principles> section."""
        assert "<essential_principles>" in skill_md
        assert "</essential_principles>" in skill_md

    def test_has_intake_section(self, skill_md):
        """SKILL.md must have <intake> section with menu."""
        assert "<intake>" in skill_md
        assert "</intake>" in skill_md
        # Should have numbered options
        assert re.search(r"1\.\s+\*\*", skill_md)

    def test_has_routing_section(self, skill_md):
        """SKILL.md must have <routing> section with table."""
        assert "<routing>" in skill_md
        assert "</routing>" in skill_md
        # Should have markdown table
        assert "| Response |" in skill_md or "| Intent |" in skill_md

    def test_has_cli_commands_section(self, skill_md):
        """SKILL.md must have <cli_commands> section."""
        assert "<cli_commands>" in skill_md
        assert "</cli_commands>" in skill_md
        assert "$RHDH_PLUGIN" in skill_md

    def test_has_success_criteria(self, skill_md):
        """SKILL.md must have <success_criteria> section."""
        assert "<success_criteria>" in skill_md
        assert "</success_criteria>" in skill_md

    def test_references_cli_variable(self, skill_md):
        """SKILL.md should use $RHDH_PLUGIN variable consistently."""
        # Count references to the variable
        matches = re.findall(r"\$RHDH_PLUGIN", skill_md)
        assert len(matches) >= 3, "Should reference $RHDH_PLUGIN multiple times"

    def test_no_markdown_headings_in_xml_body(self, skill_md):
        """XML sections should not use markdown headings (# or ##) outside code blocks."""
        # Extract content between xml tags (excluding sections that commonly have code)
        excluded = r"quick_start|cli_commands|inline_status_check|context_scan"
        xml_sections = re.findall(rf"<(?!{excluded})(\w+)>(.*?)</\1>", skill_md, re.DOTALL)

        for section_name, content in xml_sections:
            # Track if we're inside a code block
            in_code_block = False
            lines = content.split("\n")

            for line in lines:
                # Toggle code block state
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue

                # Skip lines in code blocks and table lines
                if in_code_block or line.strip().startswith("|"):
                    continue

                # Check for markdown headings at start of line
                if re.match(r"^#{1,3}\s", line.strip()):
                    # Allow in sections that commonly use subheadings for organization
                    allowed_sections = ("intake", "routing", "workflows_index", "success_criteria")
                    if section_name in allowed_sections:
                        continue
                    pytest.fail(f"Found markdown heading in <{section_name}>: {line.strip()}")


class TestWorkflowStructure:
    """Test that workflow files have required structure."""

    @pytest.fixture
    def workflow_files(self, skills_dir):
        """Get all workflow files."""
        workflows_dir = skills_dir / "workflows"
        return list(workflows_dir.glob("*.md"))

    def test_workflows_exist(self, workflow_files):
        """At least one workflow should exist."""
        assert len(workflow_files) >= 1

    def test_workflow_has_required_reading(self, workflow_files):
        """Each workflow should have <required_reading> section."""
        for workflow in workflow_files:
            content = workflow.read_text()
            assert "<required_reading>" in content or "<prerequisites>" in content, (
                f"{workflow.name} missing required_reading or prerequisites"
            )

    def test_workflow_has_process(self, workflow_files):
        """Each workflow should have <process> section."""
        for workflow in workflow_files:
            content = workflow.read_text()
            assert "<process>" in content, f"{workflow.name} missing <process> section"
            assert "</process>" in content, f"{workflow.name} missing </process> closing tag"

    def test_workflow_has_success_criteria(self, workflow_files):
        """Each workflow should have <success_criteria> section."""
        for workflow in workflow_files:
            content = workflow.read_text()
            assert "<success_criteria>" in content, (
                f"{workflow.name} missing <success_criteria> section"
            )


class TestReferenceStructure:
    """Test that reference files have required structure."""

    @pytest.fixture
    def reference_files(self, skills_dir):
        """Get all reference files."""
        refs_dir = skills_dir / "references"
        return list(refs_dir.glob("*.md"))

    def test_references_exist(self, reference_files):
        """At least one reference should exist."""
        assert len(reference_files) >= 1

    def test_reference_has_xml_sections(self, reference_files):
        """Reference files should use XML tags for structure (optional for cheatsheets)."""
        # Some reference files are practical cheatsheets without XML structure
        xml_optional = {"jira-reference.md", "github-tips.md"}

        for ref in reference_files:
            if ref.name in xml_optional:
                continue
            content = ref.read_text()
            # Should have at least one XML tag
            has_xml = bool(re.search(r"<\w+>", content))
            assert has_xml, f"{ref.name} should use XML tags for structure"


class TestTemplateStructure:
    """Test that template files exist and are valid."""

    @pytest.fixture
    def template_files(self, skills_dir):
        """Get all template files."""
        templates_dir = skills_dir / "templates"
        return list(templates_dir.glob("*.md"))

    def test_templates_exist(self, template_files):
        """At least one template should exist."""
        assert len(template_files) >= 1

    def test_template_has_code_blocks(self, template_files):
        """Templates should contain code block examples."""
        for template in template_files:
            content = template.read_text()
            assert "```" in content, f"{template.name} should have code block examples"
