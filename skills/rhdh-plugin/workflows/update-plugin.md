# Workflow: Update Plugin Version

Bump a plugin to a newer upstream commit or tag.

<required_reading>
**Read these reference files NOW:**
1. `references/overlay-repo.md` — Workspace patterns
2. `references/ci-feedback.md` — Interpreting publish output
</required_reading>

<prerequisites>
- Existing workspace in overlay repo
- New upstream version identified (commit SHA or tag)
</prerequisites>

<process>

## Step 1: Identify New Version

```bash
# Check upstream releases
gh release list -R <owner>/<repo> --limit 10

# Or recent commits
gh api repos/<owner>/<repo>/commits?per_page=5 --jq '.[].sha'
```

- [ ] Note new commit SHA or tag
- [ ] Check upstream's `backstage.json` at that commit

## Step 2: Update source.json

```bash
cd workspaces/<name>/
```

Update `source.json`:
- `repo-ref` → new commit SHA or tag
- `repo-backstage-version` → upstream's Backstage version at that commit

## Step 3: Update backstage.json (if needed)

If upstream's Backstage version changed significantly, may need to update override.

## Step 4: Create PR

```bash
git checkout -b update-<plugin-name>-<version>
git add .
git commit -m "Update <plugin-name> to <version>"
git push -u origin update-<plugin-name>-<version>

gh pr create \
  --title "Update <plugin-name> to <version>" \
  --body "Bumps <plugin-name> from <old> to <new>."
```

## Step 5: Trigger Build

Comment `/publish` and verify success.

## Step 6: Test and Merge

Follow Phase 5-6 from `workflows/onboard-plugin.md`.

</process>

<success_criteria>
- [ ] source.json updated with new ref
- [ ] `/publish` succeeds
- [ ] PR merged
</success_criteria>
