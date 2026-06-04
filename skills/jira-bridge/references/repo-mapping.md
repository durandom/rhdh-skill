# Repo Mapping

Maps Jira components, labels, and keywords to GitHub repositories. This file is the single source of truth for repo detection when `--repo` is not specified.

## How Detection Works

The bridge tries these sources in order:

1. **`repo:` label** on the Jira ticket (e.g., `repo:backstage-plugins`) → look up in the table below
2. **Component field** → look up in the table below
3. **Keywords in description** → fuzzy match against repo descriptions below
4. **Ask the user** → present the table and let them pick

## RHDH Repositories

<!-- Update this table when repos are added to or removed from fullsend -->

| Jira Component | `repo:` label | GitHub Repo | Description |
|----------------|---------------|-------------|-------------|
| TBD | TBD | TBD | TBD |

**Instructions**: Populate this table with your team's repositories. Each row maps a Jira component or label to a GitHub `owner/name` where fullsend is installed.

Example:

```markdown
| Jira Component | `repo:` label | GitHub Repo | Description |
|----------------|---------------|-------------|-------------|
| backstage-plugins | repo:backstage-plugins | redhat-developer/rhdh-plugins | RHDH plugins monorepo |
| backstage-core | repo:backstage | redhat-developer/rhdh | RHDH core |
| operator | repo:rhdh-operator | redhat-developer/rhdh-operator | RHDH Operator |
```

## Adding a New Repo

When your team adds a new repo to fullsend:

1. Add a row to the table above
2. Ensure the repo has the `fullsend` label created (`gh label create fullsend --repo owner/name`)
3. Verify fullsend is installed on the repo (check GitHub App installations)
