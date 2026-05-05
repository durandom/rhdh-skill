#!/usr/bin/env python3
"""Scaffold a Backstage app and frontend dynamic plugin for RHDH.

Automates Steps 2 + 4 of the create-frontend-plugin workflow:
  Step 2: Create Backstage app with version-matched create-app
  Step 4: Generate frontend plugin via `yarn new`

Optionally installs RHDH theme package (Step 3).

Uses only Python stdlib per project ADR-0002.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# RHDH version → @backstage/create-app version mapping
# Source: skills/rhdh/references/versions.md
# ---------------------------------------------------------------------------
VERSION_MAP: dict[str, str] = {
    "next": "0.7.6",
    "1.9": "0.7.6",
    "1.8": "0.7.3",
    "1.7": "0.6.2",
    "1.6": "0.5.25",
}

RHDH_THEME_PACKAGE = "@red-hat-developer-hub/backstage-plugin-theme"

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2

# ANSI colors (disabled when not a TTY or --json)
_is_tty = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _is_tty:
        return f"{code}{text}\033[0m"
    return text


def green(t: str) -> str:
    return _c("\033[0;32m", t)


def red(t: str) -> str:
    return _c("\033[0;31m", t)


def yellow(t: str) -> str:
    return _c("\033[1;33m", t)


def blue(t: str) -> str:
    return _c("\033[0;34m", t)


def bold(t: str) -> str:
    return _c("\033[1m", t)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def log(msg: str) -> None:
    """Print to stderr so it doesn't interfere with --json on stdout."""
    print(msg, file=sys.stderr)


def log_step(msg: str) -> None:
    log(f"  {blue('→')} {msg}")


def log_ok(msg: str) -> None:
    log(f"  {green('✓')} {msg}")


def log_fail(msg: str) -> None:
    log(f"  {red('✗')} {msg}")


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    stdin_text: str | None = None,
    use_json: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess, logging the command. Raises on failure."""
    display = " ".join(cmd)
    if stdin_text:
        display = f"echo {stdin_text!r} | {display}"
    log_step(f"Running: {display}")

    # On Windows, shell=True is needed for npx/yarn from PATH
    use_shell = sys.platform == "win32"

    result = subprocess.run(
        cmd,
        cwd=cwd,
        input=stdin_text,
        capture_output=False,
        text=True,
        shell=use_shell,
    )
    if result.returncode != 0:
        log_fail(f"Command failed (exit {result.returncode}): {display}")
        if not use_json:
            sys.exit(EXIT_FAILURE)
        else:
            # Let caller handle structured error
            raise subprocess.CalledProcessError(result.returncode, cmd)
    log_ok(f"Done: {cmd[0]}")
    return result


def resolve_create_app_version(rhdh_version: str) -> str | None:
    """Look up the create-app version for an RHDH version."""
    return VERSION_MAP.get(rhdh_version)


def check_plugin_exists(app_path: Path, plugin_id: str) -> bool:
    """Check if plugin directory already exists (idempotency)."""
    return (app_path / "plugins" / plugin_id).is_dir()


def check_app_exists(app_path: Path) -> bool:
    """Check if a Backstage app already exists at path."""
    return (app_path / "package.json").is_file() and (app_path / "packages" / "app").is_dir()


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def scaffold(args: argparse.Namespace) -> dict:
    """Run the scaffold workflow. Returns a result dict."""
    rhdh_version: str = args.rhdh_version
    plugin_id: str = args.plugin_id
    app_path = Path(args.path).resolve()
    with_theme: bool = args.with_theme
    use_json: bool = args.json

    # Resolve create-app version
    if args.create_app_version:
        create_app_version = args.create_app_version
    else:
        create_app_version = resolve_create_app_version(rhdh_version)
        if create_app_version is None:
            known = ", ".join(sorted(VERSION_MAP.keys()))
            msg = (
                f"Unknown RHDH version '{rhdh_version}'. "
                f"Known versions: {known}. "
                f"Use --create-app-version to override."
            )
            if use_json:
                return {
                    "success": False,
                    "error": {"code": "UNKNOWN_RHDH_VERSION", "message": msg},
                }
            log_fail(msg)
            sys.exit(EXIT_USAGE)

    result: dict = {
        "success": True,
        "rhdh_version": rhdh_version,
        "create_app_version": create_app_version,
        "plugin_id": plugin_id,
        "app_path": str(app_path),
        "with_theme": with_theme,
        "steps_completed": [],
    }

    log(bold(f"\nScaffolding frontend plugin '{plugin_id}' for RHDH {rhdh_version}"))
    log(f"  App path:          {app_path}")
    log(f"  create-app version: {create_app_version}")
    log(f"  Theme:             {'yes' if with_theme else 'no'}\n")

    # ------------------------------------------------------------------
    # Step 2: Create Backstage app (idempotent)
    # ------------------------------------------------------------------
    if check_app_exists(app_path):
        log_ok("Backstage app already exists — skipping create-app")
        result["steps_completed"].append("create-app (skipped, already exists)")
    else:
        log(bold("Step 2: Creating Backstage application"))
        app_path.mkdir(parents=True, exist_ok=True)
        try:
            run(
                [
                    "npx",
                    f"@backstage/create-app@{create_app_version}",
                    "--path",
                    str(app_path),
                ],
                stdin_text="backstage\n",
                use_json=use_json,
            )
        except subprocess.CalledProcessError:
            result["success"] = False
            result["error"] = {
                "code": "CREATE_APP_FAILED",
                "message": "npx @backstage/create-app failed",
            }
            return result
        result["steps_completed"].append("create-app")

    # yarn install
    if not (app_path / "node_modules").is_dir():
        log(bold("Installing dependencies"))
        try:
            run(["yarn", "install"], cwd=app_path, use_json=use_json)
        except subprocess.CalledProcessError:
            result["success"] = False
            result["error"] = {
                "code": "YARN_INSTALL_FAILED",
                "message": "yarn install failed",
            }
            return result
        result["steps_completed"].append("yarn install")
    else:
        log_ok("node_modules exists — skipping yarn install")
        result["steps_completed"].append("yarn install (skipped, already exists)")

    # ------------------------------------------------------------------
    # Step 3 (optional): Install RHDH theme
    # ------------------------------------------------------------------
    if with_theme:
        log(bold("Step 3: Installing RHDH theme package"))
        try:
            run(
                ["yarn", "workspace", "app", "add", RHDH_THEME_PACKAGE],
                cwd=app_path,
                use_json=use_json,
            )
        except subprocess.CalledProcessError:
            result["success"] = False
            result["error"] = {
                "code": "THEME_INSTALL_FAILED",
                "message": f"Failed to install {RHDH_THEME_PACKAGE}",
            }
            return result
        result["steps_completed"].append("install-theme")

    # ------------------------------------------------------------------
    # Step 4: Create frontend plugin (idempotent)
    # ------------------------------------------------------------------
    if check_plugin_exists(app_path, plugin_id):
        log_ok(f"Plugin '{plugin_id}' already exists — skipping yarn new")
        result["steps_completed"].append("yarn new (skipped, already exists)")
    else:
        log(bold("Step 4: Creating frontend plugin"))
        try:
            run(
                [
                    "yarn",
                    "new",
                    "--select",
                    "frontend-plugin",
                    "--option",
                    f"id={plugin_id}",
                ],
                cwd=app_path,
                use_json=use_json,
            )
        except subprocess.CalledProcessError:
            result["success"] = False
            result["error"] = {
                "code": "YARN_NEW_FAILED",
                "message": "yarn new --select frontend-plugin failed",
            }
            return result
        result["steps_completed"].append("yarn new")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    plugin_path = app_path / "plugins" / plugin_id
    result["plugin_path"] = str(plugin_path)

    if not use_json:
        log(bold("\n✅ Scaffold complete!\n"))
        log(f"  Plugin location: {plugin_path}")
        log(f"  RHDH version:    {rhdh_version}")
        log(f"  Steps completed: {', '.join(result['steps_completed'])}")
        log(bold("\nNext steps:"))
        log(f"  1. cd {app_path}")
        log(f"  2. Implement components in plugins/{plugin_id}/src/")
        if with_theme:
            log(f"  3. Configure theme in plugins/{plugin_id}/dev/index.tsx (see SKILL.md Step 5)")
        log(f"  {'4' if with_theme else '3'}. yarn build")
        log(f"  {'5' if with_theme else '4'}. npx @red-hat-developer-hub/cli@latest plugin export")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scaffold",
        description=(
            "Scaffold a Backstage app and frontend dynamic plugin for RHDH.\n\n"
            "Automates Steps 2+4 of the create-frontend-plugin skill:\n"
            "  Step 2: Create Backstage app with the correct create-app version\n"
            "  Step 4: Generate a new frontend plugin via yarn new\n\n"
            "Optionally installs the RHDH theme package (Step 3)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  %(prog)s --rhdh-version 1.9 --plugin-id my-plugin\n"
            "  %(prog)s --rhdh-version 1.8 --plugin-id my-card --with-theme\n"
            "  %(prog)s --rhdh-version 1.7 --plugin-id foo --path ./my-app --json\n"
            "  %(prog)s --rhdh-version next --plugin-id bar "
            "--create-app-version 0.7.6\n"
        ),
    )

    parser.add_argument(
        "--rhdh-version",
        required=True,
        metavar="VERSION",
        help=(f"Target RHDH version. Known: {', '.join(sorted(VERSION_MAP.keys()))}."),
    )
    parser.add_argument(
        "--plugin-id",
        required=True,
        metavar="ID",
        help="Plugin identifier (e.g. 'my-plugin'). Creates plugins/<ID>/.",
    )
    parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Directory in which to create the Backstage app (default: '.').",
    )
    parser.add_argument(
        "--create-app-version",
        default=None,
        metavar="VER",
        help="Override the auto-detected @backstage/create-app version.",
    )
    parser.add_argument(
        "--with-theme",
        action="store_true",
        help="Also install the RHDH theme package in the app workspace.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON result to stdout.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = scaffold(args)
    except KeyboardInterrupt:
        log("\nInterrupted.")
        sys.exit(130)
    except (OSError, PermissionError) as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "success": False,
                        "error": {
                            "code": "PATH_ERROR",
                            "message": str(exc),
                        },
                    },
                    indent=2,
                )
            )
        else:
            log(f"Error: {exc}")
        sys.exit(EXIT_FAILURE)

    if args.json:
        print(json.dumps(result, indent=2))

    sys.exit(EXIT_SUCCESS if result.get("success") else EXIT_FAILURE)


if __name__ == "__main__":
    main()
