# Workflow: Analyze Specific PR

Deep-dive analysis of a single overlay repository PR — check assignment, compatibility, and merge readiness.

Run the analysis script to get a full report in one pass:

```bash
python scripts/analyze-pr.py <pr-number>           # markdown report
python scripts/analyze-pr.py <pr-number> --json     # structured JSON
```

The steps below explain the manual approach for debugging or deeper investigation.

<required_reading>
**Read these reference files NOW:**

1. `../../rhdh/references/github-reference.md` — gh CLI patterns
2. `references/label-priority.md` — Priority classification
</required_reading>

<prerequisites>
| Requirement | Details |
|-------------|---------|
| **Input** | PR number |
| **Access** | Read access to overlay repo |
| **Tools** | `gh` CLI authenticated |
</prerequisites>

<process>

## Step 1: Fetch PR Context

```bash
REPO="redhat-developer/rhdh-plugin-export-overlays"
PR_NUMBER=<number>

# Full PR context
gh pr view $PR_NUMBER --repo $REPO \
  --json number,title,state,author,labels,assignees,reviewRequests,reviews,statusCheckRollup,files,updatedAt,createdAt
```

---

## Step 2: Classification

### 2.1 Determine Priority

Check labels:

```bash
gh pr view $PR_NUMBER --repo $REPO --json labels --jq '.labels[].name'
```

| Labels Present | Priority |
|----------------|----------|
| `mandatory-workspace` + `workspace-update` | 🔴 Critical |
| `mandatory-workspace` + `workspace-addition` | 🟡 Medium |
| `workspace-addition` only | 🟢 Low |
| `do-not-merge` | ⚫ Skip |

### 2.2 Determine PR Type

- **Update:** Existing workspace, version bump
- **Addition:** New workspace being added
- **Patch:** Fix to release branch

---

## Step 3: Assignment Check

```bash
gh pr view $PR_NUMBER --repo $REPO \
  --json assignees,reviewRequests
```

**Evaluate:**

| Condition | Status | Action |
|-----------|--------|--------|
| Individual assignee exists | ✅ Clear owner | None |
| Only team requested | ⚠️ Diluted | Suggest individual |
| No assignee or reviewer | ❌ Orphan | Assign from CODEOWNERS |

**Find suggested owner:**

```bash
# Get workspace from PR files
WORKSPACE=$(gh pr view $PR_NUMBER --repo $REPO --json files \
  --jq '.files[].path | select(startswith("workspaces/")) | split("/")[1]' | head -1)

# Check CODEOWNERS
gh api repos/$REPO/contents/CODEOWNERS --jq '.content' | base64 -d | grep "$WORKSPACE"
```

---

## Step 4: Check Status

```bash
gh pr view $PR_NUMBER --repo $REPO --json statusCheckRollup \
  --jq '.statusCheckRollup[] | "\(.name): \(.status) \(.conclusion)"'
```

### Key Checks

| Check | Required | Status |
|-------|----------|--------|
| `publish` | Yes | Must pass before merge |
| `workspace-tests` | If configured | Smoke test results |
| `check-backstage-compatibility` | Yes | Version alignment |

### If Publish Not Run

```bash
# Check if publish expected but not triggered
gh pr view $PR_NUMBER --repo $REPO --json statusCheckRollup \
  --jq '.statusCheckRollup | map(.name) | index("publish")'
```

If `null` → needs `/publish` comment.

---

## Step 5: Compatibility Check

### 5.1 Get Overlay Target Version

```bash
gh api repos/$REPO/contents/versions.json --jq '.content' | base64 -d | jq '.backstage'
```

### 5.2 Check for Bypass (if source.json modified)

```bash
# Get changed files
gh pr view $PR_NUMBER --repo $REPO --json files \
  --jq '.files[].path | select(endswith("source.json"))'
```

If source.json modified:

1. Fetch the new commit hash from PR diff
2. Check upstream's Backstage version at that commit
3. Compare to overlay target
4. Flag if upstream > overlay target

---

## Step 6: CODEOWNERS Check (for additions)

If `workspace-addition` label:

```bash
# Check if CODEOWNERS modified
gh pr view $PR_NUMBER --repo $REPO --json files \
  --jq '.files[].path | select(. == "CODEOWNERS")'
```

**Evaluate:**

- If CODEOWNERS modified → ✅ Good
- If not modified → ❌ Missing, request from contributor

---

## Step 7: Merge Readiness

### Checklist

| Requirement | Check |
|-------------|-------|
| PR is open | `state == "OPEN"` |
| Publish passed | `publish.conclusion == "success"` |
| Smoke test passed (if exists) | `workspace-tests.conclusion == "success"` |
| Has individual assignee | `assignees.length > 0` |
| CODEOWNERS entry (for additions) | CODEOWNERS file modified |
| Approved | At least one approval review |
| No conflicts | `mergeable != "CONFLICTING"` |

### Generate Readiness Badge

```
✅ Ready to merge — all checks passing
⚠️ Almost ready — needs: [list missing items]
❌ Blocked — [reason]
```

---

## Step 8: Output Summary

```markdown
## PR #1234 Analysis

**Title:** Update aws-ecs workspace to commit abc123
**Author:** @contributor
**Priority:** 🔴 Critical (mandatory-workspace + workspace-update)
**Created:** 5 days ago
**Last Activity:** 2 days ago

### Assignment
| Status | Details |
|--------|---------|
| Assignee | @johndoe |
| Reviewers | @janedoe, @rhdh-plugins (team) |
| Verdict | ✅ Clear ownership |

### Checks
| Check | Status |
|-------|--------|
| publish | ✅ success |
| workspace-tests | ✅ success |
| compatibility | ✅ aligned (1.42.5) |

### Merge Readiness
✅ **Ready to merge**

All requirements satisfied:
- [x] Publish passed
- [x] Smoke tests passed
- [x] Assignee present
- [x] Approved by @janedoe

### Suggested Action
Merge when ready, or wait for additional review if desired.
```

</process>

<tracking>

## Activity Logging

Log PR analysis for tracking review patterns:

```bash
# Analysis complete
$RHDH log add "Analyzed PR #<number>: <status> (<plugin-name>)" --tag analyze-pr --tag <plugin-name>

# Actions taken
$RHDH log add "Triggered /publish on PR #<number>" --tag analyze-pr --tag publish
$RHDH log add "Requested changes on PR #<number>: <reason>" --tag analyze-pr --tag review
$RHDH log add "Approved PR #<number>" --tag analyze-pr --tag review
```

## Follow-up Todos

```bash
# If PR needs external input
$RHDH todo add "Request CODEOWNERS entry from @<author> on PR #<number>" --context "PR #<number>"

# If compatibility concern
$RHDH todo add "Verify <plugin> compat after backstage bump" --context "PR #<number>"

# If waiting on contributor
$RHDH todo add "Follow up with @<author> on PR #<number> feedback" --context "PR #<number>"
```

</tracking>

<success_criteria>
Analysis is complete when:

- [ ] Priority classified
- [ ] Assignment evaluated
- [ ] All checks assessed
- [ ] Compatibility verified (if source.json changed)
- [ ] CODEOWNERS checked (if addition)
- [ ] Merge readiness determined
- [ ] Clear action recommended
</success_criteria>
