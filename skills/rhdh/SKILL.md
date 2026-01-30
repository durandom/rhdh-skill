---
name: rhdh
description: Orchestrator skill for RHDH plugin development. Provides CLI tooling, activity tracking, and routes to specialized skills (overlay, etc.).
---

<cli_setup>
**Set the CLI variable for this session:**

```bash
RHDH=scripts/rhdh
```

**Get oriented (run first):**

```bash
$RHDH
```

This shows environment status, discovered repos, and available tools.
</cli_setup>

<essential_principles>

<principle name="track_activity">
Use `$RHDH log` and `$RHDH todo` to maintain context across sessions.
Log milestones with tags. Create todos when blocked on external input.
This enables resuming work without re-explaining context and builds an audit trail.
See the `<tracking_system>` section for details.
</principle>

<principle name="consult_tool_references">
**Before using JIRA or GitHub CLI**, read the corresponding reference file:
- **GitHub:** `references/github-reference.md` — PR queries, CI analysis, `/publish` triggers
- **JIRA:** `references/jira-reference.md` — JQL queries, issue creation, comment format

These contain critical gotchas (jq escaping, JQL limitations, assignee format) that prevent common errors.
</principle>

</essential_principles>

<context_scan>
**Run on invocation to understand current state:**

```bash
$RHDH
```

This checks:

- Overlay repo location and status
- rhdh-local availability
- gh CLI authentication
- Container runtime (podman/docker)

**If repos not found:** Run `$RHDH config init` to auto-detect or configure paths.
</context_scan>

<intake>
## Step 1: Run CLI

```bash
$RHDH
```

**If `needs_setup: true`:** Stop and run `$RHDH doctor` to fix setup issues.

---

## Step 2: Identify Task Type

What would you like to do?

### Overlay Repository Tasks

*For working with the rhdh-plugin-export-overlays repository*

1. **Onboard a new plugin** — Add upstream plugin to Extensions Catalog
2. **Update plugin version** — Bump to newer upstream commit/tag
3. **Fix build failure** — Debug CI/publish issues
4. **Triage overlay PRs** — Prioritize open PRs by criticality
5. **Analyze specific PR** — Check assignment, compatibility, merge readiness

### General Tasks

6. **Check environment** — Run doctor, configure paths
7. **View/search activity** — Review worklog, todos

**Wait for response before proceeding.**
</intake>

<routing>
### Doctor Route (Priority)

| Condition | Action |
|-----------|--------|
| `needs_setup: true` in CLI output | Run `$RHDH doctor` |

**Always check this first.**

### Overlay Repository Routes

| Response | Skill |
|----------|-------|
| 1-5, "onboard", "update", "fix", "triage", "PR", "overlay", "plugin", "workspace" | Route to `@overlay` skill |

**To route:** Read `../overlay/SKILL.md` and follow its intake process.

### General Routes

| Response | Action |
|----------|--------|
| 6, "doctor", "setup", "config" | Use CLI commands below |
| 7, "log", "todo", "activity" | Use tracking commands below |

</routing>

<cli_commands>
**Environment status (no args):**

```bash
$RHDH
```

Shows overlay repo, rhdh-local, tools status, and next steps.

**Full environment check:**

```bash
$RHDH doctor
```

**Configuration:**

```bash
$RHDH config init              # Create config with auto-detection
$RHDH config show              # Show resolved paths
$RHDH config set overlay /path # Set repo location
$RHDH config set local /path   # Set rhdh-local location
```

**Workspace operations:**

```bash
$RHDH workspace list           # List all plugin workspaces
$RHDH workspace status <name>  # Show workspace details
```

</cli_commands>

<tracking_system>

## Activity Tracking (Recommended)

The CLI includes worklog and todo tracking to maintain context across sessions. **Use is recommended but not required.**

### Why Track?

- **Cross-session memory** — Pick up where you left off without re-explaining context
- **Audit trail** — "When did we onboard X?" / "What happened with PR #123?"
- **Follow-up reminders** — Don't lose track of blocked items waiting on external input

### Worklog Commands

Append-only activity log stored in `.rhdh/worklog.jsonl`:

```bash
# Log activity with tags for searchability
$RHDH log add "Started onboard: aws-appsync" --tag onboard --tag aws-appsync
$RHDH log add "PR #1234 merged" --tag aws-appsync --tag pr

# View recent entries
$RHDH log show --limit 10

# Search past activity
$RHDH log search "aws-appsync"
$RHDH log search "onboard"
```

### Todo Commands

Section-based markdown todos stored in `.rhdh/TODO.md`:

```bash
# Create todo when blocked
$RHDH todo add "Check license with legal" --context "aws-appsync"
$RHDH todo add "Follow up on stale PR #1234" --context "triage"

# List and manage
$RHDH todo list              # All todos
$RHDH todo list --pending    # Only open items

# Update progress
$RHDH todo note <slug> "Sent email to legal@redhat.com"
$RHDH todo done <slug>

# View raw file
$RHDH todo show
```

### When to Track

**Log these milestones:**

- Starting/completing a workflow (onboard, update, triage)
- PR actions (opened, published, merged)
- Significant decisions or findings

**Create todos for:**

- Blocked items waiting on external response (legal, upstream, team)
- Post-merge follow-ups (verify in staging, remove workarounds)
- Items that span multiple sessions

</tracking_system>

<reference_index>
**GitHub CLI (PRs, CI, workflows):** references/github-reference.md
**JIRA CLI (issues, JQL, comments):** references/jira-reference.md
</reference_index>

<skills_index>

### Specialized Skills

| Skill | Purpose | Path |
|-------|---------|------|
| overlay | Manage plugins in rhdh-plugin-export-overlays | `../overlay/SKILL.md` |

</skills_index>
