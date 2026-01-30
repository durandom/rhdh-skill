"""Unit tests for rhdh_plugin.config module.

Tests the layered configuration system:
- Project config (.rhdh/config.json in git root)
- User config (~/.config/rhdh/config.json)
- Environment variable overrides
"""

import json
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def reset_config_paths():
    """Reset config module paths before each test to ensure isolation."""
    from rhdh import config

    # Save original values
    original_user_dir = config.USER_CONFIG_DIR
    original_user_file = config.USER_CONFIG_FILE

    yield

    # Restore after test
    config.USER_CONFIG_DIR = original_user_dir
    config.USER_CONFIG_FILE = original_user_file


class TestFindRepo:
    """Test find_repo function."""

    def test_env_var_override(self, tmp_path, monkeypatch):
        """Environment variable should take precedence."""
        from rhdh import config

        # Create a directory
        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()

        # Set env var
        monkeypatch.setenv("RHDH_OVERLAY_REPO", str(repo_dir))

        result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
        assert result == repo_dir.resolve()

    def test_env_var_ignored_if_path_doesnt_exist(self, tmp_path, monkeypatch):
        """Env var should be ignored if path doesn't exist."""
        from rhdh import config

        monkeypatch.setenv("RHDH_OVERLAY_REPO", "/nonexistent/path")
        # Also set SKILL_ROOT to tmp to prevent fallback discovery
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path))

        # Reset config paths to tmp
        config.USER_CONFIG_DIR = tmp_path / ".config" / "rhdh"
        config.USER_CONFIG_FILE = config.USER_CONFIG_DIR / "config.json"

        result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
        assert result is None

    def test_user_config_lookup(self, tmp_path, monkeypatch):
        """Should find repo from user config file."""
        from rhdh import config

        # Clear env var
        monkeypatch.delenv("RHDH_OVERLAY_REPO", raising=False)
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path))

        # Set up user config file
        config_dir = tmp_path / ".config" / "rhdh"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"

        # Create a repo directory
        repo_dir = tmp_path / "repos" / "overlay"
        repo_dir.mkdir(parents=True)

        config_file.write_text(json.dumps({"repos": {"overlay": str(repo_dir)}}))

        # Point config module to our test paths
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_file

        # Mock find_git_root to return None (no project config)
        with patch.object(config, "find_git_root", return_value=None):
            result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
            assert result == repo_dir.resolve()

    def test_returns_none_when_not_found(self, tmp_path, monkeypatch):
        """Should return None when repo not found."""
        from rhdh import config

        monkeypatch.delenv("RHDH_OVERLAY_REPO", raising=False)
        # Set SKILL_ROOT to tmp to prevent fallback discovery
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path))

        config.USER_CONFIG_DIR = tmp_path / ".config" / "rhdh"
        config.USER_CONFIG_FILE = config.USER_CONFIG_DIR / "config.json"

        with patch.object(config, "find_git_root", return_value=None):
            result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
            assert result is None


class TestConfigInit:
    """Test config_init function (legacy API).

    Note: config_init() creates PROJECT config by default, not user config.
    """

    def test_creates_project_config_file(self, tmp_path, monkeypatch):
        """Should create project config file when it doesn't exist."""
        from rhdh import config

        # Mock git root to tmp_path
        with patch.object(config, "find_git_root", return_value=tmp_path):
            created, messages = config.config_init()

            project_config = tmp_path / ".rhdh" / "config.json"
            assert created is True
            assert project_config.exists()
            assert any("Created" in m for m in messages)

    def test_returns_false_if_exists(self, tmp_path, monkeypatch):
        """Should return False if config already exists."""
        from rhdh import config

        # Create existing project config
        config_dir = tmp_path / ".rhdh"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text("{}")

        with patch.object(config, "find_git_root", return_value=tmp_path):
            created, messages = config.config_init()

            assert created is False
            assert any("already exists" in m for m in messages)


class TestConfigSet:
    """Test config_set function (legacy API).

    Note: config_set() accepts any dot-notation key and does not validate paths.
    """

    def test_sets_value_with_shorthand_key(self, tmp_path):
        """Should map shorthand keys (overlay -> repos.overlay)."""
        from rhdh import config

        # Mock git root
        with patch.object(config, "find_git_root", return_value=tmp_path):
            # Create a directory to set
            repo_dir = tmp_path / "my-repo"
            repo_dir.mkdir()

            success, message = config.config_set("overlay", str(repo_dir))

            assert success is True
            assert "repos.overlay" in message

            # Verify it was saved to project config
            project_config = tmp_path / ".rhdh" / "config.json"
            saved_config = json.loads(project_config.read_text())
            assert saved_config["repos"]["overlay"] == str(repo_dir)

    def test_sets_value_with_dotnotation_key(self, tmp_path):
        """Should accept full dot-notation keys."""
        from rhdh import config

        with patch.object(config, "find_git_root", return_value=tmp_path):
            success, message = config.config_set("repos.local", "/some/path")

            assert success is True
            assert "repos.local" in message

    def test_creates_nested_structure(self, tmp_path):
        """Should create nested dict structure for deep keys."""
        from rhdh import config

        with patch.object(config, "find_git_root", return_value=tmp_path):
            success, message = config.config_set("custom.deeply.nested.key", "value")

            assert success is True

            project_config = tmp_path / ".rhdh" / "config.json"
            saved_config = json.loads(project_config.read_text())
            assert saved_config["custom"]["deeply"]["nested"]["key"] == "value"


class TestLoadSaveConfig:
    """Test load and save config functions."""

    def test_load_user_config_returns_empty_dict_if_no_file(self, tmp_path):
        """load_user_config should return empty dict if file doesn't exist."""
        from rhdh import config

        config.USER_CONFIG_FILE = tmp_path / "nonexistent.json"

        result = config.load_user_config()
        assert result == {}

    def test_load_project_config_returns_empty_dict_if_no_file(self, tmp_path, monkeypatch):
        """load_project_config should return empty dict if project config doesn't exist."""
        from rhdh import config

        # Mock find_git_root to return a tmp dir with no config file
        with patch.object(config, "find_git_root", return_value=tmp_path):
            result = config.load_project_config()
            assert result == {}

    def test_save_config_creates_directory(self, tmp_path):
        """save_config should create config directory if needed."""
        from rhdh import config

        # Test saving to user config (global_=True)
        config_dir = tmp_path / "new" / "nested" / "dir"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        result = config.save_config({"test": "value"}, global_=True)

        assert result is True
        assert config.USER_CONFIG_FILE.exists()
        saved = json.loads(config.USER_CONFIG_FILE.read_text())
        assert saved == {"test": "value"}

    def test_save_config_to_project(self, tmp_path):
        """save_config with global_=False should save to project config."""
        from rhdh import config

        with patch.object(config, "find_git_root", return_value=tmp_path):
            result = config.save_config({"project": "data"}, global_=False)

            assert result is True
            project_config = tmp_path / ".rhdh" / "config.json"
            assert project_config.exists()
            saved = json.loads(project_config.read_text())
            assert saved == {"project": "data"}

    def test_roundtrip_user_config(self, tmp_path):
        """User config should survive save/load roundtrip."""
        from rhdh import config

        config_dir = tmp_path / ".config" / "rhdh"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        original = {"repos": {"overlay": "/some/path"}, "settings": {"verbose": True}}
        config.save_config(original, global_=True)
        loaded = config.load_user_config()

        assert loaded == original

    def test_roundtrip_project_config(self, tmp_path):
        """Project config should survive save/load roundtrip."""
        from rhdh import config

        with patch.object(config, "find_git_root", return_value=tmp_path):
            original = {"repos": {"overlay": "/project/path"}}
            config.save_config(original, global_=False)
            loaded = config.load_project_config()

            assert loaded == original


class TestMergedConfig:
    """Test merged config behavior (project overrides user)."""

    def test_project_overrides_user(self, tmp_path):
        """Project config values should override user config."""
        from rhdh import config

        # Set up user config
        user_dir = tmp_path / "home" / ".config" / "rhdh"
        user_dir.mkdir(parents=True)
        user_file = user_dir / "config.json"
        user_file.write_text(
            json.dumps(
                {
                    "repos": {"overlay": "/user/overlay", "local": "/user/local"},
                    "user_only": "value",
                }
            )
        )
        config.USER_CONFIG_DIR = user_dir
        config.USER_CONFIG_FILE = user_file

        # Set up project config
        project_dir = tmp_path / "project" / ".rhdh"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "config.json"
        project_file.write_text(
            json.dumps({"repos": {"overlay": "/project/overlay"}, "project_only": "value"})
        )

        with patch.object(config, "find_git_root", return_value=tmp_path / "project"):
            merged = config.load_merged_config()

            # Project overlay overrides user
            assert merged["repos"]["overlay"] == "/project/overlay"
            # User local preserved (not in project)
            assert merged["repos"]["local"] == "/user/local"
            # Both unique keys preserved
            assert merged["user_only"] == "value"
            assert merged["project_only"] == "value"


class TestDotNotation:
    """Test dot-notation helper functions."""

    def test_get_nested(self):
        """get_nested should retrieve deeply nested values."""
        from rhdh.config import get_nested

        data = {"a": {"b": {"c": "value"}}}
        assert get_nested(data, "a.b.c") == "value"
        assert get_nested(data, "a.b") == {"c": "value"}
        assert get_nested(data, "a") == {"b": {"c": "value"}}

    def test_get_nested_raises_on_missing(self):
        """get_nested should raise KeyError for missing keys."""
        import pytest
        from rhdh.config import get_nested

        data = {"a": {"b": "value"}}
        with pytest.raises(KeyError):
            get_nested(data, "a.c")
        with pytest.raises(KeyError):
            get_nested(data, "x.y.z")

    def test_set_nested(self):
        """set_nested should create nested structure."""
        from rhdh.config import set_nested

        data = {}
        set_nested(data, "a.b.c", "value")
        assert data == {"a": {"b": {"c": "value"}}}

    def test_set_nested_overwrites_non_dict(self):
        """set_nested should replace non-dict intermediate values."""
        from rhdh.config import set_nested

        data = {"a": "string"}
        set_nested(data, "a.b", "value")
        assert data == {"a": {"b": "value"}}

    def test_collect_keys(self):
        """collect_keys should return all dot-notation paths."""
        from rhdh.config import collect_keys

        data = {"repos": {"overlay": "/path", "local": "/path2"}, "simple": "value"}
        keys = sorted(collect_keys(data))
        assert keys == ["repos.local", "repos.overlay", "simple"]

    def test_parse_value_json(self):
        """parse_value should parse JSON values."""
        from rhdh.config import parse_value

        assert parse_value("true") is True
        assert parse_value("false") is False
        assert parse_value("123") == 123
        assert parse_value('["a", "b"]') == ["a", "b"]
        assert parse_value('{"key": "value"}') == {"key": "value"}

    def test_parse_value_string_fallback(self):
        """parse_value should return string if not valid JSON."""
        from rhdh.config import parse_value

        assert parse_value("/some/path") == "/some/path"
        assert parse_value("hello world") == "hello world"
