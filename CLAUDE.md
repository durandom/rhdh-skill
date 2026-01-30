# CLAUDE.md

## Development Rules

1. **TDD First** — Write tests before implementation, even for markdown files. See `tests/unit/test_skill_structure.py` for examples.

2. **Run Tests** — `uv run pytest` before committing.

## Project Structure

```
rhdh-skill/
├── skills/
│   ├── rhdh/              # Orchestrator skill (Python CLI + routing)
│   │   ├── rhdh/          # Python CLI package (stdlib only)
│   │   ├── scripts/       # Entry point (./scripts/rhdh)
│   │   ├── references/    # General tool references (GitHub, JIRA)
│   │   └── SKILL.md       # Routes to overlay skill
│   └── overlay/           # Overlay skill (markdown only)
│       ├── workflows/     # Plugin workflows (onboard, update, fix)
│       ├── references/    # Overlay-specific references
│       └── SKILL.md       # Overlay workflow routing
├── tests/                 # pytest test suite (dev only)
└── pyproject.toml         # Dev dependencies (pytest)
```

## CLI

The CLI is stdlib-only and runs with any Python 3.9+:

```bash
./skills/rhdh/scripts/rhdh           # Status check
./skills/rhdh/scripts/rhdh doctor    # Full environment check
./skills/rhdh/scripts/rhdh --json    # Force JSON output
```

Auto-detects output format: **TTY** → human-readable, **Piped** → JSON.

## Key Patterns

- `OutputFormatter` handles JSON/human rendering — commands build data dicts
- Workflows live in `skills/overlay/workflows/` — doctor points agents there for setup
- Config discovery: env vars → project config → user config → auto-detection
