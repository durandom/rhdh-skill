"""Unit tests for rhdh_plugin.config module."""

import json


class TestFindRepo:
    """Test find_repo function."""

    def test_env_var_override(self, tmp_path, monkeypatch):
        """Environment variable should take precedence."""
        from rhdh_plugin import config

        # Create a directory
        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()

        # Set env var
        monkeypatch.setenv("RHDH_OVERLAY_REPO", str(repo_dir))

        result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
        assert result == repo_dir.resolve()

    def test_env_var_ignored_if_path_doesnt_exist(self, tmp_path, monkeypatch):
        """Env var should be ignored if path doesn't exist."""
        from rhdh_plugin import config

        monkeypatch.setenv("RHDH_OVERLAY_REPO", "/nonexistent/path")
        # Also set SKILL_ROOT to tmp to prevent fallback discovery
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path))

        # Reset config paths to tmp
        config.USER_CONFIG_DIR = tmp_path / ".config" / "rhdh-plugin-skill"
        config.USER_CONFIG_FILE = config.USER_CONFIG_DIR / "config.json"

        result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
        assert result is None

    def test_user_config_lookup(self, tmp_path, monkeypatch):
        """Should find repo from user config file."""
        from rhdh_plugin import config

        # Clear env var
        monkeypatch.delenv("RHDH_OVERLAY_REPO", raising=False)

        # Set up config file
        config_dir = tmp_path / ".config" / "rhdh-plugin-skill"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"

        # Create a repo directory
        repo_dir = tmp_path / "repos" / "overlay"
        repo_dir.mkdir(parents=True)

        config_file.write_text(json.dumps({"repos": {"overlay": str(repo_dir)}}))

        # Point config module to our test paths
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_file

        result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
        assert result == repo_dir.resolve()

    def test_returns_none_when_not_found(self, tmp_path, monkeypatch):
        """Should return None when repo not found."""
        from rhdh_plugin import config

        monkeypatch.delenv("RHDH_OVERLAY_REPO", raising=False)
        # Set SKILL_ROOT to tmp to prevent fallback discovery
        monkeypatch.setenv("SKILL_ROOT", str(tmp_path))

        config.USER_CONFIG_DIR = tmp_path / ".config" / "rhdh-plugin-skill"
        config.USER_CONFIG_FILE = config.USER_CONFIG_DIR / "config.json"

        result = config.find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")
        assert result is None


class TestConfigInit:
    """Test config_init function."""

    def test_creates_config_file(self, tmp_path, monkeypatch):
        """Should create config file when it doesn't exist."""
        from rhdh_plugin import config

        config_dir = tmp_path / ".config" / "rhdh-plugin-skill"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        created, messages = config.config_init()

        assert created is True
        assert config.USER_CONFIG_FILE.exists()
        assert any("Created" in m for m in messages)

    def test_returns_false_if_exists(self, tmp_path, monkeypatch):
        """Should return False if config already exists."""
        from rhdh_plugin import config

        config_dir = tmp_path / ".config" / "rhdh-plugin-skill"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text("{}")

        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_file

        created, messages = config.config_init()

        assert created is False
        assert any("already exists" in m for m in messages)


class TestConfigSet:
    """Test config_set function."""

    def test_validates_key(self, tmp_path):
        """Should reject invalid keys."""
        from rhdh_plugin import config

        config_dir = tmp_path / ".config" / "rhdh-plugin-skill"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        success, message = config.config_set("invalid_key", "/some/path")

        assert success is False
        assert "Unknown" in message

    def test_validates_path_exists(self, tmp_path):
        """Should reject nonexistent paths."""
        from rhdh_plugin import config

        config_dir = tmp_path / ".config" / "rhdh-plugin-skill"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        success, message = config.config_set("overlay", "/nonexistent/path")

        assert success is False
        assert "not exist" in message

    def test_sets_valid_value(self, tmp_path):
        """Should set value for valid key and path."""
        from rhdh_plugin import config

        config_dir = tmp_path / ".config" / "rhdh-plugin-skill"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        # Create a directory to set
        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()

        success, message = config.config_set("overlay", str(repo_dir))

        assert success is True
        assert str(repo_dir.resolve()) in message

        # Verify it was saved
        saved_config = json.loads(config.USER_CONFIG_FILE.read_text())
        assert saved_config["repos"]["overlay"] == str(repo_dir.resolve())


class TestLoadSaveConfig:
    """Test load_config and save_config functions."""

    def test_load_returns_empty_dict_if_no_file(self, tmp_path):
        """load_config should return empty dict if file doesn't exist."""
        from rhdh_plugin import config

        config.USER_CONFIG_FILE = tmp_path / "nonexistent.json"

        result = config.load_config()
        assert result == {}

    def test_save_creates_directory(self, tmp_path):
        """save_config should create config directory if needed."""
        from rhdh_plugin import config

        config_dir = tmp_path / "new" / "nested" / "dir"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        config.save_config({"test": "value"})

        assert config.USER_CONFIG_FILE.exists()
        saved = json.loads(config.USER_CONFIG_FILE.read_text())
        assert saved == {"test": "value"}

    def test_roundtrip(self, tmp_path):
        """Config should survive save/load roundtrip."""
        from rhdh_plugin import config

        config_dir = tmp_path / ".config" / "rhdh-plugin-skill"
        config.USER_CONFIG_DIR = config_dir
        config.USER_CONFIG_FILE = config_dir / "config.json"

        original = {"repos": {"overlay": "/some/path"}, "settings": {"verbose": True}}
        config.save_config(original)
        loaded = config.load_config()

        assert loaded == original
