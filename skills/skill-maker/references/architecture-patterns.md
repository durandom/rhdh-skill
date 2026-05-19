# Architecture Patterns for Complex Skills

Read this when the skill covers a broad domain with multiple distinct operations, needs project-level context, or has mandatory setup requirements.

## Sub-Command Router

### When to use

Use when the skill has **multiple distinct operations** that share setup, context, or domain knowledge. One skill with a router table prevents menu pollution — users install one skill, not twenty.

Do NOT use when the operations have no shared context. Separate skills are better when each task is fully independent.

### Evolving from reference files to a router

Skills often start with standalone reference files (e.g., `references/assign.md`) loaded on demand. Upgrade to a router table when:

- You have multiple distinct operations and expect to add more
- Operations share setup gates, auth, or domain context
- Users need a discoverable menu of what the skill can do

Migration path:

1. Keep existing reference files as-is — they become command references
2. Add the router table and routing rules to SKILL.md
3. Create `scripts/command-metadata.json` as the single source of truth
4. Add a "Common Workflows" section that maps user intents to commands

Do not delay the migration until the skill is "complete" — add the router as soon as the pattern is clear. Retrofitting is cheap.

### Structure

The SKILL.md contains these sections, using XML tags to create unambiguous boundaries:

1. `<essential_principles>` — domain laws that apply to every command
2. `<intake>` — ask the user what they want to do
3. `<routing>` — maps responses to reference/workflow files
4. `<reference_index>` — lists reference files with "load when..." guidance

Setup gates, success criteria, and CLI setup can use additional tags as needed (e.g., `<cli_setup>`, `<success_criteria>`). Invent descriptive tag names that fit the skill's domain.

Each command gets its own `references/<command>.md` file. The SKILL.md never contains command-specific instructions — it delegates.

### Cross-cutting conventions

When multiple sub-commands share interaction patterns, error handling rows, or domain rules, centralize them in SKILL.md under a dedicated section (e.g., "Conventions" or "Shared Rules"). Sub-commands reference them instead of repeating.

The signal to centralize: you're copying the same text into another sub-command and realizing a change would require updating multiple files.

Common candidates for centralization:

- **Confirmation flow**: `"Apply changes? [y/N/edit]"` — define once, sub-commands say "use the standard confirmation flow from SKILL.md."
- **Error rows**: If the same error/action row appears across sub-commands' error tables, move it to SKILL.md's Error Handling table. Sub-commands say "See SKILL.md Error Handling."
- **Domain conventions**: Team-specific rules that apply everywhere (e.g., "Release Pending counts as completed for velocity"). State once in SKILL.md.

### Data flow between sub-commands

When sub-commands reuse each other's analysis (e.g., sprint planning reuses assignee expertise profiles), document the data flow in SKILL.md's Common Workflows section:

```markdown
> Sub-commands share data. `plan` reuses roster/capacity from `assign`.
> `sprint-report` uses the same velocity pattern as `plan`.
> `release` references exit criteria from `workflows.md` and can invoke `assign`.
```

This tells the agent which references to load together and prevents redundant API calls when running sub-commands in sequence.

### Router table pattern

```xml
<intake>
## What would you like to do?

| # | Category | Command | Description |
|---|----------|---------|-------------|
| 1 | Setup | `init [project]` | Initialize a new project |
| 2 | Evaluate | `check [target]` | Run quality checks |
| 3 | Repair | `fix [target]` | Auto-fix common issues |

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Reference |
|----------|----------|
| 1, "init", "initialize", "new project" | `references/init.md` |
| 2, "check", "quality", "lint" | `references/check.md` |
| 3, "fix", "repair", "auto-fix" | `references/fix.md` |
| First word doesn't match | General invocation — apply shared rules with full input as context |
</routing>
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

## Creation Workflows

### When to use

Use when a skill creates structured artifacts through conversation (Jira issues, PRDs, design docs, config files). The goal is to feel like a conversation with a smart colleague, not a form.

### Draft-then-grill

Don't ask every question from scratch. Synthesize what the conversation already established into a draft, present it for review, then ask only about gaps:

1. **Draft from context** — fill in as many template sections as possible from what's already known
2. **Present for review** — "Here's what I have so far. What's missing or wrong?"
3. **Fill gaps** — ask targeted questions only for unfilled sections
4. **Challenge** — probe sizing, completeness, scope, risks on the completed draft

This respects the user's time. If they spent 10 minutes describing the problem, they don't want to re-answer it as 7 template questions.

### Field inference

When the artifact has metadata fields (priority, owner, category, labels, sizing), infer values from the conversation instead of asking for each one:

- Propose all fields at once with rationale
- User confirms or adjusts

Examples across domains:

- **Issue tracker**: "Priority Major (functional gap, not a regression). Team inferred from component. Size M based on AC count."
- **Design doc**: "Category: API Design. Reviewer: inferred from module ownership. Status: Draft."
- **Config file**: "Environment: staging — you mentioned testing. Region: us-east-1 — matches existing infra."

Inference signals depend on the domain: conversation keywords, codebase context (file paths being edited), parent artifact inheritance, historical patterns, or org conventions.

### Review gate with preview

Before creating the artifact, render a preview as a temp file so the user can review the complete picture:

```markdown
## {Type}: {summary}

### Description
{filled template}

### Fields
- **Priority**: Major — rationale
- **Team**: COPE
...
```

Present: "Review before creating. [approve / edit / cancel]"

This is a concrete implementation of the mutation gate — no artifact is created until the user approves the preview.

### Chained decomposition

When artifacts form a hierarchy (e.g., PRD → issues, design doc → tasks, Feature → Epic → Story), offer to continue down the chain after each creation:

- Context carries down — don't re-ask what was already established
- The grill narrows at each level (high-level scope → delivery plan → implementation details)
- Each level is a separate confirmation — the user can stop at any point
- Parent/child linking happens automatically where the target system supports it

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
