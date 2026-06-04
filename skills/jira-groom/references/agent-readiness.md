# Agent-Readiness Checklist

Scoring rubric, question guide, and description template for grooming Jira tickets for autonomous agent implementation. Derived from Rehor's grooming workflow (platform-frontend-ai-dev) and adapted for general use.

## Scoring Rubric

### 1. Problem Clarity (0-2)

What the agent needs: a clear understanding of what is wrong or what should change.

| Score | Criteria |
|-------|----------|
| 0 | No description, or description is a single sentence with no actionable detail ("fix the notifications page") |
| 1 | Description exists but is ambiguous — multiple interpretations possible, no current/expected behavior distinction |
| 2 | Clear problem statement: current behavior vs expected behavior (bugs), or specific feature spec (features), or CVE ID + affected package (security) |

**Questions to ask at score 0-1:**

- "What's the current behavior? What do you see happening now?"
- "What should happen instead? What does 'fixed' look like?"
- "Is this a bug (something broken), a feature (something new), or a change (something works but should work differently)?"
- For bugs: "Can you reproduce it? What are the steps?"
- For CVEs: "What's the CVE ID? Which package/dependency is affected?"

### 2. Repo Identification (0-2)

What the agent needs: which repository to clone and work in.

| Score | Criteria |
|-------|----------|
| 0 | No repository mentioned anywhere in the ticket |
| 1 | Repository implied (e.g., mentions a component name or URL path that maps to a known repo) but not explicit |
| 2 | Explicit `repo:<name>` label, or repo name/URL in description |

**Questions to ask at score 0-1:**

- "Which repository does this change belong in?"
- "Which page or URL is affected?" (narrow down frontend repo)
- "Which service handles this?" (narrow down backend repo)
- "Does the fix span multiple repos? If so, which ones?"

### 3. File/Path Hints (0-2)

What the agent needs: where to start looking. Without this, the agent wastes tool calls searching the entire codebase.

| Score | Criteria |
|-------|----------|
| 0 | No file paths, component names, or URL paths mentioned |
| 1 | General area mentioned ("the notification settings page", "the auth module") but no specific files |
| 2 | Specific file paths, component names, function names, or URL routes (e.g., `/settings/notifications`, `src/components/NotificationPrefs.tsx`) |

**Questions to ask at score 0-1:**

- "Do you know which file(s) need to change?"
- "What's the URL path where this issue is visible?" (for frontend)
- "Which component or module is involved?"
- "If you've debugged this before, what did you find?"

**Note:** Score 1 is acceptable for many tickets — the agent can find files from component names. Score 0 means the agent will spend significant time just locating the right code.

### 4. Acceptance Criteria (0-2)

What the agent needs: how to know when it's done.

| Score | Criteria |
|-------|----------|
| 0 | No acceptance criteria, no definition of done |
| 1 | Acceptance criteria implied in description but not explicit (e.g., "the button should be red" buried in a paragraph) |
| 2 | Explicit checklist of verifiable criteria (e.g., "- [ ] Button changes color to red on hover", "- [ ] Unit test added for new validation") |

**Questions to ask at score 0-1:**

- "How will you verify this is done? What should a reviewer check?"
- "Are there edge cases to handle?"
- "Should there be tests? What should they cover?"
- "Is there a visual change? Can you attach a screenshot or mockup?"

### 5. Scope (0-2)

What the agent needs: confidence that the work fits in a single PR.

| Score | Criteria |
|-------|----------|
| 0 | Scope unclear — could be a 5-line fix or a 500-line refactor. Or explicitly multi-PR without decomposition |
| 1 | Likely single PR but not stated — reasonable inference from description |
| 2 | Clearly scoped: single concern, single repo, bounded change set. Or explicitly stated "single PR" |

**Questions to ask at score 0:**

- "How big do you think this change is? A few lines, a few files, or a larger refactor?"
- "Can this be done in a single PR, or should we split it?"
- "Are there dependencies — does something else need to land first?"

**When to suggest splitting:**

- Work spans 3+ repos
- Description contains "and also..." or "while we're at it..."
- Estimated change touches 10+ files across unrelated modules
- Mix of bug fix + feature work

### 6. Type Clarity (0-2)

What the agent needs: which problem-solving approach to use.

| Score | Criteria |
|-------|----------|
| 0 | Can't tell if this is a bug, feature, refactor, CVE, or investigation |
| 1 | Type inferable from context but not explicit |
| 2 | Explicitly stated: bug with reproduction steps, feature with spec, CVE with ID, investigation with questions to answer |

**Questions to ask at score 0:**

- "Is this a bug fix, a new feature, a refactor, or a security fix?"
- For unclear bugs: "Can you describe the steps to reproduce?"
- For unclear features: "Is there a design or mockup?"

## Description Template

Use this template when rewriting the ticket description. Not all sections apply to every ticket — omit sections that aren't relevant.

```
## Problem

<What is wrong or what needs to change. For bugs: current behavior vs expected behavior. For features: what should exist that doesn't. For CVEs: CVE ID, affected package, version.>

## Context

<Why this matters. Impact on users, systems, or other teams. Any relevant history or prior attempts.>

## Location

<Which repo(s), file(s), component(s), URL path(s) are involved. Be as specific as possible.>

## Acceptance Criteria

- [ ] <Verifiable criterion 1>
- [ ] <Verifiable criterion 2>
- [ ] <Tests: what should be tested>
- [ ] <Edge cases to handle>

## Notes for the Agent

<Anything that helps the agent avoid wrong turns: "Don't touch the legacy auth flow", "The test suite uses vitest not jest", "This component uses PatternFly 6". Only include if non-obvious.>
```

## Batch Scoring Output

When running `--batch`:

```markdown
## Agent-Readiness Scores

| # | Key | Summary | Score | Problem | Repo | Files | AC | Scope | Type | Verdict |
|---|-----|---------|-------|---------|------|-------|----|-------|------|---------|
| 1 | KEY-123 | Fix notification... | 4/12 | 0 | 1 | 0 | 1 | 1 | 1 | Needs grooming |
| 2 | KEY-456 | Add dark mode... | 11/12 | 2 | 2 | 2 | 2 | 1 | 2 | Agent-ready |

### Summary
- Agent-ready (10+): 3 tickets
- Needs minor work (7-9): 5 tickets
- Needs grooming (0-6): 2 tickets

### Worst offenders (groom these first)
1. KEY-123 (4/12): Missing problem description and file paths
2. KEY-789 (5/12): No acceptance criteria, scope unclear
```

## Anti-patterns

Things that make tickets bad for agents:

| Anti-pattern | Why it's bad | Fix |
|--------------|-------------|-----|
| "Fix the X page" | Agent doesn't know what's broken | Add current vs expected behavior |
| Screenshot-only description | Agent can't read screenshots reliably | Add text description alongside screenshot |
| "See Slack thread" with link | Agent may not have Slack access | Copy relevant context into ticket |
| "Similar to PROJ-999" | Agent needs self-contained tickets | Copy the relevant parts, don't just reference |
| Multi-concern tickets | Agent produces unfocused PRs | Split into separate tickets |
| "Refactor X while fixing Y" | Mixes cleanup with bugfix | Separate tickets: fix first, refactor second |
| Implementation instructions | Over-constrains the agent, may be wrong | Describe the problem and outcome, not the solution |
