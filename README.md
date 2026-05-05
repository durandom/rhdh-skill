# RHDH Skill

Agent skills for managing Red Hat Developer Hub plugins — onboarding, updating, and triaging plugins in the Extensions Catalog.

## Installation

### Via Skills CLI (any agent)

Install skills into any [supported coding agent](https://github.com/vercel-labs/skills#supported-agents) (Claude Code, Cursor, Codex, Pi, and 50+ more):

```bash
# Install all skills
npx skills add redhat-developer/rhdh-skill

# List available skills without installing
npx skills add redhat-developer/rhdh-skill --list

# Install a specific skill
npx skills add redhat-developer/rhdh-skill --skill rhdh

# Install to a specific agent
npx skills add redhat-developer/rhdh-skill -a claude-code
```

### Via Claude Code Plugin Marketplace

```bash
claude plugin marketplace add redhat-developer/rhdh-skill
claude plugin install --scope project rhdh
```

### From Local Checkout (Development)

```bash
# Via skills CLI
npx skills add ./path/to/rhdh-skill

# Via Claude Code
claude plugin marketplace add ~/src/rhdh/rhdh-skill
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

The plugin consists of an orchestrator skill that routes to specialized workflow skills:

| Skill | Purpose | Contents |
|-------|---------|----------|
| `rhdh` | Orchestrator | Python CLI + routing logic |
| `overlay` | Overlay workflows | Onboard, update, fix, triage plugins |
| `create-backend-plugin` | Backend plugins | Bootstrap new backend dynamic plugins |
| `create-frontend-plugin` | Frontend plugins | Bootstrap new frontend dynamic plugins |
| `export-and-package` | Packaging | Export plugins as OCI/tgz/npm |
| `generate-frontend-wiring` | Frontend wiring | Mount points, routes, entity tabs |
| `rhdh-local` | Local testing | Enable/disable/test plugins locally |

The orchestrator is portable (stdlib-only Python) while workflow skills are markdown-only for easy maintenance.

## The RHDH CLI

The `rhdh` CLI is a lightweight Python tool that provides **session context** for Claude Code. It exists because:

1. **Environment Discovery** — Detects overlay repo, rhdh-local, container runtime, and tool availability
2. **Cross-Session Memory** — Worklog and todo tracking let Claude resume work without re-explaining context
3. **Machine-Readable Output** — Auto-detects TTY vs pipe, outputting JSON when Claude reads it
4. **Configuration Management** — Stores repo paths in `.rhdh/config.json` for consistent discovery

The CLI is **stdlib-only** (no dependencies) and runs on any Python 3.9+.

### Storage Locations

Data and config are stored separately to avoid scattering logs across repos/worktrees:

| Location | Contents | Purpose |
|----------|----------|---------|
| `~/.config/rhdh-skill/` | `worklog.jsonl`, `TODO.md` | Centralized activity tracking |
| `~/.config/rhdh-skill/config.json` | User config | Global settings |
| `.rhdh/config.json` | Project config | Per-project repo overrides |

**Why centralized data?** The worklog and todos track *your* activity across all projects. Storing them per-repo means logs get lost when switching worktrees or deleting clones.

**Override with env var:**

```bash
export RHDH_SKILL_DATA_DIR=/custom/path
```

This redirects `worklog.jsonl` and `TODO.md` to the specified directory.

### Quick Reference

```bash
./skills/rhdh/scripts/rhdh              # Status / orientation
./skills/rhdh/scripts/rhdh doctor       # Full environment check
./skills/rhdh/scripts/rhdh config init  # Create config with auto-detection
./skills/rhdh/scripts/rhdh setup        # Environment setup commands
./skills/rhdh/scripts/rhdh workspace list  # List plugin workspaces
./skills/rhdh/scripts/rhdh local        # Local RHDH customization operations

# Activity tracking
./skills/rhdh/scripts/rhdh log add "Started onboard" --tag onboard
./skills/rhdh/scripts/rhdh todo add "Check license" --context aws-appsync
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/rhdh` | Show status and route to appropriate workflow (skill) |
| `/onboard-plugin` | Add a new plugin to Extensions Catalog |
| `/update-plugin` | Bump plugin to newer upstream version |
| `/fix-plugin-build` | Debug CI/publish failures |
| `/plugin-status` | Check plugin health and compatibility status |
| `/triage-overlay-prs` | Prioritize open PRs (Core Team) |
| `/analyze-overlay-pr` | Analyze specific PR (Core Team) |
| `/session-log` | Document session accomplishments to logs |

## Project Structure

```
rhdh-skill/
├── .claude-plugin/        # Plugin manifest + marketplace listing
├── commands/              # Slash command definitions
├── skills/
│   ├── rhdh/              # Orchestrator skill
│   │   ├── rhdh/          # Python CLI package (stdlib only)
│   │   ├── scripts/rhdh   # Entry point
│   │   ├── references/    # GitHub, JIRA, version refs
│   │   └── SKILL.md       # Routing logic
│   ├── overlay/           # Overlay workflow skill
│   │   ├── workflows/     # onboard, update, fix, triage
│   │   ├── templates/     # Workspace file templates
│   │   ├── references/    # Overlay-specific docs
│   │   └── SKILL.md       # Workflow definitions
│   ├── create-backend-plugin/
│   ├── create-frontend-plugin/
│   ├── export-and-package/
│   ├── generate-frontend-wiring/
│   └── rhdh-local/        # Local RHDH testing
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
