# Create Feature

Create a RHDHPLAN Feature from conversation context. Grills the user on scope, customer value, and acceptance criteria before creating. Optionally chains into Epic decomposition.

## Workflow

### Step 1 — Grill

Interview the user to fill the Feature template sections. Load `assets/templates/feature.txt` for structure and `assets/examples/feature-example.txt` for tone calibration. Follow the challenging behavior in `references/grill.md`.

**Feature-specific questions** (one at a time, carry forward existing context):

1. **Feature Overview** — what is this? Elevator pitch.
2. **Goals** — what does the user get? Which persona benefits?
3. **Requirements / Acceptance Criteria** — what must be true for this to be complete? Include non-functional requirements (security, performance, scalability).
4. **Out of Scope** — what is explicitly NOT included?
5. **Customer Considerations** — any customer-specific context?
6. **Documentation Considerations** — what docs need creating/updating?
7. **Upstream engagement** — does this need Backstage community alignment?

**Jira fields to determine:**

- **Team** — which team owns this Feature?
- **Priority** — Blocker/Critical/Major/Minor
- **Size** — T-shirt size (XS/S/M/L/XL). The grill behavior handles sizing challenges.
- **Assignee** — who is the Feature Owner?
- **Labels** — `demo` if customer-facing, `rhdh-X.Y-candidate` if targeting a release, `stretch` if stretch goal

### Step 2 — Duplicate Check and Feature Request Link

Before creating, run the pre-creation check from `references/duplicates.md` using the proposed summary. Search RHDHPLAN Features specifically (`issuetype = Feature`).

Also search for accepted Feature Requests that this Feature may originate from:

```bash
jql: "project = RHDHPLAN AND issuetype = 'Feature Request' AND status = Accepted AND summary ~ \"KEYWORD1 KEYWORD2\""
```

If a matching Feature Request is found: "Found accepted Feature Request {KEY}: {summary}. Link this Feature to it?" If yes, add a `Related` issue link after creation.

If a likely duplicate Feature is found, present it and ask: "This may already exist as {KEY}: {summary}. Use the existing issue instead?"

### Step 3 — Create Feature

Fill the template with grill results. Save to a temp file. Create the issue:

```bash
acli jira workitem create --project RHDHPLAN --type Feature \
  --summary "Feature summary" \
  --description-file /tmp/feature-desc.txt \
  --assignee "ACCOUNT_ID" \
  --priority "Major" \
  --label "rhdh-2.1-candidate" \
  --yes
```

Set additional fields via REST if needed (Team, Size) — follow API preference order in SKILL.md.

### Step 4 — Comments

After creation, proactively suggest adding comments for context that doesn't belong in the description:

- **Decision trail**: "During discussion, we considered [alternative approach] but decided against it because [reason]. Worth capturing as a comment?"
- **Elaboration**: "The customer context you mentioned about [specific customer need] — add as a comment for stakeholder context?"
- **Abandoned paths**: "You mentioned initially thinking about [approach] before pivoting. Capture this for future reference?"

Add each approved comment via:

```bash
acli jira workitem comment --key RHDHPLAN-XXX --comment "comment text" --yes
```

### Step 5 — Chain Decomposition

After the Feature is created:

> "Break this Feature into Epics? The RHDH process typically creates Epics per team (Eng, QE, Doc). [y/N]"

If yes:

1. Ask: "Which teams are involved?" Default suggestion: Eng + Doc (QE is often covered within the Eng epic).
2. For each team, invoke the `to-epic` workflow with context carried down from this Feature:
   - The Feature's scope, AC, and customer considerations are established — don't re-grill on these
   - The Epic grill narrows to: delivery scope for *this team*, dependencies, team-specific AC
3. Each Epic is automatically linked to the parent Feature via `parent` field

## Error Handling

| Error | Action |
|-------|--------|
| RHDHPLAN project inaccessible | Stop. User lacks project access. |
| `acli create` fails | Fall back to REST API. See SKILL.md Error Handling. |
| Duplicate check finds match | Present match. If user confirms duplicate, open existing issue instead. |
| Team field update fails via acli | Fall back to REST. See `references/rest-api-fallback.md`. |

## Caveats

1. **Feature Owner responsibility.** Creating a Feature implies ownership. Ensure the assignee understands the Feature Owner responsibilities defined in the RHDH Agile Workflow (single point of contact, coordinates cross-team dependencies, ensures sizing and labels).
2. **Candidate label convention.** The label format is `rhdh-X.Y-candidate` (e.g., `rhdh-2.1-candidate`). Ask which release this targets during the grill.
3. **Description stays structured.** Only template sections go in the description. Decision trail, elaboration, and abandoned approaches go in comments.
