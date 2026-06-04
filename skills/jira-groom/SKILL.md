---
name: jira-groom
description: |
  Prepare Jira tickets for autonomous agent implementation. Conversational grooming that checks whether an agent can understand and implement the work: clear problem statement, repo identification, file paths, acceptance criteria, scope (single PR), and labels. Inspired by Rehor's grooming workflow. Trigger on "groom ticket", "agent-ready", "prepare for bot", "groom RHCLOUD-1234", or any Jira key with grooming intent.
compatibility: "acli on PATH or jira-cli (jira). Jira Cloud instance."
---

<essential_principles>

# Jira Agent Grooming

Prepare Jira tickets so an autonomous agent can pick them up and implement them successfully. This is NOT sprint readiness or workflow field validation (use `rhdh-jira refine` for that). This checks whether the ticket contains enough information for an agent to:

1. Understand what to change
2. Find the right files
3. Know when it's done
4. Stay within scope

The output is an improved ticket description that a bot can act on without asking humans for clarification.

</essential_principles>

<intake>

## Usage

```
jira-groom <TICKET-KEY>           # Groom a specific ticket
jira-groom <TICKET-KEY> --quick   # Non-interactive: score + recommendations only
jira-groom --batch <JQL>          # Score multiple tickets, flag worst ones
```

**Wait for response before proceeding.**

</intake>

<routing>

### Routing rules

1. **Ticket key provided** (e.g., `RHCLOUD-12345`): Fetch the ticket → run the agent-readiness checklist → conversational grooming.
2. **Ticket key + `--quick`**: Fetch → score → print report. No conversation.
3. **`--batch` + JQL**: Fetch all matching tickets → score each → summary table sorted by readiness. No conversation.
4. **No argument**: Ask for a ticket key.

</routing>

## How It Works

### Step 1 — Fetch the ticket

Read the ticket using acli:

```bash
acli jira workitem view <KEY> --json
```

Extract: summary, description, labels, components, issue links, comments. If acli is not available, fall back to `jira issue view <KEY>` (jira-cli).

### Step 2 — Score against Agent-Readiness Checklist

Load `references/agent-readiness.md` for the full checklist. Score each dimension 0-2:

| Dimension | 0 (Fail) | 1 (Partial) | 2 (Pass) |
|-----------|----------|-------------|----------|
| **Problem clarity** | Vague or missing | Has description but ambiguous | Clear current vs expected behavior |
| **Repo identification** | No repo mentioned | Repo implied but not explicit | `repo:` label or explicit repo name |
| **File/path hints** | No file paths | General area mentioned | Specific files, components, or URL paths |
| **Acceptance criteria** | None | Implicit in description | Explicit checklist |
| **Scope** | Unclear or multi-PR | Likely single PR but not stated | Clearly scoped to one PR |
| **Type clarity** | Can't tell bug vs feature | Inferable from context | Explicit (bug with repro, feature with spec, CVE with ID) |

**Total score**: 0-12. Thresholds:

- **10-12**: Agent-ready. Proceed.
- **7-9**: Needs minor improvement. Suggest fixes.
- **0-6**: Not agent-ready. Conversational grooming required.

### Step 3 — Conversational Grooming (interactive mode)

For each dimension that scored 0 or 1, ask the user targeted questions. One question at a time — don't dump all at once. Follow the question guide in `references/agent-readiness.md`.

**Rules:**

- If the user is vague, push back. A vague ticket wastes agent time and compute.
- If the work spans 3+ repos, suggest splitting into multiple tickets.
- If the work requires human judgment (design decisions, UX direction), suggest marking it `needs-investigation` so the agent reports findings instead of guessing.
- If the user doesn't know which files are affected, that's OK — help them narrow it down by asking about the feature/page/service.

### Step 4 — Produce Improved Ticket

Generate an updated description using the template in `references/agent-readiness.md`. Present to user:

```markdown
## Suggested update

**Title**: <improved title — short, specific>

**Description**:
<structured description with all agent-relevant info>

**Labels to add**:
- repo:<name> (if identified)
- <any routing labels>

**Score**: X/12 → Y/12
```

Ask: "Apply this update to the ticket? [y/N/edit]"

- **y**: Update via `acli jira workitem edit --key <KEY> --summary "..." --yes` + description update via REST/ADF
- **N**: Done, no changes
- **edit**: Let user modify before applying

### Step 5 — Bridge hint (optional)

If the ticket scores 10+ after grooming and the user has mentioned fullsend or GitHub-based agents:

> "This ticket is agent-ready. To bridge it to a GitHub Issue for fullsend, you'll need the `jira-bridge` skill (coming soon)."

## Reference Files

| File | Load when... |
|------|-------------|
| `references/agent-readiness.md` | Always — contains the scoring rubric, question guide, and description template |

## Relationship to Other Skills

- **`rhdh-jira refine`**: Checks Jira workflow fields (component, priority, sprint readiness). Complementary — run `refine` for process compliance, `jira-groom` for agent readiness.
- **`jira-bridge`** (planned): Takes a groomed ticket and creates a GitHub Issue. `jira-groom` is the prerequisite step.

## Error Handling

| Error | Action |
|-------|--------|
| Ticket not found | "Ticket <KEY> not found. Check the key and project." |
| acli not available | Fall back to `jira issue view`. If neither available, ask user to paste the ticket description. |
| Description is empty | Score Problem clarity as 0. Ask user to describe the problem from scratch. |
| Ticket is already closed | "This ticket is already closed. Nothing to groom." |
