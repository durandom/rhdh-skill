"""Parse Jira Rich Filter JSON exports for release JQL queries.

Reads the "RHIDP Operational" Rich Filter export at runtime, providing
accessor functions for static filters, smart filters, rich queues, and
the base JQL scope. Falls back gracefully when the file is not available.

The JSON structure (top-level):
    {
      "richFilter": {
        "jiraFilter": { "jql": "..." },
        "staticFilters": [{ "name": "...", "jql": "..." }, ...],
        "smartFilters": [{ "name": "...", "clauses": [{ "name": "...", "jql": "..." }, ...] }, ...],
        "richQueues": [{ "name": "...", "jql": "..." }, ...]
      }
    }
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

_RICH_FILTER_FILENAME = "rhidp-operational-rich-filter.json"
_RICH_FILTER_SUBPATH = Path("jira-rich-filter") / _RICH_FILTER_FILENAME

_cache: dict | None = None
_cache_path: str | None = None


def _configured_repo() -> Path | None:
    """Read the private-data repo from the shared RHDH configuration.

    The release scripts are also run directly, where the ``rhdh`` Python
    package is not necessarily importable. In that case, read the same
    project and user config files used by ``rhdh.config``.
    """
    env_path = os.environ.get("RHDH_PRIVATE_DATA_REPO")
    if env_path and Path(env_path).is_dir():
        return Path(env_path).resolve()

    config_paths = [Path.home() / ".config" / "rhdh-skill" / "config.json"]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        config_paths.append(Path(result.stdout.strip()) / ".rhdh" / "config.json")
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    repo_path = None
    for config_path in config_paths:
        try:
            data = json.loads(config_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        configured = data.get("repos", {}).get("private-data")
        if configured:
            repo_path = Path(configured).expanduser()

    if repo_path and repo_path.is_dir():
        return repo_path.resolve()
    return None


def discover() -> Path | None:
    """Find the Rich Filter JSON file.

    Discovery order:
    1. RHDH_RICH_FILTER_PATH env var (explicit file path override)
    2. rhdh.config.get_repo("private-data") — defers to the rhdh skill's
       config system (env var, config JSON, filesystem auto-detect)
    """
    env_path = os.environ.get("RHDH_RICH_FILTER_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p

    try:
        from rhdh.config import get_repo

        repo_path = get_repo("private-data")
    except ImportError:
        repo_path = _configured_repo()

    if repo_path:
        p = repo_path / _RICH_FILTER_SUBPATH
        if p.is_file():
            return p

    return None


def load(path: Path | str | None = None) -> dict | None:
    """Load and cache the Rich Filter JSON.

    Args:
        path: Explicit path to the JSON file. If None, auto-discovers.

    Returns:
        The parsed richFilter dict, or None if the file is not found.

    Raises:
        ValueError: If the file exists but has an unexpected structure.
    """
    global _cache, _cache_path

    if path is not None:
        resolved = str(Path(path).resolve())
    else:
        found = discover()
        if found is None:
            return None
        resolved = str(found)

    if _cache is not None and _cache_path == resolved:
        return _cache

    p = Path(resolved)
    if not p.is_file():
        return None

    data = json.loads(p.read_text())

    rf = data.get("richFilter")
    if rf is None:
        raise ValueError(f"Rich Filter JSON at {resolved} missing top-level 'richFilter' key")

    _cache = rf
    _cache_path = resolved
    return rf


def base_jql(path: Path | str | None = None) -> str | None:
    """Extract the base JQL from richFilter.jiraFilter.jql."""
    rf = load(path)
    if rf is None:
        return None
    jira_filter = rf.get("jiraFilter", {})
    jql = jira_filter.get("jql")
    if not jql:
        return None
    # Strip ORDER BY and trailing clauses — we only want the project scope
    m = re.match(r"(.+?)\s+ORDER\s+BY\s+", jql, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return jql.strip()


def _find_by_name(items: list[dict], name: str) -> dict | None:
    """Find an item in a list by its 'name' field (case-insensitive)."""
    name_lower = name.lower()
    for item in items:
        if item.get("name", "").lower() == name_lower:
            return item
    return None


def static_filter(name: str, path: Path | str | None = None) -> str | None:
    """Get a static filter's JQL by name.

    Args:
        name: Filter name (e.g. "Feature Freeze", "Code Freeze", "CVE")
        path: Optional explicit path to the JSON file.

    Returns:
        The JQL string, or None if not found.
    """
    rf = load(path)
    if rf is None:
        return None
    filters = rf.get("staticFilters", [])
    item = _find_by_name(filters, name)
    return item["jql"] if item else None


def smart_filter_clause(
    group_name: str, clause_name: str, path: Path | str | None = None
) -> str | None:
    """Get a smart filter clause's JQL.

    Args:
        group_name: Smart filter group (e.g. "Scrum Team")
        clause_name: Clause within the group (e.g. "AI", "Cope")
        path: Optional explicit path.

    Returns:
        The JQL string, or None if not found.
    """
    rf = load(path)
    if rf is None:
        return None
    groups = rf.get("smartFilters", [])
    group = _find_by_name(groups, group_name)
    if group is None:
        return None
    clause = _find_by_name(group.get("clauses", []), clause_name)
    return clause["jql"] if clause else None


def rich_queue(name: str, path: Path | str | None = None) -> str | None:
    """Get a rich queue's JQL by name.

    Args:
        name: Queue name (e.g. "RNs Unclassified")
        path: Optional explicit path.

    Returns:
        The JQL string, or None if not found.
    """
    rf = load(path)
    if rf is None:
        return None
    queues = rf.get("richQueues", [])
    item = _find_by_name(queues, name)
    return item["jql"] if item else None


def scrum_teams(path: Path | str | None = None) -> list[dict] | None:
    """Extract team name -> Cloud ID mapping from the 'Scrum Team' smart filter.

    Returns:
        List of dicts with 'name' and 'cloud_id' keys, or None if unavailable.
        The cloud_id is extracted from the JQL pattern: "Team[Team]" = <cloud_id>
    """
    rf = load(path)
    if rf is None:
        return None
    groups = rf.get("smartFilters", [])
    group = _find_by_name(groups, "Scrum Team")
    if group is None:
        return None

    teams = []
    for clause in group.get("clauses", []):
        name = clause.get("name", "")
        jql = clause.get("jql", "")
        # Extract a bare or quoted value from: "Team[Team]" = <cloud_id>
        m = re.search(r""""Team\[Team\]"\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s)]+))""", jql)
        cloud_id = next((value for value in m.groups() if value), "") if m else ""
        teams.append({"name": name, "cloud_id": cloud_id})

    return teams


def list_static_filters(path: Path | str | None = None) -> list[str] | None:
    """List available static filter names."""
    rf = load(path)
    if rf is None:
        return None
    return [f.get("name", "") for f in rf.get("staticFilters", [])]


def list_smart_filters(path: Path | str | None = None) -> list[str] | None:
    """List available smart filter group names."""
    rf = load(path)
    if rf is None:
        return None
    return [f.get("name", "") for f in rf.get("smartFilters", [])]


def list_rich_queues(path: Path | str | None = None) -> list[str] | None:
    """List available rich queue names."""
    rf = load(path)
    if rf is None:
        return None
    return [q.get("name", "") for q in rf.get("richQueues", [])]


def reset_cache() -> None:
    """Clear the cached Rich Filter data. Useful for testing."""
    global _cache, _cache_path
    _cache = None
    _cache_path = None
