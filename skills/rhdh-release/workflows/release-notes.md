# Workflow: Retrieve Outstanding Release Notes

Compile features and bugs missing Release Note Type field.

<prerequisites>

| Requirement | Check |
|-------------|-------|
| **Jira** | `python ~/.claude/skills/rhdh-jira/scripts/setup.py --json` → `"overall": "pass"` |

</prerequisites>

<process>

## Step 1: Run CLI

```bash
python scripts/release.py --json notes {{RELEASE_VERSION}}
```

Use the CLI output directly. If it reports that `release_notes` is unavailable,
run `python scripts/release.py --json check`, configure the Rich Filter as shown
in `references/config.md`, and retry. Do not substitute a hardcoded query: the
Rich Filter is the source of truth for release-note classification.

Also include the Release Notes Dashboard returned by the CLI.

</process>

<gotchas>

- Release Notes must be filled before release — this is a documentation blocker.
- Refer to [RHDH Release Notes Process](https://docs.google.com/document/d/1KFMkRVTkbDIhyZviZcuVn9UfJp64lKmokzT4ftMrj4w/edit) for the full process.

</gotchas>

<success_criteria>

- [ ] Count of issues missing Release Note Type
- [ ] Jira search link to the outstanding items
- [ ] Link to Release Notes Dashboard

</success_criteria>
