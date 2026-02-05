---
name: RHDH Dynamic Plugin Export and Package
description: This skill should be used when the user asks to "export dynamic plugin", "package plugin as OCI", "create plugin container image", "publish plugin to registry", "build OCI artifact", "package plugin as tgz", "push plugin to quay.io", "create dynamic plugin archive", "bundle multiple plugins", "generate integrity hash", or mentions exporting, packaging, or publishing an existing Backstage plugin for RHDH deployment. This skill handles the export and packaging workflow after a plugin has been implemented.
---

## Purpose

Export and package Backstage plugins as RHDH dynamic plugins for deployment. This skill covers the build, export, and packaging workflow that transforms a developed plugin into a deployable artifact (OCI image, tgz archive, or npm package).

> **Note:** This skill is for **exporting and packaging** already-implemented plugins. For creating new plugins, use the backend or frontend plugin creation skills first.

## When to Use

Use this skill when you need to:
- Export a plugin as a dynamic plugin package
- Package a plugin as an OCI container image
- Create a tgz archive for HTTP distribution
- Publish a plugin to a container registry
- Bundle multiple plugins into a single image
- Generate integrity hashes for package verification
- Troubleshoot export or packaging issues

## Prerequisites

Before starting, ensure:
- Plugin is built and compiles without errors (`yarn build`)
- Container runtime installed (`podman` or `docker`)
- Access to a container registry (e.g., quay.io) if publishing OCI images
- For backend plugins: Uses new backend system with default export
- For frontend plugins: Has valid Scalprum configuration (auto-generated if not present)

## Workflow Overview

1. **Build Plugin** - Compile TypeScript and verify no errors
2. **Export as Dynamic Plugin** - Create `dist-dynamic/` with RHDH CLI
3. **Package as Artifact** - Create OCI image, tgz, or npm package
4. **Push to Registry** - Publish to container or npm registry
5. **Verify Locally** - Test before deployment (optional)

## Step 1: Build Plugin

Before exporting, ensure the plugin builds successfully:

```bash
cd plugins/<plugin-id>  # or plugins/<plugin-id>-backend
yarn build
yarn tsc  # Verify no TypeScript errors
```

## Step 2: Export as Dynamic Plugin

Run the RHDH CLI export command from the plugin directory:

```bash
npx @red-hat-developer-hub/cli@latest plugin export
```

This creates a `dist-dynamic/` directory containing:
- Compiled JavaScript optimized for dynamic loading
- Modified `package.json` with peer/bundled dependencies
- Config schema (if defined)
- For frontend: `dist-scalprum/` with webpack federated modules

### Export Options

#### Control Shared Dependencies

By default, all `@backstage/*` packages are shared (provided by RHDH at runtime). Override this behavior:

```bash
# Bundle a @backstage package instead of sharing
npx @red-hat-developer-hub/cli@latest plugin export \
  --shared-package '!/@backstage/plugin-notifications/'

# Mark a non-backstage package as shared
npx @red-hat-developer-hub/cli@latest plugin export \
  --shared-package @my-org/shared-utils
```

#### Embed Packages

Embed workspace or third-party packages into the plugin:

```bash
npx @red-hat-developer-hub/cli@latest plugin export \
  --embed-package @my-org/plugin-common \
  --embed-package @my-org/utils
```

#### Combined Example

```bash
npx @red-hat-developer-hub/cli@latest plugin export \
  --shared-package '!/@backstage/plugin-notifications/' \
  --embed-package @internal/common-utils
```

See `references/export-options.md` for all available options.

## Step 3: Package as Artifact

Choose a packaging format based on your deployment needs.

### OCI Image (Recommended for Production)

Create a container image:

```bash
npx @red-hat-developer-hub/cli@latest plugin package \
  --tag quay.io/<namespace>/<plugin-name>:v0.1.0
```

Specify container tool if needed:

```bash
npx @red-hat-developer-hub/cli@latest plugin package \
  --container-tool docker \
  --tag quay.io/<namespace>/<plugin-name>:v0.1.0
```

Available tools: `podman` (default), `docker`, `buildah`

### tgz Archive

Create a tar archive for HTTP distribution:

```bash
cd dist-dynamic
npm pack
```

Get the integrity hash:

```bash
npm pack --json | jq -r '.[0].integrity'
```

### npm Package

Publish to a private npm registry:

```bash
cd dist-dynamic
npm publish --registry https://your-private-registry.com
```

### Multi-Plugin Image

Bundle frontend and backend plugins in one image:

```bash
# Export both plugins first
cd plugins/my-plugin && npx @red-hat-developer-hub/cli@latest plugin export
cd ../my-plugin-backend && npx @red-hat-developer-hub/cli@latest plugin export

# Package together from monorepo root
cd ../..
npx @red-hat-developer-hub/cli@latest plugin package \
  --tag quay.io/<namespace>/my-plugin-bundle:v0.1.0
```

See `references/packaging-formats.md` for detailed format comparison.

## Step 4: Push to Registry

### OCI Image

```bash
# Podman
podman push quay.io/<namespace>/<plugin-name>:v0.1.0

# Docker
docker push quay.io/<namespace>/<plugin-name>:v0.1.0
```

### Private Registry Authentication

Set the auth file environment variable:

```bash
export REGISTRY_AUTH_FILE=~/.config/containers/auth.json
# or
export REGISTRY_AUTH_FILE=~/.docker/config.json
```

### Image Digest

After pushing, get the digest for reproducible deployments:

```bash
podman inspect --format='{{.Digest}}' quay.io/<namespace>/<plugin-name>:v0.1.0
```

Use digest in `dynamic-plugins.yaml`:

```yaml
plugins:
  - package: oci://quay.io/<namespace>/<plugin-name>@sha256:abc123...!<plugin-id>-dynamic
    disabled: false
```

## Step 5: Verify Locally (Optional)

Test the exported plugin before publishing:

```bash
# Copy to local RHDH instance
cp -r dist-dynamic /path/to/rhdh/dynamic-plugins-root/<plugin-id>-dynamic

# Start RHDH and verify plugin loads
yarn workspace backend start
```

Check logs for:
- `loaded dynamic backend plugin` - Success
- `Skipping disabled dynamic plugin` - Plugin disabled in config
- Error messages during initialization

## Configuration Examples

### Backend Plugin

```yaml
plugins:
  - package: oci://quay.io/<namespace>/<plugin-name>:v0.1.0!<plugin-id>-backend-dynamic
    disabled: false
    pluginConfig:
      myPlugin:
        apiUrl: https://api.example.com
```

### Frontend Plugin

```yaml
plugins:
  - package: oci://quay.io/<namespace>/<plugin-name>:v0.1.0!<plugin-id>
    disabled: false
    pluginConfig:
      dynamicPlugins:
        frontend:
          my-org.plugin-my-plugin:
            dynamicRoutes:
              - path: /my-plugin
                importName: MyPage
```

### Multi-Plugin Bundle

```yaml
plugins:
  # Frontend from bundle
  - package: oci://quay.io/<namespace>/my-bundle:v0.1.0!my-plugin
    disabled: false
    pluginConfig:
      dynamicPlugins:
        frontend:
          my-org.plugin-my-plugin:
            mountPoints:
              - mountPoint: entity.page.overview/cards
                importName: MyCard

  # Backend from same bundle
  - package: oci://quay.io/<namespace>/my-bundle:v0.1.0!my-plugin-backend-dynamic
    disabled: false
```

See `examples/dynamic-plugins.yaml` for complete examples.

## Troubleshooting

### Export Fails

**Missing dependencies:**
```bash
yarn add -D <missing-package>
npx @red-hat-developer-hub/cli@latest plugin export
```

**TypeScript errors:**
```bash
yarn tsc
# Fix errors, then retry export
```

**Clear stale artifacts:**
```bash
rm -rf dist dist-dynamic
yarn build
npx @red-hat-developer-hub/cli@latest plugin export
```

### Package Fails

**Container tool not found:**
```bash
# Specify available tool
npx @red-hat-developer-hub/cli@latest plugin package \
  --container-tool docker \
  --tag quay.io/<namespace>/<plugin-name>:v0.1.0
```

**Permission denied:**
```bash
# Check registry login
podman login quay.io
```

### Plugin Not Loading in RHDH

1. Verify package path matches plugin ID
2. Check version compatibility with target RHDH
3. Ensure default export exists (backend plugins)
4. Verify Scalprum name matches (frontend plugins)
5. Check RHDH logs for specific errors

### Integrity Hash Mismatch

Regenerate the hash:
```bash
cd dist-dynamic
npm pack --json | jq -r '.[0].integrity'
```

Update `dynamic-plugins.yaml` with new hash.

## Reference Files

- **`references/export-options.md`** - All export CLI options
- **`references/packaging-formats.md`** - Format comparison and best practices
- **`references/integrity-hashes.md`** - Hash generation and verification

## Example Files

- **`examples/dynamic-plugins.yaml`** - Complete configuration examples
