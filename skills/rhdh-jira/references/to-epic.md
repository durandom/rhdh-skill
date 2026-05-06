# Create Epic

Create an RHIDP Epic from conversation context. Grills the user on delivery scope, dependencies, and acceptance criteria. Optionally chains into Story/Task decomposition.

## Workflow

### Step 1 — Determine Context

Two entry modes:

- **Chained from Feature**: Context carries down. The Feature's scope, AC, and customer considerations are established. The grill narrows to delivery scope for this team.
- **Standalone**: Full grill. No parent Feature context.

If chained, the parent Feature key is known. If standalone, ask: "Is this Epic part of an existing Feature? [Feature key / no]"

### Step 2 — Grill

Load `assets/templates/epic.txt` for structure and `assets/examples/epic-example.txt` for tone calibration. Follow the challenging behavior in `references/grill.md`.

Ask one question at a time. Adapt based on entry mode.

**Chained grill (narrowed):**

1. **EPIC Goal** — what does *this team's* delivery achieve within the parent Feature?
2. **Dependencies** — internal (other Epics in the Feature) and external (upstream, other teams)
3. **Acceptance Criteria** — team-specific AC. Which checklist items apply? (DEV, QE, DOC)

**Standalone grill (full):**

1. **EPIC Goal** — what are we trying to solve?
2. **Background/Feature Origin** — where did this come from?
3. **Why is this important?**
4. **User Scenarios** — who benefits and how?
5. **Dependencies** — internal and external
6. **Acceptance Criteria** — full checklist

**Jira fields to determine:**

- **Team** — which team owns this Epic?
- **Priority** — inherit from parent Feature if chained, otherwise ask
- **Size** — T-shirt size (XS/S/M/L/XL)
- **Component** — which RHIDP component(s)? See `references/fields.md` for the list.
- **Assignee** — who is the Epic Owner?

### Step 3 — Duplicate Check

Run the pre-creation check from `references/duplicates.md`. Search RHIDP Epics (`issuetype = Epic`).

### Step 4 — Create Epic

Fill the template. Create the issue:

```bash
acli jira workitem create --project RHIDP --type Epic \
  --summary "Epic summary" \
  --description-file /tmp/epic-desc.txt \
  --assignee "ACCOUNT_ID" \
  --priority "Major" \
  --component "Plugins" \
  --yes
```

If a parent Feature exists, link via REST:

```bash
curl -s -X PUT -u "$AUTH" -H "Content-Type: application/json" \
  -d '{"fields": {"parent": {"key": "RHDHPLAN-XXX"}}}' \
  "https://redhat.atlassian.net/rest/api/3/issue/RHIDP-XXX"
```

Set Team and Size via REST — follow API preference order in SKILL.md.

### Step 5 — Comments

Proactively suggest comments for:

- **Decision trail**: architectural decisions made during the grill
- **Elaboration**: technical context, upstream considerations
- **Abandoned paths**: approaches considered but rejected

Add via `acli jira workitem comment --key RHIDP-XXX --comment "text" --yes`.

### Step 6 — Chain Decomposition

After the Epic is created:

> "Break this Epic into Stories/Tasks? [y/N]"

If yes:

1. Discuss the breakdown: what are the deliverable slices?
2. For each slice, invoke the `to-issue` workflow with context carried down:
   - The Epic's goal, AC, and dependencies are established
   - The issue grill narrows to: implementation specifics, story points, approach
3. Each Story/Task is automatically linked to the parent Epic via `parent` field
4. Type inference runs per slice (Story if user-facing, Task if internal)

## Error Handling

| Error | Action |
|-------|--------|
| RHIDP project inaccessible | Stop. User lacks project access. |
| Parent Feature key invalid | Warn. Create Epic without parent link. |
| `acli create` fails | Fall back to REST API. |
| Parent link update fails | Report failure. Epic is created — user can link manually. |

## Caveats

1. **Epic Owner responsibility.** The assignee is the Epic Owner — single point of contact for delivery, works with the Feature Owner to align execution.
2. **Component is required at New status.** Don't skip this during the grill. See `references/fields.md` for the component list.
3. **Multi-team Features create multiple Epics.** When chained from a Feature, each team gets its own Epic. The Feature Owner coordinates across them.
