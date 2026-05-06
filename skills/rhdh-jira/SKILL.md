---
name: rhdh-jira
description: |
  Interacts with RHDH Jira projects (RHIDP, RHDHPLAN, RHDHBUGS, RHDHSUPP) using acli, GraphQL, and REST API. Use when the user needs to search, create, view, edit, transition, assign, refine, or report on Jira issues for RHDH. Also use for sprint planning, sprint reviews, release readiness, assignee recommendations, or issue refinement. Trigger on Jira issue keys (RHIDP-1234, RHDHPLAN-567), sprint ceremony prep, "who should take this", "refine this", "plan the sprint", "sprint report", "how's the release looking", or "release status".
compatibility: "acli (Atlassian CLI) on PATH. Python 3 for scripts. Windows, macOS, Linux."
---

# RHDH Jira

Foundational skill for interacting with RHDH's Jira instance via the Atlassian CLI (`acli`). Covers all four active projects, issue types, workflows, custom fields, and JQL patterns.

## Commands

| Command | Description | Reference |
|---------|-------------|-----------|
| `assign [issue key(s) or JQL]` | Recommend and assign team members using expertise, capacity, and context proximity analysis | [references/assign.md](references/assign.md) |
| `refine [issue key(s), JQL, or 'sprint']` | Check issues against exit criteria, identify duplicates, missing fields, unaddressed comments, and readiness | [references/refine.md](references/refine.md) |
| `plan [team]` | Sprint planning prep: carryover, velocity, capacity, ready queue, sprint fill suggestions | [references/plan.md](references/plan.md) |
| `sprint-report [team]` | Sprint review summary: committed vs completed, per-member breakdown, demo checklist | [references/sprint-report.md](references/sprint-report.md) |
| `release [version]` | Release readiness: feature matrix, PI funnel, dependency map, blocker bugs, risk assessment | [references/release.md](references/release.md) |

Single source of truth for command descriptions: `scripts/command-metadata.json`

### Routing rules

1. **No argument**: Show the command menu. Ask what to do.
2. **First word matches a command**: Load its reference file and follow it.
3. **First word doesn't match**: General Jira invocation using the full argument as context — use the reference files table below to decide what to load.

## Prerequisites

Run `scripts/setup.py` to verify everything is configured:

```bash
python scripts/setup.py
```

The script checks:

1. `acli` binary on PATH
2. Jira API token auth configured (`~/.config/acli/jira_config.yaml`)
3. `.jira-token` file next to `acli` executable (for REST API fallback)
4. Smoke test against `redhat.atlassian.net`

If `acli` is not installed, download from [Atlassian CLI](https://developer.atlassian.com/cloud/acli/) and follow the [Getting Started guide](https://developer.atlassian.com/cloud/acli/guides/how-to-get-started/) for installation and authentication setup. Use API token authentication, not OAuth — OAuth sessions expire and `acli auth status` gives false negatives with token auth (see Gotchas).

### API preference order

All operations follow this priority: **acli → GraphQL → REST API**.

- **acli** — default for simple, single-issue operations (view, edit, assign, transition).
- **GraphQL** — for bulk reads where acli would be too slow (expertise profiles, capacity, refinement checks). Skip acli entirely for bulk.
- **REST API** — for writes when already in an authenticated API context (avoids shelling out to acli mid-workflow), or as fallback when acli fails for custom field updates.

Sub-commands (`assign`, `refine`) document which API they use. When a sub-command's workflow already has `AUTH` set from GraphQL reads, prefer REST for writes.

### REST/GraphQL capability gate

Before attempting any REST API or GraphQL call:

1. Run `python scripts/setup.py --json` and check `token_file_found`
2. If missing, state: "REST API/GraphQL fallback unavailable — `.jira-token` not configured. Run `setup.py` for instructions." Continue with acli-only workflow.
3. If the user needs REST/GraphQL, load `references/auth.md` for setup instructions

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup.py` | Verify acli install + auth. Run with `--json` for structured output. |
| `scripts/parse_issues.py` | Flatten, enrich, and filter acli JSON output. Solves the core problem: `acli search --json` can't return custom fields (team, story points, sprint). Pipe search results in, get clean data out. Use `--enrich` to fetch full fields, `-f team="X"` to filter by team. |
| `scripts/command-metadata.json` | Single source of truth for sub-command descriptions and argument hints. |

## Projects

| Key | Purpose | Issue Types |
|-----|---------|-------------|
| RHIDP | Engineering work | Epic, Story, Task, Sub-task, Vulnerability |
| RHDHPLAN | Program planning | Feature, Outcome, Feature Request, Sub-task |
| RHDHBUGS | Product defects | Bug, Sub-task |
| RHDHSUPP | Support-engineering interactions | Bug |

RHDHPAI (Plugins and AI) is **archived** — JQL queries against it will fail.

### Issue type selection

- **Story** — end-user facing work (API, UI changes)
- **Task** — not end-user facing (tests, CI/CD, refactoring, code organization)
- **Epic** — collection of Stories/Tasks toward a deliverable
- **Feature** — program-level planning item in RHDHPLAN
- **Bug** — product defect (RHDHBUGS) or support case tracking (RHDHSUPP)
- **Sub-task** — child of any issue type above
- **Vulnerability** — CVE tracking in RHIDP (Product Security)

## Reference Files

Load only what the current task requires.

| File | Load when... |
|------|-------------|
| `references/acli-commands.md` | Running an acli command you haven't used before, or hitting unexpected flag behavior. Quick reference for syntax, flag differences, and output formats. |
| `references/fields.md` | Need to know a field name, custom field ID, accepted values, or label conventions. Custom fields, labels, link types, components, priorities. |
| `references/workflows.md` | Transitioning issues, checking exit criteria, or verifying readiness for the next status. |
| `references/templates.md` | Creating new issues. Also load `references/workflows.md` for required fields at entry status. |
| `references/support.md` | Handling support cases, filing bugs from customer cases, or creating feature requests from support. |
| `references/jql-patterns.md` | Building a JQL query, finding a board ID, or looking up sprint information. JQL cookbook with 23+ tested queries. |
| `references/auth.md` | Setting up authentication for REST API or GraphQL calls. Token file format, path discovery, security, instance config, common auth errors. |
| `references/rest-api-fallback.md` | `acli` failed to update a custom field (Team, Size, Story Points, Release Note Type). Curl examples, response handling, OpenAPI spec discovery. |
| `references/graphql-queries.md` | Complex read queries needing multiple fields, relationships, or custom field data in one call. Schema introspection, JQL search via GraphQL, field type fragments. Also for bulk operations where acli would be too slow. |
| `references/assign.md` | Recommending assignees for unassigned issues. Team roster lookup, expertise profiling, sprint capacity analysis, context proximity scoring. Also for applying assignments after user confirmation. |
| `references/refine.md` | Checking issues against exit criteria per status, identifying duplicates, missing fields, unaddressed comments, and readiness for the next workflow status. |
| `references/plan.md` | Sprint planning prep: carryover report, velocity trend, per-member capacity, ready-for-planning queue, sprint fill suggestions. |
| `references/sprint-report.md` | Sprint review summary: committed vs completed, per-member breakdown, epic progress, demo checklist with naming conventions, velocity trend. |
| `references/release.md` | Release readiness report: feature matrix, PI funnel states, epic roll-up, cross-team dependency map, blocker bugs, RN readiness, risk assessment. |

## Common Gotchas

1. **`acli auth status` lies.** It checks OAuth, not API token auth. Always returns "unauthorized" with token auth even when Jira works fine. Use `acli jira project list --recent 1` as a smoke test instead.
2. **`view` uses positional arg, everything else uses `--key`.** `acli jira workitem view RHIDP-123` but `acli jira workitem edit --key RHIDP-123 ...`.
3. **`--yes` is mandatory for mutations.** All `edit`, `transition`, `assign`, and `link create` commands prompt interactively without it. Always pass `--yes`.
4. **`--fields` is restrictive on search.** Only accepts `key`, `summary`, `status`, `assignee`, `issuetype`, `priority`, `description`, `labels`. For components, sprint, fixVersions, and all custom fields — use `--json` or `scripts/parse_issues.py --enrich`.
5. **Team field has two JQL syntaxes.** `customfield_10001` cannot be used in JQL WHERE clauses. However, `"Team[Team]" = {teamId}` (using the team UUID, not display name) works. Use the UUID syntax for JQL filtering; use `customfield_10001.name` in post-processing only when you need the display name from JSON output.
6. **ADF vs plain text.** Reading descriptions via `--json` returns Atlassian Document Format (nested JSON). Creating/editing with `--description` accepts plain text. Don't try to round-trip ADF through `--description`.
7. **Acceptance Criteria field is almost always null.** Scan the description for "Requirements", "Acceptance Criteria", or bullet-style criteria instead of checking `customfield_10718`.
8. **`--enrich` is MANDATORY for custom fields.** Both `acli search --json` and `acli view KEY --json` (without `--fields "*all"`) return only basic fields (assignee, issuetype, priority, status, summary). Story points, team, sprint, and size will appear as empty/null — looking like the data isn't set when it actually is. Always use `scripts/parse_issues.py --enrich` to get custom field data. Skipping `--enrich` is the #1 cause of false "missing data" reports.
9. **Custom fields may fail to update via `acli`.** `acli jira workitem edit` can silently fail or error when setting custom fields (Team, Size, Story Points). When an `acli edit` for a custom field fails, fall back to the Jira REST API. Find the token file at `.jira-token` next to the `acli` executable (discover the path with `readlink -f "$(which acli)"` or `where acli`). Read `references/rest-api-fallback.md` for curl examples and payload formats. Never read the token file into context.
10. **`acli sprint list-workitems --json` wraps results in `{"issues": [...]}`.**  The output is NOT a flat array — it's an object with an `issues` key. Extract the array before piping to `parse_issues.py`. See `references/acli-commands.md` for the workaround command.
11. **GraphQL search is beta.** `issueSearchStable` requires `X-ExperimentalApi: JiraIssueSearch` header. Load `references/graphql-queries.md` before attempting GraphQL queries.
12. **`.jira-token` format is `email:token`, not bare token.** A file containing only the API token without the email prefix will cause 401 errors on REST/GraphQL calls. The `setup.py` script validates the format.

## Error Handling

| Error | Action |
|-------|--------|
| `acli` not on PATH | Run `scripts/setup.py`. Install from Atlassian if missing. See [Getting Started](https://developer.atlassian.com/cloud/acli/guides/how-to-get-started/). |
| "unauthorized" from `auth status` | Ignore. Check `jira_config.yaml` exists. Run smoke test. |
| "required flag(s) not set" | Command syntax wrong. Run `acli jira <subcommand> --help`. |
| "field X is not allowed" | Use `--json` instead of `--fields` for that field. |
| "the value X does not exist for the field 'project'" | Project key is wrong or project is archived (e.g., RHDHPAI). |
| Rate limiting (429) | Wait 5 seconds, retry once. |
| Interactive prompt hangs | Missing `--yes` flag on a mutating command. |
| Custom field update fails via `acli` | Fall back to Jira REST API using `.jira-token` file. See Gotcha #9. |
| `issueSearchStable` returns errors | Fall back to REST API search (`/rest/api/3/search`) with the same JQL. Warn that the beta API failed. |

## Team Conventions

These apply across all sub-commands:

- **Release Pending counts as completed.** Release Pending items remain in the sprint and count toward velocity and capacity. They represent done work awaiting release.
- **Confirmation flow.** Sub-commands that modify Jira issues (assign, refine, release) use a standard prompt: `"Apply changes? [y/N/edit]"` — **y** applies all, **N** cancels, **edit** steps through each change individually.

## Common Workflows

> Sub-commands share data. `plan` reuses roster/capacity/expertise from `assign`. `sprint-report` uses the same velocity query pattern as `plan`. `release` references exit criteria from `workflows.md` and can invoke `assign` for unassigned Features.

### Creating an issue

1. Load `references/templates.md` for the body template
2. Load `references/workflows.md` for required fields at New status
3. Run `acli jira workitem create` (see `references/acli-commands.md` if unsure of syntax)

### Searching with custom fields (team, story points, sprint)

1. Build JQL using patterns from `references/jql-patterns.md`
2. Pipe results through `scripts/parse_issues.py --enrich` for full field data
3. Use `-f team="X"` to filter by team (not possible in JQL)

### Transitioning an issue

1. Load `references/workflows.md` for exit criteria at the target status
2. Verify required fields are set before transitioning
3. Run `acli jira workitem transition --key KEY --status "X" --yes`

### Complex queries (many fields, relationships)

1. Load `references/graphql-queries.md`
2. Use `issueByKey` for single issues or `issueSearchStable` (beta) for JQL search
3. Fall back to `acli` + `parse_issues.py --enrich` if GraphQL returns errors

### Recommending and assigning issues

1. Load `references/assign.md`
2. Identify unassigned issues (single key, JQL query, or passed-in list)
3. Determine the team (from issue field, parent epic, or user input)
4. Run deep or quick analysis per the reference
5. Present recommendations, get user confirmation, then assign

### Refining issues

1. Load `references/refine.md`
2. Identify issues to refine (specific keys, JQL, `sprint`, or `backlog`)
3. Run all 6 checks: missing fields, duplicates, hierarchy, comments, staleness, sprint readiness
4. Present refinement report with actionable recommendations
5. Optionally apply auto-fixable changes and prompt for manual decisions

### Sprint planning prep

1. Load `references/plan.md`
2. Resolve team, board, and sprint context
3. Generate carryover report, velocity trend, capacity snapshot, and ready-for-planning queue
4. Auto-generate sprint fill suggestions with expertise matching
5. Surface critical customer bugs (exempt from capacity) and retro action items

### Sprint review summary

1. Load `references/sprint-report.md`
2. Resolve sprint (active or previous)
3. Partition completed vs carried over, compute completion rate
4. Per-member breakdown, epic progress, demo checklist with naming conventions
5. Optionally save as markdown file

### Release readiness

1. Load `references/release.md`
2. Fetch Features for the target version/label
3. Quick mode: PI funnel, feature matrix, readiness score
4. Deep mode: adds epic roll-up, dependency map, coherence analysis, RN readiness, risk assessment
5. Optionally remediate (assign owners, create Epics, transition statuses)

### Discovering unknown fields or endpoints

1. For REST: load `references/rest-api-fallback.md` — use the OpenAPI spec or `/rest/api/3/field` endpoint
2. For GraphQL: load `references/graphql-queries.md` — use `__type` introspection queries
3. Do not guess field IDs or types — always verify against the live schema

## When NOT to Use

- **Non-RHDH Jira projects** — this skill's field mappings, workflows, and JQL patterns are specific to RHIDP/RHDHPLAN/RHDHBUGS/RHDHSUPP
- **Jira REST API directly** — use `acli` first, then GraphQL for bulk reads. REST API is the last resort for writes when acli fails and for schema discovery via OpenAPI spec (see Gotcha #9)
- **GraphQL for simple lookups** — use `acli` for single-issue views and simple searches. GraphQL is for bulk operations, complex queries needing relationships or many custom fields in one call, team roster lookups, and schema introspection
