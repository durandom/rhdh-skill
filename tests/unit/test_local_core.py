"""Tests for rhdh_local — core business logic for local RHDH operations.

Tests the copy-sync, compose builder, last-run settings, health checks,
and backup/restore functionality.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def workspace(tmp_path):
    """Create a minimal rhdh-local-setup workspace structure."""
    ws = tmp_path / "rhdh-local-setup"
    ws.mkdir()
    (ws / "rhdh-local").mkdir()
    (ws / "rhdh-customizations").mkdir()
    return ws


@pytest.fixture
def workspace_with_files(workspace):
    """Workspace with customization files ready to sync."""
    src = workspace / "rhdh-customizations"

    # Fixed files
    (src / ".env").write_text("GITHUB_TOKEN=test123")
    src_cfg = src / "configs" / "app-config"
    src_cfg.mkdir(parents=True)
    (src_cfg / "app-config.local.yaml").write_text("app:\n  title: Test")

    src_dp = src / "configs" / "dynamic-plugins"
    src_dp.mkdir(parents=True)
    (src_dp / "dynamic-plugins.override.yaml").write_text("plugins:\n  - package: test")

    # Glob files
    src_cat = src / "configs" / "catalog-entities"
    src_cat.mkdir(parents=True)
    (src_cat / "users.override.yaml").write_text("kind: User")
    (src_cat / "groups.override.yaml").write_text("kind: Group")

    src_extra = src / "configs" / "extra-files"
    src_extra.mkdir(parents=True)
    (src_extra / "github-creds.yaml").write_text("creds: test")

    return workspace


# =============================================================================
# Copy-Sync Tests
# =============================================================================


class TestApplyCustomizations:
    """Tests for apply_customizations()."""

    def test_copies_fixed_files(self, workspace_with_files):
        from rhdh_local.sync import apply_customizations

        result = apply_customizations(workspace_with_files)

        assert ".env" in result.copied
        assert "configs/app-config/app-config.local.yaml" in result.copied
        assert "configs/dynamic-plugins/dynamic-plugins.override.yaml" in result.copied
        assert not result.errors

    def test_copies_glob_files(self, workspace_with_files):
        from rhdh_local.sync import apply_customizations

        result = apply_customizations(workspace_with_files)

        assert "configs/catalog-entities/users.override.yaml" in result.copied
        assert "configs/catalog-entities/groups.override.yaml" in result.copied
        assert "configs/extra-files/github-creds.yaml" in result.copied

    def test_creates_destination_directories(self, workspace_with_files):
        from rhdh_local.sync import apply_customizations

        apply_customizations(workspace_with_files)

        dst = workspace_with_files / "rhdh-local"
        assert (dst / "configs" / "app-config" / "app-config.local.yaml").is_file()
        assert (dst / "configs" / "dynamic-plugins" / "dynamic-plugins.override.yaml").is_file()

    def test_skips_missing_source_files(self, workspace):
        from rhdh_local.sync import apply_customizations

        result = apply_customizations(workspace)

        # All fixed files should be skipped (none exist in src)
        assert len(result.skipped) > 0
        assert not result.errors
        assert not result.copied

    def test_errors_on_missing_src_dir(self, tmp_path):
        from rhdh_local.sync import apply_customizations

        ws = tmp_path / "no-customizations"
        ws.mkdir()
        (ws / "rhdh-local").mkdir()

        result = apply_customizations(ws)
        assert len(result.errors) == 1
        assert "rhdh-customizations" in result.errors[0]

    def test_errors_on_missing_dst_dir(self, tmp_path):
        from rhdh_local.sync import apply_customizations

        ws = tmp_path / "no-local"
        ws.mkdir()
        (ws / "rhdh-customizations").mkdir()

        result = apply_customizations(ws)
        assert len(result.errors) == 1
        assert "rhdh-local" in result.errors[0]

    def test_file_content_preserved(self, workspace_with_files):
        from rhdh_local.sync import apply_customizations

        apply_customizations(workspace_with_files)

        dst = workspace_with_files / "rhdh-local"
        assert (dst / ".env").read_text() == "GITHUB_TOKEN=test123"

    def test_idempotent(self, workspace_with_files):
        """Running apply twice produces the same result."""
        from rhdh_local.sync import apply_customizations

        r1 = apply_customizations(workspace_with_files)
        r2 = apply_customizations(workspace_with_files)

        assert sorted(r1.copied) == sorted(r2.copied)
        assert not r1.errors
        assert not r2.errors

    def test_copies_translation_files(self, workspace):
        """Translations glob pattern should copy configs/translations/*.json."""
        from rhdh_local.sync import apply_customizations

        src = workspace / "rhdh-customizations"
        trans_dir = src / "configs" / "translations"
        trans_dir.mkdir(parents=True)
        (trans_dir / "fr.json").write_text('{"key": "valeur"}')
        (trans_dir / "ja.json").write_text('{"key": "value_ja"}')

        result = apply_customizations(workspace)

        assert "configs/translations/fr.json" in result.copied
        assert "configs/translations/ja.json" in result.copied
        assert not result.errors


class TestRemoveCustomizations:
    """Tests for remove_customizations()."""

    def test_removes_copied_files(self, workspace_with_files):
        from rhdh_local.sync import apply_customizations, remove_customizations

        apply_customizations(workspace_with_files)
        result = remove_customizations(workspace_with_files)

        assert ".env" in result.removed
        assert "configs/app-config/app-config.local.yaml" in result.removed
        assert not result.errors

    def test_removes_glob_files(self, workspace_with_files):
        from rhdh_local.sync import apply_customizations, remove_customizations

        apply_customizations(workspace_with_files)
        result = remove_customizations(workspace_with_files)

        assert "configs/catalog-entities/users.override.yaml" in result.removed
        assert "configs/extra-files/github-creds.yaml" in result.removed

    def test_skips_already_removed_files(self, workspace):
        from rhdh_local.sync import remove_customizations

        result = remove_customizations(workspace)

        # Nothing to remove — all should be skipped
        assert len(result.skipped) > 0
        assert not result.removed
        assert not result.errors

    def test_leaves_rhdh_local_pristine(self, workspace_with_files):
        """After apply then remove, rhdh-local/ should have no copied files."""
        from rhdh_local.sync import apply_customizations, remove_customizations

        apply_customizations(workspace_with_files)
        remove_customizations(workspace_with_files)

        dst = workspace_with_files / "rhdh-local"
        assert not (dst / ".env").exists()
        assert not (dst / "configs" / "app-config" / "app-config.local.yaml").exists()


# =============================================================================
# Container Runtime Tests
# =============================================================================


class TestDetectComposeCommand:
    """Tests for detect_compose_command()."""

    def test_detects_podman(self):
        from rhdh_local.compose import detect_compose_command

        with patch(
            "shutil.which", side_effect=lambda x: "/usr/bin/podman" if x == "podman" else None
        ):
            assert detect_compose_command() == ["podman", "compose"]

    def test_detects_docker(self):
        from rhdh_local.compose import detect_compose_command

        with patch(
            "shutil.which", side_effect=lambda x: "/usr/bin/docker" if x == "docker" else None
        ):
            assert detect_compose_command() == ["docker", "compose"]

    def test_prefers_podman_over_docker(self):
        from rhdh_local.compose import detect_compose_command

        with patch("shutil.which", return_value="/usr/bin/any"):
            assert detect_compose_command() == ["podman", "compose"]

    def test_raises_when_neither_found(self):
        from rhdh_local.compose import detect_compose_command

        with patch("shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="Neither podman nor docker"):
                detect_compose_command()


class TestBuildComposeArgs:
    """Tests for build_compose_args()."""

    def test_base_args(self, workspace):
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        args = build_compose_args(rhdh_local)
        assert args == ["-f", "compose.yaml"]

    def test_includes_override(self, workspace):
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        (rhdh_local / "compose.override.yaml").write_text("services: {}")

        args = build_compose_args(rhdh_local)
        assert args == ["-f", "compose.yaml", "-f", "compose.override.yaml"]

    def test_includes_lightspeed_our_convention(self, workspace):
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        ls_dir = rhdh_local / "developer-lightspeed"
        ls_dir.mkdir()
        (ls_dir / "compose.lightspeed.yaml").write_text("services: {}")

        args = build_compose_args(rhdh_local, lightspeed=True)
        assert "-f" in args
        assert "developer-lightspeed/compose.lightspeed.yaml" in args

    def test_includes_lightspeed_rhdh_lab_convention(self, workspace):
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        ls_dir = rhdh_local / "developer-lightspeed"
        ls_dir.mkdir()
        (ls_dir / "compose.yaml").write_text("services: {}")

        args = build_compose_args(rhdh_local, lightspeed=True)
        assert "developer-lightspeed/compose.yaml" in args

    def test_includes_orchestrator(self, workspace):
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        orch_dir = rhdh_local / "developer-ai-orchestrator"
        orch_dir.mkdir()
        (orch_dir / "compose.orchestrator.yaml").write_text("services: {}")

        args = build_compose_args(rhdh_local, orchestrator=True)
        assert "developer-ai-orchestrator/compose.orchestrator.yaml" in args

    def test_lightspeed_and_orchestrator(self, workspace):
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        ls_dir = rhdh_local / "developer-lightspeed"
        ls_dir.mkdir()
        (ls_dir / "compose.lightspeed.yaml").write_text("services: {}")
        orch_dir = rhdh_local / "developer-ai-orchestrator"
        orch_dir.mkdir()
        (orch_dir / "compose.orchestrator.yaml").write_text("services: {}")

        args = build_compose_args(rhdh_local, lightspeed=True, orchestrator=True)
        assert "developer-lightspeed/compose.lightspeed.yaml" in args
        assert "developer-ai-orchestrator/compose.orchestrator.yaml" in args

    def test_skips_missing_optional_compose_files(self, workspace):
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        args = build_compose_args(rhdh_local, lightspeed=True, orchestrator=True)
        # Only base compose.yaml, no optional files found
        assert args == ["-f", "compose.yaml"]

    def test_ollama_provider(self, workspace):
        """--ollama selects compose-with-ollama.yaml instead of base."""
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        ls_dir = rhdh_local / "developer-lightspeed"
        ls_dir.mkdir()
        (ls_dir / "compose.yaml").write_text("services: {}")
        (ls_dir / "compose-with-ollama.yaml").write_text("services: {}")

        args = build_compose_args(rhdh_local, lightspeed=True, lightspeed_provider="ollama")
        assert "developer-lightspeed/compose-with-ollama.yaml" in args
        # Should NOT include base compose.yaml for lightspeed
        assert "developer-lightspeed/compose.yaml" not in args

    def test_safety_guard_base_provider(self, workspace):
        """--safety-guard adds safety guard compose file for base provider."""
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        ls_dir = rhdh_local / "developer-lightspeed"
        ls_dir.mkdir()
        (ls_dir / "compose.yaml").write_text("services: {}")
        (ls_dir / "compose-with-safety-guard.yaml").write_text("services: {}")

        args = build_compose_args(rhdh_local, lightspeed=True, safety_guard=True)
        assert "developer-lightspeed/compose.yaml" in args
        assert "developer-lightspeed/compose-with-safety-guard.yaml" in args

    def test_safety_guard_ollama_provider(self, workspace):
        """--safety-guard with --ollama uses ollama-specific safety guard file."""
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        ls_dir = rhdh_local / "developer-lightspeed"
        ls_dir.mkdir()
        (ls_dir / "compose-with-ollama.yaml").write_text("services: {}")
        (ls_dir / "compose-with-safety-guard-ollama.yaml").write_text("services: {}")

        args = build_compose_args(
            rhdh_local, lightspeed=True, lightspeed_provider="ollama", safety_guard=True
        )
        assert "developer-lightspeed/compose-with-ollama.yaml" in args
        assert "developer-lightspeed/compose-with-safety-guard-ollama.yaml" in args

    def test_safety_guard_without_lightspeed_ignored(self, workspace):
        """Safety guard without lightspeed should not add any guard files."""
        from rhdh_local.compose import build_compose_args

        rhdh_local = workspace / "rhdh-local"
        args = build_compose_args(rhdh_local, safety_guard=True)
        assert args == ["-f", "compose.yaml"]


# =============================================================================
# Last Run Settings Tests
# =============================================================================


class TestLastRunSettings:
    """Tests for save_last_run() and load_last_run()."""

    def test_save_and_load_roundtrip(self, workspace):
        from rhdh_local.settings import LastRunSettings, load_last_run, save_last_run

        settings = LastRunSettings(
            mode="customized",
            lightspeed=True,
            orchestrator=False,
            follow_logs=True,
        )
        save_last_run(workspace, settings)
        loaded = load_last_run(workspace)

        assert loaded is not None
        assert loaded.mode == "customized"
        assert loaded.lightspeed is True
        assert loaded.orchestrator is False
        assert loaded.follow_logs is True

    def test_save_baseline_mode(self, workspace):
        from rhdh_local.settings import LastRunSettings, load_last_run, save_last_run

        settings = LastRunSettings(mode="baseline")
        save_last_run(workspace, settings)
        loaded = load_last_run(workspace)

        assert loaded is not None
        assert loaded.mode == "baseline"

    def test_load_returns_none_when_missing(self, workspace):
        from rhdh_local.settings import load_last_run

        assert load_last_run(workspace) is None

    def test_load_returns_none_on_invalid_version(self, workspace):
        from rhdh_local.settings import LAST_RUN_FILE, load_last_run

        (workspace / LAST_RUN_FILE).write_text("VERSION=999\nMODE=customized\n")
        assert load_last_run(workspace) is None

    def test_load_returns_none_on_invalid_mode(self, workspace):
        from rhdh_local.settings import LAST_RUN_FILE, load_last_run

        (workspace / LAST_RUN_FILE).write_text("VERSION=1\nMODE=invalid\n")
        assert load_last_run(workspace) is None

    def test_load_returns_none_on_malformed_line(self, workspace):
        from rhdh_local.settings import LAST_RUN_FILE, load_last_run

        (workspace / LAST_RUN_FILE).write_text("not a valid line\n")
        assert load_last_run(workspace) is None

    def test_atomic_write(self, workspace):
        """Verify no .tmp file left behind after save."""
        from rhdh_local.settings import LAST_RUN_FILE, LastRunSettings, save_last_run

        save_last_run(workspace, LastRunSettings())
        assert (workspace / LAST_RUN_FILE).is_file()
        assert not (workspace / f"{LAST_RUN_FILE}.tmp").exists()

    def test_roundtrip_with_ollama_provider(self, workspace):
        """Verify lightspeed_provider persists through save/load."""
        from rhdh_local.settings import LastRunSettings, load_last_run, save_last_run

        settings = LastRunSettings(
            mode="customized",
            lightspeed=True,
            lightspeed_provider="ollama",
            safety_guard=True,
        )
        save_last_run(workspace, settings)
        loaded = load_last_run(workspace)

        assert loaded is not None
        assert loaded.lightspeed_provider == "ollama"
        assert loaded.safety_guard is True

    def test_roundtrip_defaults_provider_to_base(self, workspace):
        """Default lightspeed_provider should be 'base'."""
        from rhdh_local.settings import LastRunSettings, load_last_run, save_last_run

        settings = LastRunSettings()
        save_last_run(workspace, settings)
        loaded = load_last_run(workspace)

        assert loaded is not None
        assert loaded.lightspeed_provider == "base"
        assert loaded.safety_guard is False


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthChecks:
    """Tests for check_local_health()."""

    def test_fails_without_container_runtime(self, workspace):
        from rhdh_local.health import check_local_health

        with patch("shutil.which", return_value=None):
            checks = check_local_health(workspace)

        assert checks[0].name == "container_runtime"
        assert checks[0].status == "fail"
        # Should stop early — no further checks
        assert len(checks) == 1

    def test_detects_runtime(self, workspace):
        from rhdh_local.health import check_local_health

        with patch(
            "shutil.which", side_effect=lambda x: "/usr/bin/podman" if x == "podman" else None
        ):
            with patch("socket.create_connection", side_effect=OSError):
                checks = check_local_health(workspace)

        assert checks[0].name == "container_runtime"
        assert checks[0].status == "pass"


# =============================================================================
# Backup / Restore Tests
# =============================================================================


class TestBackup:
    """Tests for backup_customizations()."""

    def test_creates_archive(self, workspace_with_files, tmp_path):
        from rhdh_local.backup import backup_customizations

        backup_dir = tmp_path / "backups"
        info = backup_customizations(workspace_with_files, backup_dir=backup_dir)

        assert info.path.exists()
        assert info.path.suffix == ".gz"
        assert info.size_bytes > 0

    def test_archive_contains_files(self, workspace_with_files, tmp_path):
        import tarfile

        from rhdh_local.backup import backup_customizations

        backup_dir = tmp_path / "backups"
        info = backup_customizations(workspace_with_files, backup_dir=backup_dir)

        with tarfile.open(info.path, "r:gz") as tar:
            names = tar.getnames()

        assert any(".env" in n for n in names)
        assert any("dynamic-plugins.override.yaml" in n for n in names)

    def test_raises_on_missing_customizations(self, tmp_path):
        from rhdh_local.backup import backup_customizations

        ws = tmp_path / "empty"
        ws.mkdir()

        with pytest.raises(FileNotFoundError, match="rhdh-customizations"):
            backup_customizations(ws)


class TestListBackups:
    """Tests for list_backups()."""

    def test_empty_dir(self, tmp_path):
        from rhdh_local.backup import list_backups

        assert list_backups(tmp_path) == []

    def test_nonexistent_dir(self, tmp_path):
        from rhdh_local.backup import list_backups

        assert list_backups(tmp_path / "nonexistent") == []

    def test_lists_backups_newest_first(self, tmp_path):
        from rhdh_local.backup import list_backups

        (tmp_path / "rhdh-customizations-backup_2026-01-01_10-00-00.tar.gz").write_text("a")
        (tmp_path / "rhdh-customizations-backup_2026-01-02_10-00-00.tar.gz").write_text("ab")

        backups = list_backups(tmp_path)
        assert len(backups) == 2
        assert backups[0].timestamp == "2026-01-02_10-00-00"
        assert backups[1].timestamp == "2026-01-01_10-00-00"


class TestRestore:
    """Tests for restore_customizations()."""

    def test_roundtrip_backup_restore(self, workspace_with_files, tmp_path):
        from rhdh_local.backup import backup_customizations, restore_customizations

        backup_dir = tmp_path / "backups"
        info = backup_customizations(workspace_with_files, backup_dir=backup_dir)

        # Create a fresh workspace and restore into it
        new_ws = tmp_path / "restored"
        new_ws.mkdir()

        result = restore_customizations(new_ws, info.path)
        assert not result.errors
        assert len(result.copied) > 0
        assert (new_ws / "rhdh-customizations" / ".env").is_file()

    def test_errors_on_missing_archive(self, workspace):
        from rhdh_local.backup import restore_customizations

        result = restore_customizations(workspace, Path("/nonexistent.tar.gz"))
        assert len(result.errors) == 1


class TestPreviewRestore:
    """Tests for preview_restore()."""

    def test_lists_archive_contents(self, workspace_with_files, tmp_path):
        from rhdh_local.backup import backup_customizations, preview_restore

        backup_dir = tmp_path / "backups"
        info = backup_customizations(workspace_with_files, backup_dir=backup_dir)

        files = preview_restore(info.path)
        assert len(files) > 0
        assert any(".env" in f for f in files)

    def test_raises_on_missing_archive(self):
        from rhdh_local.backup import preview_restore

        with pytest.raises(FileNotFoundError):
            preview_restore(Path("/nonexistent.tar.gz"))
