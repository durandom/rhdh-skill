"""Unit tests for rhdh_plugin.workspace module."""

import json


class TestWorkspaceInfo:
    """Test WorkspaceInfo dataclass."""

    def test_from_path_basic(self, tmp_path):
        """Should create WorkspaceInfo from a basic workspace."""
        from rhdh_plugin.workspace import WorkspaceInfo

        # Create a workspace directory
        workspace = tmp_path / "my-plugin"
        workspace.mkdir()

        info = WorkspaceInfo.from_path(workspace)

        assert info.name == "my-plugin"
        assert info.path == workspace
        assert info.has_source_json is False
        assert info.has_plugins_list is False

    def test_from_path_with_source_json(self, tmp_path):
        """Should parse source.json when present."""
        from rhdh_plugin.workspace import WorkspaceInfo

        workspace = tmp_path / "my-plugin"
        workspace.mkdir()

        source_data = {
            "repo": "https://github.com/example/plugin",
            "repo-ref": "v1.2.3",
            "repo-backstage-version": "1.45.0",
        }
        (workspace / "source.json").write_text(json.dumps(source_data))

        info = WorkspaceInfo.from_path(workspace)

        assert info.has_source_json is True
        assert info.repo == "https://github.com/example/plugin"
        assert info.repo_ref == "v1.2.3"
        assert info.repo_backstage_version == "1.45.0"

    def test_from_path_with_all_files(self, tmp_path):
        """Should detect all workspace files."""
        from rhdh_plugin.workspace import WorkspaceInfo

        workspace = tmp_path / "my-plugin"
        workspace.mkdir()

        (workspace / "source.json").write_text('{"repo": "test"}')
        (workspace / "plugins-list.yaml").write_text("- plugins/test:\n")
        (workspace / "backstage.json").write_text("{}")

        info = WorkspaceInfo.from_path(workspace)

        assert info.has_source_json is True
        assert info.has_plugins_list is True
        assert info.has_backstage_json is True

    def test_from_path_with_metadata(self, tmp_path):
        """Should list metadata files."""
        from rhdh_plugin.workspace import WorkspaceInfo

        workspace = tmp_path / "my-plugin"
        workspace.mkdir()

        metadata_dir = workspace / "metadata"
        metadata_dir.mkdir()
        (metadata_dir / "readme.md").write_text("# Plugin")
        (metadata_dir / "icon.svg").write_text("<svg></svg>")

        info = WorkspaceInfo.from_path(workspace)

        assert info.metadata_files is not None
        assert set(info.metadata_files) == {"readme.md", "icon.svg"}

    def test_from_path_handles_invalid_json(self, tmp_path):
        """Should handle invalid source.json gracefully."""
        from rhdh_plugin.workspace import WorkspaceInfo

        workspace = tmp_path / "my-plugin"
        workspace.mkdir()
        (workspace / "source.json").write_text("not valid json")

        info = WorkspaceInfo.from_path(workspace)

        assert info.has_source_json is True  # File exists
        assert info.repo is None  # But couldn't parse


class TestListWorkspaces:
    """Test list_workspaces function."""

    def test_returns_none_when_no_overlay(self, tmp_path, monkeypatch):
        """Should return (None, []) when overlay repo not found."""
        from rhdh_plugin import config
        from rhdh_plugin.workspace import list_workspaces

        # Ensure no env var and set SKILL_ROOT to tmp to prevent fallback
        monkeypatch.delenv("RHDH_OVERLAY_REPO", raising=False)
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path))

        # Point config to empty tmp
        config.USER_CONFIG_DIR = tmp_path / ".config"
        config.USER_CONFIG_FILE = config.USER_CONFIG_DIR / "config.json"

        overlay_path, workspaces = list_workspaces()

        assert overlay_path is None
        assert workspaces == []

    def test_returns_empty_list_when_no_workspaces_dir(self, tmp_path, monkeypatch):
        """Should return empty list when workspaces dir doesn't exist."""
        from rhdh_plugin.workspace import list_workspaces

        overlay_dir = tmp_path / "overlay"
        overlay_dir.mkdir()

        monkeypatch.setenv("RHDH_OVERLAY_REPO", str(overlay_dir))

        overlay_path, workspaces = list_workspaces()

        assert overlay_path == overlay_dir.resolve()
        assert workspaces == []

    def test_lists_all_workspaces(self, tmp_path, monkeypatch):
        """Should list all workspace directories."""
        from rhdh_plugin.workspace import list_workspaces

        overlay_dir = tmp_path / "overlay"
        workspaces_dir = overlay_dir / "workspaces"
        workspaces_dir.mkdir(parents=True)

        # Create some workspaces
        (workspaces_dir / "plugin-a").mkdir()
        (workspaces_dir / "plugin-b").mkdir()
        (workspaces_dir / "plugin-c").mkdir()

        monkeypatch.setenv("RHDH_OVERLAY_REPO", str(overlay_dir))

        overlay_path, workspaces = list_workspaces()

        assert len(workspaces) == 3
        names = [w.name for w in workspaces]
        assert sorted(names) == ["plugin-a", "plugin-b", "plugin-c"]


class TestGetWorkspace:
    """Test get_workspace function."""

    def test_returns_workspace_when_found(self, tmp_path, monkeypatch):
        """Should return workspace info when found."""
        from rhdh_plugin.workspace import get_workspace

        overlay_dir = tmp_path / "overlay"
        workspace_dir = overlay_dir / "workspaces" / "my-plugin"
        workspace_dir.mkdir(parents=True)
        (workspace_dir / "source.json").write_text('{"repo": "test"}')

        monkeypatch.setenv("RHDH_OVERLAY_REPO", str(overlay_dir))

        found, workspace, error = get_workspace("my-plugin")

        assert found is True
        assert workspace is not None
        assert workspace.name == "my-plugin"
        assert error == ""

    def test_returns_not_found_when_missing(self, tmp_path, monkeypatch):
        """Should return not found when workspace doesn't exist."""
        from rhdh_plugin.workspace import get_workspace

        overlay_dir = tmp_path / "overlay"
        (overlay_dir / "workspaces").mkdir(parents=True)

        monkeypatch.setenv("RHDH_OVERLAY_REPO", str(overlay_dir))

        found, workspace, error = get_workspace("nonexistent")

        assert found is False
        assert workspace is None
        assert "not found" in error.lower()

    def test_returns_error_when_no_overlay(self, tmp_path, monkeypatch):
        """Should return error when overlay repo not configured."""
        from rhdh_plugin import config
        from rhdh_plugin.workspace import get_workspace

        monkeypatch.delenv("RHDH_OVERLAY_REPO", raising=False)
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path))
        config.USER_CONFIG_DIR = tmp_path / ".config"
        config.USER_CONFIG_FILE = config.USER_CONFIG_DIR / "config.json"

        found, workspace, error = get_workspace("any")

        assert found is False
        assert workspace is None
        assert "overlay" in error.lower()
