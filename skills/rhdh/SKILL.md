---
name: rhdh
description: Orchestrator skill for RHDH plugin development. Provides CLI tooling, activity tracking, and routes to specialized skills (overlay, etc.).
---

<cli_setup>
**Locate and set the CLI variable:**

The CLI script is at `scripts/rhdh` **relative to this SKILL.md file** (not the working directory).

When you read this file, note its path and derive the script location:

- If SKILL.md is at `/path/to/skills/rhdh/SKILL.md`
- Then the CLI is at `/path/to/skills/rhdh/scripts/rhdh`

```bash
RHDH="/path/to/skills/rhdh/scripts/rhdh"  # Use the actual path
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

### Plugin Creation Tasks

*For creating new RHDH dynamic plugins from scratch*

6. **Create backend plugin** — Bootstrap a new backend dynamic plugin
7. **Create frontend plugin** — Bootstrap a new frontend dynamic plugin
8. **Export and package plugin** — Export plugin and package as OCI/tgz/npm
9. **Configure frontend wiring** — Set up mount points, routes, entity tabs

### General Tasks

10. **Check environment** — Run doctor, configure paths
11. **View/search activity** — Review worklog, todos

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

### Plugin Creation Routes

| Response | Skill |
|----------|-------|
| 6, "backend plugin", "create backend", "new backend plugin" | Route to `@create-backend-plugin` skill |
| 7, "frontend plugin", "create frontend", "new frontend plugin" | Route to `@create-frontend-plugin` skill |
| 8, "export", "package", "OCI", "publish plugin" | Route to `@export-and-package` skill |
| 9, "wiring", "mount points", "routes", "entity tabs" | Route to `@generate-frontend-wiring` skill |

**To route:** Read the corresponding skill file in `../` and follow its workflow.

### General Routes

| Response | Action |
|----------|--------|
| 10, "doctor", "setup", "config" | Use CLI commands below |
| 11, "log", "todo", "activity" | Use tracking commands below |

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

### Writing Effective Todos

Todos must be **self-contained**—a new session should understand the task without re-investigating.

| ❌ Too vague | ✅ Actionable |
|-------------|---------------|
| Fix #1875 version mismatch | Fix #1875 (lightspeed): bump `1.3.0→1.4.0` in `workspace.yaml` like #1903 |
| Add /ok-to-test to #1921 | Add /ok-to-test to #1921 (techdocs) — smoke tests ready, needs external trigger |
| Review #1906 SonarCloud | Review #1906 (catalog): SonarCloud blocked on coverage — check if test file missing |

**Include:** PR number, plugin name, specific action, and *why* it's needed.

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
| create-backend-plugin | Bootstrap new RHDH backend dynamic plugins | `../create-backend-plugin/SKILL.md` |
| create-frontend-plugin | Bootstrap new RHDH frontend dynamic plugins | `../create-frontend-plugin/SKILL.md` |
| export-and-package | Export and package plugins as OCI/tgz/npm | `../export-and-package/SKILL.md` |
| generate-frontend-wiring | Configure frontend mount points, routes, tabs | `../generate-frontend-wiring/SKILL.md` |

### Shared References

| Reference | Purpose | Path |
|-----------|---------|------|
| versions | RHDH/Backstage version compatibility matrix | `references/versions.md` |

</skills_index>
