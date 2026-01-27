"""Configuration management for rhdh-plugin CLI.

Handles path discovery, user configuration, and environment variable overrides.

Location discovery order:
1. Environment variables (RHDH_OVERLAY_REPO, etc.)
2. User config (~/.config/rhdh-plugin-skill/config.json)
3. Skill install root (../repo/ relative to skill)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

# Config locations
USER_CONFIG_DIR = Path.home() / ".config" / "rhdh-plugin-skill"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.json"


def get_skill_root() -> Path:
    """Get the skill root directory.

    Uses SKILL_ROOT env var if set, otherwise derives from package location.
    """
    if "SKILL_ROOT" in os.environ:
        return Path(os.environ["SKILL_ROOT"])
    # Package is in rhdh_plugin/, skill root is parent
    return Path(__file__).parent.parent


def find_repo(repo_name: str, env_var: str) -> Optional[Path]:
    """Find a repository in well-known locations.

    Args:
        repo_name: Directory name to look for (e.g., "rhdh-plugin-export-overlays")
        env_var: Environment variable that can override (e.g., "RHDH_OVERLAY_REPO")

    Returns:
        Path to the repository, or None if not found.

    Discovery order:
    1. Environment variable override
    2. User config file
    3. Skill install root (../repo/ relative to skill)
    4. Parent's repo/ directory (if skill is deeper nested)
    """
    # 1. Environment variable override
    env_value = os.environ.get(env_var)
    if env_value:
        path = Path(env_value)
        if path.is_dir():
            return path.resolve()

    # 2. User config file
    if USER_CONFIG_FILE.exists():
        try:
            config = json.loads(USER_CONFIG_FILE.read_text())
            # Map repo_name to config key
            key_map = {
                "rhdh-plugin-export-overlays": "overlay",
                "rhdh-local": "local",
                "rhdh-dynamic-plugin-factory": "factory",
            }
            config_key = key_map.get(repo_name, repo_name)
            config_path = config.get("repos", {}).get(config_key)
            if config_path:
                path = Path(config_path)
                if path.is_dir():
                    return path.resolve()
        except (json.JSONDecodeError, OSError):
            pass

    # 3. Skill install root (../repo/ relative to skill)
    skill_root = get_skill_root()
    skill_repo_path = skill_root.parent / "repo" / repo_name
    if skill_repo_path.is_dir():
        return skill_repo_path.resolve()

    # 4. Parent's repo/ directory (if skill is deeper nested)
    parent_repo_path = skill_root.parent.parent / "repo" / repo_name
    if parent_repo_path.is_dir():
        return parent_repo_path.resolve()

    return None


def get_overlay_repo() -> Optional[Path]:
    """Get path to rhdh-plugin-export-overlays repo."""
    return find_repo("rhdh-plugin-export-overlays", "RHDH_OVERLAY_REPO")


def get_local_repo() -> Optional[Path]:
    """Get path to rhdh-local repo."""
    return find_repo("rhdh-local", "RHDH_LOCAL_REPO")


def get_factory_repo() -> Optional[Path]:
    """Get path to rhdh-dynamic-plugin-factory repo."""
    return find_repo("rhdh-dynamic-plugin-factory", "RHDH_FACTORY_REPO")


def load_config() -> dict:
    """Load user config from file.

    Returns:
        Config dict, or empty dict if file doesn't exist.
    """
    if not USER_CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(USER_CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    """Save config to user config file.

    Creates config directory if needed.
    """
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    USER_CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")


def config_init() -> tuple[bool, list[str]]:
    """Initialize user configuration file.

    Returns:
        Tuple of (created: bool, messages: list[str])
    """
    messages = []

    if USER_CONFIG_FILE.exists():
        messages.append(f"Config file already exists: {USER_CONFIG_FILE}")
        return False, messages

    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Try to auto-detect repos
    skill_root = get_skill_root()
    overlay = ""
    local_repo = ""
    factory = ""

    # Check skill root location
    overlay_path = skill_root.parent / "repo" / "rhdh-plugin-export-overlays"
    if overlay_path.is_dir():
        overlay = str(overlay_path.resolve())

    local_path = skill_root.parent / "repo" / "rhdh-local"
    if local_path.is_dir():
        local_repo = str(local_path.resolve())

    factory_path = skill_root.parent / "repo" / "rhdh-dynamic-plugin-factory"
    if factory_path.is_dir():
        factory = str(factory_path.resolve())

    config = {
        "repos": {
            "overlay": overlay,
            "local": local_repo,
            "factory": factory,
        }
    }
    save_config(config)
    messages.append(f"Created: {USER_CONFIG_FILE}")

    if overlay:
        messages.append(f"Auto-detected overlay repo: {overlay}")
    else:
        messages.append(
            "overlay repo: not found (configure with: rhdh-plugin config set overlay /path)"
        )

    if local_repo:
        messages.append(f"Auto-detected rhdh-local: {local_repo}")
    else:
        messages.append(
            "rhdh-local: not found (configure with: rhdh-plugin config set local /path)"
        )

    return True, messages


def config_set(key: str, value: str) -> tuple[bool, str]:
    """Set a config value.

    Args:
        key: Config key (overlay, local, factory)
        value: Path value to set

    Returns:
        Tuple of (success: bool, message: str)
    """
    valid_keys = {"overlay", "local", "factory"}
    if key not in valid_keys:
        return False, f"Unknown config key: {key}. Valid keys: {', '.join(sorted(valid_keys))}"

    path = Path(value)
    if not path.is_dir():
        return False, f"Path does not exist: {value}"

    # Resolve to absolute path
    abs_path = str(path.resolve())

    # Load existing config or create new
    config = load_config()
    if "repos" not in config:
        config["repos"] = {}

    config["repos"][key] = abs_path
    save_config(config)

    return True, f"Set {key} = {abs_path}"


def get_config_info() -> dict:
    """Get configuration info for display.

    Returns:
        Dict with config_file, skill_root, user_config, and resolved paths.
    """
    return {
        "config_file": str(USER_CONFIG_FILE),
        "skill_root": str(get_skill_root()),
        "user_config": load_config(),
        "resolved": {
            "overlay": get_overlay_repo(),
            "local": get_local_repo(),
            "factory": get_factory_repo(),
        },
    }
