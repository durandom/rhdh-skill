# Reference: GitHub Tips & Gotchas

Operational knowledge for working with GitHub CLI. Complements `github-queries.md`.

---

## jq Escaping Gotchas

### Avoid `!=` in jq expressions

Bash interprets `!` as history expansion even in double quotes:

```bash
# ❌ BROKEN - bash expands != as history reference
gh pr view 1 --jq '.reviews | map(select(.state != "COMMENTED"))'

# ✅ WORKS - use "not" pattern instead
gh pr view 1 --jq '.reviews | map(select(.state == "COMMENTED" | not))'

# ✅ WORKS - disable history expansion first
set +H && gh pr view 1 --jq '.reviews | map(select(.state != "COMMENTED"))'
```

---

## PR Status Staleness

**Critical:** `gh pr checks` and `statusCheckRollup` can be stale.

### Always verify with run list

```bash
# Get the branch name first
BRANCH=$(gh pr view <number> --repo $REPO --json headRefName --jq '.headRefName')

# Check latest run (not PR status)
gh run list --repo $REPO --branch $BRANCH --limit 3 --json databaseId,conclusion,status
```

### When PR status differs from actual CI

1. New commits pushed after checks started
2. Re-runs not reflected in PR status
3. Required checks renamed/changed

**Solution:** Trust `gh run list --branch` over `gh pr checks`.

---

## CI Failure Analysis

### Get failed logs

```bash
# Get run ID from branch (not from PR)
gh run list --repo $REPO --branch <branch> --limit 3 --json databaseId,conclusion,status

# View failed logs only
gh run view <run-id> --repo $REPO --log-failed

# Filter for errors (large logs)
gh run view <run-id> --repo $REPO --log-failed 2>&1 | grep -A 5 "Error\|FAIL" | head -50
```

### Common overlay repo failures

| Error Pattern | Likely Cause | Fix |
|--------------|--------------|-----|
| `source.json: backstage version mismatch` | `repo-backstage-version` doesn't match upstream | Update to actual upstream version |
| `CODEOWNERS: no entry for workspace` | Missing CODEOWNERS entry | Add entry for new workspace |
| `plugins-list.yaml: invalid format` | YAML syntax error | Validate YAML structure |
| `smoke test failed` | Plugin doesn't load | Check backstage.json overrides |

---

## Action Confirmation Tiers

### Auto-execute (no confirmation needed)

- Post `/publish` comment
- Add labels
- Request review
- Post informational comments

### Require confirmation

- `merge` — irreversible
- `approve` — official approval
- `close` — closes PR/issue
- Remove labels (could affect automation)

---

## Rate Limiting

### Batch operations

```bash
# Add delay between API calls
for num in 1234 1235 1236; do
  gh pr comment $num --repo $REPO --body "/publish"
  sleep 2  # Avoid rate limiting
done
```

### Check rate limit

```bash
gh api rate_limit --jq '.rate | "Remaining: \(.remaining)/\(.limit)"'
```

---

## JSON Output Best Practices

### Use `--json` + `--jq` for scripting

More stable than parsing text output:

```bash
# ✅ Stable - JSON output
gh pr list --json number,title --jq '.[] | "\(.number): \(.title)"'

# ❌ Fragile - text parsing
gh pr list | awk '{print $1, $2}'
```

### Always include `--limit` for large result sets

```bash
# ✅ Good - bounded result
gh pr list --repo $REPO --state open --limit 100

# ⚠️ Risky - unbounded (could be thousands)
gh pr list --repo $REPO --state all
```

---

## Review Decision Guide

### Approve if

- All CI checks pass
- No security issues
- Follows existing patterns
- CODEOWNERS entry present (for additions)

### Request Changes if

- Missing CODEOWNERS for new workspace
- Compatibility bypass detected (manual source.json edit)
- CI failures unresolved
- Missing required fields in config

### Close & Refine if

- Plugin fundamentally incompatible
- Duplicate of existing workspace
- Owner unresponsive (>30 days stale after pings)

---

## Overlay Repo Specific

### `/publish` comment trigger

The overlay repo uses a workflow triggered by `/publish` comment:

```bash
# Trigger publish
gh pr comment <number> --repo $REPO --body "/publish"

# Check if already triggered (look for publish check)
gh pr view <number> --repo $REPO --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.name | contains("publish"))'
```

**Guards before triggering:**

1. PR is open (not closed/merged)
2. No `do-not-merge` label
3. Publish check not already successful

### Bot-created PRs

Bot PRs (e.g., `github-actions[bot]`) can't auto-trigger workflows due to GitHub security restrictions. Always need manual `/publish`.

```bash
# Find bot PRs needing publish
gh pr list --repo $REPO --author "github-actions[bot]" --json number,title,statusCheckRollup \
  --jq '.[] | select(.statusCheckRollup | map(.name) | index("publish") == null)'
```
