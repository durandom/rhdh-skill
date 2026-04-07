"""Local RHDH operations (copy-sync, container lifecycle).

Business logic for the rhdh-local-setup customization system.
Patterns inspired by Ben Wilcock's rhdh-lab (https://github.com/benwilcock/rhdh-lab),
licensed under Apache 2.0. See skills/rhdh-local/scripts/NOTICE for details.
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import urlopen

# =============================================================================
# Copy-Sync Operations
# =============================================================================

# Single source of truth for the customization file mapping.
# These are relative paths within the workspace (rhdh-customizations/ → rhdh-local/).
CUSTOMIZATION_FILES = [
    "compose.override.yaml",
    ".env",
    "configs/app-config/app-config.local.yaml",
    "configs/dynamic-plugins/dynamic-plugins.override.yaml",
    "developer-lightspeed/configs/app-config/app-config.lightspeed.local.yaml",
]

CUSTOMIZATION_GLOBS = [
    "configs/catalog-entities/*.override.yaml",
    "configs/extra-files/*",
]


@dataclass
class SyncResult:
    """Result of a copy-sync operation."""

    copied: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def apply_customizations(workspace: Path) -> SyncResult:
    """Copy override files from rhdh-customizations/ into rhdh-local/.

    Args:
        workspace: Path to rhdh-local-setup workspace root.

    Returns:
        SyncResult with lists of copied, skipped, and errored paths.
    """
    src = workspace / "rhdh-customizations"
    dst = workspace / "rhdh-local"
    result = SyncResult()

    if not src.is_dir():
        result.errors.append(f"rhdh-customizations not found: {src}")
        return result
    if not dst.is_dir():
        result.errors.append(f"rhdh-local not found: {dst}")
        return result

    # Fixed files
    for rel in CUSTOMIZATION_FILES:
        _copy_file(src / rel, dst / rel, rel, result)

    # Glob patterns
    for pattern in CUSTOMIZATION_GLOBS:
        for src_file in src.glob(pattern):
            if not src_file.is_file():
                continue
            rel = str(src_file.relative_to(src))
            _copy_file(src_file, dst / rel, rel, result)

    return result


def remove_customizations(workspace: Path) -> SyncResult:
    """Remove copied override files from rhdh-local/.

    Uses rhdh-customizations/ as the reference for wildcard removals,
    so only files that were actually copied get removed.

    Args:
        workspace: Path to rhdh-local-setup workspace root.

    Returns:
        SyncResult with lists of removed and skipped paths.
    """
    src = workspace / "rhdh-customizations"
    dst = workspace / "rhdh-local"
    result = SyncResult()

    # Fixed files — remove from dst regardless of src existence
    for rel in CUSTOMIZATION_FILES:
        _remove_file(dst / rel, rel, result)

    # Glob patterns — use src as reference for what to remove
    if src.is_dir():
        for pattern in CUSTOMIZATION_GLOBS:
            for src_file in src.glob(pattern):
                if not src_file.is_file():
                    continue
                rel = str(src_file.relative_to(src))
                _remove_file(dst / rel, rel, result)

    return result


def _copy_file(src: Path, dst: Path, rel: str, result: SyncResult) -> None:
    """Copy a single file, updating the SyncResult."""
    if not src.is_file():
        result.skipped.append(rel)
        return
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        result.copied.append(rel)
    except OSError as e:
        result.errors.append(f"{rel}: {e}")


def _remove_file(dst: Path, rel: str, result: SyncResult) -> None:
    """Remove a single file, updating the SyncResult."""
    if dst.is_file():
        try:
            dst.unlink()
            result.removed.append(rel)
        except OSError as e:
            result.errors.append(f"{rel}: {e}")
    else:
        result.skipped.append(rel)


# =============================================================================
# Container Runtime
# =============================================================================


def detect_compose_command() -> list[str]:
    """Auto-detect container runtime and return compose command parts.

    Returns:
        ["podman", "compose"] or ["docker", "compose"]

    Raises:
        RuntimeError: If neither podman nor docker is found.
    """
    if shutil.which("podman"):
        return ["podman", "compose"]
    if shutil.which("docker"):
        return ["docker", "compose"]
    raise RuntimeError("Neither podman nor docker found in PATH")


# Compose files to include, checked in order. Both our naming convention
# and rhdh-lab's naming convention are supported.
_LIGHTSPEED_COMPOSE_FILES = [
    "developer-lightspeed/compose.lightspeed.yaml",  # our convention
    "developer-lightspeed/compose.yaml",  # rhdh-lab convention
]
_ORCHESTRATOR_COMPOSE_FILES = [
    "developer-ai-orchestrator/compose.orchestrator.yaml",  # our convention
    "orchestrator/compose.yaml",  # rhdh-lab convention
]


def build_compose_args(
    rhdh_local: Path,
    lightspeed: bool = False,
    orchestrator: bool = False,
) -> list[str]:
    """Build the compose -f flag chain from available files.

    Args:
        rhdh_local: Path to rhdh-local/ directory.
        lightspeed: Include Lightspeed compose file.
        orchestrator: Include Orchestrator compose file.

    Returns:
        List of args like ["-f", "compose.yaml", "-f", "compose.override.yaml", ...].
    """
    args = ["-f", "compose.yaml"]

    if (rhdh_local / "compose.override.yaml").is_file():
        args.extend(["-f", "compose.override.yaml"])

    if lightspeed:
        for candidate in _LIGHTSPEED_COMPOSE_FILES:
            if (rhdh_local / candidate).is_file():
                args.extend(["-f", candidate])
                break

    if orchestrator:
        for candidate in _ORCHESTRATOR_COMPOSE_FILES:
            if (rhdh_local / candidate).is_file():
                args.extend(["-f", candidate])
                break

    return args


def _run_compose(
    compose_cmd: list[str],
    compose_args: list[str],
    action_args: list[str],
    cwd: Path,
) -> tuple[int, str, str]:
    """Run a compose command and return (returncode, stdout, stderr)."""
    full_cmd = [*compose_cmd, *compose_args, *action_args]
    try:
        proc = subprocess.run(full_cmd, capture_output=True, text=True, cwd=cwd)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {full_cmd[0]}"


# =============================================================================
# Orchestrators (up / down)
# =============================================================================


def local_up(
    workspace: Path,
    baseline: bool = False,
    lightspeed: bool = False,
    orchestrator: bool = False,
    follow_logs: bool = False,
) -> tuple[SyncResult, int, str, str]:
    """Apply customizations (or remove if baseline) and start containers.

    Returns:
        Tuple of (sync_result, compose_returncode, stdout, stderr).
    """
    rhdh_local = workspace / "rhdh-local"

    # Step 1: sync customizations
    if baseline:
        sync = remove_customizations(workspace)
    else:
        sync = apply_customizations(workspace)

    if sync.errors:
        return sync, 1, "", "\n".join(sync.errors)

    # Step 2: detect runtime and build command
    compose_cmd = detect_compose_command()
    compose_args = build_compose_args(rhdh_local, lightspeed=lightspeed, orchestrator=orchestrator)

    # Step 3: start containers
    rc, stdout, stderr = _run_compose(compose_cmd, compose_args, ["up", "-d"], cwd=rhdh_local)

    # Step 4: follow logs if requested (blocking)
    if rc == 0 and follow_logs:
        # Run logs in foreground — this blocks until Ctrl+C
        try:
            subprocess.run(
                [*compose_cmd, *compose_args, "logs", "-f"],
                cwd=rhdh_local,
            )
        except KeyboardInterrupt:
            pass

    return sync, rc, stdout, stderr


def local_down(
    workspace: Path,
    volumes: bool = False,
) -> tuple[SyncResult, int, str, str]:
    """Stop containers and remove customizations.

    Returns:
        Tuple of (sync_result, compose_returncode, stdout, stderr).
    """
    rhdh_local = workspace / "rhdh-local"

    # Step 1: detect runtime and build command (include all available files)
    compose_cmd = detect_compose_command()
    compose_args = build_compose_args(rhdh_local, lightspeed=True, orchestrator=True)

    # Step 2: stop containers
    action_args = ["down", "-v"] if volumes else ["down"]
    rc, stdout, stderr = _run_compose(compose_cmd, compose_args, action_args, cwd=rhdh_local)

    # Step 3: always remove customizations after shutdown
    sync = remove_customizations(workspace)

    return sync, rc, stdout, stderr


# =============================================================================
# Last Run Settings (--last flag)
# =============================================================================

LAST_RUN_FILE = ".last-run-settings"
_LAST_RUN_VERSION = "1"
_KEY_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


@dataclass
class LastRunSettings:
    """Persisted settings from the last successful rhdh local up."""

    mode: str = "customized"
    lightspeed: bool = False
    orchestrator: bool = False
    follow_logs: bool = False


def save_last_run(workspace: Path, settings: LastRunSettings) -> Path:
    """Save settings atomically after successful container start.

    Returns:
        Path to the saved settings file.
    """
    path = workspace / LAST_RUN_FILE
    tmp_path = workspace / f"{LAST_RUN_FILE}.tmp"

    content = (
        f"# Last successful rhdh local up configuration (auto-generated)\n"
        f"VERSION={_LAST_RUN_VERSION}\n"
        f"MODE={settings.mode}\n"
        f"INCLUDE_LIGHTSPEED={'true' if settings.lightspeed else 'false'}\n"
        f"INCLUDE_ORCHESTRATOR={'true' if settings.orchestrator else 'false'}\n"
        f"FOLLOW_LOGS={'true' if settings.follow_logs else 'false'}\n"
    )

    tmp_path.write_text(content)
    os.replace(tmp_path, path)
    return path


def load_last_run(workspace: Path) -> Optional[LastRunSettings]:
    """Load and validate last run settings.

    Returns:
        LastRunSettings if valid, None if file missing or invalid.
    """
    path = workspace / LAST_RUN_FILE
    if not path.is_file():
        return None

    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _KEY_PATTERN.match(line)
        if not m:
            return None  # malformed line
        values[m.group(1)] = m.group(2).strip()

    # Validate version
    if values.get("VERSION") != _LAST_RUN_VERSION:
        return None

    # Validate mode
    mode = values.get("MODE", "")
    if mode not in ("customized", "baseline"):
        return None

    def _parse_bool(key: str) -> bool:
        return values.get(key, "false").lower() == "true"

    return LastRunSettings(
        mode=mode,
        lightspeed=_parse_bool("INCLUDE_LIGHTSPEED"),
        orchestrator=_parse_bool("INCLUDE_ORCHESTRATOR"),
        follow_logs=_parse_bool("FOLLOW_LOGS"),
    )


# =============================================================================
# Health Checks
# =============================================================================


@dataclass
class HealthCheck:
    """Result of a single health check."""

    name: str
    status: str  # "pass", "fail", "warn", "info"
    message: str
    detail: str = ""


def check_local_health(workspace: Path) -> list[HealthCheck]:
    """Run health checks on the local RHDH instance.

    Checks: container runtime, port 7007, container status,
    backend health endpoint, plugin install log.
    """
    checks: list[HealthCheck] = []
    rhdh_local = workspace / "rhdh-local"

    # 1. Container runtime
    try:
        compose_cmd = detect_compose_command()
        checks.append(
            HealthCheck(
                name="container_runtime",
                status="pass",
                message=f"{compose_cmd[0]} found",
            )
        )
    except RuntimeError as e:
        checks.append(
            HealthCheck(
                name="container_runtime",
                status="fail",
                message=str(e),
            )
        )
        return checks  # can't continue without runtime

    # 2. Port 7007 reachable
    port_open = False
    try:
        with socket.create_connection(("localhost", 7007), timeout=2):
            port_open = True
    except OSError:
        pass

    if port_open:
        checks.append(
            HealthCheck(
                name="rhdh_port",
                status="pass",
                message="RHDH reachable on http://localhost:7007",
            )
        )
    else:
        checks.append(
            HealthCheck(
                name="rhdh_port",
                status="fail",
                message="Port 7007 not reachable (RHDH not running?)",
            )
        )

    # 3. Container status via compose ps
    if rhdh_local.is_dir():
        compose_args = build_compose_args(rhdh_local, lightspeed=True, orchestrator=True)
        rc, stdout, _ = _run_compose(
            compose_cmd, compose_args, ["ps", "--format", "json"], cwd=rhdh_local
        )
        if rc == 0 and stdout.strip():
            checks.append(
                HealthCheck(
                    name="containers",
                    status="pass",
                    message="Containers running",
                    detail=stdout.strip(),
                )
            )
        else:
            checks.append(
                HealthCheck(
                    name="containers",
                    status="fail",
                    message="No containers found or compose ps failed",
                )
            )

    # 4. Backend health endpoint
    if port_open:
        try:
            with urlopen("http://localhost:7007/api/catalog/health", timeout=5) as resp:
                body = resp.read().decode()
                if "ok" in body.lower():
                    checks.append(
                        HealthCheck(
                            name="backend_health",
                            status="pass",
                            message="Catalog backend healthy",
                        )
                    )
                else:
                    checks.append(
                        HealthCheck(
                            name="backend_health",
                            status="warn",
                            message=f"Unexpected response: {body[:100]}",
                        )
                    )
        except (URLError, OSError) as e:
            checks.append(
                HealthCheck(
                    name="backend_health",
                    status="warn",
                    message=f"Health endpoint not reachable: {e}",
                )
            )

    return checks


# =============================================================================
# Backup / Restore
# =============================================================================

DEFAULT_BACKUP_DIR = Path.home() / "rhdh-local-backups"


@dataclass
class BackupInfo:
    """Information about a backup archive."""

    path: Path
    timestamp: str
    size_bytes: int


def backup_customizations(
    workspace: Path,
    backup_dir: Optional[Path] = None,
) -> BackupInfo:
    """Create a timestamped tar.gz archive of rhdh-customizations/.

    Args:
        workspace: Path to rhdh-local-setup workspace root.
        backup_dir: Where to store backups (default: ~/rhdh-local-backups/).

    Returns:
        BackupInfo with path, timestamp, and size.

    Raises:
        FileNotFoundError: If rhdh-customizations/ doesn't exist.
    """
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR

    customizations = workspace / "rhdh-customizations"
    if not customizations.is_dir():
        raise FileNotFoundError(f"rhdh-customizations not found: {customizations}")

    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    archive_name = f"rhdh-customizations-backup_{ts}.tar.gz"
    archive_path = backup_dir / archive_name

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(customizations, arcname="rhdh-customizations")

    return BackupInfo(
        path=archive_path,
        timestamp=ts,
        size_bytes=archive_path.stat().st_size,
    )


def list_backups(backup_dir: Optional[Path] = None) -> list[BackupInfo]:
    """List available backup archives, newest first."""
    if backup_dir is None:
        backup_dir = DEFAULT_BACKUP_DIR

    if not backup_dir.is_dir():
        return []

    backups = []
    for f in sorted(backup_dir.glob("rhdh-customizations-backup_*.tar.gz"), reverse=True):
        # Extract timestamp from filename
        m = re.search(r"backup_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})", f.name)
        ts = m.group(1) if m else "unknown"
        backups.append(
            BackupInfo(
                path=f,
                timestamp=ts,
                size_bytes=f.stat().st_size,
            )
        )

    return backups


def preview_restore(archive: Path) -> list[str]:
    """List files that would be extracted from a backup archive.

    Returns:
        List of relative paths in the archive.
    """
    if not archive.is_file():
        raise FileNotFoundError(f"Archive not found: {archive}")

    with tarfile.open(archive, "r:gz") as tar:
        return [m.name for m in tar.getmembers() if m.isfile()]


def restore_customizations(
    workspace: Path,
    archive: Path,
) -> SyncResult:
    """Extract backup archive into the workspace.

    Extracts rhdh-customizations/ from the archive, overwriting existing files.

    Args:
        workspace: Path to rhdh-local-setup workspace root.
        archive: Path to the backup .tar.gz file.

    Returns:
        SyncResult with extracted files listed in 'copied'.
    """
    result = SyncResult()

    if not archive.is_file():
        result.errors.append(f"Archive not found: {archive}")
        return result

    try:
        with tarfile.open(archive, "r:gz") as tar:
            # Security: filter out absolute paths and path traversal
            members = []
            for m in tar.getmembers():
                if m.name.startswith("/") or ".." in m.name:
                    result.errors.append(f"Skipping unsafe path: {m.name}")
                    continue
                members.append(m)

            tar.extractall(path=workspace, members=members)
            result.copied = [m.name for m in members if m.isfile()]
    except (tarfile.TarError, OSError) as e:
        result.errors.append(str(e))

    return result
