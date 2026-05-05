#!/usr/bin/env python3
"""Scaffold a Backstage app and backend plugin for RHDH.

Automates Steps 2-3 of the create-backend-plugin workflow:
  1. Creates a Backstage app using the correct create-app version for the
     target RHDH release.
  2. Runs yarn install.
  3. Generates a backend plugin via `yarn new`.

Uses only Python stdlib (no external dependencies).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ─── RHDH → create-app version mapping (from versions.md) ───────────────────

RHDH_VERSION_MAP: dict[str, str] = {
    "next": "0.7.6",
    "1.9": "0.7.6",
    "1.8": "0.7.3",
    "1.7": "0.6.2",
    "1.6": "0.5.25",
}

SUPPORTED_VERSIONS = sorted(
    (v for v in RHDH_VERSION_MAP if v != "next"),
    key=lambda v: list(map(int, v.split("."))),
    reverse=True,
)

# ─── ANSI helpers ────────────────────────────────────────────────────────────

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
NC = "\033[0m"


def _color(code: str, text: str) -> str:
    if sys.stdout.isatty():
        return f"{code}{text}{NC}"
    return text


# ─── Validation ──────────────────────────────────────────────────────────────

PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def validate_plugin_id(value: str) -> str:
    """Validate plugin ID is a lowercase kebab-case identifier."""
    if not PLUGIN_ID_RE.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid plugin ID '{value}'. Must be lowercase kebab-case (e.g., 'my-plugin')."
        )
    return value


def validate_rhdh_version(value: str) -> str:
    """Validate RHDH version is in the known map."""
    if value not in RHDH_VERSION_MAP:
        supported = ", ".join(["next", *SUPPORTED_VERSIONS])
        raise argparse.ArgumentTypeError(f"Unknown RHDH version '{value}'. Supported: {supported}")
    return value


# ─── Tool checks ─────────────────────────────────────────────────────────────


def check_tool(name: str) -> str | None:
    """Return path to tool or None if missing."""
    return shutil.which(name)


def check_prerequisites() -> list[str]:
    """Return list of missing prerequisite tools."""
    missing = []
    for tool in ("npx", "yarn", "node"):
        if not check_tool(tool):
            missing.append(tool)
    return missing


# ─── Subprocess helpers ──────────────────────────────────────────────────────


def run_cmd(
    args: list[str],
    *,
    cwd: Path | None = None,
    stdin_text: str | None = None,
    description: str = "",
    use_json: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a command, stream output in human mode, capture in JSON mode."""
    if not use_json:
        print(f"  {_color(BLUE, '→')} {description or ' '.join(args)}")

    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            input=stdin_text,
            capture_output=use_json,
            text=True,
            # On Windows, shell=True is needed for npx/yarn .cmd scripts
            shell=(os.name == "nt"),
        )
    except FileNotFoundError as exc:
        msg = f"Command not found: {args[0]}"
        if use_json:
            _json_error("COMMAND_NOT_FOUND", msg)
        else:
            print(f"  {_color(RED, '✗')} {msg}: {exc}", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        msg = f"Command failed (exit {result.returncode}): {' '.join(args)}"
        if use_json:
            stderr_text = getattr(result, "stderr", "") or ""
            _json_error("COMMAND_FAILED", msg, detail=stderr_text.strip())
        else:
            print(f"  {_color(RED, '✗')} {msg}", file=sys.stderr)
        sys.exit(1)

    return result


# ─── Output helpers ──────────────────────────────────────────────────────────


def _json_error(code: str, message: str, *, detail: str = "", exit_code: int = 1) -> None:
    """Print a JSON error and exit."""
    resp: dict = {"success": False, "error": {"code": code, "message": message}}
    if detail:
        resp["error"]["detail"] = detail
    print(json.dumps(resp, indent=2))
    sys.exit(exit_code)


def _json_success(data: dict) -> None:
    """Print a JSON success payload."""
    print(json.dumps({"success": True, **data}, indent=2))


# ─── Core workflow ───────────────────────────────────────────────────────────


def scaffold(
    *,
    rhdh_version: str,
    plugin_id: str,
    app_path: Path,
    create_app_version: str,
    use_json: bool,
) -> None:
    """Run the full scaffold workflow (Steps 2-3)."""

    plugin_dir_name = f"{plugin_id}-backend"
    plugin_path = app_path / "plugins" / plugin_dir_name

    # ── Idempotency: check if plugin already exists ──────────────────────
    if plugin_path.exists():
        msg = f"Plugin directory already exists: {plugin_path}"
        if use_json:
            _json_error("ALREADY_EXISTS", msg)
        else:
            print(f"  {_color(YELLOW, '⚠')} {msg}")
            print("  Remove it first if you want to re-scaffold.")
        sys.exit(1)

    # ── Step 2a: Create Backstage app ────────────────────────────────────
    app_pkg_json = app_path / "package.json"
    if app_pkg_json.exists():
        if not use_json:
            print(
                f"  {_color(GREEN, '✓')} Backstage app already exists at "
                f"{app_path} — skipping create-app"
            )
    else:
        if not use_json:
            print(
                f"\n{_color(BOLD, 'Step 2: Create Backstage app')}"
                f" (create-app@{create_app_version})"
            )

        # Ensure parent directory exists
        app_path.mkdir(parents=True, exist_ok=True)

        run_cmd(
            [
                "npx",
                f"@backstage/create-app@{create_app_version}",
                "--path",
                str(app_path),
            ],
            stdin_text="backstage\n",
            description=(f"npx @backstage/create-app@{create_app_version} --path {app_path}"),
            use_json=use_json,
        )

    # ── Step 2b: yarn install ────────────────────────────────────────────
    if not use_json:
        print(f"\n  {_color(BLUE, '→')} Running yarn install …")

    run_cmd(
        ["yarn", "install"],
        cwd=app_path,
        description="yarn install",
        use_json=use_json,
    )

    # ── Step 3: Create backend plugin ────────────────────────────────────
    if not use_json:
        print(f"\n{_color(BOLD, 'Step 3: Create backend plugin')} (id={plugin_id})")

    run_cmd(
        [
            "yarn",
            "new",
            "--select",
            "backend-plugin",
            "--option",
            f"id={plugin_id}",
        ],
        cwd=app_path,
        description=f"yarn new --select backend-plugin --option id={plugin_id}",
        use_json=use_json,
    )

    # ── Summary ──────────────────────────────────────────────────────────
    if not plugin_path.exists():
        msg = (
            f"Expected plugin directory not found at {plugin_path}. "
            "The scaffold command may have used a different naming convention."
        )
        if use_json:
            _json_error("PLUGIN_DIR_MISSING", msg)
        else:
            print(f"  {_color(YELLOW, '⚠')} {msg}")
        sys.exit(1)

    if use_json:
        _json_success(
            {
                "rhdh_version": rhdh_version,
                "create_app_version": create_app_version,
                "plugin_id": plugin_id,
                "app_path": str(app_path.resolve()),
                "plugin_path": str(plugin_path.resolve()),
            }
        )
    else:
        print(f"\n{_color(GREEN, '✓')} Scaffold complete!")
        print(f"  RHDH version:      {rhdh_version}")
        print(f"  create-app:        @backstage/create-app@{create_app_version}")
        print(f"  Plugin ID:         {plugin_id}")
        print(f"  App path:          {app_path.resolve()}")
        print(f"  Plugin path:       {plugin_path.resolve()}")
        print(f"\n{_color(BOLD, 'Next steps:')}")
        print(f"  cd {plugin_path}")
        print("  # Implement plugin logic in src/plugin.ts")
        print("  yarn build")


# ─── CLI ─────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    supported = ", ".join(["next", *SUPPORTED_VERSIONS])
    parser = argparse.ArgumentParser(
        description=(
            "Scaffold a Backstage app and backend plugin for Red Hat Developer Hub. "
            "Automates Steps 2-3 of the create-backend-plugin workflow: creates the "
            "Backstage app with the correct create-app version, installs dependencies, "
            "and generates the backend plugin."
        ),
        epilog=f"Supported RHDH versions: {supported}",
    )
    parser.add_argument(
        "--rhdh-version",
        required=True,
        type=validate_rhdh_version,
        metavar="VERSION",
        help=f"Target RHDH version ({supported})",
    )
    parser.add_argument(
        "--plugin-id",
        required=True,
        type=validate_plugin_id,
        metavar="ID",
        help="Plugin identifier in kebab-case (e.g., 'my-plugin')",
    )
    parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Directory in which to create the Backstage app (default: current dir)",
    )
    parser.add_argument(
        "--create-app-version",
        default=None,
        metavar="VERSION",
        help="Override the auto-detected @backstage/create-app version",
    )
    parser.add_argument(
        "--json",
        dest="use_json",
        action="store_true",
        default=False,
        help="Output structured JSON instead of human-readable text",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    use_json: bool = args.use_json

    # ── Resolve create-app version ───────────────────────────────────────
    create_app_version = args.create_app_version or RHDH_VERSION_MAP[args.rhdh_version]

    # ── Check prerequisites ──────────────────────────────────────────────
    missing = check_prerequisites()
    if missing:
        msg = f"Missing required tools: {', '.join(missing)}"
        next_steps = [f"Install {tool} and ensure it is on PATH" for tool in missing]
        if use_json:
            _json_error(
                "MISSING_TOOLS",
                msg,
                detail="; ".join(next_steps),
            )
        else:
            print(f"  {_color(RED, '✗')} {msg}", file=sys.stderr)
            for step in next_steps:
                print(f"    - {step}", file=sys.stderr)
        return 1

    # ── Resolve path ─────────────────────────────────────────────────────
    app_path = Path(args.path).resolve()

    if not use_json:
        print(f"{_color(BOLD, 'Scaffolding backend plugin for RHDH')} {args.rhdh_version}")

    try:
        scaffold(
            rhdh_version=args.rhdh_version,
            plugin_id=args.plugin_id,
            app_path=app_path,
            create_app_version=create_app_version,
            use_json=use_json,
        )
    except (OSError, PermissionError) as exc:
        if use_json:
            _json_error("PATH_ERROR", str(exc))
        else:
            print(f"  {_color(RED, '✗')} {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
