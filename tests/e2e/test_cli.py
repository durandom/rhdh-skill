"""End-to-end tests for rhdh-plugin CLI.

These tests run the actual Python CLI code (no subprocess).
Output is JSON by default (non-TTY context), so we parse the structured response.
"""

import json


def parse_response(result):
    """Parse JSON response from CLI."""
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


class TestCliStatus:
    """Test CLI status command (no args)."""

    def test_no_args_shows_status(self, cli, isolated_env):
        """Running with no args should show status."""
        result = cli()

        # Should succeed (exit 0)
        assert result.returncode == 0, f"stderr: {result.stderr}"

        # Should return valid JSON with success=True
        response = parse_response(result)
        assert response is not None
        assert response["success"] is True
        assert "data" in response

    def test_status_shows_needs_setup(self, cli, isolated_env):
        """Status should include needs_setup flag."""
        result = cli()

        response = parse_response(result)
        assert response is not None
        assert "needs_setup" in response["data"]

    def test_status_shows_checks(self, cli, isolated_env):
        """Status should include checks array."""
        result = cli()

        response = parse_response(result)
        assert response is not None
        assert "checks" in response["data"]
        assert isinstance(response["data"]["checks"], list)

    def test_status_shows_next_steps(self, cli, isolated_env):
        """Status should include next_steps."""
        result = cli()

        response = parse_response(result)
        assert response is not None
        assert "next_steps" in response


class TestCliDoctor:
    """Test CLI doctor command."""

    def test_doctor_runs(self, cli, isolated_env):
        """Doctor command should run without error."""
        result = cli("doctor")

        # Should complete (may have issues but shouldn't crash)
        assert result.returncode in [0, 1]

        response = parse_response(result)
        assert response is not None
        assert response["success"] is True

    def test_doctor_returns_checks(self, cli, isolated_env):
        """Doctor should return checks array."""
        result = cli("doctor")

        response = parse_response(result)
        assert response is not None
        assert "checks" in response["data"]
        assert isinstance(response["data"]["checks"], list)

    def test_doctor_returns_all_passed(self, cli, isolated_env):
        """Doctor should return all_passed field."""
        result = cli("doctor")

        response = parse_response(result)
        assert response is not None
        assert "all_passed" in response["data"]


class TestCliConfig:
    """Test CLI config commands."""

    def test_config_init_creates_file(self, cli, isolated_env):
        """config init should create config file."""
        result = cli("config", "init")

        assert result.returncode == 0

        response = parse_response(result)
        assert response is not None
        assert response["success"] is True

    def test_config_show_displays_config(self, cli, isolated_env):
        """config show should display configuration."""
        # First init
        cli("config", "init")

        result = cli("config", "show")

        assert result.returncode == 0

        response = parse_response(result)
        assert response is not None
        assert "config_file" in response["data"]
        assert "resolved" in response["data"]

    def test_config_set_updates_value(self, cli, isolated_env):
        """config set should update a value."""
        # First init
        cli("config", "init")

        # Set a path (use the mock overlay dir)
        result = cli("config", "set", "overlay", str(isolated_env["overlay_dir"]))

        assert result.returncode == 0

        response = parse_response(result)
        assert response is not None
        assert response["success"] is True
        assert response["data"]["key"] == "overlay"

    def test_config_set_validates_path(self, cli, isolated_env):
        """config set should validate path exists."""
        result = cli("config", "set", "overlay", "/nonexistent/path")

        assert result.returncode != 0

        response = parse_response(result)
        assert response is not None
        assert response["success"] is False
        assert "error" in response

    def test_config_set_validates_key(self, cli, isolated_env):
        """config set should validate key name."""
        result = cli("config", "set", "invalid_key", "/tmp")

        assert result.returncode != 0

        response = parse_response(result)
        assert response is not None
        assert response["success"] is False


class TestCliWorkspace:
    """Test CLI workspace commands."""

    def test_workspace_list_works(self, cli, isolated_env):
        """workspace list should show workspaces."""
        # Configure the overlay repo
        cli("config", "init")
        cli("config", "set", "overlay", str(isolated_env["overlay_dir"]))

        result = cli("workspace", "list")

        assert result.returncode == 0

        response = parse_response(result)
        assert response is not None
        assert response["success"] is True
        assert "items" in response["data"]

    def test_workspace_list_shows_test_plugin(self, cli, isolated_env):
        """workspace list should show our test plugin."""
        # Use env var to override the default discovery
        env = {"RHDH_OVERLAY_REPO": str(isolated_env["overlay_dir"])}

        result = cli("workspace", "list", env=env)

        response = parse_response(result)
        assert response is not None

        items = response["data"]["items"]
        names = [item["name"] for item in items]
        assert "test-plugin" in names

    def test_workspace_status_shows_details(self, cli, isolated_env):
        """workspace status should show workspace details."""
        # Use env var to override the default discovery
        env = {"RHDH_OVERLAY_REPO": str(isolated_env["overlay_dir"])}

        result = cli("workspace", "status", "test-plugin", env=env)

        assert result.returncode == 0

        response = parse_response(result)
        assert response is not None
        assert response["data"]["name"] == "test-plugin"
        assert "files" in response["data"]

    def test_workspace_status_unknown_workspace(self, cli, isolated_env):
        """workspace status should error for unknown workspace."""
        cli("config", "set", "overlay", str(isolated_env["overlay_dir"]))

        result = cli("workspace", "status", "nonexistent")

        assert result.returncode != 0

        response = parse_response(result)
        assert response is not None
        assert response["success"] is False
        assert response["error"]["code"] == "WORKSPACE_NOT_FOUND"


class TestCliHelp:
    """Test CLI help."""

    def test_help_flag(self, cli, isolated_env):
        """--help should show help."""
        result = cli("--help")

        assert result.returncode == 0
        # Help is always human-readable
        assert "rhdh-plugin" in result.stdout

    def test_help_command(self, cli, isolated_env):
        """help command should show help."""
        result = cli("help")

        assert result.returncode == 0
        assert "rhdh-plugin" in result.stdout


class TestCliUnknownCommand:
    """Test CLI handles unknown commands."""

    def test_unknown_command_errors(self, cli, isolated_env):
        """Unknown command should show error."""
        result = cli("unknown_command")

        # argparse returns 2 for unknown commands
        assert result.returncode != 0


class TestCliEnvironmentVariables:
    """Test CLI respects environment variables."""

    def test_overlay_env_var(self, cli, isolated_env):
        """RHDH_OVERLAY_REPO env var should override config."""
        env = {"RHDH_OVERLAY_REPO": str(isolated_env["overlay_dir"])}

        result = cli("workspace", "list", env=env)

        assert result.returncode == 0

        response = parse_response(result)
        assert response is not None

        items = response["data"]["items"]
        names = [item["name"] for item in items]
        assert "test-plugin" in names


class TestCliVersion:
    """Test CLI version command."""

    def test_version_flag(self, cli, isolated_env):
        """--version should show version."""
        result = cli("--version")

        assert result.returncode == 0
        assert "1.0.0" in result.stdout


class TestCliOutputFormat:
    """Test CLI output format detection."""

    def test_json_flag_forces_json(self, cli, isolated_env):
        """--json flag should force JSON output."""
        result = cli("--json")

        response = parse_response(result)
        assert response is not None
        assert response["success"] is True

    def test_human_flag_forces_human(self, cli, isolated_env):
        """--human flag should force human-readable output."""
        result = cli("--human")

        # Human output is not JSON
        response = parse_response(result)
        assert response is None

        # Should have human-readable content
        assert "Next steps" in result.stdout or "✓" in result.stdout
