"""Discover local Claude Code session transcripts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


@dataclass
class SessionInfo:
    path: Path
    mtime: float
    title: str
    cwd: Optional[str]
    size: int
    line_count: int


def _metadata(path: Path) -> tuple[str, Optional[str]]:
    title = ""
    cwd = None
    try:
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if item.get("type") == "ai-title":
                    title = item.get("aiTitle", "")
                if (
                    cwd is None
                    and item.get("type") == "user"
                    and item.get("sessionId") is not None
                    and item.get("cwd") is not None
                ):
                    cwd = item["cwd"]
    except OSError:
        pass
    return title or "(untitled)", cwd


def discover_sessions(
    projects_dir: Optional[Path] = None, max_results: int = 20
) -> List[SessionInfo]:
    base = projects_dir or CLAUDE_PROJECTS_DIR
    if not base.is_dir():
        return []
    sessions = []
    for transcript in base.glob("*/*.jsonl"):
        try:
            stat = transcript.stat()
            with transcript.open(encoding="utf-8") as stream:
                lines = sum(1 for _ in stream)
        except OSError:
            continue
        title, cwd = _metadata(transcript)
        sessions.append(SessionInfo(transcript, stat.st_mtime, title, cwd, stat.st_size, lines))
    sessions.sort(key=lambda item: item.mtime, reverse=True)
    return sessions[:max_results]
