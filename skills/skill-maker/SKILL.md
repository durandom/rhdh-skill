---
name: skill-maker
description: Create new agent skills following the Agent Skills open standard (agentskills.io). Interviews the user relentlessly about intent, scope, and edge cases before drafting. Covers SKILL.md structure, frontmatter, progressive disclosure, description optimization, script bundling, sub-command architecture, setup gates, context systems, and review. Use when the user wants to create a skill, write a skill, build a new skill, make a skill, draft a SKILL.md, or mentions "skill-maker". Also use when asked to package expertise, workflows, or domain knowledge into a reusable skill.
---

# Create Skill

Create agent skills following the [Agent Skills open standard](https://agentskills.io/specification).

## Phase 1: Interview

Interview the user about every aspect of this skill until reaching shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

### Interview cadence

Ask **one question at a time**. Wait for the answer before asking the next. Adapt follow-ups based on what you learn. Each question should provide clear benefit toward building a better skill — cut questions the codebase can answer for you.

If a question can be answered by exploring the codebase, explore the codebase instead of asking.

Focus areas, roughly in order:

1. **Purpose and audience.** What task does this skill cover? What specific problem does it solve? What does the user do today without it?
2. **Scope boundaries.** What should this skill NOT do? What adjacent tasks belong to other skills?
3. **Input/output.** What does the user provide? What does the skill produce? Specific formats?
4. **Edge cases.** What goes wrong? Common mistakes? Gotchas for new users?
5. **Success criteria.** How do you know the skill worked correctly?
6. **What can be scripted?** Look for deterministic operations that should be code, not LLM instructions. Scripts are cheaper, faster, and more reliable.
7. **References needed?** Domain knowledge too large for SKILL.md that should live in separate files?
8. **Existing patterns.** Similar skills or workflows to draw from? Check the codebase.
9. **Platform constraints.** macOS, Windows, and Linux? Scripts must handle path separators, temp directories, and shell differences.
10. **Architecture.** Based on the answers above, decide whether the skill's scope warrants sub-commands, context systems, or setup gates. Most skills don't need this — skip to Phase 2 if the skill is straightforward. If it does, ask:
    - **Should this be one skill with sub-commands or multiple skills?** One skill with a router table prevents menu pollution. Multiple skills are appropriate when the tasks have no shared context or setup.
    - **Does the skill need project-level context?** If every command needs the same background (project config, conventions), design a context file pattern with a loader script.
    - **Are there mandatory setup gates?** Steps that must pass before any work begins (context loaded, config valid, dependencies present). Gates prevent generic output.
    - **Does behavior vary by task type?** If so, design a register/mode system that classifies the task first, then loads different references.

Read `references/architecture-patterns.md` when the skill needs sub-commands, context systems, or setup gates.

Do not proceed to Phase 2 until the user confirms the scope is complete.

## Phase 2: Draft the SKILL.md

Write the skill following the spec. Read `references/spec-guide.md` for the full format reference before drafting.

### Frontmatter

```yaml
---
name: skill-name        # lowercase, hyphens, max 64 chars
description: |           # max 1024 chars — this is the ONLY triggering mechanism
  What the skill does. Use when [specific triggers].
  Also use when [additional triggers].
---
```

The description must be slightly "pushy" — agents tend to undertrigger. Include both what the skill does AND specific phrases/contexts that should activate it.

### Body structure

Follow progressive disclosure — three loading levels:

1. **Metadata** (~100 tokens): `name` and `description` loaded at startup for all skills
2. **Instructions** (< 500 lines): Full SKILL.md body loaded when skill activates
3. **Resources** (as needed): `references/`, `scripts/`, `assets/` loaded only when required

Keep the SKILL.md body under 500 lines. If approaching this limit, split domain-specific content into `references/` files with clear pointers about when to read them.

### Writing patterns

- **Imperative form**: "Run the command" not "You should run the command"
- **Output templates**: Define exact formats when the output structure matters
- **Concrete examples**: Show input → output for non-obvious workflows
- **Gotchas sections**: Common mistakes the agent should avoid
- **Checklists**: Multi-step workflows with validation gates
- **Conditional loading**: "Read `references/api-errors.md` if the API returns a non-200 status code" — not "see references/ for details"
- **Absolute bans**: When certain patterns are always wrong, use match-and-refuse lists. "If you're about to write X, stop and do Y instead." More effective than vague "be careful" guidance.

### Sub-command router (when applicable)

For skills with multiple distinct operations, use a router table in SKILL.md:

```markdown
## Commands

| Command | Description | Reference |
|---|---|---|
| `craft [feature]` | Build a feature end-to-end | [references/craft.md](references/craft.md) |
| `audit [target]` | Technical quality checks | [references/audit.md](references/audit.md) |

### Routing rules

1. **No argument**: Show the command menu. Ask what to do.
2. **First word matches a command**: Load its reference file and follow it.
3. **First word doesn't match**: General invocation using the full argument as context.
```

Back the router with a `scripts/command-metadata.json` as the single source of truth:

```json
{
  "craft": {
    "description": "Full build flow. Use when building a new feature end-to-end.",
    "argumentHint": "[feature description]"
  }
}
```

### Setup gates (when applicable)

Non-negotiable checks before any file edits. Gates prevent generic output from missing context.

```markdown
## Setup (non-optional)

| Gate | Required check | If fail |
|---|---|---|
| Context | Project config loaded via `python scripts/load_context.py` | Run the loader first |
| Config | Config file exists and is valid | Run `skill-name setup` |
| Command | Sub-command reference is loaded | Load the reference |
| Mutation | All gates above pass | Do not edit project files |
```

### Register/mode system (when applicable)

When behavior varies by task type, classify first, then load different references:

```markdown
## Register

Every task is **library** (published, API-stable) or **application** (internal, can break).
Identify before acting. Load the matching reference: [references/library.md] or [references/application.md].
```

### Capability-gating

Steps that depend on optional environment capabilities (browser automation, specific CLI tools) must degrade gracefully:

```markdown
### Automated Scan (Capability-Gated)

Run the automated scanner when ALL of these are true:
- The target files exist and are readable
- The required CLI tool is installed

If unavailable, state in one line that the step is skipped and why. Do not ask the user to install tooling.
```

### Structured artifacts as handoffs

When one command produces output that another consumes, define the artifact structure explicitly. The producing command's reference defines the format; the consuming command's reference says what it expects:

```markdown
### Plan Structure

**1. Summary** (2-3 sentences)
**2. Primary Goal**
**3. Approach**
...
```

### Self-critique loops

For build/implementation commands, mandate inspect-and-fix passes with explicit exit bars:

```markdown
### Critique and fix loop

After the first pass, write a short self-critique and patch. Repeat until no material issues remain:
1. Does it match the requirements?
2. Does it pass the [quality test]?
3. Check every expected scenario.
4. Check edge cases.

The exit bar is not "it works." It is: [explicit quality threshold].
```

## Phase 3: Description Optimization

The description is the only thing agents see at startup. Read `references/description-guide.md` for the full optimization process.

Quick validation:

1. Write 5 should-trigger queries (different phrasings, including ones that don't name the skill directly)
2. Write 5 should-not-trigger queries (near-misses that share keywords but need different skills)
3. Check: would the description correctly distinguish these?
4. Revise if needed — broaden for missed triggers, narrow for false triggers
5. Verify under 1024 characters

For skills with sub-commands, the main description covers the skill broadly. Each sub-command's description in `command-metadata.json` is optimized separately for auto-trigger keyword matching.

## Phase 4: Scripts

Read `references/scripts-guide.md` for the full guide.

**Bias toward scripts.** Every deterministic operation should be a script, not an instruction. Scripts are cheaper (no LLM tokens), faster (no reasoning), and more reliable (no hallucination).

For each piece of the skill's workflow, ask: "Could a script do this?" If yes, write the script.

**Should be scripts:**
- Validation (input format, required fields, schema compliance)
- File generation from templates
- Data extraction and transformation
- API calls with structured responses
- Setup and environment checks
- Output formatting
- Context loading (read project files, resolve paths, return JSON)
- Pin/unpin shortcuts (create/remove command aliases)
- Cleanup (remove deprecated files after skill updates)

**Should stay as instructions:**
- Deciding between architectural approaches
- Reviewing code for quality or style
- Explaining tradeoffs to the user
- Creative writing or design decisions
- Interview/discovery conversations

Key patterns:
- **Python without dependencies**: stdlib only, `argparse` for CLI parsing
- **Python with dependencies**: PEP 723 inline metadata with `uv run`
- **All scripts**: Structured output (JSON when piped), clear exit codes, descriptive `--help`

### Context loader pattern

For skills that need project-level context, write a loader script:

The script should follow all standard patterns: `argparse` with `--help`, structured JSON output (pretty when interactive, compact when piped), clear exit codes (0 = found, 1 = missing), `pathlib` for cross-platform paths, and stdlib-only imports. See the "Context File System" section in `references/architecture-patterns.md` for a skeleton.

The SKILL.md references it: "Load context via `python scripts/load_context.py`. Consume the full JSON output. Never pipe through `head`, `tail`, or `grep`."

## Phase 5: Review

Before presenting the final skill, verify against this checklist:

### Basics
- [ ] `name` is lowercase, hyphens only, max 64 chars
- [ ] `description` is under 1024 chars and includes trigger phrases
- [ ] `description` is slightly pushy — covers edge phrasings that should activate the skill
- [ ] SKILL.md body is under 500 lines
- [ ] Instructions use imperative form

### Architecture (if applicable)
- [ ] Sub-commands have a router table with clear routing rules
- [ ] `command-metadata.json` is the single source of truth for command descriptions
- [ ] Setup gates are defined with fail actions for each gate
- [ ] Register/mode system classifies before loading references
- [ ] Capability-gated steps degrade gracefully with one-line skip reasons

### References
- [ ] Domain knowledge split into `references/` with clear "when to read" pointers
- [ ] Each reference is self-contained — an agent can load it without reading others
- [ ] Reference loading is conditional, not eager ("Read X if Y happens")

### Scripts
- [ ] Scripts (if any) have shebangs, structured output, and `--help`
- [ ] Context loader returns JSON, handles missing files, resolves fallback paths
- [ ] Scripts are cross-platform (pathlib, tempfile, no hardcoded paths)
- [ ] Scripts are idempotent — safe to re-run

### Quality
- [ ] No time-sensitive information (URLs to specific versions, dates that will go stale)
- [ ] Consistent terminology throughout
- [ ] Concrete examples included for non-obvious workflows
- [ ] Absolute bans defined for patterns that are always wrong
- [ ] Self-critique loops defined for build/implementation commands with explicit exit bars
