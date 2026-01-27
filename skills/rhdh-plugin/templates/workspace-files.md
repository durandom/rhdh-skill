# Templates: Workspace Files

Copy-paste templates for workspace configuration files.

<source_json>
## source.json

Defines the upstream source location.

```json
{
  "repo": "https://github.com/<owner>/<repo>",
  "repo-ref": "<commit-sha-or-tag>",
  "repo-flat": false,
  "repo-backstage-version": "<upstream-backstage-version>"
}
```

**Fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `repo` | Yes | Upstream GitHub URL (only `https://github.com/xxx` supported) |
| `repo-ref` | Yes | Target commit SHA or tag |
| `repo-flat` | Yes | `true` if plugins at repo root, `false` if inside workspace folder |
| `repo-backstage-version` | Yes | Backstage version from upstream's `backstage.json` |

**Validate upstream version:**
```bash
curl -s https://raw.githubusercontent.com/<owner>/<repo>/<commit>/backstage.json | jq .version
```

**Example (AWS CodeBuild):**
```json
{
  "repo": "https://github.com/awslabs/backstage-plugins-for-aws",
  "repo-ref": "v0.7.1",
  "repo-flat": false,
  "repo-backstage-version": "1.43.1"
}
```
</source_json>

<plugins_list_yaml>
## plugins-list.yaml

Lists plugin paths to export.

```yaml
# Frontend plugin
- plugins/<name>/frontend:

# Backend plugin
- plugins/<name>/backend:

# With embedded dependencies (for unpublished shared packages)
- plugins/<name>/frontend:
  - --embed-package=@scope/shared-package
```

**Path format:** `plugins/<folder>/<type>:` where type is `frontend`, `backend`, or `common`

**Flags:**
| Flag | Purpose |
|------|---------|
| `--embed-package=<pkg>` | Bundle unpublished shared dependency |

**Example (AWS ECS with embedded package):**
```yaml
- plugins/ecs/frontend:
  - --embed-package=@aws/backstage-plugin-aws-apps-common
- plugins/ecs/backend:
  - --embed-package=@aws/backstage-plugin-aws-apps-common
```

**Example (simple plugin):**
```yaml
- plugins/todo/frontend:
- plugins/todo/backend:
```
</plugins_list_yaml>

<backstage_json>
## backstage.json (Optional)

Override Backstage version for RHDH compatibility.

```json
{
  "version": "<rhdh-target-backstage-version>"
}
```

**When to use:**
- CI reports "incompatible workspaces"
- Upstream version is older than RHDH target

**Important:**
- This is the **override** version (RHDH's target)
- Keep `source.json`'s `repo-backstage-version` as upstream's **actual** version
- CI validates that `repo-backstage-version` matches upstream

**Example:**
```json
{
  "version": "1.45.3"
}
```
</backstage_json>

<codeowners_entry>
## CODEOWNERS Entry

```
/workspaces/<workspace-name>/ @<your-github-username>
```

Append to the `CODEOWNERS` file in repo root.
</codeowners_entry>
