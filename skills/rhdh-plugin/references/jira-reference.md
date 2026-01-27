# Reference: JIRA CLI for Plugin Tracking

Working with JIRA issues related to RHDH plugins using `jira-cli`.

---

## Tool Setup

**Repository:** <https://github.com/ankitpokhrel/jira-cli>
**Configuration:** `~/.jira/.config.yml` (user's authentication)
**Projects:** RHIDP (main), RHDHPLAN (planning)

---

## Essential Flags

### Always use these flags

```bash
# --raw for full details (custom fields, all metadata)
jira issue show RHIDP-1234 --comments 10 --raw

# --no-input for non-interactive (required in scripts)
jira issue create --project="RHIDP" --type="Task" --summary="..." --no-input

# --plain for machine-readable output
jira issue list --jql 'project = RHIDP' --plain
```

---

## JQL Queries

### Plugin-related issues

```bash
# All open plugin issues
jira issue list --jql 'project = RHIDP AND component = "Plugins" AND resolution = Unresolved'

# Plugin issues assigned to me
jira issue list --jql 'project = RHIDP AND component = "Plugins" AND assignee = currentUser()'

# Recently updated
jira issue list --jql 'project IN (RHIDP, RHDHPLAN) AND component = "Plugins" AND updated >= -14d'

# By keyword
jira issue list --jql 'project = RHIDP AND text ~ "marketplace"'
```

### ⚠️ JQL Limitation: NO ORDER BY

```bash
# ❌ WILL FAIL - jira-cli doesn't support ORDER BY
jira issue list --jql 'project = RHIDP ORDER BY updated DESC'

# ✅ CORRECT - remove ORDER BY
jira issue list --jql 'project = RHIDP'
```

Sort results after retrieval if needed.

---

## Reading Issues

### Always include comments

```bash
jira issue show RHIDP-1234 --comments 20 --raw
```

**Why comments matter:**

- Recent technical reviews often in comments
- Action items and blockers
- Stakeholder feedback
- Fresher context than description

### Comment analysis priority

1. **Recent comments** (last 30 days)
2. **Action items** (questions, requests, blockers)
3. **Technical feedback** (engineering reviews)
4. **Stakeholder involvement** (who's engaged)

---

## Creating Issues

### Standard task

```bash
echo 'h1. Description

Plugin onboarding request for XYZ plugin.' | jira issue create \
  --project="RHIDP" \
  --type="Task" \
  --summary="Onboard XYZ plugin to Extensions Catalog" \
  --component="Plugins" \
  --body=- \
  --no-input
```

### Epic with parent link

```bash
echo 'h1. Epic Description' | jira issue create \
  --project="RHIDP" \
  --type="Epic" \
  --summary="Q1 Plugin Onboarding" \
  --custom parent-link="RHIDP-5678" \
  --body=- \
  --no-input
```

### Task linked to epic

```bash
echo 'h1. Task Description' | jira issue create \
  --project="RHIDP" \
  --type="Task" \
  --summary="Onboard AWS ECS plugin" \
  --custom epic-link="RHIDP-1234" \
  --body=- \
  --no-input
```

### Body content format

Use **echo piping** (not subshells) to avoid timeouts:

```bash
# ✅ Correct - echo pipe
echo 'h1. Heading
My content here' | jira issue create ... --body=- --no-input

# ❌ Incorrect - subshell (timeouts)
jira issue create --body="$(cat <<'EOF'
Content
EOF
)"
```

### Jira Wiki Markup

| Syntax | Result |
|--------|--------|
| `h1.` | Heading 1 |
| `h2.` | Heading 2 |
| `*bold*` | **bold** |
| `_italic_` | *italic* |
| `* item` | Bullet list |
| `# item` | Numbered list |
| `{code}...{code}` | Code block |

---

## Assignee Handling

### Use full names, NOT emails

```bash
# ✅ Correct
jira issue create --assignee="Marcel Hild" --no-input

# ❌ Incorrect (will fail)
jira issue create --assignee="mhild@redhat.com" --no-input
```

### Check format from existing issue

```bash
jira issue show RHIDP-1234 --raw | grep -A2 "assignee"
```

---

## Issue Linking

### Link types in RHIDP

| Link Type | JQL Field | CLI Flag |
|-----------|-----------|----------|
| Epic → Parent Feature | `"Feature Link"` | `--custom parent-link="FEATURE-ID"` |
| Task → Epic | `"Epic Link"` | `--custom epic-link="EPIC-ID"` |
| Sub-task → Parent | `parent` | `--parent="PARENT-ID"` |

### Find issues linked to epic

```bash
jira issue list --jql 'project = RHIDP AND "Epic Link" = RHIDP-1234' --plain
```

---

## Issue Transitions

### List available transitions

```bash
jira issue move RHIDP-1234 --list
```

### Move to status

```bash
jira issue move RHIDP-1234 "In Progress"
jira issue move RHIDP-1234 "Done"
```

---

## Comments

### Add comment

```bash
jira issue comment add RHIDP-1234 --body "PR merged: https://github.com/..."
```

### Add formatted comment

```bash
echo 'h2. Status Update

* PR: [#1234|https://github.com/redhat-developer/rhdh-plugin-export-overlays/pull/1234]
* Status: Smoke tests passing
* Next: Awaiting CODEOWNERS approval' | jira issue comment add RHIDP-1234 --body=-
```

---

## Connectivity Protocol

### Limited retries

- Test max 1-2 calls only
- Stop immediately after failures
- Warn user about sub-optimal results

### Failure response

```
⚠️ jira-cli not working. Results will be sub-optimal without live JIRA data.

Alternatives:
- Run manual command: jira issue list --jql '[query]'
- Direct JIRA URL: https://issues.redhat.com/browse/RHIDP-1234
```

---

## Plugin Workflow Integration

### Link JIRA to GitHub PR

When creating plugin tracking issues, include PR reference:

```bash
echo 'h1. Plugin Onboarding

*PR:* [#1234|https://github.com/redhat-developer/rhdh-plugin-export-overlays/pull/1234]
*Workspace:* aws-ecs
*Status:* In Review

h2. Checklist
* CODEOWNERS entry
* Smoke tests passing
* Metadata complete' | jira issue create \
  --project="RHIDP" \
  --type="Task" \
  --summary="[Plugin] Onboard aws-ecs to Extensions Catalog" \
  --component="Plugins" \
  --body=- \
  --no-input
```

### Update JIRA when PR merges

```bash
jira issue move RHIDP-1234 "Done"
jira issue comment add RHIDP-1234 --body "PR merged. Plugin available in Extensions Catalog."
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Assignee not found" | Wrong name format | Use full name, not email |
| "Required fields missing" | Project-specific fields | Check project config, add `--custom` |
| "ORDER BY not supported" | JQL limitation | Remove ORDER BY clause |
| Timeout | Large body content | Use echo piping, break into parts |
