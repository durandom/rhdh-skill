"""Build metadata and copy session transcripts to the shared repository."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ExportResult:
    dest: Path
    verb: str
    project: str
    username: str


def build_metadata_line(project: str, username: str, timestamp: Optional[str] = None) -> str:
    ts = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cwd = f"/sessions/{username}_{project}"
    meta = {
        "type": "user",
        "timestamp": ts,
        "message": {"content": f"[Session: {project}] by {username}\nProject: {cwd}"},
        "cwd": cwd,
    }
    return json.dumps(meta, separators=(",", ":"))


def destination(repo: Path, username: str, project: str, session_id: str) -> Path:
    return repo / "sessions" / f"{username}_{project}" / f"{session_id}.jsonl"


def _content_size(exported: Path) -> int:
    with exported.open("rb") as stream:
        first_line = stream.readline()
        return exported.stat().st_size - len(first_line)


def prepare_export(
    transcript: Path,
    session_id: str,
    project: str,
    sessions_repo: Path,
    username: str,
    timestamp: Optional[str] = None,
) -> Optional[ExportResult]:
    if not transcript.is_file() or transcript.stat().st_size == 0:
        return None
    dest = destination(sessions_repo, username, project, session_id)
    verb = "add"
    if dest.exists():
        if transcript.stat().st_size == _content_size(dest):
            return None
        verb = "update"

    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as output:
        output.write(build_metadata_line(project, username, timestamp) + "\n")
        with transcript.open(encoding="utf-8") as source:
            shutil.copyfileobj(source, output)
    return ExportResult(dest, verb, project, username)
