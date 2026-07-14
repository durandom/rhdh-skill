# Private Data Repository

Internal repository containing Jira Rich Filter exports and other private operational data that cannot be checked into the public `rhdh-skill` repo.

## Repository

- **URL:** `git@gitlab.cee.redhat.com:rhidp/rhdh-skill-private-data.git`
- **Access:** Requires Red Hat VPN / internal network
- **Maintainers:** Matt Reid, Jasper Chui (Rich Filter owners)

## Contents

| Path | Description |
|------|-------------|
| `jira-rich-filter/rhidp-operational-rich-filter.json` | Exported "RHIDP Operational" Rich Filter — project-scoped JQL, component exclusion lists, team Cloud ID mappings, queue definitions |

## Setup

**Clone** (sibling to `rhdh-skill`):

```bash
cd "$(dirname /path/to/rhdh-skill)"
git clone git@gitlab.cee.redhat.com:rhidp/rhdh-skill-private-data.git
```

**Configure** (if cloned elsewhere):

```bash
$RHDH config set private-data /path/to/rhdh-skill-private-data
```

**Update** (pull latest Rich Filter export):

```bash
cd /path/to/rhdh-skill-private-data && git pull
```

## How It's Used

The `rhdh-release` skill's `rich_filter.py` module reads the Rich Filter JSON at runtime to source JQL queries. When the file is available, it overlays the hardcoded JQL templates in `jql-release.md` with queries composed from the Rich Filter. When the file is missing, the skill falls back to the markdown templates.
