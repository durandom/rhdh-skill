"""Tests for fs-sessions policy, config, export, and hook management."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

FS_SKILL = Path(__file__).parents[2] / "skills" / "fs-sessions"
sys.path.insert(0, str(FS_SKILL))

from fs_sessions import config  # noqa: E402
from fs_sessions.cli import main  # noqa: E402
from fs_sessions.export import prepare_export  # noqa: E402
from fs_sessions.hook import hook_status, install_hook, uninstall_hook  # noqa: E402
from fs_sessions.policy import (  # noqa: E402
    RepositoryContext,
    add_rule,
    evaluate_policy,
    normalize_origin,
    remove_rule,
    validate_policy,
)


@pytest.fixture()
def global_config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setenv(config.USER_CONFIG_ENV, str(path))
    repo = tmp_path / "sessions-repo"
    repo.mkdir()
    (repo / "sessions").mkdir()
    data = config.initialize_sessions_config(repo)
    return path, repo, data


def test_initialize_preserves_rhdh_config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"repos": {"rhdh": "/code/rhdh"}, "github": {"username": "octo"}}))
    monkeypatch.setenv(config.USER_CONFIG_ENV, str(path))
    sessions_repo = tmp_path / "sessions"
    sessions_repo.mkdir()

    config.initialize_sessions_config(sessions_repo)

    saved = json.loads(path.read_text())
    assert saved["repos"]["rhdh"] == "/code/rhdh"
    assert saved["repos"]["sessions"] == str(sessions_repo)
    assert saved["github"]["username"] == "octo"
    assert saved["sessions"]["policy"] == {"default": "deny", "rules": []}


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("git@github.com:redhat-developer/rhdh.git", "github.com/redhat-developer/rhdh"),
        ("https://github.com/redhat-developer/rhdh.git", "github.com/redhat-developer/rhdh"),
        ("ssh://git@gitlab.example.com/team/repo.git", "gitlab.example.com/team/repo"),
    ],
)
def test_normalize_origin(url, expected):
    assert normalize_origin(url) == expected


def _context(path: Path, origin: str = "github.com/redhat-developer/rhdh") -> RepositoryContext:
    return RepositoryContext(str(path), str(path), origin)


def test_whitelist_and_last_match_wins(global_config):
    _, _, data = global_config
    rules = data["sessions"]["policy"]["rules"]
    rules.extend(
        [
            {"action": "allow", "origin": "github.com/redhat-developer/*"},
            {"action": "deny", "origin": "github.com/redhat-developer/rhdh"},
            {"action": "allow", "path": "/code/safe-rhdh"},
        ]
    )
    with patch(
        "fs_sessions.policy.discover_repository", return_value=_context(Path("/code/safe-rhdh"))
    ):
        decision = evaluate_policy(data, Path("."))
    assert decision.allowed is True
    assert decision.matched_rule == 3


def test_blacklist_default_allow(global_config):
    _, _, data = global_config
    data["sessions"]["policy"] = {
        "default": "allow",
        "rules": [{"action": "deny", "origin": "github.com/private/*"}],
    }
    with patch(
        "fs_sessions.policy.discover_repository",
        return_value=_context(Path("/code/repo"), "github.com/private/repo"),
    ):
        assert evaluate_policy(data, Path(".")).allowed is False


def test_non_git_is_always_denied(global_config):
    _, _, data = global_config
    data["sessions"]["policy"]["default"] = "allow"
    context = RepositoryContext("/tmp", None, None)
    with patch("fs_sessions.policy.discover_repository", return_value=context):
        decision = evaluate_policy(data, Path("/tmp"))
    assert decision.allowed is False
    assert decision.reason == "not_git_repository"


def test_project_can_opt_out(global_config, tmp_path):
    _, _, data = global_config
    root = tmp_path / "project"
    (root / ".rhdh").mkdir(parents=True)
    (root / ".rhdh" / "config.json").write_text('{"sessions":{"enabled":false}}')
    data["sessions"]["policy"]["default"] = "allow"
    with patch("fs_sessions.policy.discover_repository", return_value=_context(root)):
        decision = evaluate_policy(data, root)
    assert decision.allowed is False
    assert decision.reason == "project_opt_out"


@pytest.mark.parametrize(
    "policy",
    [
        {"default": "maybe", "rules": []},
        {"default": "deny", "rules": {}},
        {"default": "deny", "rules": [{"action": "allow"}]},
        {"default": "deny", "rules": [{"action": "allow", "path": "*", "origin": "*"}]},
    ],
)
def test_invalid_policies_fail_closed(policy):
    with pytest.raises(config.ConfigError):
        validate_policy(policy)


def test_rule_mutation(global_config):
    _, _, data = global_config
    assert add_rule(data, "allow", "origin", "github.com/acme/*") == 1
    assert add_rule(data, "deny", "path", "*/secret") == 2
    assert remove_rule(data, 1) == {"action": "allow", "origin": "github.com/acme/*"}
    assert data["sessions"]["policy"]["rules"] == [{"action": "deny", "path": "*/secret"}]


def test_hook_install_migrates_legacy_and_preserves_other_hooks(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "theme": "dark",
                "hooks": {
                    "SessionEnd": [
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": "bash /x/export-session.sh"}],
                        },
                        {
                            "matcher": "",
                            "hooks": [{"type": "command", "command": "notify-send done"}],
                        },
                    ]
                },
            }
        )
    )
    script = tmp_path / "skill" / "scripts" / "fs-sessions"
    script.parent.mkdir(parents=True)
    script.touch()

    first = install_hook(script, settings)
    second = install_hook(script, settings)

    assert first["replaced"] == 1
    assert second["replaced"] == 1
    saved = json.loads(settings.read_text())
    commands = [
        hook["command"] for entry in saved["hooks"]["SessionEnd"] for hook in entry["hooks"]
    ]
    assert commands.count("notify-send done") == 1
    assert len([command for command in commands if "hook run" in command]) == 1
    assert saved["theme"] == "dark"


def test_hook_uninstall_is_scoped_and_idempotent(tmp_path):
    settings = tmp_path / "settings.json"
    script = tmp_path / "fs-sessions"
    script.touch()
    install_hook(script, settings)
    assert hook_status(settings)["installed"] is True
    assert uninstall_hook(settings)["removed"] == 1
    assert uninstall_hook(settings)["removed"] == 0
    assert hook_status(settings)["installed"] is False


def test_export_add_update_and_unchanged(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    transcript = tmp_path / "session.jsonl"
    transcript.write_text('{"type":"user"}\n')

    first = prepare_export(transcript, "session", "project", repo, "user", "2026-01-01T00:00:00Z")
    assert first is not None and first.verb == "add"
    assert prepare_export(transcript, "session", "project", repo, "user") is None

    transcript.write_text('{"type":"user"}\n{"type":"assistant"}\n')
    updated = prepare_export(transcript, "session", "project", repo, "user")
    assert updated is not None and updated.verb == "update"
    metadata = json.loads(updated.dest.read_text().splitlines()[0])
    assert metadata["message"]["content"].startswith("[Session: project] by user")


def test_hook_run_exports_allowed_repository(global_config, tmp_path, monkeypatch):
    _, repo, data = global_config
    data["sessions"]["policy"]["default"] = "allow"
    config.save_user_config(data)
    source_repo = tmp_path / "source"
    source_repo.mkdir()
    transcript = tmp_path / "source.jsonl"
    transcript.write_text('{"type":"user"}\n')
    context = _context(source_repo)
    event = {
        "cwd": str(source_repo),
        "transcript_path": str(transcript),
        "session_id": "session-1",
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    monkeypatch.setattr(
        "fs_sessions.cli.evaluate_policy",
        lambda *_: type("Decision", (), {"allowed": True, "context": context})(),
    )
    monkeypatch.setattr("fs_sessions.cli._username", lambda: "test-user")
    monkeypatch.setattr("fs_sessions.cli.commit_file", lambda *args: True)
    monkeypatch.setattr("fs_sessions.cli.pull_rebase", lambda *args: True)
    monkeypatch.setattr("fs_sessions.cli.push", lambda *args: True)

    assert main(["hook", "run"]) == 0
    assert (repo / "sessions" / "test-user_source" / "session-1.jsonl").exists()


def test_hook_run_skips_denied_repository(global_config, tmp_path, monkeypatch):
    _, repo, _ = global_config
    transcript = tmp_path / "source.jsonl"
    transcript.write_text('{"type":"user"}\n')
    event = {
        "cwd": str(tmp_path),
        "transcript_path": str(transcript),
        "session_id": "session-1",
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(event)))
    monkeypatch.setattr(
        "fs_sessions.cli.evaluate_policy", lambda *_: type("Decision", (), {"allowed": False})()
    )

    assert main(["hook", "run"]) == 0
    assert list((repo / "sessions").glob("*/*.jsonl")) == []


def test_commit_file_does_not_include_other_staged_changes(tmp_path):
    from fs_sessions.git import commit_file

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    target = tmp_path / "target"
    other = tmp_path / "other"
    target.write_text("target")
    other.write_text("other")
    subprocess.run(["git", "add", "other"], cwd=tmp_path, check=True)

    assert commit_file(tmp_path, "target", "feat: add target") is True

    committed = subprocess.run(
        ["git", "show", "--pretty=", "--name-only", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert committed == ["target"]
    assert (
        subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", "other"], cwd=tmp_path
        ).returncode
        == 1
    )
