---
name: jira-bridge
description: |
  Bridge groomed Jira tickets to GitHub Issues for fullsend agent processing. Reads a Jira ticket, creates a GitHub Issue in the target repo with fullsend-compatible formatting, and links both sides. Trigger on "bridge ticket", "jira to github", "jira-bridge RHIDP-1234", "send to fullsend", or any Jira key with bridging intent.
compatibility: "acli or jira-cli on PATH. gh CLI authenticated. Target repos must have fullsend installed."
---

<essential_principles>

# Jira-to-GitHub Bridge

Create GitHub Issues from Jira tickets so fullsend agents can pick them up and implement them. This skill is the second step after `jira-groom` — it assumes the ticket is already agent-ready (score 10+ on the readiness rubric).

The skill does three things:

1. Reads the Jira ticket and extracts structured information
2. Creates a GitHub Issue with fullsend-compatible formatting
3. Links both sides (Jira comment with GH link, GH issue body with Jira link)

</essential_principles>

<intake>

## Usage

```
jira-bridge <TICKET-KEY>                    # Bridge to auto-detected repo
jira-bridge <TICKET-KEY> --repo owner/name  # Bridge to specific repo
jira-bridge <TICKET-KEY> --dry-run          # Show what would be created, don't file
jira-bridge --batch <JQL> --repo owner/name # Bridge multiple tickets
```

**Wait for response before proceeding.**

</intake>

<routing>

### Routing rules

1. **Ticket key provided**: Fetch Jira ticket → detect target repo → create GitHub Issue → link both sides.
2. **Ticket key + `--repo`**: Skip repo detection, use the specified repo.
3. **Ticket key + `--dry-run`**: Show the GitHub Issue that would be created. No mutations.
4. **`--batch` + JQL + `--repo`**: Bridge multiple tickets to the same repo. Confirm before filing.
5. **No argument**: Ask for a ticket key.

</routing>

## How It Works

### Step 1 — Fetch and validate the Jira ticket

Read the ticket:

```bash
acli jira workitem view <KEY> --json
```

Fall back to `jira issue view <KEY>` if acli is unavailable.

**Validate agent-readiness**: Run a quick score against the `jira-groom` rubric (load `../jira-groom/references/agent-readiness.md`). If score < 7:

> "This ticket scores {score}/12 on agent-readiness. Run `jira-groom <KEY>` first to improve it, or proceed anyway? [groom/proceed/cancel]"

If score is 7-9, note the weak dimensions but proceed.

### Step 2 — Detect target repository

Resolution order:

1. **`--repo` flag**: Use as-is.
2. **`repo:` label on Jira ticket**: Extract repo name from label value. Map to full `owner/name` using the repo mapping in `references/repo-mapping.md`.
3. **Component field**: Map Jira component to a repo using `references/repo-mapping.md`.
4. **Ask the user**: Present known repos from the mapping file, let them pick.

Verify the repo exists and has fullsend installed:

```bash
gh repo view <owner/name> --json name,owner
```

### Step 3 — Check for existing GitHub Issues

Search for duplicates before creating:

```bash
gh issue list --repo <owner/name> --state open --search "<jira key OR summary keywords>"
```

If a match exists:

> "Found existing issue #{number}: '{title}'. Is this the same work? [skip/link/create-anyway]"

- **skip**: Don't create. Optionally add Jira link to existing issue.
- **link**: Link Jira ticket to existing issue (comment on both sides). Done.
- **create-anyway**: Proceed with new issue.

### Step 4 — Create the GitHub Issue

Build the issue using the template in `references/issue-template.md`.

```bash
gh issue create --repo <owner/name> \
  --title "<title>" \
  --label "fullsend" \
  --body "$(cat <<'EOF'
<body>
EOF
)"
```

**Labels**: Always add `fullsend` so the triage agent picks it up. Add additional labels based on ticket type:

| Jira type | GitHub labels |
|-----------|--------------|
| Bug | `fullsend`, `bug` |
| Story/Task | `fullsend`, `enhancement` |
| Vulnerability/CVE | `fullsend`, `security` |
| Investigation (`needs-investigation`) | `fullsend`, `needs-investigation` |

### Step 5 — Link both sides

**On Jira** — add a comment:

```
acli jira workitem comment --key <KEY> --comment "Bridged to GitHub: <issue-url>" --yes
```

**On GitHub** — the Jira link is already in the issue body (from the template).

### Step 6 — Report

```markdown
Bridged: <JIRA-KEY> → <owner/name>#<number>
  Jira:   https://redhat.atlassian.net/browse/<KEY>
  GitHub: <issue-url>
  Score:  <readiness-score>/12
```

## Reference Files

| File | Load when... |
|------|-------------|
| `references/issue-template.md` | Always — GitHub Issue body template with fullsend-compatible formatting |
| `references/repo-mapping.md` | Repo detection — maps Jira components/labels to GitHub repos |
| `../jira-groom/references/agent-readiness.md` | Validation — agent-readiness scoring before bridge |

## Relationship to Other Skills

- **`jira-groom`**: Prerequisite — grooms tickets to agent-readiness. Bridge validates the score before proceeding.
- **`rhdh-jira`**: Provides Jira infrastructure (acli, fields, workflows). Bridge uses the same tooling but doesn't duplicate it.
- **fullsend triage agent**: Downstream consumer — picks up the GitHub Issue created by this skill.

## Error Handling

| Error | Action |
|-------|--------|
| Jira ticket not found | "Ticket <KEY> not found." |
| Target repo not found | "Repository <owner/name> not found or no access." |
| `gh issue create` fails | Show error. Common cause: missing labels (create them first). |
| No repo detected | Ask user to specify with `--repo`. |
| Ticket already bridged | Check Jira comments for existing "Bridged to GitHub" link. Ask before creating a second issue. |
