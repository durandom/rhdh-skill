# Workflow: Review rhdh-operator PR on Live Cluster

Fetch a PR's CI-built operator image, swap it into a running RHDH cluster, and generate a targeted review checklist from the diff.

<required_reading>

Read these reference files before starting:

1. `../references/operator-pr-images.md` — Image naming, extraction, validation
2. `../../rhdh/references/github-reference.md` — gh CLI patterns

</required_reading>

<prerequisites>

| Requirement | Details |
|-------------|---------|
| **Input** | PR number for rhdh-operator (or full PR URL) |
| **Access** | Read access to `redhat-developer/rhdh-operator` |
| **Tools** | `gh` CLI authenticated, `oc` CLI available |
| **Cluster** | Running OpenShift cluster (will offer to deploy if no RHDH instance) |

</prerequisites>

<process>

## Phase 1: Fetch PR Context

```bash
REPO="redhat-developer/rhdh-operator"
PR_NUMBER=<number>

gh pr view $PR_NUMBER --repo $REPO \
  --json number,title,state,author,body,files,createdAt,headRefOid
```

Validate:
- PR state is `OPEN` (warn if merged or closed — images may still work but PR is not active)
- PR belongs to `redhat-developer/rhdh-operator`

Fetch the diff for later checklist generation:

```bash
gh pr diff $PR_NUMBER --repo $REPO
```

Save the changed file list for Phase 5:

```bash
gh pr view $PR_NUMBER --repo $REPO --json files --jq '.files[].path'
```

---

## Phase 2: Extract CI-Built Images

Follow `../references/operator-pr-images.md`:

1. Use `<extracting_from_pr>` to find CI-posted image URLs from the PR comments
2. Parse out the three image URLs (operator, operator-bundle, operator-catalog)
3. If no comment found, check CI workflow status using the fallback commands
4. Use `<validation>` to verify the operator image exists in the registry

---

## Phase 3: Ensure a Running RHDH Cluster

### 3.1 Verify cluster access

```bash
oc whoami 2>&1
oc cluster-info 2>/dev/null | head -2
```

### 3.2 Check for running RHDH operator

```bash
oc get deployment -A -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name \
  --no-headers 2>/dev/null | grep -i rhdh-operator
```

### 3.3 Check for Backstage CR

```bash
oc get backstage -A 2>/dev/null
```

### 3.4 Decision tree

| Cluster state | Action |
|---------------|--------|
| Operator running + Backstage CR exists | Skip to Phase 4 |
| Cluster accessible but no RHDH operator | Deploy RHDH on existing cluster (see 3.5b) |
| No cluster access (`oc whoami` fails) | Provision a cluster via rhdh-test-instance PR (see 3.5a) |

### 3.5 Provision or deploy RHDH

Use `redhat-developer/rhdh-test-instance` — see `../../rhdh/references/rhdh-repos.md` for its capabilities, Makefile targets, and `/test deploy` slash commands. Read the repo's own README for full usage.

- **No cluster at all** (`oc whoami` fails) → use the rhdh-test-instance PR workflow: comment `/test deploy operator <version> 4h` on a PR via `gh pr comment`. Use a 4h TTL (reviews are short-lived). Match the version to the PR's target branch.
- **Cluster accessible but no RHDH** → use rhdh-test-instance locally: `make install-operator` then `make deploy-operator`. Read the repo's README for `.env` setup.

Once the operator and Backstage CR are healthy, proceed to Phase 4.

---

## Phase 4: Swap Operator Image

### 4.1 Detect install method

```bash
oc get subscription -A 2>/dev/null | grep -i rhdh
```

- If Subscription found → **OLM-managed** (use 4.4a)
- If no Subscription → **direct deployment** (use 4.4b)

### 4.2 Identify operator deployment and namespace

```bash
OPERATOR_NS=$(oc get deployment -A --no-headers \
  -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name \
  | grep rhdh-operator | awk '{print $1}')

OPERATOR_DEPLOY=$(oc get deployment -n $OPERATOR_NS --no-headers \
  -o custom-columns=NAME:.metadata.name | grep rhdh-operator)
```

### 4.3 Record current image (for rollback)

```bash
CURRENT_IMAGE=$(oc get deployment $OPERATOR_DEPLOY -n $OPERATOR_NS \
  -o jsonpath='{.spec.template.spec.containers[?(@.name=="manager")].image}')
echo "Current operator image: $CURRENT_IMAGE"
```

### 4.4a Swap image — OLM-managed install

**IMPORTANT:** Do NOT use `oc set image` or patch the Deployment directly — OLM owns the Deployment and will overwrite any direct changes. Patch the CSV instead.

```bash
PR_IMAGE="quay.io/rhdh-community/operator:<tag>"

# Find the CSV name
CSV_NAME=$(oc get csv -n $OPERATOR_NS --no-headers \
  -o custom-columns=NAME:.metadata.name | grep rhdh)

# Record current CSV image for rollback
CSV_CURRENT_IMAGE=$(oc get csv $CSV_NAME -n $OPERATOR_NS \
  -o jsonpath='{.spec.install.spec.deployments[0].spec.template.spec.containers[0].image}')
echo "Current CSV image: $CSV_CURRENT_IMAGE"

# Patch the CSV to use the PR image
oc patch csv $CSV_NAME -n $OPERATOR_NS --type='json' \
  -p="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/image\", \"value\": \"$PR_IMAGE\"}]"
```

OLM will detect the CSV change and roll out a new operator pod automatically.

### 4.4b Swap image — direct deployment (non-OLM)

```bash
PR_IMAGE="quay.io/rhdh-community/operator:<tag>"

oc set image deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS \
  manager=$PR_IMAGE
```

### 4.5 Wait for rollout

```bash
oc rollout status deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS --timeout=120s
```

### 4.6 Verify the swap

```bash
# Confirm new image is running
oc get deployment $OPERATOR_DEPLOY -n $OPERATOR_NS \
  -o jsonpath='{.spec.template.spec.containers[0].image}'

# Check pod is healthy
oc get pods -n $OPERATOR_NS -l control-plane=controller-manager

# Check operator logs for errors
oc logs deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS --tail=20

# Check Backstage CR health
RHDH_NS=$(oc get backstage -A --no-headers 2>/dev/null | head -1 | awk '{print $1}')
if [ -n "$RHDH_NS" ]; then
  oc get backstage -n $RHDH_NS
  oc get pods -n $RHDH_NS
fi
```

### 4.7 Record rollback commands

Record rollback commands for Phase 7. Do not present them yet — they will be included in the findings report.

**OLM-managed — restore CSV image:**

```bash
oc patch csv $CSV_NAME -n $OPERATOR_NS --type='json' \
  -p="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/image\", \"value\": \"$CSV_CURRENT_IMAGE\"}]"
```

**Non-OLM — revert deployment image:**

```bash
oc set image deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS \
  manager=$CURRENT_IMAGE
```

---

## Phase 5: Generate Review Checklist

Analyze the diff from Phase 1 and categorize changed files:

| File pattern | Category | Review focus |
|-------------|----------|--------------|
| `api/`, `*_types.go` | CRD/API | New fields, deprecations, backward compatibility |
| `internal/controller/`, `pkg/model/` | Controller/Reconciler | Reconciliation behavior, status updates, edge cases |
| `config/profile/`, `default-config/` | Default config | Verify defaults applied, check for regressions |
| `*_test.go`, `integration_tests/` | Tests | Run the new/modified tests |
| `.github/`, `Makefile`, `Dockerfile` | Build/CI | Verify builds still work |
| `docs/`, `*.md` | Documentation | Review for accuracy |
| `go.mod`, `go.sum` | Dependencies | Check for major version bumps |

### Generate the checklist

For each category with changes, generate specific verification items.

**Always include these baseline checks:**

```markdown
### Baseline Checks
- [ ] Operator pod started successfully with PR image (no crash loops)
- [ ] Operator logs show no errors (`oc logs deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS --tail=50`)
- [ ] Existing Backstage CR reconciled without errors
- [ ] RHDH pods are running and healthy
```

**CRD/API changes — add:**

```markdown
### CRD/API Verification
- [ ] Apply a Backstage CR with the new/changed field(s) set
- [ ] Apply a Backstage CR without the new field(s) — verify backward compatibility
- [ ] Verify existing CRs still reconcile correctly after CRD update
- [ ] Check `oc explain backstage.spec.<new-field>` shows correct schema
```

**Controller/Reconciler changes — add:**

```markdown
### Controller Verification
- [ ] Check operator logs during reconciliation for the changed code paths
- [ ] Verify status conditions update correctly on the Backstage CR
- [ ] Test with multiple Backstage CRs (if applicable)
- [ ] Delete and recreate a Backstage CR — verify clean reconciliation
```

**Default config changes — add:**

```markdown
### Default Config Verification
- [ ] Deploy a fresh Backstage CR with defaults only
- [ ] Verify changed defaults are applied to the RHDH deployment
- [ ] Compare pod spec / configmaps before and after the change
```

**Test changes — add:**

```markdown
### Tests
- [ ] `make test` — unit tests pass
- [ ] `make integration-test USE_EXISTING_CLUSTER=true USE_EXISTING_CONTROLLER=true` — integration tests pass against live cluster
```

**Dependency changes — add:**

```markdown
### Dependency Review
- [ ] Review `go.mod` diff for major version bumps
- [ ] Check if new dependencies have acceptable licenses
```

**End the checklist with:**

```markdown
### Rollback
When done testing, rollback the operator image:
[rollback commands from Phase 4.7]
```

---

## Phase 6: Active Verification

Test the PR's actual changes on the live cluster. Use the diff from Phase 1 and the operator architecture from `../../rhdh/references/rhdh-repos.md` to understand what changed.

### 6.1 Analyze the diff

Read the diff hunks from Phase 1. For each changed file, understand:

- What the code did **before** the change
- What it does **after**
- What behavioral difference this introduces on a running cluster

### 6.2 Propose a verification plan

Based on the analysis, propose a concrete plan to the user:

- What cluster actions will exercise the changed code paths
- What to observe (logs, pod spec, CR status, events) to confirm the fix works
- What constitutes a pass or fail

**Wait for the user to accept the plan before proceeding.**

### 6.3 Execute the plan

Run the accepted verification steps on the cluster. Capture evidence (operator logs, pod specs, events, CR status) as you go.

---

## Phase 7: Findings & Recommendations

Synthesize the verification results and provide a complete review assessment.

### 7.1 Verification summary

Summarize what was tested and the results:

| Category | Test performed | Result | Evidence |
|---|---|---|---|
| *[category]* | *[what was tested]* | Pass/Fail | *[key observation]* |

### 7.2 Best practice assessment

Review the PR's approach against operator development best practices. Reference `../../rhdh/references/rhdh-repos.md` for operator conventions:

- Does the change follow the existing reconciliation flow pattern (preprocess → init model → apply → cleanup → status)?
- Are status conditions updated appropriately for new features or error cases?
- Are new ConfigMap/Secret references watched via `rhdh.redhat.com/ext-config-sync` label?
- Is error handling consistent with existing controller patterns (wrapped errors, retryable vs terminal)?
- Are new CRD fields documented with appropriate kubebuilder markers?
- Does the code avoid non-deterministic iteration patterns (sorted keys, stable ordering)?

### 7.3 Security review

Evaluate the changes from a security perspective:

- Are new environment variables or secrets handled safely (no plaintext logging, proper RBAC)?
- Do RBAC changes follow least-privilege principle?
- Are container image references pinned by digest where appropriate?
- Are new network exposures (ports, routes, service accounts) intentional and documented?
- Do dependency updates (`go.mod`) introduce known CVEs?
- Are user-supplied inputs validated before use in resource names or labels?

### 7.4 Improvement suggestions

Based on the findings, suggest concrete improvements if any:

- Code changes needed (reference specific files and lines from the diff)
- Missing test coverage for the changed code paths
- Documentation gaps
- Configuration or operational concerns

### 7.5 Rollback instructions

Present the rollback commands recorded in Phase 4.7:

**OLM-managed — restore CSV image:**

```bash
oc patch csv $CSV_NAME -n $OPERATOR_NS --type='json' \
  -p="[{\"op\": \"replace\", \"path\": \"/spec/install/spec/deployments/0/spec/template/spec/containers/0/image\", \"value\": \"$CSV_CURRENT_IMAGE\"}]"
```

**Non-OLM — revert deployment image:**

```bash
oc set image deployment/$OPERATOR_DEPLOY -n $OPERATOR_NS \
  manager=$CURRENT_IMAGE
```

</process>

<action_triggers>

| Trigger | Type | What | Resume When |
|---------|------|------|-------------|
| No CI images found | Wait | CI workflow may still be running | Workflow completes and posts comment |
| Images expired | Stop | PR images past 14-day TTL | Author pushes new commit to retrigger CI |
| No cluster access | Stop | User needs to `oc login` | User logs in and re-runs skill |
| No RHDH instance | Deploy | Deploy via rhdh-test-instance `make install-operator && make deploy-operator` | Operator and Backstage CR are running |

</action_triggers>

<tracking>

## Activity Logging

```bash
$RHDH log add "Review PR #<number> (rhdh-operator): swapped image <tag>, generated checklist" \
  --tag review-pr --tag rhdh-operator

$RHDH log add "PR #<number> active verification: <categories tested>, results: <pass/fail summary>" \
  --tag review-pr --tag rhdh-operator

$RHDH log add "PR #<number> review findings: <summary>" \
  --tag review-pr --tag rhdh-operator
```

## Follow-up Todos

```bash
$RHDH todo add "Follow up on PR #<number> finding: <description>" --context "review-pr"

$RHDH todo add "Rollback operator image on cluster after PR #<number> review" --context "review-pr"
```

</tracking>

<success_criteria>

Review is complete when:

- [ ] PR images identified from CI comment
- [ ] Images validated as existing in Quay registry
- [ ] Cluster has RHDH operator running with PR image
- [ ] Operator pod is healthy (no crash loops)
- [ ] Backstage CR reconciles successfully
- [ ] Review checklist generated from diff analysis
- [ ] Active verification plan proposed and accepted by user
- [ ] Verification executed with evidence captured
- [ ] Findings summary with pass/fail
- [ ] Best practice and security assessment completed
- [ ] Rollback instructions documented and shared with user
- [ ] Activity logged

</success_criteria>
