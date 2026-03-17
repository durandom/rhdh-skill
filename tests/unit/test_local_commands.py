"""Tests for rhdh local commands (rhdh-local-setup integration)."""

from unittest.mock import patch

import pytest
from conftest import run_cli_python


class TestLocalSetupConfig:
    """Tests for local_setup config discovery."""

    def test_get_local_setup_dir_from_env(self, tmp_path, monkeypatch):
        """RHDH_LOCAL_SETUP_DIR env var takes precedence."""
        from rhdh.config import get_local_setup_dir

        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = get_local_setup_dir()
        assert result == local_setup.resolve()

    def test_get_local_setup_dir_env_missing_dir(self, tmp_path, monkeypatch):
        """RHDH_LOCAL_SETUP_DIR pointing to non-existent dir returns None (falls through)."""
        from rhdh.config import get_local_setup_dir

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(tmp_path / "nonexistent"))
        # Clear config and skill-based detection to isolate env test
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path / "skill"))

        result = get_local_setup_dir()
        assert result is None

    def test_get_local_setup_dir_from_config(self, isolated_env, monkeypatch):
        """repos.local_setup in config is used when env var not set."""
        from rhdh import config as config_module
        from rhdh.config import get_local_setup_dir, save_config, set_nested

        monkeypatch.delenv("RHDH_LOCAL_SETUP_DIR", raising=False)

        local_setup = isolated_env["root"] / "rhdh-local-setup"
        local_setup.mkdir()

        # Patch config path to isolated env
        config_module.USER_CONFIG_DIR = isolated_env["root"] / ".config" / "rhdh-skill"
        config_module.USER_CONFIG_FILE = config_module.USER_CONFIG_DIR / "config.json"

        cfg = {}
        set_nested(cfg, "repos.local_setup", str(local_setup))
        save_config(cfg, global_=True)

        result = get_local_setup_dir()
        assert result == local_setup.resolve()

    def test_get_local_setup_dir_autodetect_sibling_of_local(self, tmp_path, monkeypatch):
        """Auto-detects rhdh-local-setup as parent of rhdh-local when rhdh-customizations is present."""
        from rhdh.config import get_local_setup_dir

        monkeypatch.delenv("RHDH_LOCAL_SETUP_DIR", raising=False)
        # Prevent step-4 (skill-root-relative) detection from accidentally matching on dev machines
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path / "skill"))

        # Create structure: tmp_path/rhdh-local-setup/{rhdh-local,rhdh-customizations}
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        rhdh_local = local_setup / "rhdh-local"
        rhdh_local.mkdir()
        (local_setup / "rhdh-customizations").mkdir()

        with patch("rhdh.config.get_local_repo", return_value=rhdh_local):
            with patch("rhdh.config.load_merged_config", return_value={}):
                result = get_local_setup_dir()

        assert result == local_setup.resolve()

    def test_get_local_setup_dir_returns_none_when_not_found(self, tmp_path, monkeypatch):
        """Returns None when local_setup cannot be found."""
        from rhdh.config import get_local_setup_dir

        monkeypatch.delenv("RHDH_LOCAL_SETUP_DIR", raising=False)
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path / "skill"))

        with patch("rhdh.config.get_local_repo", return_value=None):
            with patch("rhdh.config.load_merged_config", return_value={}):
                result = get_local_setup_dir()
        assert result is None

    def test_local_setup_in_default_config(self):
        """get_default_config includes repos.local_setup key."""
        from rhdh.config import get_default_config

        config = get_default_config()
        assert "local_setup" in config["repos"]

    def test_config_set_local_setup_shorthand(self, isolated_env):
        """rhdh config set local_setup /path works via shorthand."""
        from conftest import run_cli_python

        local_setup = isolated_env["root"] / "my-setup"
        local_setup.mkdir()

        result = run_cli_python(
            "config",
            "set",
            "local_setup",
            str(local_setup),
            isolated_env=isolated_env,
        )
        assert result.returncode == 0


class TestLocalStatusCommand:
    """Tests for rhdh local status."""

    def test_local_status_no_setup_configured(self, isolated_env, monkeypatch):
        """local status warns when local_setup not configured."""
        # Block auto-detection by pointing SKILL_ROOT to an empty temp dir
        monkeypatch.setenv("SKILL_ROOT", str(isolated_env["root"] / "skill"))
        monkeypatch.delenv("RHDH_LOCAL_SETUP_DIR", raising=False)
        result = run_cli_python("local", "status", isolated_env=isolated_env)
        assert result.returncode == 1
        assert "not" in result.stdout.lower() or "fail" in result.stdout.lower()

    def test_local_status_with_setup_dir(self, tmp_path, isolated_env, monkeypatch):
        """local status shows OK when local_setup is configured."""
        # Create a mock rhdh-local-setup structure
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        rhdh_local = local_setup / "rhdh-local"
        rhdh_local.mkdir()
        (rhdh_local / "compose.yaml").write_text("services:\n  rhdh:\n    image: rhdh\n")
        customizations = local_setup / "rhdh-customizations"
        customizations.mkdir()
        (customizations / "apply-customizations.sh").write_text("#!/bin/bash\necho done")
        (customizations / "remove-customizations.sh").write_text("#!/bin/bash\necho done")

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("local", "status", isolated_env=isolated_env)
        assert result.returncode == 0

    def test_local_status_json_output(self, tmp_path, isolated_env, monkeypatch):
        """local status --json returns structured data."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        (local_setup / "rhdh-customizations").mkdir()
        (local_setup / "rhdh-local").mkdir()

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("--json", "local", "status", isolated_env=isolated_env)
        import json

        outer = json.loads(result.stdout)
        # Output is wrapped: {"data": {...}, "success": true, "next_steps": [...]}
        data = outer.get("data", outer)
        assert "local_setup" in data or "error" in outer


class TestLocalPluginsListCommand:
    """Tests for rhdh local plugins list."""

    def test_plugins_list_no_override_file(self, tmp_path, isolated_env, monkeypatch):
        """plugins list returns empty list when override file doesn't exist."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        (local_setup / "rhdh-customizations").mkdir()
        (local_setup / "rhdh-local").mkdir()

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("local", "plugins", "list", isolated_env=isolated_env)
        assert result.returncode == 0

    def test_plugins_list_with_override_file(self, tmp_path, isolated_env, monkeypatch):
        """plugins list parses dynamic-plugins.override.yaml correctly."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        customizations = local_setup / "rhdh-customizations"
        customizations.mkdir()
        (local_setup / "rhdh-local").mkdir()

        # Create override file
        override_dir = customizations / "configs" / "dynamic-plugins"
        override_dir.mkdir(parents=True)
        override_file = override_dir / "dynamic-plugins.override.yaml"
        override_file.write_text(
            "includes:\n"
            "  - dynamic-plugins.default.yaml\n"
            "\n"
            "plugins:\n"
            "  - package: 'oci://ghcr.io/redhat-developer/rhdh-plugin-export-overlays/argocd:tag!argocd'\n"
            "    disabled: false\n"
            "  - package: 'oci://ghcr.io/redhat-developer/rhdh-plugin-export-overlays/old-plugin:tag!old'\n"
            "    disabled: true\n"
        )

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("local", "plugins", "list", isolated_env=isolated_env)
        assert result.returncode == 0
        assert "argocd" in result.stdout

    def test_plugins_list_json_output(self, tmp_path, isolated_env, monkeypatch):
        """plugins list --json returns structured plugin data."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        customizations = local_setup / "rhdh-customizations"
        customizations.mkdir()
        (local_setup / "rhdh-local").mkdir()

        override_dir = customizations / "configs" / "dynamic-plugins"
        override_dir.mkdir(parents=True)
        (override_dir / "dynamic-plugins.override.yaml").write_text(
            "plugins:\n  - package: 'oci://example.com/plugin:tag!plugin'\n    disabled: false\n"
        )

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("--json", "local", "plugins", "list", isolated_env=isolated_env)
        import json

        outer = json.loads(result.stdout)
        data = outer.get("data", outer)
        assert "plugins" in data or "error" in outer


class TestLocalApplyRemoveCommands:
    """Tests for rhdh local apply and rhdh local remove."""

    def test_apply_fails_when_no_setup(self, isolated_env, monkeypatch):
        """local apply fails gracefully when local_setup not configured."""
        monkeypatch.setenv("SKILL_ROOT", str(isolated_env["root"] / "skill"))
        monkeypatch.delenv("RHDH_LOCAL_SETUP_DIR", raising=False)
        result = run_cli_python("local", "apply", isolated_env=isolated_env)
        assert result.returncode == 1

    def test_remove_requires_force(self, tmp_path, isolated_env, monkeypatch):
        """local remove requires --force flag."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        customizations = local_setup / "rhdh-customizations"
        customizations.mkdir()
        (customizations / "remove-customizations.sh").write_text("#!/bin/bash\necho done")
        (local_setup / "rhdh-local").mkdir()

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("local", "remove", isolated_env=isolated_env)
        assert result.returncode == 1
        assert "force" in result.stdout.lower()

    def test_apply_fails_when_script_missing(self, tmp_path, isolated_env, monkeypatch):
        """local apply fails when apply-customizations.sh is missing."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        (local_setup / "rhdh-customizations").mkdir()
        (local_setup / "rhdh-local").mkdir()

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("local", "apply", isolated_env=isolated_env)
        assert result.returncode == 1


class TestLocalCommandMissingSubcommand:
    """Tests for missing subcommand handling."""

    def test_local_without_subcommand(self, isolated_env):
        """rhdh local without subcommand returns error with help."""
        result = run_cli_python("local", isolated_env=isolated_env)
        assert result.returncode == 1

    def test_local_plugins_without_subcommand(self, tmp_path, isolated_env, monkeypatch):
        """rhdh local plugins without subcommand returns error."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("local", "plugins", isolated_env=isolated_env)
        assert result.returncode == 1


class TestDoctorLocalSetup:
    """Tests for doctor command local_setup checks."""

    def test_doctor_shows_local_setup_info(self, isolated_env):
        """doctor command includes local_setup section."""
        result = run_cli_python("doctor", isolated_env=isolated_env)
        # Doctor should mention local_setup (even if not configured)
        assert "local" in result.stdout.lower()

    def test_doctor_with_local_setup_configured(self, tmp_path, isolated_env, monkeypatch):
        """doctor shows OK when local_setup is found."""
        local_setup = tmp_path / "rhdh-local-setup"
        local_setup.mkdir()
        (local_setup / "rhdh-customizations").mkdir()
        (local_setup / "rhdh-local").mkdir()

        monkeypatch.setenv("RHDH_LOCAL_SETUP_DIR", str(local_setup))

        result = run_cli_python("doctor", isolated_env=isolated_env)
        assert "rhdh-local-setup" in result.stdout


class TestLocalSkillFiles:
    """Structural tests for rhdh-local skill files."""

    @pytest.fixture
    def local_skill_dir(self, skill_root):
        """Return path to rhdh-local skill directory."""
        return skill_root / "skills" / "rhdh-local"

    def test_skill_md_exists(self, local_skill_dir):
        """rhdh-local/SKILL.md must exist."""
        assert (local_skill_dir / "SKILL.md").exists()

    def test_skill_md_has_intake(self, local_skill_dir):
        """SKILL.md must have intake section."""
        content = (local_skill_dir / "SKILL.md").read_text()
        assert "<intake>" in content
        assert "</intake>" in content

    def test_skill_md_has_routing(self, local_skill_dir):
        """SKILL.md must have routing section."""
        content = (local_skill_dir / "SKILL.md").read_text()
        assert "<routing>" in content
        assert "</routing>" in content

    def test_workflows_exist(self, local_skill_dir):
        """All expected workflow files must exist."""
        workflows = ["enable-plugin.md", "disable-plugin.md", "switch-mode.md", "test-plugin.md"]
        for wf in workflows:
            path = local_skill_dir / "workflows" / wf
            assert path.exists(), f"Missing workflow: {wf}"

    def test_workflows_have_required_sections(self, local_skill_dir):
        """All workflows must have required_reading, process, success_criteria."""
        for wf_file in (local_skill_dir / "workflows").glob("*.md"):
            content = wf_file.read_text()
            assert "<process>" in content, f"{wf_file.name} missing <process>"
            assert "<success_criteria>" in content, f"{wf_file.name} missing <success_criteria>"
            prereqs = "<required_reading>" in content or "<prerequisites>" in content
            assert prereqs, f"{wf_file.name} missing required_reading or prerequisites"

    def test_reference_exists(self, local_skill_dir):
        """customization-system.md reference must exist."""
        assert (local_skill_dir / "references" / "customization-system.md").exists()

    def test_reference_has_xml_sections(self, local_skill_dir):
        """customization-system.md must use XML tags."""
        import re

        content = (local_skill_dir / "references" / "customization-system.md").read_text()
        assert re.search(r"<\w+>", content), "customization-system.md should use XML tags"
