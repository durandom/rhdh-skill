# Architecture Patterns for Complex Skills

Read this when the skill covers a broad domain with multiple distinct operations, needs project-level context, or has mandatory setup requirements.

## Sub-Command Router

### When to use

Use when the skill has **multiple distinct operations** that share setup, context, or domain knowledge. One skill with a router table prevents menu pollution — users install one skill, not twenty.

Do NOT use when the operations have no shared context. Separate skills are better when each task is fully independent.

### Structure

The SKILL.md contains:
1. **Setup section** — shared gates that run before any command
2. **Shared rules** — domain laws that apply to every command
3. **Router table** — maps command names to reference files
4. **Routing rules** — how to interpret user input

Each command gets its own `references/<command>.md` file. The SKILL.md never contains command-specific instructions — it delegates.

### Router table pattern

```markdown
## Commands

| Command | Category | Description | Reference |
|---|---|---|---|
| `init [project]` | Setup | Initialize a new project | [references/init.md](references/init.md) |
| `check [target]` | Evaluate | Run quality checks | [references/check.md](references/check.md) |
| `fix [target]` | Repair | Auto-fix common issues | [references/fix.md](references/fix.md) |
```

Group commands by category (Setup, Evaluate, Repair, Generate, etc.) for the user-facing menu.

### Routing rules

```markdown
### Routing rules

1. **No argument**: Render the table as a user-facing command menu, grouped by category. Ask what to do.
2. **First word matches a command**: Load its reference file and follow its instructions. Everything after the command name is the target.
3. **First word doesn't match**: General invocation. Apply setup, shared rules, and the full argument as context.
```

Setup runs before routing. Sub-commands don't re-invoke the parent skill.

### Command metadata as data

Keep a `scripts/command-metadata.json` as the single source of truth for each command's description and argument hint. Both the SKILL.md router table and any tooling (pin scripts, build systems) read from this file.

```json
{
  "init": {
    "description": "Initialize a new project with scaffolding and config. Use when starting fresh.",
    "argumentHint": "[project name or path]"
  },
  "check": {
    "description": "Run quality checks across linting, tests, and conventions. Use when reviewing code.",
    "argumentHint": "[file, directory, or area]"
  }
}
```

The `description` here is optimized for auto-trigger keyword matching. Pack it with trigger phrases and near-miss scenarios.

### Pin/unpin shortcuts

Allow users to create standalone shortcuts: `/check` → `/skill-name check`. Write a script that creates redirect shims in the harness directory.

## Setup Gates

### When to use

Use when the skill produces noticeably worse output without certain preconditions. Gates turn "the output was mediocre" into "the agent tells you what's missing."

### Gate table pattern

Define gates as a table with required check and fail action:

```markdown
## Setup (non-optional)

| Gate | Required check | If fail |
|---|---|---|
| Context | Project context loaded via `python scripts/load_context.py` | Run the loader |
| Config | Config file exists and is not placeholder | Run `skill-name setup` |
| Command | Sub-command reference is loaded | Load the reference |
| Mutation | All gates above pass | Do not edit project files |
```

The **Mutation** gate is always last. No file edits until every other gate passes.

### Preflight declaration

For environments that support it, require the agent to state gate status before editing files:

```text
SKILL_PREFLIGHT: context=pass config=pass command_reference=pass mutation=open
```

This forces the agent to explicitly evaluate each gate rather than skipping silently.

### Common gates

| Gate type | Checks for | Example |
|---|---|---|
| Context | Project-level config loaded | Config file exists and is valid |
| Config | Required configuration present | API keys, workspace settings |
| Dependencies | Required tools installed | CLI tools, runtimes |
| Command | Sub-command reference loaded | Reference file read into context |
| Plan | User-confirmed plan exists | Plan approved before building |
| Mutation | All above pass | Final gate before file edits |

## Register/Mode System

### When to use

Use when the skill's behavior varies significantly by task type, but all types share the same commands and setup. The register classifies the task, then loads different reference material.

### Pattern

1. Define 2-4 registers with clear criteria:

```markdown
## Register

Every task is **library** (published, API-stable) or **application** (internal, can break).

Identify before acting. Priority: (1) cue in the task itself; (2) the target in focus; (3) explicit field in config. First match wins.

Load the matching reference: [references/library.md](references/library.md) or [references/application.md](references/application.md).
```

2. Each register gets its own reference file with register-specific rules.
3. Sub-command references add a short `## Register` section only where behavior diverges between registers. Don't restate the register file — link to it.

### More examples

- **Documentation**: `tutorial` (learning-focused, guided) vs `reference` (lookup-focused, exhaustive)
- **Testing**: `unit` (isolated, fast, mock-heavy) vs `integration` (realistic, slow, infra-dependent)
- **Deployment**: `development` (fast feedback, verbose) vs `production` (optimized, hardened)

## Context File System

### When to use

Use when every command in the skill needs the same project background. Without it, the agent asks the same questions every session, or produces generic output.

### Pattern

Define 1-2 context files at the project root:

| File | Purpose | Required? |
|---|---|---|
| `PROJECT.md` | Strategic context: users, goals, constraints, principles | Yes |
| `CONVENTIONS.md` | Technical context: patterns, naming, structure | Recommended |

The names should match the domain. A design skill uses `PRODUCT.md` and `DESIGN.md`. A deployment skill might use `INFRA.md`. Pick names that are obvious to the user.

### Loader script

Write a script that finds, reads, and returns context as JSON:

```python
#!/usr/bin/env python3
"""Load project context files and return structured JSON."""

import argparse
import json
import os
import sys
from pathlib import Path

CONFIG_NAMES = ["PROJECT.md", "Project.md", "project.md"]
FALLBACK_DIRS = [".agents/context", "docs"]

def load_context(cwd=None):
    cwd = Path(cwd or os.getcwd())
    # 1. Check env override (SKILL_CONTEXT_DIR)
    # 2. Check cwd for context files
    # 3. Fallback to subdirectories (.agents/context/, docs/)
    # 4. Return structured JSON
    config_path = ...  # resolve from cwd + fallbacks
    config = config_path.read_text(encoding="utf-8") if config_path else None
    return {
        "hasConfig": config is not None,
        "config": config,
        "configPath": str(config_path.relative_to(cwd)) if config_path else None,
        "contextDir": str(cwd),
    }

def main():
    parser = argparse.ArgumentParser(
        description="Load project context files and return structured JSON."
    )
    parser.add_argument("--dir", default=".", help="Project root directory")
    args = parser.parse_args()

    result = load_context(args.dir)
    if sys.stdout.isatty():
        print(json.dumps(result, indent=2))
    else:
        json.dump(result, sys.stdout)
    sys.exit(0 if result["hasConfig"] else 1)

if __name__ == "__main__":
    main()
```

Key behaviors:
- **Case-insensitive filename matching**: Accept `PROJECT.md`, `Project.md`, `project.md`
- **Env override**: `SKILL_CONTEXT_DIR=path/to/dir` for non-standard layouts
- **Fallback directories**: Check `.agents/context/` and `docs/` if root is clean
- **Full JSON output**: Never pipe through `head`, `tail`, `grep`, or `jq`

### Context validation

Handle missing, empty, or placeholder files:

```markdown
If PROJECT.md is missing or placeholder (`[TODO]` markers, <200 chars):
run `skill-name setup`, then resume the original task with fresh context.
```

### Session caching

Don't re-run the loader if context is already in the conversation. Exceptions: the user just ran a setup command that rewrites the files, or manually edited them.

## Capability-Gating

### When to use

Use when a step depends on optional environment capabilities (browser automation, specific CLI tools, API keys) that may not be present.

### Pattern

```markdown
### Automated Scan (Capability-Gated)

Run the scan when ALL of these are true:
- The target files exist and are readable
- The required CLI tool is installed

When conditions are met, this step is mandatory. If unavailable, state in one line
that the step is skipped and why. Do not ask the user to install tooling. Proceed.
```

Rules:
- State the conditions explicitly (ALL must be true)
- Make the step mandatory when conditions are met — don't let the agent skip out of laziness
- Provide a one-line skip reason template
- Never ask users to install tooling just to satisfy a gated step

## Structured Artifacts as Handoffs

### When to use

Use when one command produces output that another command consumes. The artifact is the contract between them.

### Pattern

Define the artifact structure in the producing command's reference:

```markdown
### Plan Structure

**1. Summary** (2-3 sentences)
**2. Primary Goal**
**3. Approach**
**4. Scope** (breadth, depth, time intent)
**5. Key Scenarios** (default, error, edge cases)
**6. Open Questions**
```

The consuming command's reference defines what it expects:

```markdown
## Build Gate

Build cannot start until:
1. Context is valid and current.
2. The plan is explicitly confirmed by the user.
3. Relevant references from the plan are loaded.
```

Key: the plan must be **user-confirmed**, not self-authored by the agent. A separate user response approving the plan is required before proceeding.

## Self-Critique Loops

### When to use

Use for any command that produces artifacts (code, documents, configs). The first pass is never the final pass.

### Pattern

```markdown
### Critique and fix loop

After the first pass, write a short self-critique and patch. Repeat until no material issues remain:

1. Does it match the requirements?
2. Does it pass the quality checks? (define explicitly)
3. Check every expected scenario.
4. Check against the absolute bans list.

The exit bar is not "it works." It is: [specific, measurable quality threshold].
```

Define the exit bar explicitly. "Looks good" is not a bar. "All tests pass, all expected scenarios are handled, no placeholders remain, and the output would survive code review" is a bar.

## Anti-Patterns in Skill Design

### Monolithic SKILL.md

**Problem**: Everything in one file. 800+ lines, mixing setup, rules, and command-specific logic.
**Fix**: Router table + reference files. SKILL.md under 500 lines.

### Eager reference loading

**Problem**: "Before starting, read all reference files." Wastes context.
**Fix**: Conditional loading. "Read `references/aws.md` if deploying to AWS."

### Missing setup gates

**Problem**: Agent produces generic output because it never checked for project context.
**Fix**: Gate table with explicit fail actions. Mutation gate last.

### Dumping all interview questions

**Problem**: Agent asks 15 questions at once. User abandons.
**Fix**: Ask one question at a time, wait for the answer, adapt. Every question should earn its place.

### Self-authored plans

**Problem**: Agent writes a plan, approves its own plan, and builds from it.
**Fix**: Require a separate user response approving the plan before proceeding.

### Vague quality bars

**Problem**: "Make sure it's good quality" — unenforceable.
**Fix**: Explicit checklists, scoring rubrics, or match-and-refuse ban lists.
