"""Tests for marketplace configuration files."""

import json
import re

import pytest
import yaml


class TestPluginJson:
    """Test .claude-plugin/plugin.json structure."""

    @pytest.fixture
    def plugin_json(self, skill_root):
        """Load plugin.json content."""
        path = skill_root / ".claude-plugin" / "plugin.json"
        return json.loads(path.read_text())

    def test_has_name(self, plugin_json):
        """plugin.json must have name field."""
        assert "name" in plugin_json
        assert plugin_json["name"] == "rhdh"

    def test_has_description(self, plugin_json):
        """plugin.json must have description field."""
        assert "description" in plugin_json
        assert len(plugin_json["description"]) > 10

    def test_has_version(self, plugin_json):
        """plugin.json must have version field."""
        assert "version" in plugin_json
        # Should be semver format
        version = plugin_json["version"]
        parts = version.split(".")
        assert len(parts) == 3, f"Version should be semver: {version}"

    def test_has_license(self, plugin_json):
        """plugin.json must have license field."""
        assert "license" in plugin_json

    def test_has_keywords(self, plugin_json):
        """plugin.json should have keywords array."""
        assert "keywords" in plugin_json
        assert isinstance(plugin_json["keywords"], list)
        assert len(plugin_json["keywords"]) > 0


class TestMarketplaceJson:
    """Test .claude-plugin/marketplace.json structure."""

    @pytest.fixture
    def marketplace_json(self, skill_root):
        """Load marketplace.json content."""
        path = skill_root / ".claude-plugin" / "marketplace.json"
        return json.loads(path.read_text())

    def test_has_name(self, marketplace_json):
        """marketplace.json must have name field."""
        assert "name" in marketplace_json
        assert marketplace_json["name"] == "rhdh"

    def test_has_owner(self, marketplace_json):
        """marketplace.json must have owner field."""
        assert "owner" in marketplace_json
        assert "name" in marketplace_json["owner"]

    def test_has_metadata(self, marketplace_json):
        """marketplace.json must have metadata field."""
        assert "metadata" in marketplace_json
        assert "version" in marketplace_json["metadata"]

    def test_has_plugins_array(self, marketplace_json):
        """marketplace.json must have plugins array."""
        assert "plugins" in marketplace_json
        assert isinstance(marketplace_json["plugins"], list)
        assert len(marketplace_json["plugins"]) >= 1

    def test_plugin_entry_has_required_fields(self, marketplace_json):
        """Each plugin entry must have required fields."""
        for plugin in marketplace_json["plugins"]:
            assert "name" in plugin
            assert "source" in plugin
            assert "version" in plugin


class TestCommandFiles:
    """Test command files have proper structure."""

    @pytest.fixture
    def command_files(self, skill_root):
        """Get all command files."""
        commands_dir = skill_root / "commands"
        return list(commands_dir.glob("*.md"))

    def test_commands_exist(self, command_files):
        """At least one command should exist."""
        assert len(command_files) >= 1

    def test_command_has_frontmatter(self, command_files):
        """Each command should have YAML frontmatter."""
        for cmd in command_files:
            content = cmd.read_text()
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            assert match, f"{cmd.name} missing YAML frontmatter"

            frontmatter = yaml.safe_load(match.group(1))
            assert "description" in frontmatter, f"{cmd.name} missing description"

    def test_command_has_allowed_tools(self, command_files):
        """Each command should specify allowed-tools."""
        for cmd in command_files:
            content = cmd.read_text()
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            assert match, f"{cmd.name} missing YAML frontmatter"
            frontmatter = yaml.safe_load(match.group(1))

            assert "allowed-tools" in frontmatter, f"{cmd.name} missing allowed-tools"
            # Should reference the skill
            assert "Skill" in frontmatter["allowed-tools"], (
                f"{cmd.name} allowed-tools should reference Skill"
            )


class TestSettingsJson:
    """Test .claude/settings.json structure."""

    @pytest.fixture
    def settings_json(self, skill_root):
        """Load settings.json content."""
        path = skill_root / ".claude" / "settings.json"
        return json.loads(path.read_text())

    def test_has_commands(self, settings_json):
        """settings.json should have commands section."""
        assert "commands" in settings_json
        assert len(settings_json["commands"]) >= 1

    def test_has_skills(self, settings_json):
        """settings.json should have skills section."""
        assert "skills" in settings_json
        assert "rhdh" in settings_json["skills"]

    def test_skill_has_path(self, settings_json):
        """Skill entry should have path."""
        skill = settings_json["skills"]["rhdh"]
        assert "path" in skill

    def test_command_paths_are_valid(self, settings_json, skill_root):
        """Command paths should resolve to existing files."""
        claude_dir = skill_root / ".claude"

        for name, cmd in settings_json["commands"].items():
            if "path" in cmd:
                # Resolve relative path from .claude/
                cmd_path = (claude_dir / cmd["path"]).resolve()
                assert cmd_path.exists(), f"Command {name} path does not exist: {cmd_path}"
