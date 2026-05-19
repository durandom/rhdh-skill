---
name: skill-maker
description: Create, audit, or consolidate agent skills following the Agent Skills open standard (agentskills.io). Interviews the user relentlessly about intent, scope, and edge cases before drafting. Covers SKILL.md structure, frontmatter, progressive disclosure, description optimization, script bundling, sub-command architecture, setup gates, context systems, and review. Use when the user wants to create a skill, write a skill, build a new skill, make a skill, draft a SKILL.md, or mentions "skill-maker". Also use when asked to review a skill, audit a SKILL.md, check why a skill never triggers, improve an existing skill, or fix a skill. Also use when asked to package expertise, workflows, or domain knowledge into a reusable skill. Also use when asked to consolidate skills, merge skills, combine skills, reduce skill count, or refactor multiple skills into one.
---

<intake>

# Create, Audit, or Consolidate Skills

Create agent skills following the [Agent Skills open standard](https://agentskills.io/specification).

What do you need to do?

1. **Audit an existing skill** — Review, improve, or debug a SKILL.md
2. **Create a new skill** — Interview, draft, and review from scratch
3. **Consolidate skills** — Merge multiple skills into fewer

</intake>

<routing>

| Response | Workflow |
|----------|----------|
| 1, "audit", "review", "check", "fix", "improve" | Follow the Audit Workflow below |
| 2, "create", "write", "build", "new", "draft" | Follow Phases 1–5 below |
| 3, "consolidate", "merge", "combine" | Read `references/consolidation-guide.md` and follow its workflow. Return to Phase 5 (Review) for the final checklist. |

</routing>

## Audit Workflow

Use this workflow when reviewing, improving, or debugging an existing skill.

### Step 1: Locate and read the skill

Read the full SKILL.md and list all files in the skill directory (`references/`, `scripts/`, `templates/`, `assets/`).

### Step 2: Run the audit checklist

Check each category. Note issues as you go.

**Frontmatter:**

- [ ] `name` matches the directory name, lowercase+hyphens, max 64 chars
- [ ] `description` is under 1024 chars, non-empty, third person
- [ ] `description` includes trigger phrases (not just a summary of what the skill does)
- [ ] `description` covers edge phrasings users would actually say

**Structure:**

- [ ] SKILL.md body is under 500 lines
- [ ] Essential principles are inline in SKILL.md (not only in a reference file)
- [ ] All referenced files exist (check every path in the SKILL.md)
- [ ] References are one level deep (no nested chains: A → B → C)

**Content quality:**

- [ ] No rigid ALWAYS/NEVER rules without reasoning (explain WHY)
- [ ] No explanations of things the agent already knows from training
- [ ] Steps are specific and verifiable (not "handle errors appropriately")
- [ ] Success criteria are observable and testable
- [ ] Examples use fake data where appropriate

**Router pattern** (if applicable):

- [ ] Intake question asks what the user wants before routing
- [ ] Router table maps commands to reference files
- [ ] All referenced workflow/reference files exist
- [ ] Essential principles are in SKILL.md, not only in sub-command references
- [ ] If skill has multiple semantic sections, consider XML tags for structure (see `references/xml-structure-guide.md`)

**Scripts** (if present):

- [ ] Scripts have shebangs, `--help`, and structured output
- [ ] No interactive prompts (all input via flags/env/stdin)
- [ ] Cross-platform paths (pathlib, no hardcoded separators)
- [ ] Error messages explain what went wrong and what to do

Read `references/anti-patterns.md` for the full catalog of common failures.

### Step 3: Generate the report

Present findings grouped by severity:

1. **Critical** — skill won't trigger or produces wrong output
2. **Important** — structural issues, missing files, spec violations
3. **Minor** — style, conciseness, optimization opportunities

For each finding, state the issue, cite the specific line or section, and recommend a fix.

### Step 4: Offer fixes

Ask the user which findings to fix. Apply changes surgically — don't rewrite sections that aren't broken. Run the Phase 5 review checklist on the modified skill before finishing.

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
10. **External services and APIs.** Does the skill call external APIs or services? If yes, read `references/api-skill-patterns.md` — it covers credential handling, schema discovery, instance-specific values, and error placement.

### Architecture decision tree

After the interview questions above, decide the architecture. Most skills are simple — only escalate when the answers demand it.

**Question 1: How many distinct things can a user want to do?**

- One specific thing → **Simple skill** (single SKILL.md, under 200 lines)
- Multiple things with shared principles → continue to Q2

**Question 2: Is there shared domain knowledge across those operations?**

- No, each operation is self-contained → **Simple skill** (or multiple separate simple skills)
- Yes, multiple operations share knowledge → **Router skill** (SKILL.md + `references/`)

**Question 3: Does it cover a full lifecycle (build, debug, test, ship)?**

- No → **Router skill** is sufficient
- Yes → **Domain expertise skill** (exhaustive references, full lifecycle workflows)

| What you're building | Pattern |
|---|---|
| "A skill that commits with a conventional message" | Simple |
| "A skill that manages PRs — create, review, merge, close" | Router |
| "A skill for building and shipping macOS apps" | Domain expertise |
| "A skill that audits other skills" | Simple (upgrade to Router if it grows) |

For Router and Domain expertise patterns, also ask:

- **Does the skill need project-level context?** If every command needs the same background, design a context file pattern with a loader script.
- **Are there mandatory setup gates?** Steps that must pass before any work begins. Gates prevent generic output.
- **Does behavior vary by task type?** If so, design a register/mode system that classifies the task first, then loads different references.

Read `references/architecture-patterns.md` for implementation details of each pattern.

**Consolidation signal check:** If the interview reveals the new skill overlaps significantly with existing skills (shared scripts, cross-references, linear pipeline), consider consolidating instead of creating. Read `references/consolidation-guide.md` for the signals and workflow.

Do not proceed to Phase 2 until the user confirms the scope is complete.

## Phase 2: Draft the SKILL.md

Write the skill following the spec. Read `references/spec-guide.md` for the full format reference before drafting.

**Starter templates:** Use `templates/simple-skill.md` for single-purpose skills, `templates/router-skill.md` for multi-command skills using markdown headings, or `templates/router-skill-xml.md` for multi-command skills using XML structure. Copy the template as a starting point, then customize.

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

### Deduplication check

Before writing domain knowledge into a new reference file, check if it already exists in another reference. Shared data (exit criteria, field mappings, workflow rules) must live in exactly one file. New references should point to the existing source — not embed a copy.

Common trap: a new sub-command reference duplicates tables from an existing reference because it "needs them for context." Instead, add a one-line pointer: "Load `references/workflows.md` for exit criteria per status."

**Exception: intentional duplication.** When two sub-commands need the same query pattern but referencing each other would create a transitive loading chain (A → B → C), duplicate the pattern and add a note: "Same query pattern as X.md Step N — duplicated here to avoid transitive loading." This is cheaper than forcing the agent to load an unrelated file.

### Writing patterns

- **Imperative form**: "Run the command" not "You should run the command"
- **Explain WHY, not just what**: Avoid rigid ALWAYS/NEVER rules without reasoning. Agents generalize from principles better than from rigid rules. Instead of "ALWAYS use pdfplumber. NEVER use PyPDF2," write "Use pdfplumber over PyPDF2 — it handles malformed PDFs more gracefully and preserves layout metadata needed for table extraction." Principles adapt to edge cases; rigid rules break.
- **Don't explain what the agent already knows**: Skip basic programming concepts, standard library usage, and well-known tool behavior. Only add context the agent doesn't have — project-specific conventions, non-obvious behavior, domain-specific gotchas. A 30-token code example beats a 150-token explanation of what a library is.
- **Output templates**: Define exact formats when the output structure matters
- **Concrete examples**: Show input → output for non-obvious workflows
- **Gotchas sections**: Common mistakes the agent should avoid
- **Checklists**: Multi-step workflows with validation gates
- **Conditional loading**: "Read `references/api-errors.md` if the API returns a non-200 status code" — not "see references/ for details"
- **Absolute bans**: When certain patterns are always wrong, use match-and-refuse lists. "If you're about to write X, stop and do Y instead." More effective than vague "be careful" guidance.
- **Avoid hardcoded thresholds**: Don't write arbitrary numbers as rules (e.g., "when you have 3+ sub-commands" or "if more than 5 issues") unless the threshold comes from a real constraint (API limit, spec requirement). Instead, describe the signal that triggers the behavior (e.g., "when you're copying the same text into another sub-command"). Hardcoded numbers feel authoritative but are usually guesses that don't generalize.

Read `references/anti-patterns.md` during drafting to avoid known pitfalls.

### XML structure (router and domain expertise skills)

Agents parse XML tags more reliably than markdown headings when a skill has semantically distinct sections (principles, intake, routing, references). XML tags create unambiguous containers; markdown headings blend together in long prompts.

Read `references/xml-structure-guide.md` for suggested patterns and anti-patterns.

**When XML helps:**

- Skills with an intake question + routing table + essential principles
- Skills where an agent needs to quickly locate a specific section
- Skills with inline workflows that need clear start/end boundaries

**When markdown is enough:**

- Simple skills with a single linear workflow
- Sequential instructional content (phases, steps) where order matters more than section lookup

### Sub-command router (when applicable)

For skills with multiple distinct operations, use a router table in SKILL.md.

```xml
<intake>
## What would you like to do?

1. **Craft a feature** — Build end-to-end
2. **Audit code** — Technical quality checks

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "craft", "build" | `references/craft.md` |
| 2, "audit", "check" | `references/audit.md` |
</routing>
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
- [ ] Router/domain skills with distinct sections (intake, routing, principles) consider XML tags for clarity (`references/xml-structure-guide.md`)

### References

- [ ] Domain knowledge split into `references/` with clear "when to read" pointers
- [ ] Each reference is self-contained — no transitive loading (see `spec-guide.md` → Reference Architecture)
- [ ] Reference loading is conditional, not eager ("Read X if Y happens")
- [ ] Shared concerns (auth, config) extracted into their own reference, not embedded in a consumer
- [ ] Error handling lives in the reference for the tool that produces the error
- [ ] Multi-approach skills include a decision table routing to the correct reference
- [ ] No browser-only tools referenced (Postman, API consoles, OAuth login pages)

### Scripts

- [ ] Scripts (if any) have shebangs, structured output, and `--help`
- [ ] Context loader returns JSON, handles missing files, resolves fallback paths
- [ ] Scripts are cross-platform (pathlib, tempfile, no hardcoded paths)
- [ ] Scripts are idempotent — safe to re-run

### API/Service Skills (if applicable)

- [ ] Credential files are never read into context — passed via shell substitution only
- [ ] Credential setup is single-sourced in its own reference file
- [ ] Capability gate checks for credentials before attempting API calls
- [ ] API schema discovery is documented (OpenAPI download, GraphQL introspection, or live endpoints)
- [ ] API examples have been validated against the live endpoint
- [ ] Instance-specific values include programmatic discovery methods

### Consolidation (if merging existing skills)

- [ ] No references to old skill names anywhere in the project (`grep -rn` the entire repo)
- [ ] Router intake menus are sequentially numbered (no gaps from removed items)
- [ ] Script docstrings and `--help` text reference the new skill name, not the old ones
- [ ] Reference paths resolve correctly from each file's location (no `references/references/` nesting)
- [ ] All example files from old skills are represented in the consolidated examples
- [ ] Scripts in the same skill use consistent patterns (NO_COLOR, shell flags, TTY checks, exit codes)
- [ ] README, ADRs, and other docs updated to reflect new skill structure
- [ ] New description covers all trigger phrases from all old skills' descriptions

### Quality

- [ ] No time-sensitive information (URLs to specific versions, dates that will go stale)
- [ ] Examples use fake data where possible (emails, names, tokens) — see `spec-guide.md` → Fake Data in Examples
- [ ] Consistent terminology throughout
- [ ] Concrete examples included for non-obvious workflows
- [ ] Absolute bans defined for patterns that are always wrong
- [ ] Self-critique loops defined for build/implementation commands with explicit exit bars

<reference_index>

## Reference Index

| Reference | Load when... |
|-----------|-------------|
| `references/spec-guide.md` | Drafting a SKILL.md (Phase 2) — full format reference |
| `references/description-guide.md` | Optimizing the description (Phase 3) |
| `references/scripts-guide.md` | Writing scripts (Phase 4) |
| `references/anti-patterns.md` | Drafting or auditing — common failures to avoid |
| `references/architecture-patterns.md` | Choosing between simple, router, and domain expertise patterns |
| `references/api-skill-patterns.md` | Skill calls external APIs or services |
| `references/consolidation-guide.md` | Merging multiple skills into fewer |
| `references/xml-structure-guide.md` | Deciding on XML vs markdown structure |

</reference_index>
