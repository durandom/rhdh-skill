"""CLI for rhdh-plugin.

Follows agentic CLI patterns:
- Auto-detects output format: JSON when piped (for Claude), human when TTY
- No-arg default shows orientation (status + needs_setup flag)
- Dry-run by default, --force for destructive actions
- Non-interactive (all input via flags)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from . import __version__
from .config import (
    SUBMODULE_REPOS,
    get_factory_repo,
    get_github_username,
    get_local_repo,
    get_overlay_repo,
    list_submodule_repos,
    save_github_username,
    setup_submodule,
)
from .formatters import OutputFormatter
from .todo import (
    add_note as todo_add_note,
)
from .todo import (
    add_todo,
    get_todo_file_path,
    list_todos,
    mark_done,
)
from .todo import (
    show_raw as todo_show_raw,
)
from .worklog import (
    add_entry as worklog_add_entry,
)
from .worklog import (
    format_entry_human,
    read_entries,
    search_entries,
)
from .workspace import get_workspace, list_workspaces

# =============================================================================
# Helper Functions
# =============================================================================


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def check_tool(name: str) -> bool:
    """Check if a tool is available in PATH."""
    return shutil.which(name) is not None


def get_git_branch(repo_path: Path) -> str:
    """Get current git branch for a repo."""
    rc, stdout, _ = run_command(["git", "branch", "--show-current"], cwd=repo_path)
    return stdout.strip() if rc == 0 else "unknown"


def has_uncommitted_changes(repo_path: Path) -> bool:
    """Check if repo has uncommitted changes."""
    rc, stdout, _ = run_command(["git", "status", "--porcelain"], cwd=repo_path)
    return rc == 0 and bool(stdout.strip())


# =============================================================================
# Status/Orientation Command
# =============================================================================


def cmd_status(fmt: OutputFormatter, _args: argparse.Namespace) -> int:
    """Show environment status (orientation).

    Returns structured data with needs_setup flag for agentic use.
    """
    fmt.header("RHDH Plugin Environment")

    checks: list[dict[str, Any]] = []
    next_steps: list[str] = []
    needs_setup = False

    # Check overlay repo
    overlay_repo = get_overlay_repo()
    if overlay_repo:
        branch = get_git_branch(overlay_repo)
        status = "uncommitted" if has_uncommitted_changes(overlay_repo) else "clean"
        checks.append(
            {
                "name": "overlay_repo",
                "status": "pass",
                "message": f"{overlay_repo} ({branch}, {status})",
                "path": str(overlay_repo),
                "branch": branch,
                "clean": status == "clean",
            }
        )
        fmt.log_ok(f"overlay repo: {overlay_repo} ({branch}, {status})")
    else:
        checks.append(
            {
                "name": "overlay_repo",
                "status": "fail",
                "message": "not found",
            }
        )
        fmt.log_fail("overlay repo: not found")
        needs_setup = True

    # Check rhdh-local
    local_repo = get_local_repo()
    if local_repo:
        # Check if running (podman)
        running = False
        if check_tool("podman"):
            rc, stdout, _ = run_command(["podman", "ps", "--format", "{{.Names}}"])
            running = rc == 0 and "rhdh" in stdout

        status_msg = "running" if running else "not running"
        check_status = "pass" if running else "warn"
        checks.append(
            {
                "name": "rhdh_local",
                "status": check_status,
                "message": f"{local_repo} ({status_msg})",
                "path": str(local_repo),
                "running": running,
            }
        )
        if running:
            fmt.log_ok(f"rhdh-local: {local_repo} (running)")
        else:
            fmt.log_warn(f"rhdh-local: {local_repo} (not running)")
    else:
        checks.append(
            {
                "name": "rhdh_local",
                "status": "fail",
                "message": "not found",
            }
        )
        fmt.log_fail("rhdh-local: not found")
        needs_setup = True

    # Check factory (optional)
    factory_repo = get_factory_repo()
    if factory_repo:
        checks.append(
            {
                "name": "factory",
                "status": "pass",
                "message": str(factory_repo),
                "path": str(factory_repo),
            }
        )
        fmt.log_ok(f"factory: {factory_repo}")
    else:
        checks.append(
            {
                "name": "factory",
                "status": "info",
                "message": "not configured (optional)",
            }
        )
        fmt.log_info("factory: not configured (optional)")

    # Check tools
    fmt.header("Tools")

    if check_tool("gh"):
        rc, _, _ = run_command(["gh", "auth", "status"])
        if rc == 0:
            checks.append({"name": "gh_cli", "status": "pass", "message": "authenticated"})
            fmt.log_ok("gh CLI: authenticated")
        else:
            checks.append({"name": "gh_cli", "status": "warn", "message": "not authenticated"})
            fmt.log_warn("gh CLI: installed but not authenticated")
            next_steps.append("gh auth login")
    else:
        checks.append({"name": "gh_cli", "status": "fail", "message": "not installed"})
        fmt.log_fail("gh CLI: not installed")
        next_steps.append("Install gh CLI: https://cli.github.com/")

    if check_tool("podman"):
        rc, stdout, _ = run_command(["podman", "--version"])
        version = stdout.strip() if rc == 0 else "unknown"
        checks.append({"name": "podman", "status": "pass", "message": version})
        fmt.log_ok(f"podman: {version}")
    elif check_tool("docker"):
        rc, stdout, _ = run_command(["docker", "--version"])
        version = stdout.strip() if rc == 0 else "unknown"
        checks.append({"name": "docker", "status": "pass", "message": version})
        fmt.log_ok(f"docker: {version}")
    else:
        checks.append({"name": "container_runtime", "status": "warn", "message": "not found"})
        fmt.log_warn("container runtime: not found (needed for rhdh-local)")

    if check_tool("jq"):
        checks.append({"name": "jq", "status": "pass", "message": "installed"})
        fmt.log_ok("jq: installed")
    else:
        checks.append({"name": "jq", "status": "warn", "message": "not installed"})
        fmt.log_warn("jq: not installed (recommended)")

    if check_tool("jira"):
        rc, _, _ = run_command(["jira", "me"])
        if rc == 0:
            checks.append({"name": "jira", "status": "pass", "message": "authenticated"})
            fmt.log_ok("jira: authenticated")
        else:
            checks.append(
                {
                    "name": "jira",
                    "status": "warn",
                    "message": "not authenticated",
                    "reference": "references/jira-reference.md",
                }
            )
            fmt.log_warn("jira: not authenticated (see references/jira-reference.md)")
    else:
        checks.append(
            {
                "name": "jira",
                "status": "info",
                "message": "not installed (optional)",
                "reference": "references/jira-reference.md",
            }
        )
        fmt.log_info("jira: not installed (optional)")

    # Build output based on state
    data: dict[str, Any] = {
        "needs_setup": needs_setup,
        "checks": checks,
    }

    if needs_setup:
        # Just point to doctor - it has all the setup guidance
        next_steps.append("rhdh-plugin doctor")
        fmt.render_banner("Configuration needed. Run:", call_to_action="rhdh-plugin doctor")
    else:
        next_steps.extend(
            [
                "rhdh-plugin workspace list",
                "rhdh-plugin doctor",
            ]
        )

    fmt.success(data, next_steps=next_steps)
    return 0


# =============================================================================
# Doctor Command
# =============================================================================


def cmd_doctor(fmt: OutputFormatter, _args: argparse.Namespace) -> int:
    """Run full environment check."""
    fmt.header("Environment Check")

    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    # Check repos
    overlay_repo = get_overlay_repo()
    if overlay_repo:
        checks.append({"name": "overlay_repo", "status": "pass", "message": str(overlay_repo)})
        fmt.log_ok(f"Overlay repo found: {overlay_repo}")

        # Check it's a git repo
        rc, _, _ = run_command(["git", "rev-parse", "--git-dir"], cwd=overlay_repo)
        if rc == 0:
            checks.append({"name": "overlay_git", "status": "pass", "message": "valid"})
            fmt.log_ok("  Git repository valid")
        else:
            checks.append({"name": "overlay_git", "status": "fail", "message": "invalid"})
            fmt.log_fail("  Not a valid git repository")
            issues.append("Overlay repo is not a git repository")

        # Check remote
        rc, stdout, _ = run_command(["git", "remote", "get-url", "origin"], cwd=overlay_repo)
        if rc == 0:
            remote = stdout.strip()
            if "rhdh-plugin-export-overlays" in remote:
                checks.append({"name": "overlay_remote", "status": "pass", "message": remote})
                fmt.log_ok(f"  Remote: {remote}")
            else:
                checks.append({"name": "overlay_remote", "status": "warn", "message": remote})
                fmt.log_warn(f"  Remote may be incorrect: {remote}")
    else:
        checks.append({"name": "overlay_repo", "status": "fail", "message": "not found"})
        fmt.log_fail("Overlay repo not found")
        issues.append("Configure overlay repo: rhdh-plugin config set overlay /path/to/repo")

    local_repo = get_local_repo()
    if local_repo:
        checks.append({"name": "rhdh_local", "status": "pass", "message": str(local_repo)})
        fmt.log_ok(f"rhdh-local found: {local_repo}")

        # Check compose file exists
        has_compose = (local_repo / "compose.yaml").exists() or (
            local_repo / "docker-compose.yaml"
        ).exists()
        if has_compose:
            checks.append({"name": "compose_file", "status": "pass", "message": "found"})
            fmt.log_ok("  Compose file found")
        else:
            checks.append({"name": "compose_file", "status": "warn", "message": "not found"})
            fmt.log_warn("  No compose file found")
    else:
        checks.append({"name": "rhdh_local", "status": "fail", "message": "not found"})
        fmt.log_fail("rhdh-local not found")
        issues.append("Configure rhdh-local: rhdh-plugin config set local /path/to/repo")

    fmt.header("GitHub CLI")

    if check_tool("gh"):
        checks.append({"name": "gh_installed", "status": "pass", "message": "installed"})
        fmt.log_ok("gh CLI installed")

        rc, _, _ = run_command(["gh", "auth", "status"])
        if rc == 0:
            checks.append({"name": "gh_auth", "status": "pass", "message": "authenticated"})
            fmt.log_ok("  Authenticated")

            # Check repo access
            rc, _, _ = run_command(
                ["gh", "api", "repos/redhat-developer/rhdh-plugin-export-overlays", "--silent"]
            )
            if rc == 0:
                checks.append(
                    {"name": "gh_access", "status": "pass", "message": "can access overlay repo"}
                )
                fmt.log_ok("  Can access overlay repo")
            else:
                checks.append(
                    {"name": "gh_access", "status": "warn", "message": "cannot access overlay repo"}
                )
                fmt.log_warn("  Cannot access overlay repo (may need permissions)")
        else:
            checks.append({"name": "gh_auth", "status": "fail", "message": "not authenticated"})
            fmt.log_fail("  Not authenticated")
            issues.append("Run: gh auth login")
    else:
        checks.append({"name": "gh_installed", "status": "fail", "message": "not installed"})
        fmt.log_fail("gh CLI not installed")
        issues.append("Install gh CLI: https://cli.github.com/")

    fmt.header("Container Runtime")

    if check_tool("podman"):
        checks.append({"name": "podman", "status": "pass", "message": "installed"})
        fmt.log_ok("podman installed")

        rc, _, _ = run_command(["podman", "ps"])
        if rc == 0:
            checks.append({"name": "podman_running", "status": "pass", "message": "running"})
            fmt.log_ok("  Podman running")
        else:
            checks.append({"name": "podman_running", "status": "warn", "message": "not running"})
            fmt.log_warn("  Podman not running or not accessible")
    elif check_tool("docker"):
        checks.append({"name": "docker", "status": "pass", "message": "installed"})
        fmt.log_ok("docker installed")
    else:
        checks.append({"name": "container_runtime", "status": "fail", "message": "not found"})
        fmt.log_fail("No container runtime found")
        issues.append("Install podman or docker for local testing")

    # JIRA CLI (optional)
    fmt.header("JIRA CLI")

    if check_tool("jira"):
        checks.append({"name": "jira_installed", "status": "pass", "message": "installed"})
        fmt.log_ok("jira CLI installed")

        rc, _, _ = run_command(["jira", "me"])
        if rc == 0:
            checks.append({"name": "jira_auth", "status": "pass", "message": "authenticated"})
            fmt.log_ok("  Authenticated")
        else:
            checks.append(
                {
                    "name": "jira_auth",
                    "status": "warn",
                    "message": "not authenticated",
                    "reference": "references/jira-reference.md",
                }
            )
            fmt.log_warn("  Not authenticated (see references/jira-reference.md)")
    else:
        checks.append(
            {
                "name": "jira_installed",
                "status": "info",
                "message": "not installed (optional)",
                "reference": "references/jira-reference.md",
            }
        )
        fmt.log_info("jira: not installed (optional, see references/jira-reference.md)")

    # Summary
    fmt.header("Summary")

    all_passed = len(issues) == 0
    next_steps = []

    needs_setup = not all_passed

    if all_passed:
        fmt.log_ok("All checks passed!")
        next_steps = ["rhdh-plugin workspace list", "/onboard-plugin"]
        data: dict[str, Any] = {
            "needs_setup": needs_setup,
            "all_passed": all_passed,
            "checks": checks,
            "issues": issues,
        }
    else:
        fmt.log_warn(f"{len(issues)} issue(s) found")
        next_steps = ["Read workflows/doctor.md for setup instructions"]
        data = {
            "needs_setup": needs_setup,
            "all_passed": all_passed,
            "checks": checks,
            "issues": issues,
            "workflow": "workflows/doctor.md",
            "agent_instruction": "Read the workflow file for detailed setup steps",
        }

    fmt.success(data, next_steps=next_steps)
    return 0 if all_passed else 1


# =============================================================================
# Config Commands
# =============================================================================


def cmd_config_init(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Initialize configuration file."""
    from .config import run_config

    force = getattr(args, "force", False)
    global_ = getattr(args, "global_", False)
    scope = "user" if global_ else "project"

    fmt.header(f"Initializing {scope.title()} Configuration")

    success, data, next_steps = run_config("init", force=force, global_=global_)

    if success and isinstance(data, dict):
        fmt.log_ok(f"Created: {data.get('created', '')}")
        config = data.get("config", {})
        repos = config.get("repos", {})
        if repos.get("overlay"):
            fmt.log_ok(f"Auto-detected overlay: {repos['overlay']}")
        else:
            fmt.log_info(
                "overlay: not found (configure with: rhdh-plugin config set repos.overlay /path)"
            )
        if repos.get("local"):
            fmt.log_ok(f"Auto-detected local: {repos['local']}")
        else:
            fmt.log_info(
                "local: not found (configure with: rhdh-plugin config set repos.local /path)"
            )
        fmt.success(data, next_steps=next_steps)
        return 0
    else:
        fmt.error("CONFIG_INIT_FAILED", str(data), next_steps=next_steps)
        return 1


def cmd_config_show(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Show current configuration."""
    from .config import run_config

    global_ = getattr(args, "global_", False)

    fmt.header("Configuration")

    success, data, next_steps = run_config("show", global_=global_)

    if success and isinstance(data, dict):
        # Human-readable output
        fmt.log_info(f"User config: {data.get('user_config_path', '')}")
        fmt.log_info(f"Project config: {data.get('project_config_path', '')}")

        fmt.header("Resolved Paths")
        resolved = data.get("resolved", {})
        if resolved.get("overlay"):
            fmt.log_ok(f"overlay: {resolved['overlay']}")
        else:
            fmt.log_fail("overlay: not found")
        if resolved.get("local"):
            fmt.log_ok(f"local: {resolved['local']}")
        else:
            fmt.log_fail("local: not found")
        if resolved.get("factory"):
            fmt.log_ok(f"factory: {resolved['factory']}")
        else:
            fmt.log_info("factory: not configured")

        fmt.success(data, next_steps=next_steps)
        return 0
    else:
        fmt.error("CONFIG_SHOW_FAILED", str(data), next_steps=next_steps)
        return 1


def cmd_config_keys(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """List all config keys."""
    from .config import run_config

    global_ = getattr(args, "global_", False)

    success, data, next_steps = run_config("keys", global_=global_)

    if success and isinstance(data, dict):
        keys = data.get("keys", [])
        scope = data.get("scope", "merged")
        fmt.header(f"Config Keys ({scope})")
        for key in keys:
            fmt.log_info(key)
        fmt.success(data, next_steps=next_steps)
        return 0
    else:
        fmt.error("CONFIG_KEYS_FAILED", str(data), next_steps=next_steps)
        return 1


def cmd_config_get(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Get a config value."""
    from .config import run_config

    key = getattr(args, "key", None)

    success, data, next_steps = run_config("get", key=key)

    if success and isinstance(data, dict):
        fmt.log_ok(f"{data.get('key')}: {data.get('value')}")
        fmt.success(data, next_steps=next_steps)
        return 0
    else:
        fmt.error("CONFIG_GET_FAILED", str(data), next_steps=next_steps)
        return 1


def cmd_config_set(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Set a config value."""
    from .config import run_config

    key = getattr(args, "key", None)
    value = getattr(args, "value", None)
    global_ = getattr(args, "global_", False)

    success, data, next_steps = run_config("set", key=key, value=value, global_=global_)

    if success and isinstance(data, dict):
        scope = data.get("scope", "project")
        fmt.log_ok(f"Set {data.get('key')} = {data.get('value')} ({scope} config)")
        fmt.success(data, next_steps=next_steps)
        return 0
    else:
        fmt.error("CONFIG_SET_FAILED", str(data), next_steps=next_steps)
        return 1


# =============================================================================
# Setup Commands
# =============================================================================


def cmd_setup_submodule_list(fmt: OutputFormatter, _args: argparse.Namespace) -> int:
    """List available repositories for submodule setup."""
    fmt.header("Available Repositories")

    repos = list_submodule_repos()
    github_username = get_github_username()

    # Check if any repos need username
    needs_username = any(r.get("needs_username") for r in repos)

    from .formatters import BLUE, GREEN, NC, RED, YELLOW

    # Show GitHub username status
    if github_username:
        fmt.log_info(f"GitHub user: {BLUE}{github_username}{NC}")
    elif needs_username:
        fmt.log_warn("GitHub user: not detected (needed for fork repos)")
        fmt.log_info("Run: gh auth login")

    def format_repo(repo: dict) -> str:
        status = repo["status"]
        required = " (required)" if repo["required"] else " (optional)"

        if status == "submodule":
            color = GREEN
            status_text = "✓ submodule"
        elif status == "configured":
            color = GREEN
            status_text = "✓ configured"
        elif status == "directory_exists":
            color = YELLOW
            status_text = "⚠ directory exists"
        else:
            color = RED if repo["required"] else YELLOW
            status_text = "✗ not configured"

        lines = [f"{color}{repo['name']:<35}{NC} {status_text}{required}"]
        lines.append(f"    {repo['description']}")
        if repo["path"]:
            lines.append(f"    Path: {repo['path']}")
        if repo.get("has_fork"):
            if repo.get("origin"):
                lines.append(f"    Fork: {repo['origin']}")
            else:
                lines.append(f"    {YELLOW}Fork: requires GitHub username{NC}")
        return "\n".join(lines)

    fmt.render_list(repos, format_repo)

    data = {
        "github_username": github_username,
        "repos": repos,
    }

    # Determine next steps based on status
    unconfigured_required = [r for r in repos if r["status"] == "not_configured" and r["required"]]
    if needs_username and not github_username:
        next_steps = [
            "gh auth login",
            "rhdh-plugin config set github.username <your-username>",
        ]
    elif unconfigured_required:
        next_steps = [
            "rhdh-plugin setup submodule add --all",
            f"rhdh-plugin setup submodule add {unconfigured_required[0]['name']}",
        ]
    else:
        next_steps = ["rhdh-plugin", "rhdh-plugin workspace list"]

    fmt.success(data, next_steps=next_steps)
    return 0


def cmd_setup_submodule_add(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Add repository as submodule."""
    add_all = getattr(args, "all", False)
    name = getattr(args, "name", None)
    dry_run = getattr(args, "dry_run", False)

    # Detect GitHub username (needed for repos with forks)
    github_username = get_github_username()
    if github_username:
        fmt.log_info(f"GitHub user: {github_username}")
        # Save to config if not already saved
        save_github_username(github_username)

    if add_all:
        # Add all required repos
        fmt.header("Setting up all required repositories")

        results = []
        all_success = True

        for repo_name, repo_info in SUBMODULE_REPOS.items():
            if not repo_info["required"]:
                continue

            fmt.log_info(f"Setting up: {repo_name}")
            success, data, _ = setup_submodule(
                repo_name, dry_run=dry_run, github_username=github_username
            )

            if success:
                if isinstance(data, dict):
                    status = data.get("status", "unknown")
                    if status == "already_configured":
                        fmt.log_ok("  Already configured")
                    elif dry_run:
                        fmt.log_info("  Would create submodule")
                    else:
                        fmt.log_ok(f"  Created at: {data.get('path')}")
            else:
                fmt.log_fail(f"  Failed: {data}")
                all_success = False

            results.append({"name": repo_name, "success": success, "data": data})

        output_data: dict[str, Any] = {
            "github_username": github_username,
            "results": results,
            "all_success": all_success,
        }

        if all_success:
            fmt.success(output_data, next_steps=["rhdh-plugin", "rhdh-plugin doctor"])
            return 0
        else:
            fmt.success(output_data, next_steps=["rhdh-plugin setup submodule list"])
            return 1

    elif name:
        # Add single repo
        fmt.header(f"Setting up: {name}")

        success, data, next_steps = setup_submodule(
            name, dry_run=dry_run, github_username=github_username
        )

        if success:
            if isinstance(data, dict):
                status = data.get("status", "unknown")
                if status == "already_configured":
                    fmt.log_ok("Already configured as submodule")
                elif dry_run:
                    for action in data.get("actions", []):
                        fmt.log_info(action)
                else:
                    fmt.log_ok(f"Created at: {data.get('path')}")
                    if data.get("upstream"):
                        fmt.log_ok(f"Upstream: {data.get('upstream')}")
            fmt.success(data, next_steps=next_steps)
            return 0
        else:
            fmt.error("SUBMODULE_SETUP_FAILED", str(data), next_steps=next_steps)
            return 1

    else:
        fmt.error(
            "MISSING_ARGUMENT",
            "Specify repository name or use --all",
            next_steps=[
                "rhdh-plugin setup submodule list",
                "rhdh-plugin setup submodule add --all",
            ],
        )
        return 1


# =============================================================================
# Workspace Commands
# =============================================================================


def cmd_workspace_list(fmt: OutputFormatter, _args: argparse.Namespace) -> int:
    """List plugin workspaces."""
    overlay_repo, workspaces = list_workspaces()

    if overlay_repo is None:
        fmt.error(
            "OVERLAY_NOT_FOUND",
            "Overlay repo not found",
            next_steps=["rhdh-plugin config init", "rhdh-plugin doctor"],
        )
        return 1

    fmt.header("Plugin Workspaces")
    fmt.log_info(f"Location: {overlay_repo}/workspaces/")

    items = []
    for ws in workspaces:
        items.append(
            {
                "name": ws.name,
                "detail": ws.repo_ref or "(no source.json)",
                "repo": ws.repo,
                "repo_ref": ws.repo_ref,
            }
        )

    # Render items in human mode
    from .formatters import BLUE, NC

    fmt.render_list(
        items,
        lambda i: f"{BLUE}{i['name']:<30}{NC} {i['detail']}",
        summary=f"Total: {len(items)} workspaces",
    )

    data = {
        "overlay_repo": str(overlay_repo),
        "count": len(workspaces),
        "items": items,
    }

    fmt.success(data, next_steps=["rhdh-plugin workspace status <name>", "/onboard-plugin"])
    return 0


def cmd_workspace_status(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Show workspace details."""
    found, ws, error = get_workspace(args.name)

    if not found:
        fmt.error(
            "WORKSPACE_NOT_FOUND",
            error,
            next_steps=["rhdh-plugin workspace list"],
        )
        return 1

    assert ws is not None  # Type narrowing

    fmt.header(f"Workspace: {ws.name}")

    # Files check
    files = []
    files.append({"name": "source.json", "exists": ws.has_source_json, "required": True})
    files.append({"name": "plugins-list.yaml", "exists": ws.has_plugins_list, "required": True})
    files.append({"name": "backstage.json", "exists": ws.has_backstage_json, "required": False})

    for f in files:
        if f["exists"]:
            fmt.log_ok(f["name"])
        elif f["required"]:
            fmt.log_fail(f"{f['name']} (required)")
        else:
            fmt.log_info(f"{f['name']} (optional)")

    data = {
        "name": ws.name,
        "path": str(ws.path),
        "files": files,
        "source": {
            "repo": ws.repo,
            "repo_ref": ws.repo_ref,
            "backstage_version": ws.repo_backstage_version,
        }
        if ws.has_source_json
        else None,
        "metadata_files": ws.metadata_files,
    }

    fmt.success(data, next_steps=[f"cd {ws.path}", "rhdh-plugin workspace list"])
    return 0


# =============================================================================
# Worklog Commands
# =============================================================================


def cmd_log_add(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Add a worklog entry."""
    message = args.message
    tags = args.tag if args.tag else None

    entry = worklog_add_entry(message, tags)

    fmt.log_ok(f"Added: {format_entry_human(entry)}")
    fmt.success(
        {"entry": entry},
        next_steps=["rhdh-plugin log show", "rhdh-plugin log search <query>"],
    )
    return 0


def cmd_log_show(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Show recent worklog entries."""
    limit = args.limit
    since = args.since

    entries = read_entries(limit=limit, since=since)

    if not entries:
        fmt.log_info("No entries found")
        fmt.success(
            {"count": 0, "entries": []},
            next_steps=["rhdh-plugin log add <message>"],
        )
        return 0

    fmt.header("Worklog")

    fmt.render_list(
        entries,
        lambda e: format_entry_human(e),
        summary=f"Showing {len(entries)} entries",
    )

    fmt.success(
        {"count": len(entries), "entries": entries},
        next_steps=["rhdh-plugin log add <message>", "rhdh-plugin log search <query>"],
    )
    return 0


def cmd_log_search(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Search worklog entries."""
    query = args.query
    limit = args.limit

    matches = search_entries(query, limit=limit)

    if not matches:
        fmt.log_info(f"No entries matching '{query}'")
        fmt.success(
            {"query": query, "count": 0, "entries": []},
            next_steps=["rhdh-plugin log show", "rhdh-plugin log add <message>"],
        )
        return 0

    fmt.header(f"Search: {query}")

    fmt.render_list(
        matches,
        lambda e: format_entry_human(e),
        summary=f"Found {len(matches)} matches",
    )

    fmt.success(
        {"query": query, "count": len(matches), "entries": matches},
        next_steps=["rhdh-plugin log show", "rhdh-plugin log add <message>"],
    )
    return 0


# =============================================================================
# Todo Commands
# =============================================================================


def cmd_todo_add(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Add a new todo item."""
    title = args.title
    context = args.context

    todo = add_todo(title, context)

    fmt.log_ok(f"Added: {todo.title}")
    fmt.log_info(f"Slug: {todo.slug}")
    fmt.success(
        {
            "slug": todo.slug,
            "title": todo.title,
            "created": todo.created,
            "context": todo.context,
        },
        next_steps=["rhdh-plugin todo list", f"rhdh-plugin todo note {todo.slug} <text>"],
    )
    return 0


def cmd_todo_list(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """List todo items."""
    include_done = not args.pending

    todos = list_todos(include_done=include_done)

    if not todos:
        fmt.log_info("No todos found")
        fmt.success(
            {"count": 0, "items": []},
            next_steps=["rhdh-plugin todo add <title>"],
        )
        return 0

    fmt.header("Todos")

    from .formatters import GREEN, NC, YELLOW

    items = []
    for todo in todos:
        items.append(
            {
                "slug": todo.slug,
                "title": todo.title,
                "done": todo.done,
                "created": todo.created,
                "context": todo.context,
            }
        )

    def format_todo(item: dict) -> str:
        status = "[x]" if item["done"] else "[ ]"
        color = GREEN if item["done"] else YELLOW
        context_str = f" ({item['context']})" if item["context"] else ""
        return f"{color}{status}{NC} {item['title']}{context_str}\n      slug: {item['slug']}"

    pending = sum(1 for t in todos if not t.done)
    done = sum(1 for t in todos if t.done)
    fmt.render_list(items, format_todo, summary=f"{pending} pending, {done} done")

    fmt.success(
        {"count": len(todos), "items": items},
        next_steps=["rhdh-plugin todo add <title>", "rhdh-plugin todo done <slug>"],
    )
    return 0


def cmd_todo_done(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Mark a todo as done."""
    slug = args.slug

    todo = mark_done(slug)

    if not todo:
        fmt.error(
            "TODO_NOT_FOUND",
            f"No todo matching '{slug}'",
            next_steps=["rhdh-plugin todo list"],
        )
        return 1

    if todo.completed:
        fmt.log_ok(f"Marked done: {todo.title}")
    else:
        fmt.log_info(f"Already done: {todo.title}")

    fmt.success(
        {"slug": todo.slug, "title": todo.title, "completed": todo.completed},
        next_steps=["rhdh-plugin todo list"],
    )
    return 0


def cmd_todo_note(fmt: OutputFormatter, args: argparse.Namespace) -> int:
    """Add a note to a todo."""
    slug = args.slug
    note = args.note

    todo = todo_add_note(slug, note)

    if not todo:
        fmt.error(
            "TODO_NOT_FOUND",
            f"No todo matching '{slug}'",
            next_steps=["rhdh-plugin todo list"],
        )
        return 1

    fmt.log_ok(f"Added note to: {todo.title}")
    fmt.success(
        {"slug": todo.slug, "title": todo.title, "note": note},
        next_steps=["rhdh-plugin todo show", "rhdh-plugin todo list"],
    )
    return 0


def cmd_todo_show(fmt: OutputFormatter, _args: argparse.Namespace) -> int:
    """Show the raw TODO.md file."""
    content = todo_show_raw()
    file_path = get_todo_file_path()

    fmt.render_raw(content)

    # In JSON mode, also output structured data
    if not fmt.is_human:
        fmt.success(
            {"file": str(file_path), "content": content},
            next_steps=["rhdh-plugin todo list", "rhdh-plugin todo add <title>"],
        )

    return 0


# =============================================================================
# CLI Setup
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="rhdh-plugin",
        description="CLI helper for RHDH plugin management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
OUTPUT FORMAT:
    Auto-detected: JSON when piped (for Claude), human-readable in terminal.
    Override with --json or --human flags.

ENVIRONMENT VARIABLES:
    RHDH_OVERLAY_REPO   Path to rhdh-plugin-export-overlays
    RHDH_LOCAL_REPO     Path to rhdh-local
    RHDH_FACTORY_REPO   Path to rhdh-dynamic-plugin-factory

EXAMPLES:
    rhdh-plugin                           # Show status (orientation)
    rhdh-plugin doctor                    # Check setup
    rhdh-plugin config init               # Create config
    rhdh-plugin workspace list            # List workspaces
    rhdh-plugin --json workspace list     # Force JSON output

    # Worklog
    rhdh-plugin log add "Started onboarding aws-appsync" --tag onboard
    rhdh-plugin log show --limit 10
    rhdh-plugin log search "aws"

    # Todos
    rhdh-plugin todo add "Check license with legal" --context aws-appsync
    rhdh-plugin todo list
    rhdh-plugin todo done check-license
    rhdh-plugin todo note check-license "Sent email to legal@"
    rhdh-plugin todo show
""",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Output format flags
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "--json",
        action="store_true",
        help="Force JSON output (default when piped)",
    )
    format_group.add_argument(
        "--human",
        action="store_true",
        help="Force human-readable output (default in terminal)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include debug information",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # Status (also default when no command)
    status_parser = subparsers.add_parser("status", help="Show environment status")
    status_parser.set_defaults(func=cmd_status)

    # Doctor
    doctor_parser = subparsers.add_parser("doctor", help="Full environment check")
    doctor_parser.set_defaults(func=cmd_doctor)

    # Config
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_command", metavar="SUBCOMMAND")

    # config init
    config_init_parser = config_subparsers.add_parser("init", help="Initialize configuration file")
    config_init_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing config"
    )
    config_init_parser.add_argument(
        "--global",
        "-g",
        dest="global_",
        action="store_true",
        help="Initialize user config instead of project",
    )
    config_init_parser.set_defaults(func=cmd_config_init)

    # config show
    config_show_parser = config_subparsers.add_parser("show", help="Show current configuration")
    config_show_parser.add_argument(
        "--global", "-g", dest="global_", action="store_true", help="Show only user config"
    )
    config_show_parser.set_defaults(func=cmd_config_show)

    # config keys
    config_keys_parser = config_subparsers.add_parser("keys", help="List all config keys")
    config_keys_parser.add_argument(
        "--global", "-g", dest="global_", action="store_true", help="Show only user config keys"
    )
    config_keys_parser.set_defaults(func=cmd_config_keys)

    # config get
    config_get_parser = config_subparsers.add_parser("get", help="Get a config value")
    config_get_parser.add_argument("key", help="Key in dot notation (e.g., repos.overlay)")
    config_get_parser.set_defaults(func=cmd_config_get)

    # config set
    config_set_parser = config_subparsers.add_parser("set", help="Set config value")
    config_set_parser.add_argument("key", help="Key in dot notation (e.g., repos.overlay)")
    config_set_parser.add_argument("value", help="Value to set (JSON parsed if valid)")
    config_set_parser.add_argument(
        "--global",
        "-g",
        dest="global_",
        action="store_true",
        help="Set in user config instead of project",
    )
    config_set_parser.set_defaults(func=cmd_config_set)

    # Setup
    setup_parser = subparsers.add_parser("setup", help="Environment setup commands")
    setup_subparsers = setup_parser.add_subparsers(dest="setup_command", metavar="SUBCOMMAND")

    # setup submodule
    submodule_parser = setup_subparsers.add_parser("submodule", help="Manage repository submodules")
    submodule_subparsers = submodule_parser.add_subparsers(
        dest="submodule_command", metavar="SUBCOMMAND"
    )

    # setup submodule list
    submodule_list_parser = submodule_subparsers.add_parser(
        "list", help="List available repositories"
    )
    submodule_list_parser.set_defaults(func=cmd_setup_submodule_list)

    # setup submodule add
    submodule_add_parser = submodule_subparsers.add_parser(
        "add", help="Add repository as submodule"
    )
    submodule_add_parser.add_argument(
        "name", nargs="?", help="Repository name (e.g., rhdh-plugin-export-overlays)"
    )
    submodule_add_parser.add_argument(
        "--all", "-a", action="store_true", help="Add all required repositories"
    )
    submodule_add_parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without making changes",
    )
    submodule_add_parser.set_defaults(func=cmd_setup_submodule_add)

    # Workspace
    workspace_parser = subparsers.add_parser("workspace", help="Workspace operations")
    workspace_subparsers = workspace_parser.add_subparsers(
        dest="workspace_command", metavar="SUBCOMMAND"
    )

    workspace_list_parser = workspace_subparsers.add_parser("list", help="List plugin workspaces")
    workspace_list_parser.set_defaults(func=cmd_workspace_list)

    workspace_status_parser = workspace_subparsers.add_parser(
        "status", help="Show workspace details"
    )
    workspace_status_parser.add_argument("name", help="Workspace name")
    workspace_status_parser.set_defaults(func=cmd_workspace_status)

    # Log (worklog)
    log_parser = subparsers.add_parser("log", help="Worklog operations")
    log_subparsers = log_parser.add_subparsers(dest="log_command", metavar="SUBCOMMAND")

    log_add_parser = log_subparsers.add_parser("add", help="Add a worklog entry")
    log_add_parser.add_argument("message", help="Log message")
    log_add_parser.add_argument("--tag", "-t", action="append", help="Tag (repeatable)")
    log_add_parser.set_defaults(func=cmd_log_add)

    log_show_parser = log_subparsers.add_parser("show", help="Show recent entries")
    log_show_parser.add_argument(
        "--limit", "-n", type=int, default=20, help="Number of entries (default: 20)"
    )
    log_show_parser.add_argument("--since", "-s", help="Show entries since date (YYYY-MM-DD)")
    log_show_parser.set_defaults(func=cmd_log_show)

    log_search_parser = log_subparsers.add_parser("search", help="Search entries")
    log_search_parser.add_argument("query", help="Search query")
    log_search_parser.add_argument("--limit", "-n", type=int, help="Max results")
    log_search_parser.set_defaults(func=cmd_log_search)

    # Todo
    todo_parser = subparsers.add_parser("todo", help="Todo operations")
    todo_subparsers = todo_parser.add_subparsers(dest="todo_command", metavar="SUBCOMMAND")

    todo_add_parser = todo_subparsers.add_parser("add", help="Add a new todo")
    todo_add_parser.add_argument("title", help="Todo title")
    todo_add_parser.add_argument("--context", "-c", help="Context (workspace, PR, etc.)")
    todo_add_parser.set_defaults(func=cmd_todo_add)

    todo_list_parser = todo_subparsers.add_parser("list", help="List todos")
    todo_list_parser.add_argument(
        "--pending", "-p", action="store_true", help="Show only pending todos"
    )
    todo_list_parser.set_defaults(func=cmd_todo_list)

    todo_done_parser = todo_subparsers.add_parser("done", help="Mark todo as done")
    todo_done_parser.add_argument("slug", help="Todo slug (or partial match)")
    todo_done_parser.set_defaults(func=cmd_todo_done)

    todo_note_parser = todo_subparsers.add_parser("note", help="Add note to todo")
    todo_note_parser.add_argument("slug", help="Todo slug")
    todo_note_parser.add_argument("note", help="Note text")
    todo_note_parser.set_defaults(func=cmd_todo_note)

    todo_show_parser = todo_subparsers.add_parser("show", help="Show raw TODO.md")
    todo_show_parser.set_defaults(func=cmd_todo_show)

    # Help command (for compatibility with bash version)
    help_parser = subparsers.add_parser("help", help="Show help")
    help_parser.set_defaults(func=lambda f, a: parser.print_help() or 0)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0=success, 1=fixable, 2=critical)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Determine output mode
    if args.json:
        mode = "json"
    elif args.human:
        mode = "human"
    else:
        mode = "auto"  # Will auto-detect based on TTY

    # Create formatter
    fmt = OutputFormatter(mode=mode, verbose=getattr(args, "verbose", False))

    # No command = show status (orientation)
    if args.command is None:
        return cmd_status(fmt, args)

    # Config without subcommand
    if args.command == "config" and args.config_command is None:
        fmt.error(
            "MISSING_SUBCOMMAND",
            "Config subcommand required",
            next_steps=[
                "rhdh-plugin config init",
                "rhdh-plugin config show",
                "rhdh-plugin config set <key> <path>",
            ],
        )
        return 1

    # Workspace without subcommand
    if args.command == "workspace" and args.workspace_command is None:
        fmt.error(
            "MISSING_SUBCOMMAND",
            "Workspace subcommand required",
            next_steps=["rhdh-plugin workspace list", "rhdh-plugin workspace status <name>"],
        )
        return 1

    # Log without subcommand
    if args.command == "log" and args.log_command is None:
        fmt.error(
            "MISSING_SUBCOMMAND",
            "Log subcommand required",
            next_steps=[
                "rhdh-plugin log add <message>",
                "rhdh-plugin log show",
                "rhdh-plugin log search <query>",
            ],
        )
        return 1

    # Todo without subcommand
    if args.command == "todo" and args.todo_command is None:
        fmt.error(
            "MISSING_SUBCOMMAND",
            "Todo subcommand required",
            next_steps=[
                "rhdh-plugin todo list",
                "rhdh-plugin todo add <title>",
                "rhdh-plugin todo show",
            ],
        )
        return 1

    # Setup without subcommand
    if args.command == "setup" and getattr(args, "setup_command", None) is None:
        fmt.error(
            "MISSING_SUBCOMMAND",
            "Setup subcommand required",
            next_steps=[
                "rhdh-plugin setup submodule list",
                "rhdh-plugin setup submodule add --all",
            ],
        )
        return 1

    # Setup submodule without subcommand
    if (
        args.command == "setup"
        and getattr(args, "setup_command", None) == "submodule"
        and getattr(args, "submodule_command", None) is None
    ):
        fmt.error(
            "MISSING_SUBCOMMAND",
            "Submodule subcommand required",
            next_steps=[
                "rhdh-plugin setup submodule list",
                "rhdh-plugin setup submodule add --all",
                "rhdh-plugin setup submodule add <name>",
            ],
        )
        return 1

    # Run the command
    if hasattr(args, "func"):
        return args.func(fmt, args)

    # Fallback
    parser.print_help()
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
