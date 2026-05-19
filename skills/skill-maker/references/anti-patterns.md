# Skill Anti-Patterns

Common failures and how to fix them. Read this during Phase 2 (drafting) to avoid known pitfalls.

## Discovery Failures

### Context Selection Omission (CSO)

The description matches how the *author* thinks about the skill, not how *users* phrase requests.

**Symptom:** Skill exists but never triggers. Users rephrase until they give up.

**Example:**

```yaml
# BAD — author's mental model
description: Manages Kubernetes pod lifecycle annotations

# GOOD — how users actually ask
description: |
  Manage Kubernetes pod annotations and labels. Use when deploying,
  updating pod metadata, debugging pod scheduling, or when the user
  mentions annotations, labels, taints, tolerations, or pod spec changes.
```

**Fix:** Write should-trigger queries first (Phase 3), then write the description to match them.

### Description Summarizes the Workflow

The description explains *how* the skill works instead of *when* to use it.

**Symptom:** Description is accurate but doesn't contain the words users would say.

**Example:**

```yaml
# BAD — describes internals
description: |
  Loads project config, runs validation checks, generates a report
  with findings, and offers auto-fixes.

# GOOD — describes when to use it
description: |
  Audit agent skills for spec violations, structural issues, and
  content quality. Use when reviewing a SKILL.md, checking why a
  skill never triggers, or improving an existing skill.
```

**Fix:** Lead with the task the user wants done, not the steps the skill takes.

## Structure Failures

### Monolithic Skill

**Symptom:** Single SKILL.md over 500 lines covering multiple distinct workflows.

**Fix:** Extract workflows into `references/` files. Add a router table to SKILL.md. Each reference should be self-contained.

### Mixed Concerns

**Symptom:** Procedures and domain knowledge interleaved in the same file.

**Fix:** Procedures (step-by-step workflows) stay in SKILL.md or `references/` command files. Domain knowledge (patterns, rules, examples) goes in separate `references/` files with conditional loading.

### Nested Reference Chains

**Symptom:** Reference A says "read reference B", which says "read reference C." The agent loads three files to answer one question.

**Fix:** Each reference should be self-contained. If two references need the same data, either duplicate it with a note ("Same pattern as X.md — duplicated to avoid transitive loading") or extract the shared data into a third file that both reference directly.

## Content Failures

### Explaining What the Agent Already Knows

**Symptom:** Skill explains basic programming concepts, standard library usage, or well-known tools.

**Fix:** Trust the agent's training data. Only add context the agent doesn't already have — project-specific conventions, non-obvious tool behavior, domain-specific gotchas.

```markdown
# BAD (~150 tokens wasted)
PDF files are a common document format. To extract text from PDFs,
we use pdfplumber, a Python library. First, import it at the top
of your file. Then open the file using a context manager...

# GOOD (~30 tokens)
Extract text with pdfplumber:
  with pdfplumber.open("file.pdf") as pdf:
      text = pdf.pages[0].extract_text()
```

### Rigid Rules Without Reasoning

**Symptom:** ALWAYS/NEVER rules in all caps with no explanation of why.

**Fix:** Explain the reasoning. Agents generalize from principles better than from rigid rules. Rigid rules also break at edge cases; principles adapt.

```markdown
# BAD
ALWAYS use pdfplumber. NEVER use PyPDF2.

# GOOD
Use pdfplumber over PyPDF2 — it handles malformed PDFs more gracefully
and preserves layout metadata needed for table extraction.
```

### Vague Steps

**Symptom:** Instructions like "handle errors appropriately" or "ensure quality."

**Fix:** Be specific. Name the errors. Define the quality bar. Show the expected output.

```markdown
# BAD
Handle API errors appropriately.

# GOOD
If the API returns 401, re-check credentials. If 429, wait 60 seconds
and retry once. If 5xx, report the status code and body to the user.
```

### Untestable Success Criteria

**Symptom:** "The skill works correctly" or "output is high quality."

**Fix:** Define observable, verifiable outcomes.

```markdown
# BAD
The migration is successful.

# GOOD
Migration is complete when: all tests pass, no deprecated imports remain
(grep -rn 'old_module'), and the changelog entry exists.
```

### Offering Too Many Options

**Symptom:** Skill presents 5+ approaches and asks the user to choose.

**Fix:** Recommend the best default. Present alternatives only when the tradeoffs genuinely depend on the user's situation. Two options is usually the right number — a default and an escape hatch.

## Script Failures

### Interactive Prompts

**Symptom:** Script blocks waiting for user input; agent hangs.

**Fix:** Accept all input via flags, env vars, or stdin. Scripts must be fully non-interactive.

### Opaque Error Messages

**Symptom:** Script prints "Error" or exits silently on failure.

**Fix:** Print what went wrong, what was expected, and what the user can do about it. Use structured output (JSON with an `error` field) when the consumer is an agent.

### Absolute Script Paths

**Symptom:** Script references `/Users/alice/.skills/mything/scripts/helper.py`.

**Fix:** Use relative paths from the skill directory. Reference scripts as `scripts/helper.py` in SKILL.md.

## Routing Failures

### Missing Intake Question

**Symptom:** Router skill launches into the first workflow without asking what the user wants.

**Fix:** Wrap the menu in `<intake>` and the routing table in `<routing>`. Ask first, then route:

```xml
<intake>
What would you like to do?
1. **Command A** — description
2. **Command B** — description

**Wait for response before proceeding.**
</intake>
```

Support both menu selection and intent-based routing for users who skip the menu.

### Broken References

**Symptom:** Router table points to files that don't exist, or file paths are wrong.

**Fix:** After writing the router table, verify every referenced file exists. Use consistent paths (`references/command.md`, not `./references/command.md` or `references/commands/command.md`).

### Redundant Content

**Symptom:** Same instructions appear in SKILL.md and in a referenced workflow file.

**Fix:** Single-source everything. If principles must always apply, they live in SKILL.md. If instructions are command-specific, they live in the reference file. Never both.
