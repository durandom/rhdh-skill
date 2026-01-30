# Workflow: Triage Overlay PRs

Prioritize open PRs in the overlay repository by criticality and surface actionable next steps.

<required_reading>
**Read these reference files NOW:**

1. `references/label-priority.md` — PR classification by labels
2. `references/github-queries.md` — gh CLI patterns for PR analysis
</required_reading>

<prerequisites>
| Requirement | Details |
|-------------|---------|
| **Access** | Read access to [rhdh-plugin-export-overlays](https://github.com/redhat-developer/rhdh-plugin-export-overlays) |
| **Tools** | `gh` CLI authenticated |
| **Role** | Core Team (COPE, Plugins team) |
</prerequisites>

<process>

## Phase 1: Fetch Open PRs

```bash
REPO="redhat-developer/rhdh-plugin-export-overlays"

# Get all open PRs with full context
gh pr list --repo $REPO --state open --limit 100 \
  --json number,title,labels,assignees,updatedAt,author,reviewRequests \
  > /tmp/overlay-prs.json
```

**Quick count:**

```bash
gh pr list --repo $REPO --state open --json number | jq length
```

---

## Phase 2: Classify by Priority

### Priority Tiers

| Priority | Labels | Meaning |
|----------|--------|---------|
| 🔴 Critical | `mandatory-workspace` + `workspace-update` | Updates to RHDH catalog plugins |
| 🟡 Medium | `mandatory-workspace` + `workspace-addition` | New plugins for RHDH catalog |
| 🟢 Low | `workspace-addition` only | Community plugins, not in catalog |
| ⚫ Skip | `do-not-merge` | OCI artifact generation only |

### Filter Commands

```bash
# Critical: mandatory updates
gh pr list --repo $REPO --state open \
  --label mandatory-workspace --label workspace-update \
  --json number,title,updatedAt,assignees

# Medium: mandatory additions
gh pr list --repo $REPO --state open \
  --label mandatory-workspace --label workspace-addition \
  --json number,title,updatedAt,assignees

# Skip: do-not-merge
gh pr list --repo $REPO --state open \
  --label do-not-merge \
  --json number,title
```

---

## Phase 3: Assess Each Priority PR

For each Critical and Medium PR, check:

### 3.1 Assignment Status

```bash
gh pr view <number> --repo $REPO \
  --json assignees,reviewRequests \
  --jq '{assignees: .assignees[].login, reviewers: .reviewRequests[].login}'
```

**Flags:**

- ❌ No assignee AND no individual reviewer → needs assignment
- ⚠️ Only team reviewer (no individual) → responsibility diluted
- ✅ Individual assigned → clear ownership

### 3.2 Check Status

```bash
gh pr view <number> --repo $REPO \
  --json statusCheckRollup \
  --jq '.statusCheckRollup[] | {name: .name, status: .status, conclusion: .conclusion}'
```

**Key checks:**

- `publish` — must pass before merge
- `workspace-tests` / `smoke` — validates plugin loads

### 3.3 Staleness

```bash
gh pr view <number> --repo $REPO \
  --json updatedAt \
  --jq '.updatedAt'
```

**Thresholds:**

| Priority | Warn | Alert |
|----------|------|-------|
| Critical | 2 days | 5 days |
| Medium | 5 days | 10 days |
| Low | 14 days | 30 days |

---

## Phase 4: Generate Report

Output a markdown report:

```markdown
## Overlay PR Triage Report
Generated: {date}

### 🔴 Critical — Mandatory Workspace Updates

| PR | Plugin | Days Stale | Assignee | Checks | Action |
|----|--------|------------|----------|--------|--------|
| #1234 | aws-ecs | 3 | @user | ✅ Publish ✅ Smoke | Ready to merge |
| #1235 | lightspeed | 7 | (none) | ⏳ Publish | Assign + /publish |

### 🟡 Medium — Mandatory Workspace Additions

| PR | Plugin | Days Stale | Assignee | Checks | Action |
|----|--------|------------|----------|--------|--------|
| #1240 | new-plugin | 2 | @contributor | ❌ Missing CODEOWNERS | Request CODEOWNERS |

### 🟢 Low — Community Additions
[... or "No low-priority PRs" ...]

### ⚫ Skipped — Do Not Merge
| PR | Plugin | Reason |
|----|--------|--------|
| #1250 | orchestrator-test | OCI artifact only |

---

## Suggested Actions

1. [ ] **Assign** @someone to PR #1235 (lightspeed, 7 days stale)
2. [ ] **Trigger** `/publish` on PR #1236
3. [ ] **Ping** @owner for PR #1237 (blocking release)
4. [ ] **Request** CODEOWNERS from contributor on PR #1240
```

---

## Phase 5: Take Action

Based on report, decide which actions to take:

### Trigger Publish

```bash
gh pr comment <number> --repo $REPO --body "/publish"
```

### Suggest Assignment

```bash
# Check CODEOWNERS for the workspace
gh api repos/$REPO/contents/CODEOWNERS --jq '.content' | base64 -d | grep <workspace>
```

### Draft Slack Ping

See `workflows/draft-notification.md` (future) or compose manually:

```
Hey @handle - PR #1234 needs your attention.
Status: Smoke tests passing, awaiting review.
Priority: Mandatory workspace for RHDH catalog.
```

</process>

<output_format>
The triage report should be:

1. **Actionable** — each row has a clear "Action" column
2. **Scannable** — group by priority, most important first
3. **Time-aware** — show staleness, flag alerts
4. **Complete** — account for all open PRs (even if just to skip)
</output_format>

<tracking>

## Activity Logging

Log triage sessions to track patterns over time:

```bash
# Session start/end
rhdh-plugin log add "Triage: <N> open PRs, <X> critical, <Y> medium" --tag triage

# Actions taken
rhdh-plugin log add "Triggered /publish on PR #<number> (<plugin-name>)" --tag triage --tag publish
rhdh-plugin log add "Assigned @<user> to PR #<number>" --tag triage --tag assignment
rhdh-plugin log add "Pinged @<user> on stale PR #<number>" --tag triage --tag stale
```

## Follow-up Todos

Create todos for items that need follow-up beyond this session:

```bash
# Stale critical PRs
rhdh-plugin todo add "Follow up on stale PR #<number> (<plugin>)" --context "triage"

# Assignment needed
rhdh-plugin todo add "Find owner for orphan PR #<number>" --context "triage"

# Release blocker
rhdh-plugin todo add "Escalate: PR #<number> blocking release" --context "triage"
```

## Viewing History

```bash
# Past triage sessions
rhdh-plugin log search "triage"

# Track specific PR across sessions
rhdh-plugin log search "#<number>"
```

</tracking>

<success_criteria>
Triage is complete when:

- [ ] All open PRs classified by priority
- [ ] Critical PRs have assignees or action to assign
- [ ] Publish triggered on PRs that need it
- [ ] Stale PRs flagged with suggested owners
- [ ] Report generated for team review
</success_criteria>
