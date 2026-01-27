# Workflow: Fix Build Failure

Debug and resolve CI/publish failures.

<required_reading>
**Read this reference file NOW:**

1. `references/ci-feedback.md` — Error patterns and solutions
</required_reading>

<process>

## Step 1: Read the PR Comment

The publish workflow provides detailed feedback. Look for:

- **Backstage Compatibility Check** — version mismatches
- **"How to fix" section** — specific guidance
- **Failed exports** — which plugin failed

## Step 2: Identify Error Type

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| "incompatible workspaces" | Version mismatch | Add `backstage.json` override |
| "repo-backstage-version does not match" | Wrong version in source.json | Update to match upstream |
| "Export failed" | Build error | Check logs, add patches |

## Step 3: Check Similar Workspaces

```bash
# Find similar workspace
ls workspaces/ | grep -i <similar-pattern>

# Compare structure
diff -r workspaces/<yours>/ workspaces/<similar>/
```

## Step 4: Apply Fix

**For version issues:**

```bash
# Check upstream version
curl -s https://raw.githubusercontent.com/<owner>/<repo>/<commit>/backstage.json | jq .version
```

**For build issues:**

```bash
# Read full logs
gh run view <run-id> --repo redhat-developer/rhdh-plugin-export-overlays --log | grep -i error
```

## Step 5: Re-trigger

```bash
git add .
git commit -m "Fix: <what was fixed>"
git push
```

Comment `/publish` to retry.

</process>

<success_criteria>

- [ ] Error identified
- [ ] Fix applied
- [ ] `/publish` succeeds
</success_criteria>
