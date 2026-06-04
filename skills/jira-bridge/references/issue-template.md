# GitHub Issue Template for Fullsend

Template for creating GitHub Issues that fullsend's triage agent can pick up and route to the coder agent.

## Template

```markdown
## Problem

{problem_description}

## Context

{context}

**Jira ticket**: [{jira_key}]({jira_url})
**Type**: {issue_type}
**Priority**: {priority}

## Location

{location_hints}

## Acceptance Criteria

{acceptance_criteria}

## Notes for the Agent

{agent_notes}

---
*Bridged from Jira by `jira-bridge`*
```

## Field Mapping

How to populate each section from the Jira ticket:

| Template section | Jira source | Fallback |
|-----------------|-------------|----------|
| `problem_description` | Description — extract "Problem" or "Current vs Expected" section | Full description if unstructured |
| `context` | Description — extract "Context" section, plus linked issues | Summary + priority as minimal context |
| `jira_key` | Issue key (e.g., RHIDP-1234) | -- |
| `jira_url` | `https://redhat.atlassian.net/browse/{key}` | Use `issues.redhat.com` if JQL source differs |
| `issue_type` | Issue type field (Bug, Story, Task, etc.) | -- |
| `priority` | Priority field | "Undefined" if not set |
| `location_hints` | Description — extract "Location" section, or `repo:` labels, or component field | Omit section if no location info |
| `acceptance_criteria` | Description — extract "Acceptance Criteria" section | Omit section if none |
| `agent_notes` | Description — extract "Notes for the Agent" section, plus any agent-relevant comments | Omit section if none |

## Title Rules

- Use the Jira summary as the GitHub Issue title
- If the Jira summary is too vague, prepend the type: `fix: {summary}`, `feat: {summary}`
- Keep under 80 characters
- Don't include the Jira key in the title (it's in the body)

## Label Mapping

| Condition | Labels to add |
|-----------|--------------|
| Always | `fullsend` |
| Jira type = Bug | `bug` |
| Jira type = Story or Task | `enhancement` |
| Jira type = Vulnerability | `security` |
| Jira label `needs-investigation` | `needs-investigation` |
| Jira priority = Blocker or Critical | `priority/critical` |

## Idempotency

Before creating, check if the issue already exists:

1. Search for `{jira_key}` in open issues (the Jira link in the body makes this searchable)
2. If found, report "Already bridged" with the existing issue URL
3. If the user wants to re-bridge (ticket was updated), close the old issue with a comment and create a new one

## Batch Mode

When bridging multiple tickets (`--batch`):

1. Fetch all matching Jira tickets
2. Score each against agent-readiness
3. Present a summary table:

```markdown
| # | Jira Key | Summary | Score | Target Repo | Action |
|---|----------|---------|-------|-------------|--------|
| 1 | RHIDP-123 | Fix auth redirect | 11/12 | owner/repo | Bridge |
| 2 | RHIDP-456 | Update notification | 6/12 | owner/repo | Needs grooming |
| 3 | RHIDP-789 | Add dark mode | 10/12 | owner/repo | Bridge |
```

4. Ask: "Bridge {n} ready tickets? [y/N]"
5. Create issues sequentially, report each URL
