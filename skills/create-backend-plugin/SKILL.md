---
name: RHDH Backend Dynamic Plugin Bootstrap
description: This skill should be used when the user asks to "create RHDH backend plugin", "bootstrap backend dynamic plugin", "create backstage backend plugin for RHDH", "new backend plugin for Red Hat Developer Hub", "create dynamic backend plugin", "scaffold RHDH backend plugin", "new scaffolder action", "create catalog processor", or mentions creating a new backend plugin, backend module, or server-side functionality for Red Hat Developer Hub or RHDH. This skill is specifically for backend plugins - for frontend plugins, use the separate frontend plugin skill.
---

## Purpose

Bootstrap a new **backend** dynamic plugin for Red Hat Developer Hub (RHDH). RHDH is the enterprise-ready Backstage applicationthat supports dynamic plugins - plugins that can be installed or uninstalled without rebuilding the application.

> **Note:** This skill covers **backend plugins only**. Frontend dynamic plugins have different requirements (Scalprum configuration, mount points, dynamic routes) and are covered in a separate skill.

## When to Use

Use this skill when creating a new **backend** plugin intended for RHDH dynamic plugin deployment. This includes:
- New backend API plugins
- Backend modules for existing plugins (e.g., `catalog-backend-module-*`)
- Scaffolder actions and templates
- Catalog processors and providers
- Authentication modules
- Any server-side functionality for RHDH

**Do NOT use this skill for:**
- Frontend plugins (UI components, pages, cards)
- Frontend plugin wiring (mount points, dynamic routes)
- Themes or frontend customizations

## Prerequisites

Before starting, ensure the following are available:
- Node.js 22+ and Yarn
- Container runtime (`podman` or `docker`)
- Access to a container registry (e.g., quay.io) for publishing

## Workflow Overview

1. **Determine RHDH Version** - Identify target RHDH version for compatibility
2. **Create Backstage App** - Scaffold Backstage app with matching version
3. **Create Backend Plugin** - Generate new backend plugin using Backstage CLI
4. **Implement Plugin Logic** - Write the plugin code using new backend system
5. **Export and Package** - Build, export, and package using RHDH CLI (see export-and-package skill)
6. **Configure for RHDH** - Create dynamic-plugins.yaml configuration

## Step 1: Determine RHDH Version
Check the target RHDH version and find the compatible Backstage version. Consult  `../rhdh/references/versions.md` file for the version compatibility matrix and available RHDH versions.

Ask the user which RHDH version they are targeting if not specified.

## Step 2: Create Backstage Application

Create a new Backstage application in the current directory using the version-appropriate create-app:

```bash
# For RHDH 1.8 (adjust version as needed)
echo "backstage" | npx @backstage/create-app@0.7.3 --path .
```

After creation, install dependencies:

```bash
yarn install
```

 The only purpose this serves is to ensure you can later create the plugin using the correct version of the Backstage CLI. All development and testing will be done in the plugin directory.


## Step 3: Create Backend Plugin

Generate a new backend plugin using the Backstage CLI:

```bash
yarn new
```

When prompted:
1. Select **"backend-plugin"** as the plugin type
2. Enter a plugin ID (e.g., `my-plugin`)
3. The plugin will be created at `plugins/<plugin-id>-backend/`

The generated plugin structure:

```
plugins/<plugin-id>-backend/
├── src/
│   ├── index.ts           # Main entry point
│   ├── plugin.ts          # Plugin definition (new backend system)
│   └── service/
│       └── router.ts      # Express router
├── package.json
└── README.md
```

## Step 4: Implement Plugin Logic

Backend plugins must use the **new backend system** for dynamic plugin compatibility. The plugin entry point should export a default using `createBackendPlugin()` or `createBackendModule()`.

Example plugin structure (`src/plugin.ts`):

```typescript
import {
  coreServices,
  createBackendPlugin,
} from '@backstage/backend-plugin-api';
import { createRouter } from './service/router';

export const myPlugin = createBackendPlugin({
  pluginId: 'my-plugin',
  register(env) {
    env.registerInit({
      deps: {
        httpRouter: coreServices.httpRouter,
        logger: coreServices.logger,
        config: coreServices.rootConfig,
      },
      async init({ httpRouter, logger, config }) {
        httpRouter.use(
          await createRouter({
            logger,
            config,
          }),
        );
        httpRouter.addAuthPolicy({
          path: '/health',
          allow: 'unauthenticated',
        });
      },
    });
  },
});

export default myPlugin;
```

The `src/index.ts` must export the plugin as default:

```typescript
export { default } from './plugin';
```

Build and verify the plugin compiles:

```bash
cd plugins/<plugin-id>-backend
yarn build
```

## Step 5: Export and Package

Export the plugin as a dynamic plugin and package it for deployment. For detailed export and packaging options, see the **export-and-package** skill.

### Quick Export

```bash
cd plugins/<plugin-id>-backend
npx @red-hat-developer-hub/cli@latest plugin export
```

This creates `dist-dynamic/` with the dynamic plugin package.

### Quick Package and Push

```bash
npx @red-hat-developer-hub/cli@latest plugin package \
  --tag quay.io/<namespace>/<plugin-name>:v0.1.0

podman push quay.io/<namespace>/<plugin-name>:v0.1.0
```

For advanced options (dependency handling, multi-plugin bundles, tgz/npm packaging), consult the **export-and-package** skill.

## Step 6: Configure for RHDH

Create the dynamic plugin configuration for RHDH. Add to `dynamic-plugins.yaml`:

```yaml
plugins:
  - package: oci://quay.io/<namespace>/<plugin-name>:v0.1.0!<plugin-id>-backend-dynamic
    disabled: false
    pluginConfig:
      # Plugin-specific configuration (optional)
      myPlugin:
        someOption: value
```

For local development/testing, copy `dist-dynamic` to RHDH's `dynamic-plugins-root`:

```bash
cp -r dist-dynamic /path/to/rhdh/dynamic-plugins-root/<plugin-id>-backend-dynamic
```

See `examples/dynamic-plugins.yaml` for a complete configuration example.

## Common Issues

### Plugin Not Loading
- Verify plugin uses new backend system (`createBackendPlugin`)
- Check plugin is exported as default export
- Ensure version compatibility with target RHDH

### Dependency Conflicts
- Use `--shared-package` to exclude problematic shared deps
- Use `--embed-package` to bundle required deps

### Build Failures
- Run `yarn tsc` to check TypeScript errors before export
- Ensure all `@backstage/*` versions match target RHDH

## Additional Resources

### Related Skills

- **export-and-package** - Complete export/packaging workflow (OCI, tgz, npm)

### Reference Files

- **`rhdh/references/versions.md`** - Complete version compatibility matrix

### Example Files

- **`examples/dynamic-plugins.yaml`** - Example RHDH plugin configuration

### External Resources

- [RHDH Dynamic Plugins Documentation](https://github.com/redhat-developer/rhdh/tree/main/docs/dynamic-plugins)
- [Backstage New Backend System](https://backstage.io/docs/backend-system/)
