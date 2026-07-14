# Release Manager Configuration

Static configuration values for the RHDH Release Manager skill.

## JQL Scope

| Key | Value |
|-----|-------|
| `jira_default_base_jql` | `project IN (RHIDP, RHDHBugs, RHDHPLAN, RHDHSUPP) AND status != closed` |

## Google Drive Resources

| Key | Value | Description |
|-----|-------|-------------|
| `team_mapping_gdrive_id` | `1vQXfvID72qwqvLb17eyGOvnZXrZG7NBzTGv6RP9wvyM` | RHDH Team Mapping spreadsheet (sheet: "Team") |
| `release_schedule_gdrive_id` | `1knVzlMW0l0X4c7gkoiuaGql1zuFgEGwHHBsj-ygUTnc` | RHDH Release Schedule spreadsheet |
| `release_process_doc_id` | `13OkypJ3u_7Jq6kEhKhjEFwHQ12oPFDKXVzFjYW4XLdk` | Release process Google Doc |

## Rich Filter

| Key | Value | Description |
|-----|-------|-------------|
| `private_data_repo` | `../rhdh-skill-private-data` | Sibling directory with Jira Rich Filter exports |
| `rich_filter_path` | `jira-rich-filter/rhidp-operational-rich-filter.json` | Rich Filter JSON file within the private data repo |

The Rich Filter JSON is sourced from the "RHIDP Operational" Rich Filter in Jira, maintained by Matt Reid and Jasper Chui. When available, it overrides hardcoded JQL templates for Feature Freeze, Code Freeze, and Release Notes queries.

**Setup:** See `../../rhdh/references/private-data.md` for clone instructions.

**Override:** Set `RHDH_RICH_FILTER_PATH=/path/to/file.json` to use a specific file.

## gog CLI Setup

Google Sheets and Docs access uses the [gog CLI](https://gogcli.sh).

1. Install: `brew install gogcli` (requires Homebrew; `brew trust openclaw/tap` if prompted)
2. Get OAuth credentials: request `client_secret.json` from <mhild@redhat.com>
3. Import credentials: `gog auth credentials client_secret.json`
4. Authenticate: `gog auth add <your-email> --services sheets,docs,drive`
5. Verify: `gog sheets metadata 1vQXfvID72qwqvLb17eyGOvnZXrZG7NBzTGv6RP9wvyM --json`
