---
name: rhdh-test-plan-review
description: |
  Reviews an RHDH test plan Jira ticket and suggests platform/integration version updates based on support lifecycle pages and RHDH release milestones. Use when given an RHDH test plan Jira ticket ID to check which platform/integration versions to add or remove. Use when asked to "update test plan", "review test plan", "check platform versions in test plan", "review RHDH test plan", "what platforms should we test for RHDH X", or "update supported versions in test plan".
---

# RHDH Test Plan Review

Reviews a test plan Jira ticket against platform and integration support lifecycle pages. Suggests adding versions GA before RHDH Code Freeze and removing versions EOL before RHDH GA date. No changes are applied without explicit user approval.

## Prerequisites

**Jira (required):** Verify `acli` is configured:

```bash
python ~/.claude/skills/rhdh-jira/scripts/setup.py --json
```

If not configured, load `~/.claude/skills/rhdh-jira/SKILL.md` and follow its Prerequisites section before continuing.

**Google Sheets API (required):** Ensure `gcloud` is on your `PATH`, then check auth:

```bash
python scripts/check_gsheets.py
```

If the check fails, load `references/google-sheets-setup.md` and walk the user through setup before continuing.

## Workflow

### Step 1: Fetch the test plan Jira ticket

```bash
acli jira workitem view TICKET-ID --json
```

Extract the RHDH version from `fixVersions[0].name`. If empty, check `summary` for a version string (e.g., "RHDH 1.6 Test Plan").

Normalize the version: strip any non-numeric prefix ("RHDH ", "v", "rhdh-") to get plain `major.minor` (e.g., "1.6").

If the version cannot be determined from either field, ask: "I couldn't determine the RHDH version from this ticket. What version is this test plan for?"

### Step 2: Fetch RHDH milestone dates

```bash
python scripts/fetch_schedule.py --version "1.6"
```

Use `--sheet-id <id>` only when the schedule lives in a different spreadsheet than the default (e.g. a fork or replacement sheet).

Expected output:
```json
{
  "version": "1.6",
  "feature_freeze": "2025-09-15",
  "code_freeze": "2025-10-01",
  "ga_date": "2025-10-15",
  "tab": "2025 Schedule"
}
```

If the script returns `{"error": "spreadsheet_not_found"}`, ask:

> "I couldn't access the RHDH Release Schedule sheet (ID: `<spreadsheet_id>`). Please share the sheet URL or ID."

Extract the spreadsheet ID from the URL — it is the long alphanumeric string between `/d/` and `/edit` (e.g., `https://docs.google.com/spreadsheets/d/<ID>/edit`). Then retry:

```bash
python scripts/fetch_schedule.py --version "1.6" --sheet-id <id>
```

If the script returns `{"error": "version_not_found"}`, ask: "I couldn't find RHDH [version] milestones in the schedule sheet. Could you confirm the exact version string as it appears in the sheet?"

Use `code_freeze` and `ga_date` throughout the rest of the workflow.

### Step 3: Parse the test plan description

The description from `acli jira workitem view TICKET-ID --json` is in Atlassian Document Format (ADF). Parse the ADF JSON to locate:

1. **Key dates table** — the first table in the description, with rows for Feature Freeze, Code Freeze, and GA. Each row has the milestone name in the first cell and the date in the second cell (may be empty).
2. **Platform versions table** — rows listing OCP, ARO, AKS, EKS, GKE, OSD, ROSA with version numbers
3. **Integration versions table** — rows listing PostgreSQL variants, RHBK, Quay with version numbers

Record the current version set for each entry. Normalize version strings to `major.minor` for comparison.

Also record the current key dates from the table (may be blank if not yet filled in).

### Step 4: Fetch lifecycle data

Load `references/sources.md` for all lifecycle URLs and how to extract version/date information from each source.

For each source, fetch the page using WebFetch:
- Retry up to 3 times on failure
- If all 3 attempts fail: skip this source and record a warning — do not abort the entire run

Apply these rules using `code_freeze` and `ga_date` from Step 2:
- **Add**: version is GA on or before `code_freeze` AND is not already in the table
- **Remove**: version reaches EOL on or before `ga_date` AND is currently in the table

**Special rule — AKS, EKS, GKE (managed Kubernetes services):**
These platforms test only the **latest available version**. Do not accumulate versions.
- Identify the newest version that is GA on or before `code_freeze`
- If it differs from the current version in the table, suggest **replacing** the current value with only that latest version
- Do not suggest adding alongside the existing version

**Special rule — ARO, OSD, ROSA:**
Each of these platforms tracks a **single version** at a time (not necessarily the latest). Do not accumulate versions.
- Suggest **replacing** the current version if a newer version is GA on or before `code_freeze` and not EOL before `ga_date`
- ARO and ROSA are evaluated **independently** — their versions may differ from each other and from OSD; do not assume they share the same value
- OSD follows the same single-version rule but is evaluated separately from ARO and ROSA

**Special rule — RHBK:**
Track **major versions only** (e.g., `24`, `26`). Accumulate all major versions that are not fully EOL.
- A major version is considered active if it has at least one minor release that is GA on or before `code_freeze` and not EOL before `ga_date`
- Add a major version if it becomes active before `code_freeze` and is not already in the table
- Remove a major version only when **all** of its minor releases are EOL before `ga_date`
- Do not list individual minor versions (26.0, 26.2, 26.4) — list only the major version number (26)

**Special rule — Quay:**
Test only the **latest available version**. Single version, same as AKS/EKS/GKE rule.
- Identify the newest Quay version with a known GA date on or before `code_freeze`
- Suggest replacing the current version with only that latest version

**Special rule — PostgreSQL:**
PostgreSQL version support in RHDH is driven by two sources (see `references/sources.md`):
1. Fetch the currently supported Postgres versions from the RHDH support policy page
2. Fetch what Backstage currently supports from the Backstage versioning policy page

Use the RHDH support policy page as the **baseline** — these are already officially supported. For any Postgres version that Backstage supports but is NOT yet in the RHDH support policy:
- Suggest it as a candidate to add
- Include a **prominent warning**: "⚠ Adding a new PostgreSQL version requires a dedicated RHDH Jira Feature ticket to extend database support — do not add without one."
- Apply the standard EOL removal rule: remove any version whose EOL date is on or before `ga_date` across all three providers (RDS, Azure DB, CloudSQL)

### Step 5: Present the overview diff

Include the key dates table changes at the top of the diff, then platforms, then integrations.

Show a color-coded side-by-side summary of all proposed changes. Use ANSI terminal colors:
- Removals in **red**: `\033[31m−version\033[0m`
- Additions in **green**: `\033[32m+version\033[0m`
- Unchanged versions in plain text

Output the overview using a code block so colors render:

```
Key Dates
─────────────────────────────────────────────────────────────────────
Milestone        │ Current    │ Suggested  │ Source
─────────────────────────────────────────────────────────────────────
Feature Freeze   │ (empty)    │ 2026-04-28 │ RHDH schedule sheet
Code Freeze      │ (empty)    │ 2026-05-19 │ RHDH schedule sheet
GA               │ (empty)    │ 2026-06-10 │ RHDH schedule sheet
─────────────────────────────────────────────────────────────────────

Platforms
─────────────────────────────────────────────────────────────────────
Platform  │ Current              │ Suggested            │ Reason
─────────────────────────────────────────────────────────────────────
ARO       │ 4.19                 │ →4.20                │ ARO GA Apr 20 ≤ code freeze
AKS       │ 1.34                 │ →1.35                │ AKS GA Mar 2026 ≤ code freeze
EKS       │ 1.34                 │ →1.35                │ EKS release Jan 27 ≤ code freeze
GKE       │ 1.35                 │ →1.36                │ GKE GA Apr 28 ≤ code freeze
─────────────────────────────────────────────────────────────────────

Integrations
─────────────────────────────────────────────────────────────────────
Integration  │ Current            │ Suggested            │ Reason
─────────────────────────────────────────────────────────────────────
Postgres     │ v14, v15, v16      │ v14–v16, +v17, +v18  │ v17/v18 GA before code freeze
─────────────────────────────────────────────────────────────────────
```

Where colors apply: render `+version` in green and `−version` in red inline within the Suggested column.

Skip rows with no proposed changes (including key dates already correctly filled). Note skipped sources with ⚠.

### Step 6: Interactive line-by-line review

Walk through each proposed change **one at a time** — key dates first, then platforms, then integrations. This is a decision-collection phase only — nothing is written to Jira here.

For each change, print a prompt like this (colors apply):

```
──────────────────────────────────────────
 AKS  │ Current: 1.34
      │ Suggested: →1.35
      │ Reason: AKS GA Mar 2026 ≤ code freeze May 19
──────────────────────────────────────────
  [a] Accept suggestion  →  1.35
  [k] Keep current       →  1.34
  [e] Enter your own value
Choice [a/k/e]:
```

- **[a]**: record the suggested value — does NOT update Jira yet
- **[k]**: record "no change" for this row — move on
- **[e]**: prompt the user to type their desired value, confirm it, then record it

Continue until every proposed change has a decision. Never update Jira mid-review.

After all decisions are collected, print a final summary of every row that will be changed:

```
Review complete. Decisions collected:

  Feature Freeze  :  (empty)       →  2026-04-28
  Code Freeze     :  (empty)       →  2026-05-19
  GA              :  (empty)       →  2026-06-10
  AKS             :  1.34          →  1.35
  EKS             :  1.34          →  1.35
  Postgres        :  v14, v15, v16 →  v14, v15, v16, v17
```

Then ask how to apply the changes:

```
How would you like to apply these changes?
  [d] Update the Jira description directly
  [c] Post a comment on the ticket with the suggested changes
  [n] Do nothing — discard all decisions
Choice [d/c/n]:
```

- **[d]**: proceed to Step 7 (direct update + child tasks)
- **[c]**: proceed to Step 7b (post comment only)
- **[n]**: confirm no changes were made and stop

### Step 7: Apply changes — direct update

Load `~/.claude/skills/rhdh-jira/references/auth.md` for REST API setup. Use the `ACLI_DIR` / `TOKEN_FILE` lines in each snippet below; if `readlink -f` is unavailable on your OS, use the fallbacks in auth.md ("Token Discovery").

Modify only:
- The version strings within the platform and integration table cells in the ADF
- The date cells in the key dates table (Feature Freeze, Code Freeze, GA rows — match by row label, update the date cell)

Preserve all other ADF structure exactly — other tables, headings, paragraphs, and non-version rows must remain untouched.

Update via REST API:

```bash
ACLI_DIR=$(dirname "$(readlink -f "$(which acli)")")
TOKEN_FILE="$ACLI_DIR/.jira-token"

curl -s -X PUT \
  -u "$(cat "$TOKEN_FILE")" \
  -H "Content-Type: application/json" \
  "https://redhat.atlassian.net/rest/api/3/issue/TICKET-ID" \
  -d '{"fields": {"description": <updated_adf_json>}}'
```

A 204 response confirms success. After confirming success, proceed to Step 8.

### Step 7b: Apply changes — post comment

Format all accepted decisions as a readable comment. Use plain text — no ADF required for comments.

```
*Test Plan Version Review — RHDH X.Y*

*Key Dates (from RHDH schedule sheet):*
• Feature Freeze: 2026-04-28
• Code Freeze: 2026-05-19
• GA: 2026-06-10

*Suggested platform/integration updates:*
• AKS: 1.34 → 1.35
• EKS: 1.34 → 1.35
• PostgreSQL: v14, v15, v16 → v14, v15, v16, v17

These suggestions are based on support lifecycle pages checked on [today's date].
No changes have been applied to this ticket.
```

Post via REST API:

```bash
ACLI_DIR=$(dirname "$(readlink -f "$(which acli)")")
TOKEN_FILE="$ACLI_DIR/.jira-token"

curl -s -X POST \
  -u "$(cat "$TOKEN_FILE")" \
  -H "Content-Type: application/json" \
  "https://redhat.atlassian.net/rest/api/3/issue/TICKET-ID/comment" \
  -d '{"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "<comment text>"}]}]}}'
```

A 201 response confirms success. Stop after posting the comment — do not create child tasks.

### Step 8: Create child tasks (after direct update only)

For each accepted change that has an infrastructure impact, generate a child task. Walk through them **one at a time** — never create tasks in bulk.

**Infrastructure change mapping:**

| Change type | Child task title template |
|---|---|
| AKS version changed | `[RHDH X.Y] Update Kubernetes version to X.Y on AKS cluster` |
| EKS version changed | `[RHDH X.Y] Update Kubernetes version to X.Y on EKS cluster` |
| GKE version changed | `[RHDH X.Y] Update Kubernetes version to X.Y on GKE cluster` |
| OCP version added | `[RHDH X.Y] Create prow job for OCP X.Y` |
| OCP version removed | `[RHDH X.Y] Remove prow job for OCP X.Y` |
| ARO version changed | `[RHDH X.Y] Update ARO cluster to OCP X.Y` |
| OSD version changed | `[RHDH X.Y] Update OSD cluster to OCP X.Y` |
| ROSA version changed | `[RHDH X.Y] Update ROSA cluster to OCP X.Y` |

For each candidate child task, prompt:

```
──────────────────────────────────────────────────────────────
 Child task  │ [RHDH 1.10] Update Kubernetes version to 1.35 on EKS cluster
             │ Parent: RHIDP-XXXXX
──────────────────────────────────────────────────────────────
  [c] Create this task
  [s] Skip — do not create
  [e] Edit the title before creating
Choice [c/s/e]:
```

- **[c]**: create the child task as shown, link it as a subtask of the test plan ticket
- **[s]**: skip this task — move on
- **[e]**: prompt for a new title, confirm, then create

Create child tasks via REST API:

```bash
ACLI_DIR=$(dirname "$(readlink -f "$(which acli)")")
TOKEN_FILE="$ACLI_DIR/.jira-token"

curl -s -X POST \
  -u "$(cat "$TOKEN_FILE")" \
  -H "Content-Type: application/json" \
  "https://redhat.atlassian.net/rest/api/3/issue" \
  -d '{
    "fields": {
      "project": {"key": "RHIDP"},
      "summary": "<child task title>",
      "issuetype": {"name": "Task"},
      "parent": {"key": "TICKET-ID"}
    }
  }'
```

A 201 response with the new issue key confirms success. Print the created issue key after each creation.

After all child task decisions are collected, print a final summary of what was created and what was skipped.

## Gotchas

- **ADF round-trip**: The description is ADF (nested JSON). Send ADF when updating via REST — converting to plain text and back destroys formatting. Modify only the version strings inside existing table cells.
- **Never read `.jira-token` into context.** Use `"$(cat "$TOKEN_FILE")"` after setting `ACLI_DIR` / `TOKEN_FILE` like the curl snippets above; if `readlink -f` fails, follow `~/.claude/skills/rhdh-jira/references/auth.md` ("Token Discovery").
- **Key dates table**: The first table in the description has milestone rows. Match by the label in the first cell (e.g., "Feature Freeze", "Code Freeze"). Update only the date cell (second column). If the row label text differs (e.g., "Code Freeze" vs "RHDH 1.10.0 push"), match loosely on keyword. Leave rows you cannot match untouched.
- **Version string normalization**: Tables may use "v1.29", "1.29.x", or "Kubernetes 1.29". Normalize to `major.minor` before comparing with lifecycle data.
- **fixVersions format varies**: May be "1.6", "RHDH 1.6", "rhdh-1.6". Strip prefixes before passing to `fetch_schedule.py`.
- **RHBK and Quay use doc version dropdowns**, not traditional lifecycle pages — see `references/sources.md` for extraction approach.
- **PostgreSQL has three distinct hosting variants** (Amazon RDS, Azure DB, CloudSQL) — check each separately; EOL dates differ between providers.
- **Schedule tab is year-based**: `fetch_schedule.py` tries current year first, then adjacent years. If the target RHDH version is in a future year, the script will still find it. If the schedule lives in a different spreadsheet than the default, pass `--sheet-id` (error payloads include `spreadsheet_id` when lookup fails).
- **Child task project key**: Use the same project key as the parent ticket (e.g., `RHIDP`). Extract it from the ticket ID.
- **Child task issuetype**: Use `"Task"` — subtask creation requires `"Subtask"` on some Jira configurations. If `"Task"` with a `parent` field fails with 400, retry with `"issuetype": {"name": "Subtask"}`.
