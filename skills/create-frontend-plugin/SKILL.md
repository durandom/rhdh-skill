---
name: RHDH Frontend Dynamic Plugin Bootstrap
description: This skill should be used when the user asks to "create RHDH frontend plugin", "bootstrap frontend dynamic plugin", "create UI plugin for RHDH", "new frontend plugin for Red Hat Developer Hub", "add entity card to RHDH", "create dynamic route", "add sidebar menu item", "configure mount points", "create theme plugin", or mentions creating frontend components, UI pages, entity cards, or visual customizations for Red Hat Developer Hub or RHDH. This skill is specifically for frontend plugins - for backend plugins, use the separate backend plugin skill.
---

## Purpose

Bootstrap a new **frontend** dynamic plugin for Red Hat Developer Hub (RHDH). Frontend dynamic plugins provide UI components, pages, entity cards, themes, and visual customizations that integrate with the RHDH application shell.

> **Note:** This skill covers **frontend plugins only**. Backend dynamic plugins (APIs, scaffolder actions, processors) are covered in a separate skill.

## When to Use

Use this skill when creating a new **frontend** plugin intended for RHDH dynamic plugin deployment. This includes:
- New pages and routes
- Entity page cards and tabs
- Sidebar menu items
- Custom themes
- Scaffolder field extensions
- TechDocs addons
- Search result types and filters
- Any UI component for RHDH

**Do NOT use this skill for:**
- Backend API plugins
- Scaffolder actions (server-side)
- Catalog processors or providers
- Authentication modules

## Prerequisites

Before starting, ensure the following are available:
- Node.js 22+ and Yarn
- Container runtime (`podman` or `docker`)
- Access to a container registry (e.g., quay.io) for publishing

## Workflow Overview

1. **Determine RHDH Version** - Identify target RHDH version for compatibility
2. **Create Backstage App** - Scaffold Backstage app with matching version
3. **Create Frontend Plugin** - Generate new frontend plugin using Backstage CLI
4. **Implement Plugin Components** - Build React components and exports
5. **Configure Scalprum** - Set up module federation for dynamic loading
6. **Export and Package** - Build, export, and package using RHDH CLI (see export-and-package skill)
7. **Configure Plugin Wiring** - Define routes, mount points, and menu items

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


## Step 3: Decide if you want to use RHDH themes. 

If you want to use RHDH themes, follow the steps below. If you don't want to use RHDH themes, skip to Step 4.

Add RHDH theme to Backstage app dependencies:

```bash
yarn workspace app add @red-hat-developer-hub/backstage-plugin-theme
```

Update `packages/app/src/App.tsx` and apply the themes to `createApp`:

```typescript
import { getThemes } from '@red-hat-developer-hub/backstage-plugin-theme';

// ...

const app = createApp({
  apis,
  // ...
  themes: getThemes(),
});
```

## Step 3: Create Frontend Plugin

Generate a new frontend plugin:

```bash
yarn new --select frontend-plugin --option id=<plugin-id>
```

The plugin will be created at `plugins/<plugin-id>/`

Generated structure:

```
plugins/<plugin-id>/
├── src/
│   ├── index.ts              # Public exports
│   ├── plugin.ts             # Plugin definition
│   ├── routes.ts             # Route references
│   └── components/
│       └── ExampleComponent/
├── package.json
└── dev/
    └── index.tsx             # Development harness
```


## Step 4: If you decided to use RHDH themes, add RHDH Theme to Development Harness

By default, `yarn start` uses standard Backstage themes. To preview your plugin with RHDH styling during local development, configure the RHDH theme package.

### Install Theme Package

```bash
cd plugins/<plugin-id>
yarn add @red-hat-developer-hub/backstage-plugin-theme
```

### Configure Development Harness

Update `dev/index.tsx` to use RHDH themes:

```typescript
import { getAllThemes } from '@red-hat-developer-hub/backstage-plugin-theme';
import { createDevApp } from '@backstage/dev-utils';
import { myPlugin, MyPage } from '../src';

createDevApp()
  .registerPlugin(myPlugin)
  .addPage({
    element: <MyPage />,
    title: 'My Plugin',
    path: '/my-plugin',
  })
  .addThemes(getAllThemes())
  .render();
```

### Available Theme APIs

- `getThemes()` / `useThemes()` - Latest RHDH light and dark themes
- `getAllThemes()` / `useAllThemes()` - All themes including legacy versions
- `useLoaderTheme()` - Returns Material-UI v5 theme object

> **Note:** When deployed to RHDH, the application shell provides theming automatically. This configuration is only needed for local development.



## Step 5: Implement Plugin Components

### Page Component

Create a full-page component for dynamic routes:

```typescript
// src/components/MyPage/MyPage.tsx
import React from 'react';
import { Page, Header, Content } from '@backstage/core-components';

export const MyPage = () => (
  <Page themeId="tool">
    <Header title="My Plugin" />
    <Content>
      <h1>Hello from My Plugin</h1>
    </Content>
  </Page>
);
```

### Entity Card Component

Create a card for entity pages:

```typescript
// src/components/MyCard/MyCard.tsx
import React from 'react';
import { InfoCard } from '@backstage/core-components';
import { useEntity } from '@backstage/plugin-catalog-react';

export const MyEntityCard = () => {
  const { entity } = useEntity();
  return (
    <InfoCard title="My Plugin Info">
      <p>Entity: {entity.metadata.name}</p>
    </InfoCard>
  );
};
```

### Export Components

Export all components in `src/index.ts`:

```typescript
// src/index.ts
export { myPlugin } from './plugin';
export { MyPage } from './components/MyPage';
export { MyEntityCard } from './components/MyCard';
```

Build and verify:

```bash
cd plugins/<plugin-id>
yarn build
```

## Step 6: Export and Package

Export the plugin as a dynamic plugin and package it for deployment. For detailed export and packaging options, see the **export-and-package** skill.

### Quick Export

```bash
cd plugins/<plugin-id>
npx @red-hat-developer-hub/cli@latest plugin export
```

Output shows the generated Scalprum configuration. Creates `dist-dynamic/` with `dist-scalprum/` (webpack federated modules).

### Quick Package and Push

```bash
npx @red-hat-developer-hub/cli@latest plugin package \
  --tag quay.io/<namespace>/<plugin-name>:v0.1.0

podman push quay.io/<namespace>/<plugin-name>:v0.1.0
```

For advanced options (custom Scalprum config, multi-plugin bundles, tgz/npm packaging), consult the **export-and-package** skill.

## Step 7: Configure Plugin Wiring

Frontend plugins require configuration in `dynamic-plugins.yaml` to define how they integrate with RHDH.

### Basic Example

```yaml
plugins:
  - package: oci://quay.io/<namespace>/<plugin-name>:v0.1.0!my-plugin
    disabled: false
    pluginConfig:
      dynamicPlugins:
        frontend:
          my-org.plugin-my-plugin:  # Must match scalprum.name
            dynamicRoutes:
              - path: /my-plugin
                importName: MyPage
                menuItem:
                  icon: dashboard
                  text: My Plugin
```

### Key Wiring Options

| Option | Purpose |
|--------|---------|
| `dynamicRoutes` | Full page routes with optional sidebar menu items |
| `mountPoints` | Entity page cards, tabs, and other integrations |
| `menuItems` | Sidebar ordering and nesting |
| `appIcons` | Custom icons for routes and menus |
| `entityTabs` | New tabs on entity pages |

For complete wiring configuration (mount points, conditional rendering, custom tabs, themes, scaffolder extensions), use the **generate-frontend-wiring** skill.

## Known Issues

### MUI v5 Styles Missing

If using MUI v5, add class name generator to `src/index.ts`:

```typescript
import { unstable_ClassNameGenerator as ClassNameGenerator } from '@mui/material/className';

ClassNameGenerator.configure(componentName =>
  componentName.startsWith('v5-') ? componentName : `v5-${componentName}`
);

export * from './plugin';
```

### Grid Spacing Missing

Apply spacing manually to MUI v5 Grid:

```tsx
<Grid container spacing={2}>
  <Grid item>...</Grid>
</Grid>
```

## Additional Resources

### Related Skills

- **export-and-package** - Complete export/packaging workflow
- **generate-frontend-wiring** - Advanced wiring configuration (mount points, tabs, themes, etc.)

### Reference Files

- **`references/frontend-wiring.md`** - Complete mount points, routes, bindings
- **`references/entity-page.md`** - Entity page customization

### Example Files

- **`examples/frontend-plugin-config.yaml`** - Complete frontend wiring example

### External Resources

- [RHDH Frontend Plugin Wiring](https://github.com/redhat-developer/rhdh/blob/main/docs/dynamic-plugins/frontend-plugin-wiring.md)
- [Backstage Plugin Development](https://backstage.io/docs/plugins/)
