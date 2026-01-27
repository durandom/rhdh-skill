---
name: rhdh-plugin
description: Manage RHDH plugins - onboard, update, and maintain plugins in the Extensions Catalog. Use when working with plugin workspaces, overlay repo PRs, or plugin lifecycle tasks.
---

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
# Check if in overlay repo
[ -f versions.json ] && echo "IN_OVERLAY_REPO"

# Check for existing workspaces
ls workspaces/ 2>/dev/null | head -10

# Check current branch
git branch --show-current 2>/dev/null
```

**If not in overlay repo:** Guide user to clone or navigate to it.
</context_scan>

<intake>
What would you like to do?

1. **Onboard a new plugin** — Add upstream plugin to Extensions Catalog
2. **Update plugin version** — Bump to newer upstream commit/tag
3. **Check plugin status** — Verify health and compatibility
4. **Fix build failure** — Debug CI/publish issues

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "onboard", "add", "new plugin", "import" | `workflows/onboard-plugin.md` |
| 2, "update", "bump", "upgrade", "version" | `workflows/update-plugin.md` |
| 3, "status", "check", "health" | Run inline status checks |
| 4, "fix", "debug", "failure", "error" | `workflows/fix-build.md` |

**After reading the workflow, follow it exactly.**
</routing>

<inline_status_check>
For status checks, run these commands and report findings:

```bash
# Plugin workspace status
ls -la workspaces/<name>/

# Recent CI runs
gh run list --repo redhat-developer/rhdh-plugin-export-overlays --limit 5

# Open PRs for workspace
gh pr list --repo redhat-developer/rhdh-plugin-export-overlays --search "<name>"
```
</inline_status_check>

<reference_index>
**Overlay repo patterns:** references/overlay-repo.md
**CI feedback interpretation:** references/ci-feedback.md
**Metadata format:** references/metadata-format.md
</reference_index>

<workflows_index>
| Workflow | Purpose |
|----------|---------|
| onboard-plugin.md | Full 6-phase process to add new plugin |
| update-plugin.md | Bump to newer upstream version |
| fix-build.md | Debug and resolve CI failures |
</workflows_index>

<templates_index>
| Template | Purpose |
|----------|---------|
| workspace-files.md | source.json, plugins-list.yaml, backstage.json |
</templates_index>

<success_criteria>
This skill succeeds when:
- Plugin workspace created with correct structure
- CI passes (`/publish` succeeds)
- Plugin tested locally with rhdh-local
- PR merged to overlay repo
</success_criteria>
