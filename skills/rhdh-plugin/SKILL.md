---
name: rhdh-plugin
description: Manage RHDH plugins - onboard, update, maintain, and triage plugins in the Extensions Catalog. Supports both Plugin Owners and Core Team workflows.
---

<cli_setup>
**Set the CLI variable for this session:**

```bash
RHDH_PLUGIN="${CLAUDE_PLUGIN_ROOT}/scripts/rhdh-plugin"
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

<reference_index>
**Overlay repo patterns:** references/overlay-repo.md
**CI feedback interpretation:** references/ci-feedback.md
**Metadata format:** references/metadata-format.md
**GitHub CLI queries:** references/github-queries.md
**GitHub tips & gotchas:** references/github-tips.md
**PR label priorities:** references/label-priority.md
**JIRA CLI for plugin tracking:** references/jira-reference.md
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

### Core Team Success

- PR backlog prioritized with actionable next steps
- Stale PRs identified with suggested owners
- Publish triggered on PRs needing it
- Compatibility issues flagged before merge
</success_criteria>
