"""Claude Code SessionEnd hook installation and lifecycle management."""

from __future__ import annotations

import json
import shlex
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_SETTINGS = Path.home() / ".claude" / "settings.json"


class HookError(ValueError):
    """Raised when Claude settings cannot be safely updated."""


def _load_settings(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HookError(f"invalid Claude settings {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise HookError(f"Claude settings must contain a JSON object: {path}")
    return data


def _save_settings(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="settings-", suffix=".json", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        Path(temp_name).replace(path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def is_managed_command(command: Any) -> bool:
    if not isinstance(command, str):
        return False
    return "export-session" in command or ("fs-sessions" in command and "hook run" in command)


def _remove_managed(entries: Any) -> Tuple[List[Dict[str, Any]], int]:
    if entries is None:
        return [], 0
    if not isinstance(entries, list):
        raise HookError("hooks.SessionEnd must be an array")
    kept = []
    removed = 0
    for entry in entries:
        if not isinstance(entry, dict):
            kept.append(entry)
            continue
        hooks = entry.get("hooks")
        if not isinstance(hooks, list):
            kept.append(entry)
            continue
        remaining = []
        for hook in hooks:
            command = hook.get("command") if isinstance(hook, dict) else None
            if is_managed_command(command):
                removed += 1
            else:
                remaining.append(hook)
        if remaining:
            updated = dict(entry)
            updated["hooks"] = remaining
            kept.append(updated)
    return kept, removed


def hook_command(script_path: Path) -> str:
    return f"python3 {shlex.quote(str(script_path.resolve()))} hook run"


def install_hook(script_path: Path, settings_path: Path = DEFAULT_SETTINGS) -> Dict[str, Any]:
    data = _load_settings(settings_path)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise HookError("Claude settings key 'hooks' must be an object")
    entries, removed = _remove_managed(hooks.get("SessionEnd"))
    command = hook_command(script_path)
    entries.append(
        {
            "matcher": "",
            "hooks": [{"type": "command", "command": command}],
        }
    )
    hooks["SessionEnd"] = entries
    _save_settings(settings_path, data)
    return {
        "installed": True,
        "settings": str(settings_path),
        "command": command,
        "replaced": removed,
    }


def uninstall_hook(settings_path: Path = DEFAULT_SETTINGS) -> Dict[str, Any]:
    data = _load_settings(settings_path)
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return {"installed": False, "settings": str(settings_path), "removed": 0}
    entries, removed = _remove_managed(hooks.get("SessionEnd"))
    if entries:
        hooks["SessionEnd"] = entries
    else:
        hooks.pop("SessionEnd", None)
    if not hooks:
        data.pop("hooks", None)
    _save_settings(settings_path, data)
    return {"installed": False, "settings": str(settings_path), "removed": removed}


def hook_status(settings_path: Path = DEFAULT_SETTINGS) -> Dict[str, Any]:
    data = _load_settings(settings_path)
    hooks = data.get("hooks")
    entries = hooks.get("SessionEnd", []) if isinstance(hooks, dict) else []
    commands = []
    if isinstance(entries, list):
        for entry in entries:
            for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
                command = hook.get("command") if isinstance(hook, dict) else None
                if is_managed_command(command):
                    commands.append(command)
    return {
        "installed": bool(commands),
        "settings": str(settings_path),
        "commands": commands,
    }
