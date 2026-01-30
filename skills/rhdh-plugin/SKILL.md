---
name: rhdh-plugin
description: Manage RHDH plugins - onboard, update, maintain, and triage plugins in the Extensions Catalog. Supports both Plugin Owners and Core Team workflows.
---

<cli_setup>
**Set the CLI variable for this session:**

```bash
RHDH_PLUGIN=scripts/rhdh-plugin
```

**Get oriented (run first):**

```bash
$RHDH_PLUGIN
```

This shows environment status, discovered repos, and available tools.
</cli_setup>

<essential_principles>

<principle name="overlay_repo_pattern">
All plugin exports go through [rhdh-plugin-export-overlays](https://github.com/redhat-developer/rhdh-plugin-export-overlays).
Each plugin lives in a workspace folder with `source.json` + `plugins-list.yaml`.
CI handles the actual export - we define the configuration.
</principle>

<principle name="version_fields">
Two Backstage version fields serve different purposes:
- `source.json` → `repo-backstage-version` = upstream's **actual** version
- `backstage.json` → `version` = our **override** for RHDH compatibility

Never confuse these. CI validates the source.json value matches upstream.
</principle>

<principle name="test_with_pr_artifacts">
Always test with PR artifacts before merge using rhdh-local.
OCI format: `oci://<registry>/<image>:pr_<number>__<version>!<package-name>`
Success = plugin loads and attempts API calls (auth errors are expected without real credentials).
</principle>

<principle name="copy_similar_workspaces">
When stuck, find a similar workspace and copy its patterns.
AWS plugins → copy from `aws-ecs/` or `aws-codebuild/`
Community plugins → copy from `backstage/`
Check existing PRs for structure examples.
</principle>

<principle name="track_activity">
Use `$RHDH_PLUGIN log` and `$RHDH_PLUGIN todo` to maintain context across sessions.
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
$RHDH_PLUGIN
```

This checks:

- Overlay repo location and status
- rhdh-local availability
- gh CLI authentication
- Container runtime (podman/docker)

**If repos not found:** Run `$RHDH_PLUGIN config init` to auto-detect or configure paths.
</context_scan>

<intake>
## Step 1: Run CLI

```bash
$RHDH_PLUGIN
```

**If `needs_setup: true`:** Stop and follow the setup instructions in the output. Resume after setup completes.

---

## Step 2: Identify Role

What would you like to do?

### Plugin Owner Tasks

*For contributors managing their own plugin(s)*

1. **Onboard a new plugin** — Add upstream plugin to Extensions Catalog
2. **Update plugin version** — Bump to newer upstream commit/tag
3. **Check plugin status** — Verify health and compatibility
4. **Fix build failure** — Debug CI/publish issues

### Core Team Tasks

*For COPE/Plugins team managing the overlay repository*

5. **Triage overlay PRs** — Prioritize open PRs by criticality
6. **Analyze specific PR** — Check assignment, compatibility, merge readiness
7. **Trigger publish** — Add /publish comment to PR(s)

**Wait for response before proceeding.**
</intake>

<routing>
### Doctor Route (Priority)

| Condition | Workflow |
|-----------|----------|
| `needs_setup: true` in CLI output | `workflows/doctor.md` |

**Always check this first.** Do not proceed to task workflows if setup is needed.

### Plugin Owner Routes

| Response | Workflow |
|----------|----------|
| 1, "onboard", "add", "new plugin", "import" | `workflows/onboard-plugin.md` |
| 2, "update", "bump", "upgrade", "version" | `workflows/update-plugin.md` |
| 3, "status", "check", "health" | Run inline status checks |
| 4, "fix", "debug", "failure", "error" | `workflows/fix-build.md` |

### Core Team Routes

| Response | Workflow |
|----------|----------|
| 5, "triage", "prioritize", "backlog" | `workflows/triage-prs.md` |
| 6, "analyze", "check PR", "PR #" | `workflows/analyze-pr.md` |
| 7, "publish", "trigger" | Run inline publish trigger |

**After reading the workflow, follow it exactly.**
</routing>

<inline_status_check>
For status checks, use the CLI:

```bash
$RHDH_PLUGIN workspace list              # List all workspaces
$RHDH_PLUGIN workspace status <name>     # Check specific workspace
```

Or run direct commands:

```bash
# Recent CI runs
gh run list --repo redhat-developer/rhdh-plugin-export-overlays --limit 5

# Open PRs for workspace
gh pr list --repo redhat-developer/rhdh-plugin-export-overlays --search "<name>"
```

</inline_status_check>

<inline_publish_trigger>
For triggering publish on one or more PRs:

```bash
REPO="redhat-developer/rhdh-plugin-export-overlays"

# Single PR
gh pr comment <number> --repo $REPO --body "/publish"

# Check if publish already ran
gh pr view <number> --repo $REPO --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.name | contains("publish"))'
```

**Guards before triggering:**

1. PR is open (not closed/merged)
2. No `do-not-merge` label
3. Publish check not already successful

See `references/github-queries.md` for full patterns.
</inline_publish_trigger>

<cli_commands>
**Invocation:** Set the variable for this session:

```bash
RHDH_PLUGIN="${CLAUDE_PLUGIN_ROOT}/scripts/rhdh-plugin"
```

**Environment status (no args):**

```bash
$RHDH_PLUGIN
```

Shows overlay repo, rhdh-local, tools status, and next steps.

**Full environment check:**

```bash
$RHDH_PLUGIN doctor
```

**Configuration:**

```bash
$RHDH_PLUGIN config init              # Create config with auto-detection
$RHDH_PLUGIN config show              # Show resolved paths
$RHDH_PLUGIN config set overlay /path # Set repo location
$RHDH_PLUGIN config set local /path   # Set rhdh-local location
```

**Workspace operations:**

```bash
$RHDH_PLUGIN workspace list           # List all plugin workspaces
$RHDH_PLUGIN workspace status <name>  # Show workspace details
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

Append-only activity log stored in `.rhdh-plugin/worklog.jsonl`:

```bash
# Log activity with tags for searchability
$RHDH_PLUGIN log add "Started onboard: aws-appsync" --tag onboard --tag aws-appsync
$RHDH_PLUGIN log add "PR #1234 merged" --tag aws-appsync --tag pr

# View recent entries
$RHDH_PLUGIN log show --limit 10

# Search past activity
$RHDH_PLUGIN log search "aws-appsync"
$RHDH_PLUGIN log search "onboard"
```

### Todo Commands

Section-based markdown todos stored in `.rhdh-plugin/TODO.md`:

```bash
# Create todo when blocked
$RHDH_PLUGIN todo add "Check license with legal" --context "aws-appsync"
$RHDH_PLUGIN todo add "Follow up on stale PR #1234" --context "triage"

# List and manage
$RHDH_PLUGIN todo list              # All todos
$RHDH_PLUGIN todo list --pending    # Only open items

# Update progress
$RHDH_PLUGIN todo note <slug> "Sent email to legal@redhat.com"
$RHDH_PLUGIN todo done <slug>

# View raw file
$RHDH_PLUGIN todo show
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

### Session Logs

For comprehensive session documentation, use the `/session-log` command:

```bash
/session-log <descriptive-name>
```

This creates a detailed markdown document in `.rhdh-plugin/logs/` capturing:

- Work completed (files, PRs, decisions)
- Remaining work with file:line context
- Blockers and open questions
- Resumption context for future sessions

**Use session logs when:**

- Finishing a significant work session (onboarding complete, major PR merged)
- Stopping mid-task and need to hand off or resume later
- Creating an audit trail of complex multi-session work

Session logs complement the quick `log add` entries—logs are for activity tracking, session logs are for narrative context.

### Example Session

```bash
# Starting work
$RHDH_PLUGIN log add "Starting onboard: backstage-plugin-todo" --tag onboard

# Hit a blocker
$RHDH_PLUGIN todo add "Clarify MIT+Apache dual license with legal" --context "backstage-plugin-todo"
$RHDH_PLUGIN log add "Paused onboard: license review needed" --tag onboard --tag blocked

# Later, resuming
$RHDH_PLUGIN log search "backstage-plugin-todo"  # Recall context
$RHDH_PLUGIN todo list --pending                  # See blockers

# After resolution
$RHDH_PLUGIN todo note clarify-mit "Legal approved - attribution required"
$RHDH_PLUGIN todo done clarify-mit
$RHDH_PLUGIN log add "Resumed onboard: license approved" --tag onboard
```

**Each workflow file includes a `<tracking>` section with specific commands for that workflow.**

</tracking_system>

<reference_index>
**GitHub CLI (PRs, CI, workflows):** references/github-reference.md
**JIRA CLI (issues, JQL, comments):** references/jira-reference.md
**Overlay repo patterns:** references/overlay-repo.md
**CI feedback interpretation:** references/ci-feedback.md
**Metadata format:** references/metadata-format.md
**PR label priorities:** references/label-priority.md
**RHDH Local testing:** references/rhdh-local.md
</reference_index>

<workflows_index>

### Plugin Owner Workflows

| Workflow | Purpose |
|----------|---------|
| onboard-plugin.md | Full 6-phase process to add new plugin |
| update-plugin.md | Bump to newer upstream version |
| fix-build.md | Debug and resolve CI failures |

### Core Team Workflows

| Workflow | Purpose |
|----------|---------|
| triage-prs.md | Prioritize open PRs by criticality |
| analyze-pr.md | Deep-dive on single PR (assignment, compat, readiness) |
</workflows_index>

<templates_index>

| Template | Purpose |
|----------|---------|
| workspace-files.md | source.json, plugins-list.yaml, backstage.json |
</templates_index>

<success_criteria>

### Plugin Owner Success

- Plugin workspace created with correct structure
- CODEOWNERS entry added for the workspace
- CI passes (`/publish` succeeds)
- Plugin tested locally with rhdh-local
- PR merged to overlay repo
- *(Recommended)* Activity logged for future reference

### Core Team Success

- PR backlog prioritized with actionable next steps
- Stale PRs identified with suggested owners
- Publish triggered on PRs needing it
- Compatibility issues flagged before merge
- *(Recommended)* Triage session logged, follow-ups tracked as todos
</success_criteria>
