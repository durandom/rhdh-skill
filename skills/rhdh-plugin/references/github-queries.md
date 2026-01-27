# Reference: GitHub CLI Queries

Common `gh` CLI patterns for working with the overlay repository.

<overview>
The `gh` CLI is the primary tool for PR analysis and actions.
All queries assume: `REPO="redhat-developer/rhdh-plugin-export-overlays"`
</overview>

## PR Listing

### All Open PRs

```bash
gh pr list --repo $REPO --state open --limit 100 \
  --json number,title,labels,assignees,updatedAt,author
```

### Filter by Label

```bash
# Single label
gh pr list --repo $REPO --label mandatory-workspace

# Multiple labels (AND)
gh pr list --repo $REPO --label mandatory-workspace --label workspace-update

# Search for label (OR) - use search syntax
gh pr list --repo $REPO --search "label:mandatory-workspace label:workspace-update"
```

### Filter by Author

```bash
gh pr list --repo $REPO --author github-actions[bot]
```

---

## PR Details

### Full Context

```bash
gh pr view <number> --repo $REPO \
  --json number,title,state,author,labels,assignees,reviewRequests,reviews,statusCheckRollup,files,updatedAt,createdAt,mergeable,body
```

### Just Labels

```bash
gh pr view <number> --repo $REPO --json labels --jq '.labels[].name'
```

### Just Assignees

```bash
gh pr view <number> --repo $REPO --json assignees --jq '.assignees[].login'
```

### Just Review Requests

```bash
gh pr view <number> --repo $REPO --json reviewRequests \
  --jq '.reviewRequests[] | {login: .login, type: .type}'
```

### Check Status

```bash
gh pr view <number> --repo $REPO --json statusCheckRollup \
  --jq '.statusCheckRollup[] | "\(.name): \(.status) \(.conclusion)"'
```

### Specific Check

```bash
# Find publish check
gh pr view <number> --repo $REPO --json statusCheckRollup \
  --jq '.statusCheckRollup[] | select(.name | contains("publish"))'
```

### Files Changed

```bash
gh pr view <number> --repo $REPO --json files --jq '.files[].path'
```

### Extract Workspace Name

```bash
gh pr view <number> --repo $REPO --json files \
  --jq '.files[].path | select(startswith("workspaces/")) | split("/")[1]' | sort -u
```

---

## PR Actions

### Comment

```bash
gh pr comment <number> --repo $REPO --body "/publish"
```

### Add Label

```bash
gh pr edit <number> --repo $REPO --add-label "needs-review"
```

### Remove Label

```bash
gh pr edit <number> --repo $REPO --remove-label "needs-review"
```

### Add Assignee

```bash
gh pr edit <number> --repo $REPO --add-assignee username
```

### Request Review

```bash
gh pr edit <number> --repo $REPO --add-reviewer username
```

---

## Repository Content

### Get File Content

```bash
gh api repos/$REPO/contents/<path> --jq '.content' | base64 -d
```

### Get CODEOWNERS

```bash
gh api repos/$REPO/contents/CODEOWNERS --jq '.content' | base64 -d
```

### Get versions.json

```bash
gh api repos/$REPO/contents/versions.json --jq '.content' | base64 -d | jq '.'
```

### Get File from PR Branch

```bash
# First get the branch name
BRANCH=$(gh pr view <number> --repo $REPO --json headRefName --jq '.headRefName')

# Then get file from that branch
gh api repos/$REPO/contents/<path>?ref=$BRANCH --jq '.content' | base64 -d
```

---

## Workflow Runs

### Recent Runs

```bash
gh run list --repo $REPO --limit 10
```

### Runs for PR

```bash
gh run list --repo $REPO --branch <branch-name>
```

### Run Details

```bash
gh run view <run-id> --repo $REPO
```

---

## Comparison & Diff

### PR Diff

```bash
gh pr diff <number> --repo $REPO
```

### File Names Only

```bash
gh pr diff <number> --repo $REPO --name-only
```

### Specific File Diff

```bash
gh pr diff <number> --repo $REPO -- <path>
```

---

## Batch Operations

### Get Multiple PRs

```bash
# Get numbers first
NUMBERS=$(gh pr list --repo $REPO --label mandatory-workspace --json number --jq '.[].number')

# Then iterate
for num in $NUMBERS; do
  gh pr view $num --repo $REPO --json title,assignees
done
```

### Trigger Publish on Multiple PRs

```bash
for num in 1234 1235 1236; do
  gh pr comment $num --repo $REPO --body "/publish"
  sleep 2  # Rate limiting
done
```

---

## jq Patterns

### Filter by Conclusion

```bash
gh pr view <number> --repo $REPO --json statusCheckRollup \
  --jq '[.statusCheckRollup[] | select(.conclusion == "success")] | length'
```

### Check if Label Exists

```bash
gh pr view <number> --repo $REPO --json labels \
  --jq '.labels | map(.name) | index("do-not-merge") != null'
```

### Days Since Update

```bash
gh pr view <number> --repo $REPO --json updatedAt \
  --jq '((now - (.updatedAt | fromdateiso8601)) / 86400 | floor)'
```

### Group PRs by Label

```bash
gh pr list --repo $REPO --state open --json number,labels \
  --jq 'group_by(.labels | map(.name) | sort) | .[] | {labels: .[0].labels | map(.name), prs: map(.number)}'
```
