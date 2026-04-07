# Workflow: Enable a Plugin in Local RHDH

<required_reading>
Read before starting:

- `references/customization-system.md` — file mapping and edit rules
- `../overlay/references/rhdh-local.md` section `<dynamic_plugins_config>` — YAML format, OCI references, tag patterns
- `references/troubleshooting.md` — restart patterns and network namespace rules
</required_reading>

<process>
## Step 1: Identify the Plugin

Ask the user which plugin to enable. If unsure, list available plugins:

> **Pre-installed vs OCI plugins:** Check the plugin YAML for `extensions.backstage.io/pre-installed: 'true'`.
>
> - **Pre-installed** — bundled with RHDH, `spec.dynamicArtifact` is a local path like `./dynamic-plugins/dist/...`. No download needed, but may have version-specific issues in a given RHDH build (e.g. `PluginRoot not found`). The `rhdh-local` `CHANGELOG` or known-issues list is the authoritative source.
> - **OCI** — fetched from `ghcr.io` at startup, always the exact tested version. More reliable for third-party plugins.

```bash
curl -s https://api.github.com/repos/redhat-developer/rhdh-plugin-export-overlays/contents/catalog-entities/extensions/plugins \
  | jq -r '.[].name' | sed 's/\.yaml$//'
```

Validate the plugin name exists. If not found, try similar names and ask user to confirm.

---

## Step 2: Fetch Plugin Definition

```bash
curl -s https://raw.githubusercontent.com/redhat-developer/rhdh-plugin-export-overlays/main/catalog-entities/extensions/plugins/<plugin-name>.yaml
```

Extract:

- `metadata.name` — canonical plugin name
- `spec.packages` — list of package names that make up this plugin
- `spec.categories` — plugin category

---

## Step 3: Fetch Package Metadata

For each package in `spec.packages`:

```bash
curl -s https://raw.githubusercontent.com/redhat-developer/rhdh-plugin-export-overlays/main/workspaces/<plugin-name>/metadata/<package-name>.yaml
```

Extract from each:

- `spec.dynamicArtifact` — the OCI reference to use (e.g. `oci://ghcr.io/...`)
- `spec.backstage.role` — `frontend-plugin`, `backend-plugin`, or `backend-plugin-module`
- `spec.appConfigExamples` — example configuration snippets
- `spec.partOf` — which plugin(s) this package belongs to

> **Note:** Some packages live in a different workspace. If not found under `<plugin-name>`, try the workspace derived from the package name (e.g. `backstage-plugin-kubernetes-backend` → `workspaces/kubernetes/`).

---

## Step 4: Add to `dynamic-plugins.override.yaml`

Edit `rhdh-customizations/configs/dynamic-plugins/dynamic-plugins.override.yaml`.

**Critical:** Never remove or overwrite the `includes:` block. Append to the existing `plugins:` list.

If creating from scratch, the file must start with:

```yaml
includes:
  - dynamic-plugins.default.yaml
  - dynamic-plugins.yaml
```

**For a backend plugin (no UI config needed):**

```yaml
plugins:
  - package: 'oci://ghcr.io/redhat-developer/rhdh-plugin-export-overlays/<package>:<tag>!<package>'
    disabled: false
```

**For a frontend plugin (use `spec.appConfigExamples` content):**

```yaml
plugins:
  - package: 'oci://ghcr.io/redhat-developer/rhdh-plugin-export-overlays/<package>:<tag>!<package>'
    disabled: false
    pluginConfig:
      dynamicPlugins:
        frontend:
          <plugin-config-key>:
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

Always use `spec.dynamicArtifact` as the `package:` value — do NOT construct OCI URLs manually.

Backend plugins should be listed before their corresponding frontend plugins.

---

## Step 5: Add Backend Configuration (if needed)

If `spec.appConfigExamples` includes configuration outside the `dynamicPlugins` key, add it to:
`rhdh-customizations/configs/app-config/app-config.local.yaml`

Example:

```yaml
argocd:
  username: ${ARGOCD_USERNAME}
  password: ${ARGOCD_PASSWORD}
  appLocatorMethods:
    - type: config
      instances:
        - name: argoInstance1
          url: ${ARGOCD_INSTANCE1_URL}
```

---

## Step 6: Set Required Environment Variables

If backend config references `${VAR_NAME}` variables, tell the user to add them to `rhdh-customizations/.env` (bare format — no `export`, no quotes):

```
ARGOCD_USERNAME=my-username
ARGOCD_PASSWORD=my-password
```

This file overrides `rhdh-local/default.env`.

---

## Step 7: Present Summary

Before applying, show the user:

- Which packages were added to `dynamic-plugins.override.yaml`
- What app-config was added (if any)
- What environment variables need to be set in `.env`
- The commands from Step 8

---

## Step 8: Apply and Restart

```bash
rhdh local apply
rhdh local down && rhdh local up --customized
```

Add `--lightspeed`, `--orchestrator`, or `--both` flags if those components are enabled.

> **Note:** A full restart is always required — both for plugin changes (new `dynamic-plugins.override.yaml`) and for `app-config` changes. Neither hot-reloads inside the container.

**Verify:**

```bash
cd rhdh-local
podman compose logs install-dynamic-plugins    # Plugin installation
podman compose logs rhdh 2>&1 | tail -50       # RHDH startup
```

</process>

<success_criteria>

- [ ] Plugin packages appear in `dynamic-plugins.override.yaml` with `disabled: false`
- [ ] `rhdh local apply` ran without errors
- [ ] No errors in `podman compose logs install-dynamic-plugins`
- [ ] No errors in `podman compose logs rhdh` related to the plugin
- [ ] RHDH accessible at `http://localhost:7007`
- [ ] (If backend) Health endpoint responds: `curl http://localhost:7007/api/<plugin>/health`
</success_criteria>

<error_handling>
**GitHub API rate limit (403):** Wait and retry, or use `Authorization: token <PAT>` header with curl.

**404 on package metadata:** Try the workspace derived from the package name itself (not the plugin name).

**Plugin not loading:** Check `podman compose logs install-dynamic-plugins` for install errors.

**Homepage 404s after change:** The `includes:` block was likely removed. Ensure `dynamic-plugins.default.yaml` is included.

**Plugin init failure:** One failing module blocks RHDH startup. Check logs for `threw an error during startup`.
</error_handling>
