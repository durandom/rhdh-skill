# Reference: RHDH Local Testing

Patterns for testing dynamic plugins locally using [RHDH Local](https://github.com/redhat-developer/rhdh-local).

<overview>
**Purpose:** Test dynamic plugins before PR merge using PR artifacts from the overlay repo CI.

**When to use:**

- Phase 5 of onboard/update workflows
- Verifying plugin functionality before requesting review
- Debugging plugin issues locally

**What you can test:**

- Plugin loads without errors
- Entity cards render on catalog pages
- Plugin appears in Extensions Catalog
- Backend health endpoints respond
</overview>

<setup>
**Prerequisites:**
- Podman 5.4.1+ or Docker 28.1.0+ with Compose
- RHDH Local cloned as submodule in `repo/rhdh-local`

**Basic startup:**

```bash
cd repo/rhdh-local
podman compose up -d
# Access at http://localhost:7007
# Login as Guest
```

</setup>

<dynamic_plugins_config>
**File:** `configs/dynamic-plugins/dynamic-plugins.override.yaml`

**Template:**

```yaml
includes:
  - dynamic-plugins.default.yaml

plugins:
  # Backend plugin (no pluginConfig needed for most backends)
  - package: oci://ghcr.io/redhat-developer/rhdh-plugin-export-overlays/<package>-backend:<tag>!<package>-backend
    disabled: false

  # Frontend plugin (needs pluginConfig for mount points)
  - package: oci://ghcr.io/redhat-developer/rhdh-plugin-export-overlays/<package>:<tag>!<package>
    disabled: false
    pluginConfig:
      dynamicPlugins:
        frontend:
          <scope>.<plugin-name>:
            mountPoints:
              - mountPoint: entity.page.overview/cards
                importName: <CardComponent>
                config:
                  layout:
                    gridColumn: "1 / span 6"
                  if:
                    anyOf:
                      - hasAnnotation: <annotation-key>
```

**Tag patterns:**

| Format | When Used | Example |
|--------|-----------|---------|
| `pr_<number>__<version>` | PR artifacts (before merge) | `pr_1873__0.8.0` |
| `bs_<backstage>__<version>` | Released artifacts | `bs_1.45.3__0.8.0` |

**Finding the OCI reference:**

```bash
# Check PR /publish comment for exact OCI URLs
gh pr view <number> --repo redhat-developer/rhdh-plugin-export-overlays --comments
```

**Copying pluginConfig from metadata:**
Look in `workspaces/<plugin>/metadata/<package>.yaml` for `appConfigExamples`.
</dynamic_plugins_config>

<test_entities>
**File:** `configs/catalog-entities/components.override.yaml`

**Purpose:** Create a catalog entity with the required annotations so the plugin card appears.

**Template:**

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: <plugin>-test-service
  description: Test entity for <plugin> plugin verification
  annotations:
    # Add the annotation(s) required by the plugin
    <annotation-key>: <test-value>
spec:
  type: service
  lifecycle: experimental
  owner: user:default/guest
```

**Common annotation patterns:**

| Plugin Family | Annotation Key | Example Value |
|---------------|----------------|---------------|
| AWS CodePipeline | `aws.amazon.com/aws-codepipeline-arn` | `arn:aws:codepipeline:us-east-1:000000000000:test` |
| AWS CodeBuild | `aws.amazon.com/aws-codebuild-project-arn` | `arn:aws:codebuild:us-east-1:000000000000:project/test` |
| Tekton | `janus-idp.io/tekton` | `<namespace>` |
| ArgoCD | `argocd/app-name` | `<app-name>` |

> ⚠️ Check the plugin's README or metadata file for required annotations.
</test_entities>

<extensions_catalog_visibility>
**Goal:** Make Plugin entities visible in the Extensions Catalog UI at `/extensions/catalog`.

**Requires two files:**

**1. `compose.override.yaml`** (in rhdh-local root):

```yaml
services:
  rhdh:
    volumes:
      # Mount Plugin entities from overlay repo
      - type: bind
        source: ../rhdh-plugin-export-overlays/catalog-entities/extensions/plugins/
        target: /marketplace/catalog-entities/plugins
        read_only: true
```

> ⚠️ The path is `extensions/plugins/` not `marketplace/plugins/`. Adjust `source:` if repos are in different locations.

**2. `configs/app-config/app-config.local.yaml`:**

```yaml
# YAML arrays don't merge - must include ALL default locations
catalog:
  rules:
    - allow: [Component, API, Location, Template, Domain, User, Group, System, Resource, Plugin, Package]

  locations:
    # === Default locations (copy from app-config.yaml) ===
    - type: file
      target: /opt/app-root/src/catalog-info.yaml
    - type: file
      target: /opt/app-root/src/configs/catalog-entities/users.yaml
      rules:
        - allow: [User, Group]
    - type: file
      target: /opt/app-root/src/configs/catalog-entities/components.override.yaml
    - type: url
      target: https://github.com/redhat-developer/red-hat-developer-hub-software-templates/blob/main/templates/create-frontend-plugin/template.yaml
      rules:
        - allow: [Template]
    - type: url
      target: https://github.com/redhat-developer/red-hat-developer-hub-software-templates/blob/main/templates/create-backend-plugin/template.yaml
      rules:
        - allow: [Template]
    - type: url
      target: https://github.com/redhat-developer/red-hat-developer-hub-software-templates/blob/main/templates/github/techdocs/template.yaml
      rules:
        - allow: [Template]
    - type: url
      target: https://github.com/redhat-developer/red-hat-developer-hub-software-templates/blob/main/templates/github/register-component/template.yaml
      rules:
        - allow: [Template]

    # === Extensions Catalog ===
    - type: file
      target: /marketplace/catalog-entities/plugins/all.yaml
      rules:
        - allow: [Location, Plugin]
```

**Critical:** The `rules` must include both `Location` (for the index file) and `Plugin` (for individual entities).
</extensions_catalog_visibility>

<commands>
**Start/stop:**
```bash
podman compose up -d                    # Start
podman compose down                     # Stop
podman compose down && podman compose up -d  # Full restart (required for volume changes)
```

**Reinstall plugins (after changing dynamic-plugins.override.yaml):**

```bash
podman compose run install-dynamic-plugins
podman compose restart rhdh
```

**View logs:**

```bash
podman compose logs rhdh                        # All logs
podman compose logs rhdh 2>&1 | tail -50        # Recent logs
podman compose logs rhdh 2>&1 | grep -i <plugin> # Plugin-specific
podman compose logs install-dynamic-plugins     # Plugin installation logs
```

**Check mounts inside container:**

```bash
podman exec rhdh ls -la /marketplace/catalog-entities/plugins/
podman exec rhdh ls -la /opt/app-root/src/configs/
```

**Verify backend health:**

```bash
curl http://localhost:7007/api/<plugin>/health
# Expected: {"status":"ok"}
```

</commands>

<troubleshooting>

| Symptom | Cause | Solution |
|---------|-------|----------|
| File not found in container | Volume mounted before file created | Full restart: `podman compose down && podman compose up -d` |
| Plugin not loading | Package name mismatch | Check OCI URL matches exactly from PR comment |
| Card not appearing on entity | Missing annotation | Add required annotation to test entity |
| Plugin not in Extensions Catalog | Missing app-config.local.yaml | Create file with `Plugin` in rules and locations |
| "Location not allowed" error | Missing `Location` in rules | Add `Location` to catalog rules allow list |
| Plugin validation error in logs | Schema mismatch | Check Plugin entity YAML against schema |

**Debug steps:**

1. Check plugin installer logs: `podman compose logs install-dynamic-plugins`
2. Check RHDH startup logs: `podman compose logs rhdh | head -100`
3. Verify files mounted: `podman exec rhdh ls /path/to/expected/file`
4. Check catalog processing: `podman compose logs rhdh 2>&1 | grep -i catalog`
</troubleshooting>

<verification_checklist>
**Plugin loads correctly:**

- [ ] No errors in `podman compose logs rhdh`
- [ ] Backend health endpoint returns `{"status":"ok"}`

**Entity card works:**

- [ ] Test entity visible in catalog at `/catalog`
- [ ] Plugin card renders on entity Overview tab
- [ ] Card shows expected content (errors about credentials are OK)

**Extensions Catalog (optional):**

- [ ] Plugin appears in `/extensions/catalog`
- [ ] Plugin name, description, categories display correctly
</verification_checklist>

<cleanup>
After testing, remove override files (don't commit to rhdh-local):
```bash
rm configs/dynamic-plugins/dynamic-plugins.override.yaml
rm configs/catalog-entities/components.override.yaml
rm compose.override.yaml
rm configs/app-config/app-config.local.yaml
podman compose down
```
</cleanup>
