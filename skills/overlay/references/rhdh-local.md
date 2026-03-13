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

<customization_system>
**Purpose:** The `rhdh-customizations/` copy-sync system manages all configuration overrides without touching the pristine `rhdh-local/` git repo.

**Architecture:**

```
rhdh-local-setup/
├── rhdh-local/               # Upstream git repo (NEVER edit directly)
└── rhdh-customizations/      # Your config files (always edit here)
    ├── apply-customizations.sh   # Copies files INTO rhdh-local/
    ├── remove-customizations.sh  # Deletes copies from rhdh-local/
    ├── .env                      # Environment variables
    ├── compose.override.yaml     # Extra compose services
    └── configs/
        ├── app-config/app-config.local.yaml
        ├── dynamic-plugins/dynamic-plugins.override.yaml
        ├── catalog-entities/*.override.yaml
        └── extra-files/          # e.g. github-app-credentials.yaml
```

**File mapping** (source → destination after `apply-customizations.sh`):

| Source in `rhdh-customizations/` | Destination in `rhdh-local/` |
|----------------------------------|-------------------------------|
| `compose.override.yaml` | `compose.override.yaml` |
| `.env` | `.env` |
| `configs/app-config/app-config.local.yaml` | `configs/app-config/app-config.local.yaml` |
| `configs/dynamic-plugins/dynamic-plugins.override.yaml` | `configs/dynamic-plugins/dynamic-plugins.override.yaml` |
| `configs/catalog-entities/*.override.yaml` | `configs/catalog-entities/*.override.yaml` |
| `configs/extra-files/*` | `configs/extra-files/*` |
| `developer-lightspeed/configs/app-config/app-config.lightspeed.local.yaml` | same path |

**Configuration precedence (lowest → highest):**

1. `rhdh-local/` defaults (`default.env`, `app-config.yaml`, `dynamic-plugins.default.yaml`)
2. Override files copied from `rhdh-customizations/` (`.env`, `app-config.local.yaml`, `dynamic-plugins.override.yaml`)
3. `app-config.local.yaml` loads last (highest precedence among config files)
4. Environment variables from `.env` override `default.env`

**Standard workflow:**

```bash
# 1. Edit customizations (ALWAYS in rhdh-customizations/)
# 2. Sync copies into rhdh-local/
cd rhdh-customizations && ./apply-customizations.sh
# 3. Restart
cd .. && ./down.sh && ./up.sh --customized [flags]
```

**NEVER:**

- Modify files in `rhdh-local/` directly
- Manually copy files — always use `apply-customizations.sh`
- Commit `*.local.yaml`, `*.override.yaml`, `.env` to the rhdh-local repo

**Verify pristine state:**

```bash
cd rhdh-local && git status  # Should show "working tree clean"
```

**What to edit and where:**

| Change | File to edit |
|--------|-------------|
| App configuration | `rhdh-customizations/configs/app-config/app-config.local.yaml` |
| Plugins | `rhdh-customizations/configs/dynamic-plugins/dynamic-plugins.override.yaml` |
| Environment variables | `rhdh-customizations/.env` |
| Extra compose services | `rhdh-customizations/compose.override.yaml` |
| Credentials | `rhdh-customizations/configs/extra-files/github-app-credentials.yaml` |
</customization_system>

<container_lifecycle>
**Critical rule:** Use `up.sh` / `down.sh` scripts — NEVER `podman compose restart` or `podman compose up/down` directly when Lightspeed or Orchestrator are enabled.

**Why:** Several containers share RHDH's network namespace via `network_mode: "service:rhdh"`:

- `lightspeed-core-service` (port 8080)
- `llama-stack` (port 8321)

When RHDH restarts, it gets a NEW network namespace. Containers in `service:rhdh` mode stay in the OLD namespace → **504 Gateway Timeout** even though containers appear "running".

**Startup scripts:**

```bash
./up.sh --customized                  # With customizations (most common)
./up.sh --baseline                    # Pristine RHDH only
./up.sh --customized --lightspeed    # With AI assistant
./up.sh --customized --orchestrator  # With Orchestrator
./up.sh --customized --both --ollama # Everything enabled
./up.sh --customized --follow-logs   # Tail logs after startup
```

**Shutdown scripts:**

```bash
./down.sh                    # Stop (interactive)
./down.sh --keep-volumes     # Keep database for fast restart
./down.sh --volumes          # Full clean slate
```

> `down.sh` removes customization copies from `rhdh-local/`. Reapply before next start:
> `cd rhdh-customizations && ./apply-customizations.sh`

**FORBIDDEN** (when Lightspeed/Orchestrator enabled):

```bash
podman compose restart rhdh
podman compose down && podman compose up -d
podman compose -f compose.yaml -f orchestrator/compose.yaml restart
```

**Exception:** If running ONLY base RHDH (no Lightspeed, no Orchestrator), direct `podman compose restart rhdh` is acceptable for config-only changes.

**Services and network membership:**

| Service | Network | Purpose |
|---------|---------|---------|
| `install-dynamic-plugins` | Independent | Plugin installation (runs once) |
| `rhdh` | Owns namespace | Main application |
| `lightspeed-core-service` | Shares `rhdh` | AI assistant |
| `llama-stack` | Shares `rhdh` | LLM inference |
| `sonataflow` | Independent | Workflow engine |
| `ollama` | Independent | Local LLM runtime |

**Startup flow:**

1. `install-dynamic-plugins` installs plugins from `dynamic-plugins.override.yaml`
2. `rhdh` waits for installation to complete
3. `rhdh` applies config overrides and starts Backstage
4. Network-sharing containers attach to RHDH's namespace
</container_lifecycle>

<common_operations>
**Restart decision table:**

| Situation | Action |
|-----------|--------|
| Changed `dynamic-plugins.override.yaml` | `apply-customizations.sh` → `down.sh` → `up.sh --customized` |
| Changed `app-config.local.yaml` | `apply-customizations.sh` → `down.sh` → `up.sh --customized` |
| Changed `.env` | `apply-customizations.sh` → `down.sh` → `up.sh --customized` |
| Base RHDH only, config change | `apply-customizations.sh` → `podman compose restart rhdh` |
| Update rhdh-local from upstream | `down.sh` → `cd rhdh-local && git pull` → `apply-customizations.sh` → `up.sh --customized` |
| Test pristine (no customizations) | `down.sh` → `up.sh --baseline` |
| Full clean slate | `down.sh --volumes` → `apply-customizations.sh` → `up.sh --customized` |

**Add a plugin:**

```bash
# 1. Edit
code rhdh-customizations/configs/dynamic-plugins/dynamic-plugins.override.yaml
# 2. Sync + restart
cd rhdh-customizations && ./apply-customizations.sh
cd .. && ./down.sh && ./up.sh --customized [flags]
```

**Switch to pristine mode (no customizations):**

```bash
./down.sh
./up.sh --baseline
# Restore when done:
cd rhdh-customizations && ./apply-customizations.sh
cd .. && ./down.sh && ./up.sh --customized [flags]
```

**View logs:**

```bash
./up.sh --customized --follow-logs         # Auto-tail after startup
cd rhdh-local
podman compose logs -f rhdh               # Main RHDH logs
podman compose logs install-dynamic-plugins  # Plugin installation
```

**Troubleshooting: customizations not applied:**

```bash
cd rhdh-customizations && ./apply-customizations.sh
ls -la ../rhdh-local/.env                 # Verify copy exists
ls -la ../rhdh-local/configs/dynamic-plugins/dynamic-plugins.override.yaml
# Verify pristine status clean:
cd ../rhdh-local && git status
```

**Troubleshooting: 504 Gateway Timeout:**

```bash
# Cause: network namespace desync (Lightspeed/Orchestrator running)
./down.sh && ./up.sh --customized --both [flags]  # Full restart required
```

**Share setup with team:**

```bash
./backup.sh  # Creates archive in ~/rhdh-local-backups/
# Recipients follow RESTORE.md inside the archive
```

</common_operations>
