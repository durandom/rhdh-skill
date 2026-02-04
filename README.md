# RHDH Skill

A Claude Code skill for managing Red Hat Developer Hub plugins — onboarding, updating, and triaging plugins in the Extensions Catalog.

## Installation

### From Local Checkout (Development)

```bash
claude plugin marketplace add ~/src/rhdh/rhdh-skill
claude plugin install --scope project rhdh
```

### From Published Plugin

```bash
claude plugin marketplace add durandom/rhdh-skill
claude plugin install --scope project rhdh
```

> **Note:** Always install in project scope. The skill references repository-specific paths.

## Setup

After installation, run the skill to check environment:

```bash
/rhdh
```

If `needs_setup: true`, follow the setup instructions to configure required repositories.

## Architecture

The skill is split into two focused components:

| Skill | Purpose | Contents |
|-------|---------|----------|
| `rhdh` | Orchestrator | Python CLI + routing logic |
| `overlay` | Workflows | Markdown-only workflow definitions |

This separation allows the orchestrator to be portable (stdlib-only Python) while keeping workflow documentation easy to maintain.

## The RHDH CLI

The `rhdh` CLI is a lightweight Python tool that provides **session context** for Claude Code. It exists because:

1. **Environment Discovery** — Detects overlay repo, rhdh-local, container runtime, and tool availability
2. **Cross-Session Memory** — Worklog and todo tracking let Claude resume work without re-explaining context
3. **Machine-Readable Output** — Auto-detects TTY vs pipe, outputting JSON when Claude reads it
4. **Configuration Management** — Stores repo paths in `.rhdh/config.json` for consistent discovery

The CLI is **stdlib-only** (no dependencies) and runs on any Python 3.9+.

### Storage Locations

All state is stored in a `.rhdh/` directory at the project root (git repo), with fallback to `~/.config/rhdh/` when outside a repo:

| File | Purpose |
|------|---------|
| `config.json` | Repo paths, settings |
| `worklog.jsonl` | Append-only activity log |
| `TODO.md` | Section-based task tracking |

The `.rhdh/` directory should be added to `.gitignore` — it contains session-specific state, not project configuration.

### Quick Reference

```bash
./skills/rhdh/scripts/rhdh              # Status / orientation
./skills/rhdh/scripts/rhdh doctor       # Full environment check
./skills/rhdh/scripts/rhdh config init  # Create config with auto-detection
./skills/rhdh/scripts/rhdh workspace list  # List plugin workspaces

# Activity tracking
./skills/rhdh/scripts/rhdh log add "Started onboard" --tag onboard
./skills/rhdh/scripts/rhdh todo add "Check license" --context aws-appsync
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/rhdh` | Show status and route to appropriate workflow |
| `/onboard-plugin` | Add a new plugin to Extensions Catalog |
| `/update-plugin` | Bump plugin to newer upstream version |
| `/fix-plugin-build` | Debug CI/publish failures |
| `/triage-overlay-prs` | Prioritize open PRs (Core Team) |
| `/analyze-overlay-pr` | Analyze specific PR (Core Team) |

## Project Structure

```
rhdh-skill/
├── skills/
│   ├── rhdh/              # Orchestrator skill
│   │   ├── rhdh/          # Python CLI package (stdlib only)
│   │   ├── scripts/rhdh   # Entry point
│   │   ├── references/    # GitHub, JIRA tool guides
│   │   └── SKILL.md       # Routing logic
│   └── overlay/           # Workflow skill (markdown only)
│       ├── workflows/     # onboard, update, fix, triage
│       ├── references/    # Overlay-specific docs
│       └── SKILL.md       # Workflow definitions
├── tests/                 # pytest test suite
└── pyproject.toml         # Dev dependencies
```

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run CLI directly
./skills/rhdh/scripts/rhdh --help
```

## License

Apache-2.0
