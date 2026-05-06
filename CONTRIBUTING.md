# Contributing to RHDH Skill

Contributions are welcome, and they are greatly appreciated! Every little bit helps. ❤️

This project is released under the Apache 2.0 License.

## Get Started

```bash
git clone https://github.com/redhat-developer/rhdh-skill.git
cd rhdh-skill
uv sync --extra dev
git config core.hooksPath .githooks
```

That last command enables pre-commit hooks (linting, formatting, tests) automatically — no `pre-commit install` needed.

### Running Tests

```bash
uv run pytest
```

### Linting

```bash
uv run ruff check .
uv run ruff format --check .
```

Both run automatically via the pre-commit hook.

## Submitting a Pull Request

1. Fork the repo and create a branch from `main`.
2. Make your changes. Keep commits focused — one concern per commit.
3. Make sure `uv run pytest` and `uv run ruff check .` pass.
4. Open a pull request.

## CLAUDE.md

`CLAUDE.md` contains `@AGENTS.md` — a directive that points Claude Code to the canonical file. Edit `AGENTS.md`, not `CLAUDE.md`.
