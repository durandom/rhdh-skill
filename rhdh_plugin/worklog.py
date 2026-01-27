"""Worklog management for rhdh-plugin CLI.

Simple append-only JSONL log for tracking work activities.
Stored in ~/.config/rhdh-plugin-skill/worklog.jsonl
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import USER_CONFIG_DIR

WORKLOG_FILE = USER_CONFIG_DIR / "worklog.jsonl"


def _ensure_worklog() -> Path:
    """Ensure worklog file exists, return path."""
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not WORKLOG_FILE.exists():
        WORKLOG_FILE.touch()
    return WORKLOG_FILE


def add_entry(message: str, tags: Optional[list[str]] = None) -> dict:
    """Add a new worklog entry.

    Args:
        message: The log message
        tags: Optional list of tags

    Returns:
        The created entry dict
    """
    _ensure_worklog()

    entry: dict[str, str | list[str]] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "msg": message,
    }
    if tags:
        entry["tags"] = tags

    with WORKLOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def read_entries(
    limit: Optional[int] = None,
    since: Optional[str] = None,
) -> list[dict]:
    """Read worklog entries.

    Args:
        limit: Maximum number of entries to return (most recent first)
        since: ISO date string to filter entries after

    Returns:
        List of entry dicts, most recent first
    """
    if not WORKLOG_FILE.exists():
        return []

    entries = []
    since_dt = None
    if since:
        # Parse date (accepts YYYY-MM-DD or full ISO)
        try:
            if "T" in since:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            else:
                since_dt = datetime.fromisoformat(since + "T00:00:00+00:00")
        except ValueError:
            pass  # Ignore invalid dates

    with WORKLOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if since_dt:
                    entry_ts = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
                    if entry_ts < since_dt:
                        continue
                entries.append(entry)
            except (json.JSONDecodeError, KeyError):
                continue  # Skip malformed entries

    # Reverse for most recent first
    entries.reverse()

    if limit:
        entries = entries[:limit]

    return entries


def search_entries(query: str, limit: Optional[int] = None) -> list[dict]:
    """Search worklog entries.

    Args:
        query: Search string (case-insensitive, matches message or tags)
        limit: Maximum number of results

    Returns:
        List of matching entry dicts, most recent first
    """
    if not WORKLOG_FILE.exists():
        return []

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = []

    with WORKLOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # Search in message
                if pattern.search(entry.get("msg", "")):
                    matches.append(entry)
                    continue
                # Search in tags
                for tag in entry.get("tags", []):
                    if pattern.search(tag):
                        matches.append(entry)
                        break
            except json.JSONDecodeError:
                continue

    # Reverse for most recent first
    matches.reverse()

    if limit:
        matches = matches[:limit]

    return matches


def format_entry_human(entry: dict) -> str:
    """Format a single entry for human display."""
    ts = entry.get("ts", "")
    # Parse and format timestamp
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        ts_display = dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        ts_display = ts[:16] if len(ts) >= 16 else ts

    msg = entry.get("msg", "")
    tags = entry.get("tags", [])

    if tags:
        tags_str = " [" + ", ".join(tags) + "]"
    else:
        tags_str = ""

    return f"{ts_display}  {msg}{tags_str}"
