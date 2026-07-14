"""Repository identity discovery and ordered allow/deny policy evaluation."""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fs_sessions.config import ConfigError, get_sessions_config, project_disables_sessions


@dataclass
class RepositoryContext:
    requested_path: str
    git_root: Optional[str]
    origin: Optional[str]


@dataclass
class PolicyDecision:
    allowed: bool
    action: str
    reason: str
    matched_rule: Optional[int]
    context: RepositoryContext

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["context"] = asdict(self.context)
        return result


def _git(path: Path, *args: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def normalize_origin(url: str) -> str:
    """Normalize common SSH/HTTP Git URLs to host/owner/repository."""
    value = url.strip()
    scp_match = re.match(r"^(?:[^@]+@)?([^:]+):(.+)$", value)
    if scp_match and "://" not in value:
        host, path = scp_match.groups()
    else:
        match = re.match(r"^(?:[a-z][a-z0-9+.-]*://)(?:[^@/]+@)?([^/]+)/(.+)$", value, re.I)
        if not match:
            return value[:-4] if value.endswith(".git") else value
        host, path = match.groups()
    normalized = f"{host.lower()}/{path.lstrip('/')}"
    return normalized[:-4] if normalized.endswith(".git") else normalized


def discover_repository(path: Path) -> RepositoryContext:
    requested = path.expanduser().resolve()
    root_value = _git(requested, "rev-parse", "--show-toplevel")
    if root_value is None:
        return RepositoryContext(str(requested), None, None)
    root = Path(root_value).resolve()
    origin_value = _git(root, "remote", "get-url", "origin")
    origin = normalize_origin(origin_value) if origin_value else None
    return RepositoryContext(str(requested), str(root), origin)


def validate_policy(policy: Any) -> Dict[str, Any]:
    if not isinstance(policy, dict):
        raise ConfigError("sessions.policy must be an object")
    default = policy.get("default", "deny")
    if default not in {"allow", "deny"}:
        raise ConfigError("sessions.policy.default must be 'allow' or 'deny'")
    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        raise ConfigError("sessions.policy.rules must be an array")
    for index, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            raise ConfigError(f"policy rule {index} must be an object")
        if rule.get("action") not in {"allow", "deny"}:
            raise ConfigError(f"policy rule {index} action must be 'allow' or 'deny'")
        selectors = [key for key in ("origin", "path") if key in rule]
        if len(selectors) != 1:
            raise ConfigError(f"policy rule {index} must contain exactly one origin or path")
        if not isinstance(rule[selectors[0]], str) or not rule[selectors[0]]:
            raise ConfigError(f"policy rule {index} selector must be a non-empty string")
    return {"default": default, "rules": rules}


def _normalize_path_pattern(pattern: str) -> str:
    expanded = os.path.expanduser(pattern)
    return os.path.abspath(expanded)


def _matches(rule: Dict[str, Any], context: RepositoryContext) -> bool:
    if "origin" in rule:
        return context.origin is not None and fnmatch.fnmatchcase(context.origin, rule["origin"])
    if context.git_root is None:
        return False
    return fnmatch.fnmatchcase(context.git_root, _normalize_path_pattern(rule["path"]))


def evaluate_policy(config: Dict[str, Any], path: Path) -> PolicyDecision:
    context = discover_repository(path)
    if context.git_root is None:
        return PolicyDecision(False, "deny", "not_git_repository", None, context)

    sessions = get_sessions_config(config)
    if sessions.get("enabled", True) is not True:
        return PolicyDecision(False, "deny", "globally_disabled", None, context)

    root = Path(context.git_root)
    if project_disables_sessions(root):
        return PolicyDecision(False, "deny", "project_opt_out", None, context)

    policy = validate_policy(sessions.get("policy", {}))
    action = policy["default"]
    reason = f"default_{action}"
    matched_rule = None
    for index, rule in enumerate(policy["rules"], 1):
        if _matches(rule, context):
            action = rule["action"]
            reason = "matched_rule"
            matched_rule = index
    return PolicyDecision(action == "allow", action, reason, matched_rule, context)


def add_rule(config: Dict[str, Any], action: str, selector: str, pattern: str) -> int:
    sessions = get_sessions_config(config)
    policy = validate_policy(sessions.setdefault("policy", {}))
    rules: List[Dict[str, str]] = policy["rules"]
    rules.append({"action": action, selector: pattern})
    sessions["policy"] = policy
    return len(rules)


def remove_rule(config: Dict[str, Any], index: int) -> Dict[str, Any]:
    sessions = get_sessions_config(config)
    policy = validate_policy(sessions.get("policy", {}))
    rules = policy["rules"]
    if index < 1 or index > len(rules):
        raise ConfigError(f"policy rule index out of range: {index}")
    removed = rules.pop(index - 1)
    sessions["policy"] = policy
    return removed
