# Workflow: Onboard a Plugin to RHDH Extensions Catalog

Add a new Backstage plugin to the RHDH Extensions Catalog via the overlay repository.

<required_reading>
**Read these reference files NOW:**
1. `references/overlay-repo.md` — Workspace patterns and examples
2. `references/ci-feedback.md` — Interpreting publish workflow output
</required_reading>

<prerequisites>
| Requirement | Details |
|-------------|---------|
| **Access** | Write access to [rhdh-plugin-export-overlays](https://github.com/redhat-developer/rhdh-plugin-export-overlays) |
| **Tools** | `git`, `gh` CLI |
| **Knowledge** | Basic understanding of Backstage plugins and dynamic plugin format |
</prerequisites>

<process>

## Phase 1: Discovery & Evaluation

**Goal:** Verify the plugin is suitable for RHDH integration.

### 1.1 Identify Upstream Source

- [ ] Locate upstream repository URL
- [ ] Identify specific plugin path within repo (monorepo structure common)
- [ ] Note the package name(s) to export

**What to look for:**
- Most plugins live in monorepos under `plugins/<name>/` with `frontend`, `backend`, `common` subdirs
- Package names often follow `@<org>/<plugin-name>` and `@<org>/<plugin-name>-backend` pattern

### 1.2 License Check

- [ ] Verify license is Apache 2.0 or compatible
- [ ] Document license in evaluation notes

**Compatible licenses:**
- ✅ Apache 2.0 (preferred)
- ✅ MIT, BSD-2-Clause, BSD-3-Clause, ISC
- ⚠️ MPL-2.0 (review needed - weak copyleft)
- ❌ GPL, LGPL, AGPL (copyleft - not compatible)
- ❌ Proprietary, no license specified

### 1.3 Upstream Health

- [ ] Check last commit date (activity within 6 months preferred)
- [ ] Review open issues/PRs for red flags
- [ ] Identify maintainer responsiveness

**Quick health check commands:**
```bash
# Last commit date
gh api repos/<owner>/<repo>/commits?per_page=1 --jq '.[0].commit.committer.date'

# Open issues count
gh api repos/<owner>/<repo> --jq '.open_issues_count'

# Recent releases
gh release list -R <owner>/<repo> --limit 5
```

### 1.4 Backstage Version Compatibility

- [ ] Check upstream's `backstage.json` or `package.json` for Backstage version
- [ ] Compare against RHDH target version in [versions.json](https://github.com/redhat-developer/rhdh-plugin-export-overlays/blob/main/versions.json)
- [ ] Document any version gaps

**Version gap guidance:**
- Minor version gaps (e.g., 1.43 → 1.45) are typically safe
- Major version gaps require careful review of breaking changes

### 1.5 Decision Gate

| Criteria | Status |
|----------|--------|
| License compatible | |
| Upstream active | |
| Backstage version aligned | |

**Proceed?** Yes / No (document reason if No)

---

## Phase 2: Workspace Creation

**Goal:** Create the workspace folder structure in the overlay repo.

### 2.1 Clone and Branch

```bash
cd repo/rhdh-plugin-export-overlays  # or clone fresh
git fetch upstream
git checkout main && git pull upstream main
git checkout -b add-<plugin-name>-workspace
```

### 2.2 Create Workspace Folder

```bash
mkdir -p workspaces/<workspace-name>
```

**Naming convention:** Use upstream scope/name, e.g., `aws-codebuild`, `backstage-community-techdocs`

### 2.3 Create `source.json`

See `templates/workspace-files.md` for the template.

**Key fields:**
- `repo` - Upstream GitHub URL (only `https://github.com/xxx` supported)
- `repo-ref` - Target commit SHA or tag
- `repo-flat` - `true` if plugins at repo root, `false` if inside workspace folder
- `repo-backstage-version` - Backstage version from upstream

**Validate upstream version:**
```bash
curl -s https://raw.githubusercontent.com/<owner>/<repo>/<commit>/backstage.json | jq .version
```

### 2.4 Create `plugins-list.yaml`

See `templates/workspace-files.md` for the template.

**Key patterns:**
- Path format: `plugins/<name>/frontend:` or `plugins/<name>/backend:`
- Use `--embed-package` for shared dependencies not published separately

### 2.5 (Optional) Create `backstage.json`

Usually not needed on first attempt. The CI will tell you if a version override is required.

**When CI says "incompatible workspaces":**
1. Add `backstage.json` with RHDH's target version
2. Keep `source.json`'s `repo-backstage-version` as the upstream's actual version

### 2.6 Add CODEOWNERS Entry

```bash
echo "/workspaces/<workspace-name>/ @<your-github-username>" >> CODEOWNERS
```

---

## Phase 3: PR & Build

**Goal:** Open PR, trigger build, pass smoke tests.

### 3.1 Commit and Push

```bash
git add .
git commit -m "Add <plugin-name> workspace"
git push -u origin add-<plugin-name>-workspace
```

### 3.2 Open Pull Request

```bash
gh pr create \
  --title "Add <plugin-name> workspace" \
  --body "## Summary
- Adds <plugin-name> plugin to RHDH Extensions Catalog
- Upstream: <upstream-url>
- License: Apache 2.0

## Checklist
- [ ] source.json created
- [ ] plugins-list.yaml created
- [ ] CODEOWNERS updated"
```

### 3.3 Trigger Build

1. Comment `/publish` on the PR
2. **Watch PR comments** — automation reports:
   - Compatibility issues with suggested fixes
   - Published OCI images on success
   - Failures with actionable guidance
3. If issues arise, see `references/ci-feedback.md`
4. Re-trigger with `/publish` after fixes

---

## Phase 4: Plugin Metadata

**Goal:** Create metadata files for integration tests and catalog registration.

### 4.1 Create Package Metadata Files

Create one YAML file per exported plugin in `workspaces/<name>/metadata/`.

**Kind:** `Package` — represents a single npm package (frontend or backend)

**Documentation:** [catalog-entities/marketplace/README.md](https://github.com/redhat-developer/rhdh-plugin-export-overlays/blob/main/catalog-entities/marketplace/README.md)

### 4.2 Create Plugin Entity

Create a Plugin entity that groups your packages together.

**Kind:** `Plugin` — user-facing catalog entry

**Location:** `catalog-entities/marketplace/plugins/<plugin-name>.yaml`

**Key fields:**
- `metadata.name` — short identifier
- `metadata.description` — brief summary
- `spec.description` — full markdown documentation
- `spec.packages` — list of Package names
- `spec.categories` — for filtering (e.g., `CI/CD`, `Cloud`)

### 4.3 Trigger Build & Tests

```bash
git add workspaces/<name>/metadata/ catalog-entities/marketplace/plugins/<name>.yaml
git commit -m "Add plugin metadata"
git push
```

Comment `/publish` to rebuild. Watch for test workflow results.

---

## Phase 5: Verification

**Goal:** Confirm plugin works using PR artifacts (before merge).

### 5.1 Set Up Local Test Environment

Use [RHDH Local](https://github.com/redhat-developer/rhdh-local):

```bash
cd repo/rhdh-local
podman compose up -d
# Access at http://localhost:7007
```

### 5.2 Configure PR Artifacts

Create `configs/dynamic-plugins/dynamic-plugins.override.yaml`:

```yaml
includes:
  - dynamic-plugins.default.yaml

plugins:
  - package: oci://<registry>/<image>:pr_<number>__<version>!<package-name>
    disabled: false
    pluginConfig:
      # Copy from metadata/*.yaml appConfigExamples
```

### 5.3 Create Test Entity

Most plugins require specific annotations. Create `configs/catalog-entities/components.override.yaml`:

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: test-<plugin-name>
  annotations:
    <annotation-key>: <test-value>
spec:
  type: service
  lifecycle: experimental
  owner: user:default/guest
```

### 5.4 Verify Plugin Works

- [ ] Check logs: `podman logs rhdh 2>&1 | grep -i <plugin-name>`
- [ ] Plugin loads without errors
- [ ] Navigate to test entity in catalog
- [ ] Plugin UI renders (card, tab, page)
- [ ] No console errors (browser DevTools)

**Success:** Plugin renders and attempts API calls. Auth errors expected without real credentials.

### 5.5 Update PR Description

Add verification results to PR description (not comments).

### 5.6 Local Cleanup

- [ ] Remove test override files (don't commit to rhdh-local)
- [ ] Stop rhdh-local: `podman compose down`

---

## Phase 6: PR Approval & Merge

**Goal:** Get PR reviewed and merged.

### 6.1 Request Review

- [ ] Request review from CODEOWNERS
- [ ] For first workspace PR, request from cope team

### 6.2 Address Feedback & Merge

- [ ] Respond to review comments
- [ ] Re-trigger `/publish` after significant changes
- [ ] Merge when all checks pass

### 6.3 Close Out JIRA

After merge, update the JIRA ticket with summary and transition to Closed.

</process>

<action_triggers>
| Trigger | Type | What to Do | Resume When |
|---------|------|------------|-------------|
| License policy unclear | 👥 Sync | Check with team on acceptable licenses | Policy confirmed |
| Support tier assignment | 👥 Sync | Ask team: which `rhdh-*-packages.txt` file? | Tier confirmed |
| CI failure unclear | 📖 Reference | Check `references/ci-feedback.md` | Issue understood |
</action_triggers>

<success_criteria>
This workflow is complete when:
- [ ] Workspace created with source.json + plugins-list.yaml
- [ ] `/publish` succeeds with OCI images
- [ ] Metadata files created (Package + Plugin entities)
- [ ] Plugin tested locally with rhdh-local
- [ ] PR reviewed and merged
- [ ] JIRA ticket closed
</success_criteria>
