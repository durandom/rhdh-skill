# Patterns for Skills That Wrap APIs

Lessons learned from building skills that wrap CLIs, REST APIs, and GraphQL APIs. Read this when the skill interacts with external services or APIs.

For general reference architecture patterns (transitive loading, error placement, decision tables, agent-only audience), see `references/spec-guide.md` → Reference Architecture.

## Credential handling

Skills that authenticate against external services must handle credentials carefully.

**Rules:**

1. **Never read credential files into context.** The agent must not use `read` or `cat` to view token/password files. Credentials passed through the LLM context are logged, cached, and potentially leaked.
2. **Pass credentials via shell substitution.** Use `curl -u "$(cat path/.token)"` — the secret stays in the shell, never enters the conversation.
3. **Document the credential file format explicitly.** Show the exact format (e.g., `email:token`), not just "put your token here." Ambiguity causes auth errors.
4. **Add a capability gate.** Before attempting any authenticated call, check if the credential file exists (preferably via a setup script, not by reading the file). If missing, state the fallback clearly and continue without the feature.
5. **Warn about file permissions.** Credential files should be `chmod 600` on Unix. The setup script should warn when permissions are too open.
6. **Single-source the credential setup.** Document token format, path discovery, and security in its own reference file. Other references point to it — don't embed it in a consumer (see `spec-guide.md` → transitive loading).

Example capability gate in SKILL.md:

```markdown
Before attempting REST API calls:
1. Run `python scripts/setup.py --json` and check `token_file_found`
2. If missing, state: "REST API unavailable — token not configured." Continue with CLI-only workflow.
3. Do not ask the user to create the token unless they explicitly need the feature.
```

## API schema discovery

When a skill wraps an API, the agent should be able to discover available endpoints, fields, and types dynamically — not rely solely on hardcoded documentation.

### REST APIs (OpenAPI)

If the API publishes an OpenAPI spec:

1. Document the download URL (without version pins that go stale)
2. Show how to query it programmatically (Python `json.load` + dict traversal)
3. Do not load the spec into context — it's typically 1-10MB
4. Also document live discovery endpoints (e.g., `/rest/api/3/field` for Jira)

### GraphQL APIs

GraphQL APIs are self-describing via introspection. There is no spec file to download.

1. Document `__type(name: "TypeName")` queries for targeted discovery
2. Document full `__schema` dump for offline analysis (save to file, query programmatically)
3. Note that introspection output is large — do not load into context

### Schema discovery comparison table

Include a table comparing how to discover the schema for each API the skill covers:

```markdown
| | REST API | GraphQL |
|--|---------|---------|
| **Spec format** | OpenAPI JSON (downloadable file) | No spec file — introspection queries |
| **Download** | `curl -o spec.json 'https://...'` | `__schema` query against the live endpoint |
| **Live field registry** | `GET /rest/api/3/field` | `__type(name: "...")` introspection |
```

## Validate examples against the live API

Do not write API examples from memory or documentation alone. Run them against the real endpoint and verify the output before including them in the skill.

**Why:** API schemas drift from documentation. Field names, payload formats, and required headers discovered through docs may not match the live API. A skill with broken examples is worse than no skill — the agent will retry the broken pattern repeatedly.

**Process:**

1. Draft the example from docs or training knowledge
2. Run it against the real endpoint
3. If it fails, use schema discovery (OpenAPI spec, GraphQL introspection) to find the correct field names and formats
4. Include only verified examples in the skill

This is especially important for GraphQL APIs where field names are typed and case-sensitive — `displayName` vs `name`, `parent` vs `parentIssue`, `sprint` vs `selectedSprintsConnection` can all differ from what you'd guess.

## Multi-API preference order

When a skill wraps multiple APIs (e.g., CLI + GraphQL + REST), define the preference order once in SKILL.md. Sub-commands reference it instead of each explaining when to use which API.

**Pattern:**

```markdown
### API preference order

All operations follow this priority: **CLI → GraphQL → REST API**.

- **CLI** — default for simple, single-issue operations.
- **GraphQL** — for bulk reads where CLI would be too slow. Skip CLI entirely for bulk.
- **REST API** — for writes when already in an authenticated API context (avoid shelling out to CLI mid-workflow), or as fallback when CLI fails.

Sub-commands document which API they use. When a sub-command's workflow already has auth set from GraphQL reads, prefer REST for writes.
```

Sub-commands then say: "Writes follow the API preference order in SKILL.md" instead of repeating the decision logic.

**Key heuristic: skip the CLI for bulk operations.** If a workflow needs 10+ API calls (e.g., building expertise profiles across a team), go straight to GraphQL or REST. The CLI's per-call overhead (process spawn, auth handshake) makes it impractical for bulk.

**Context-aware write selection.** When reads already established an authenticated API session (e.g., GraphQL set up `AUTH` from a token file), prefer the same auth mechanism for writes rather than shelling out to the CLI.

## Instance-specific values

Any value that is specific to a deployment (instance URL, tenant ID, cloud ID, org name) must include a programmatic discovery method.

**Do not** just hardcode the value and move on. **Do** show how to obtain it:

```markdown
### Discovering your cloudId

The `cloudId` below is for `example.atlassian.net`. To discover it for any instance:
\`\`\`bash
curl -s -u "$AUTH" 'https://example.atlassian.net/_edge/tenant_info' | python -c "import json,sys; print(json.load(sys.stdin)['cloudId'])"
\`\`\`
```
