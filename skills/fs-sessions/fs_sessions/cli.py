"""Command-line interface for session sharing, policy, and hook management."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fs_sessions.config import (
    ConfigError,
    get_sessions_config,
    get_sessions_repo,
    get_user_config_path,
    initialize_sessions_config,
    load_user_config,
    save_user_config,
)
from fs_sessions.discovery import SessionInfo, discover_sessions
from fs_sessions.export import prepare_export
from fs_sessions.git import commit_file, pull_rebase, push
from fs_sessions.hook import (
    DEFAULT_SETTINGS,
    HookError,
    hook_status,
    install_hook,
    uninstall_hook,
)
from fs_sessions.policy import add_rule, evaluate_policy, remove_rule, validate_policy


def _emit(data: Dict[str, Any], human: Optional[str], force_json: bool) -> None:
    if force_json or not sys.stdout.isatty():
        json.dump(data, sys.stdout, indent=2 if force_json else None)
        sys.stdout.write("\n")
    elif human:
        print(human)


def _username() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            return result.stdout.strip().replace(" ", "-").lower()
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return os.environ.get("USER", "unknown")


def _script_path() -> Path:
    return Path(__file__).resolve().parent.parent / "scripts" / "fs-sessions"


def _settings(args: argparse.Namespace) -> Path:
    return Path(args.settings).expanduser() if getattr(args, "settings", None) else DEFAULT_SETTINGS


def cmd_config_init(args: argparse.Namespace) -> int:
    data = initialize_sessions_config(Path(args.repo), args.default)
    _emit(
        {"success": True, "config": str(get_user_config_path()), "sessions": data["sessions"]},
        f"Initialized session config: {get_user_config_path()}",
        args.json,
    )
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    data = load_user_config(missing_ok=False)
    payload = {
        "config": str(get_user_config_path()),
        "repo": str(get_sessions_repo(data)),
        "sessions": get_sessions_config(data),
    }
    _emit(payload, json.dumps(payload, indent=2), args.json)
    return 0


def cmd_policy_check(args: argparse.Namespace) -> int:
    decision = evaluate_policy(load_user_config(missing_ok=False), Path(args.path))
    data = decision.to_dict()
    detail = f"Policy: {decision.action} ({decision.reason})"
    if decision.matched_rule is not None:
        detail += f", rule {decision.matched_rule}"
    _emit(data, detail, args.json)
    return 0 if decision.allowed else 1


def cmd_policy_default(args: argparse.Namespace) -> int:
    data = load_user_config(missing_ok=False)
    sessions = get_sessions_config(data)
    policy = validate_policy(sessions.setdefault("policy", {}))
    policy["default"] = args.action
    sessions["policy"] = policy
    save_user_config(data)
    _emit({"success": True, "default": args.action}, f"Default policy: {args.action}", args.json)
    return 0


def cmd_policy_add(args: argparse.Namespace) -> int:
    selector = "origin" if args.origin is not None else "path"
    pattern = args.origin if args.origin is not None else args.path
    data = load_user_config(missing_ok=False)
    index = add_rule(data, args.action, selector, pattern)
    save_user_config(data)
    payload = {"success": True, "index": index, "rule": {"action": args.action, selector: pattern}}
    _emit(payload, f"Added rule {index}: {args.action} {selector} {pattern}", args.json)
    return 0


def cmd_policy_rules(args: argparse.Namespace) -> int:
    data = load_user_config(missing_ok=False)
    policy = validate_policy(get_sessions_config(data).get("policy", {}))
    payload = {"default": policy["default"], "rules": policy["rules"]}
    lines = [f"Default: {policy['default']}"]
    for index, rule in enumerate(policy["rules"], 1):
        selector = "origin" if "origin" in rule else "path"
        lines.append(f"{index}. {rule['action']} {selector} {rule[selector]}")
    _emit(payload, "\n".join(lines), args.json)
    return 0


def cmd_policy_remove(args: argparse.Namespace) -> int:
    data = load_user_config(missing_ok=False)
    removed = remove_rule(data, args.index)
    save_user_config(data)
    _emit({"success": True, "removed": removed}, f"Removed rule {args.index}", args.json)
    return 0


def cmd_hook_install(args: argparse.Namespace) -> int:
    result = install_hook(_script_path(), _settings(args))
    _emit(result, f"Installed global SessionEnd hook in {result['settings']}", args.json)
    return 0


def cmd_hook_status(args: argparse.Namespace) -> int:
    result = hook_status(_settings(args))
    message = (
        f"Hook: {'installed' if result['installed'] else 'not installed'} ({result['settings']})"
    )
    _emit(result, message, args.json)
    return 0 if result["installed"] else 1


def cmd_hook_uninstall(args: argparse.Namespace) -> int:
    result = uninstall_hook(_settings(args))
    _emit(result, f"Removed {result['removed']} session hook(s)", args.json)
    return 0


def _run_hook() -> int:
    """Run fail-closed and silent so SessionEnd itself can never fail."""
    try:
        event = json.load(sys.stdin)
        cwd = event.get("cwd")
        transcript_value = event.get("transcript_path")
        session_id = event.get("session_id")
        if not cwd or not transcript_value or not session_id:
            return 0

        config = load_user_config(missing_ok=False)
        decision = evaluate_policy(config, Path(cwd))
        if not decision.allowed:
            return 0

        transcript = Path(transcript_value)
        project = Path(decision.context.git_root or cwd).name
        repo = get_sessions_repo(config)
        result = prepare_export(transcript, session_id, project, repo, _username())
        if result is None:
            return 0
        relative = result.dest.relative_to(repo).as_posix()
        if not commit_file(
            repo,
            relative,
            f"feat: {result.verb} session {result.username}/{result.project}/{session_id}",
        ):
            return 0
        if not pull_rebase(repo):
            return 0
        push(repo)
    except Exception:
        return 0
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config = load_user_config(missing_ok=False)
    repo = get_sessions_repo(config)
    status = hook_status(_settings(args))
    count = sum(1 for _ in (repo / "sessions").glob("*/*.jsonl"))
    sessions = get_sessions_config(config)
    payload = {
        "config": str(get_user_config_path()),
        "repo": str(repo),
        "enabled": sessions.get("enabled", True),
        "policy": validate_policy(sessions.get("policy", {})),
        "hook": status,
        "session_count": count,
    }
    message = f"Sessions: {count}\nRepo: {repo}\nHook: {'installed' if status['installed'] else 'not installed'}"
    _emit(payload, message, args.json)
    return 0


def _session_payload(session: SessionInfo) -> Dict[str, Any]:
    return {
        "path": str(session.path),
        "cwd": session.cwd,
        "title": session.title,
        "size": session.size,
        "messages": session.line_count,
        "mtime": session.mtime,
    }


def cmd_list(args: argparse.Namespace) -> int:
    sessions = discover_sessions(max_results=args.limit)
    payload = {"count": len(sessions), "sessions": [_session_payload(item) for item in sessions]}
    lines = [
        f"{index}. {item.title} — {item.cwd or item.path.parent.name}"
        for index, item in enumerate(sessions, 1)
    ]
    _emit(payload, "\n".join(lines) if lines else "No sessions found", args.json)
    return 0 if sessions else 1


def cmd_share(args: argparse.Namespace) -> int:
    if args.last:
        sessions = discover_sessions(max_results=1)
        if not sessions:
            raise ConfigError("no Claude Code sessions found")
        session = sessions[0]
        transcript = session.path
        cwd = session.cwd
    else:
        transcript = Path(args.transcript).expanduser().resolve()
        cwd = args.cwd
    project = Path(cwd).name if cwd else transcript.parent.name.lstrip("-")
    repo = get_sessions_repo()
    result = prepare_export(transcript, transcript.stem, project, repo, _username())
    if result is None:
        _emit({"changed": False}, "Session unchanged", args.json)
        return 0
    relative = result.dest.relative_to(repo).as_posix()
    if not commit_file(
        repo, relative, f"feat: {result.verb} session {result.username}/{project}/{transcript.stem}"
    ):
        raise ConfigError(f"failed to commit {relative}")
    _emit({"changed": True, "path": relative}, f"Committed {relative}", args.json)
    return 0


def _add_rule_parser(parent: argparse._SubParsersAction, action: str) -> None:
    parser = parent.add_parser(action, help=f"Append an ordered {action} rule")
    selectors = parser.add_mutually_exclusive_group(required=True)
    selectors.add_argument("--origin", help="Normalized origin glob, e.g. github.com/org/*")
    selectors.add_argument("--path", help="Canonical git-root path glob")
    parser.set_defaults(func=cmd_policy_add, action=action)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Share Claude Code sessions under a global repository policy"
    )
    parser.add_argument("--json", action="store_true", help="Force JSON output")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show config, policy, hook, and session status")
    status.add_argument("--settings", help="Claude settings path override")
    status.set_defaults(func=cmd_status)

    config = sub.add_parser("config", help="Manage global session configuration")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    config_init = config_sub.add_parser(
        "init", help="Initialize config without replacing other rhdh-skill keys"
    )
    config_init.add_argument("--repo", required=True, help="Shared sessions repository")
    config_init.add_argument("--default", choices=["allow", "deny"], default="deny")
    config_init.set_defaults(func=cmd_config_init)
    config_show = config_sub.add_parser("show", help="Show effective global session config")
    config_show.set_defaults(func=cmd_config_show)

    policy = sub.add_parser("policy", help="Manage ordered repository allow/deny rules")
    policy_sub = policy.add_subparsers(dest="policy_command", required=True)
    check = policy_sub.add_parser("check", help="Explain the decision for a repository")
    check.add_argument("path", nargs="?", default=".")
    check.set_defaults(func=cmd_policy_check)
    default = policy_sub.add_parser("default", help="Set the policy fallback action")
    default.add_argument("action", choices=["allow", "deny"])
    default.set_defaults(func=cmd_policy_default)
    _add_rule_parser(policy_sub, "allow")
    _add_rule_parser(policy_sub, "deny")
    rules = policy_sub.add_parser("rules", help="List ordered policy rules")
    rules.set_defaults(func=cmd_policy_rules)
    remove = policy_sub.add_parser("remove", help="Remove a policy rule by one-based index")
    remove.add_argument("index", type=int)
    remove.set_defaults(func=cmd_policy_remove)

    hook = sub.add_parser("hook", help="Manage the global Claude Code SessionEnd hook")
    hook_sub = hook.add_subparsers(dest="hook_command", required=True)
    for name, func in (
        ("install", cmd_hook_install),
        ("status", cmd_hook_status),
        ("uninstall", cmd_hook_uninstall),
    ):
        command = hook_sub.add_parser(name, help=f"{name.capitalize()} the global hook")
        command.add_argument("--settings", help="Claude settings path override")
        command.set_defaults(func=func)
    run = hook_sub.add_parser("run", help=argparse.SUPPRESS)
    run.set_defaults(internal_hook=True)

    listing = sub.add_parser("list", help="List recent local Claude Code sessions")
    listing.add_argument("--limit", type=int, default=20)
    listing.set_defaults(func=cmd_list)
    share = sub.add_parser(
        "share", help="Explicitly export one local session without policy evaluation"
    )
    source = share.add_mutually_exclusive_group(required=True)
    source.add_argument("--last", action="store_true")
    source.add_argument("--transcript")
    share.add_argument("--cwd", help="Original session working directory")
    share.set_defaults(func=cmd_share)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    if getattr(args, "internal_hook", False):
        return _run_hook()
    try:
        return args.func(args)
    except (ConfigError, HookError, OSError) as exc:
        if args.json or not sys.stdout.isatty():
            json.dump({"success": False, "error": str(exc)}, sys.stdout)
            sys.stdout.write("\n")
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
