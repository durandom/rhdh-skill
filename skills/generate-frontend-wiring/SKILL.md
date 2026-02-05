---
name: Generate Frontend Wiring
description: This skill should be used when the user asks to "generate frontend wiring", "show frontend wiring", "create RHDH binding", "generate dynamic plugin config", "show plugin wiring for RHDH", "create app-config for frontend plugin", or wants to generate the RHDH dynamic plugin wiring configuration for an existing Backstage frontend plugin. The skill analyzes the plugin's source code and generates the appropriate configuration.
---

## Purpose

Analyze an existing Backstage frontend plugin and generate the RHDH dynamic plugin wiring configuration. This skill inspects the plugin's source files to determine exports and generates the corresponding `app-config.yaml` configuration.

## When to Use

Use this skill when:
- User has an existing Backstage frontend plugin
- User wants to deploy it to RHDH as a dynamic plugin
- User needs the wiring configuration for `dynamic-plugins.yaml`

## Prerequisites

The plugin directory must contain:
- `package.json` with plugin metadata
- `src/plugin.ts` or `src/plugin.tsx` with plugin definition
- `src/index.ts` exporting plugin components

## Workflow

### Step 1: Locate Plugin Files

Find and read the essential plugin files:

1. **`package.json`** - Get package name
2. **`src/plugin.ts`** - Find exported extensions (pages, cards)
3. **`src/index.ts`** - Find public exports (APIs, components)
4. **`dist-dynamic/dist-scalprum/plugin-manifest.json`** - Get scalprum name if built

### Step 2: Determine Scalprum Name

The scalprum name is used to reference the plugin in RHDH configuration:

1. **If `plugin-manifest.json` exists**: Use the `name` field
2. **If `scalprum` in `package.json`**: Use `scalprum.name`
3. **Otherwise derive from package name**:
   - `@my-org/backstage-plugin-foo` becomes `my-org.backstage-plugin-foo`
   - `@internal/backstage-plugin-foo` becomes `internal.backstage-plugin-foo`

### Step 3: Identify Exports

Analyze the plugin source to find:

**Routable Extensions** (pages):
- Look for `createRoutableExtension` in `plugin.ts`
- These become `dynamicRoutes` entries
- Extract the export name (e.g., `MyPluginPage`)

**Entity Cards/Content**:
- Look for `createComponentExtension` in `plugin.ts`
- These become `mountPoints` entries
- Identify if they use `useEntity` (entity-scoped)

**API Factories**:
- Look for `createApiFactory` and `createApiRef` in `plugin.ts` or `api.ts`
- These become `apiFactories` entries
- Extract the `apiRef` export name

**Icons**:
- Look for icon exports (React components returning SVG/Icon)
- These become `appIcons` entries

### Step 4: Generate Configuration

Output the complete wiring configuration in YAML format:

```yaml
# RHDH Dynamic Plugin Configuration
# Add to your dynamic-plugins.yaml or app-config.yaml

dynamicPlugins:
  frontend:
    <scalprum-name>:
      dynamicRoutes:
        - path: /<plugin-id>
          importName: <PageComponentName>
          menuItem:
            icon: <icon-name>
            text: <Plugin Display Name>

      mountPoints:
        - mountPoint: entity.page.overview/cards
          importName: <CardComponentName>
          config:
            if:
              allOf:
                - isKind: component

      apiFactories:
        - importName: <apiRefName>

      appIcons:
        - name: <iconName>
          importName: <IconComponentName>
```

### Step 5: Present to User

Show the generated configuration with:
1. The YAML configuration block
2. A table explaining each entry and its source
3. Notes about any optional configurations
4. Ask if it should be saved to a file

## Example Output

For a plugin with:
- Package: `@internal/backstage-plugin-demoplugin`
- Page: `DemopluginPage`
- API: `todoApiRef`

Generate:

```yaml
dynamicPlugins:
  frontend:
    internal.backstage-plugin-demoplugin:
      dynamicRoutes:
        - path: /demoplugin
          importName: DemopluginPage
          menuItem:
            icon: extension
            text: Demo Plugin
      apiFactories:
        - importName: todoApiRef
```

## Configuration Options Reference

### Dynamic Routes

```yaml
dynamicRoutes:
  - path: /my-plugin           # URL path
    importName: MyPage         # Exported component name
    module: PluginRoot         # Optional: scalprum module (default: PluginRoot)
    menuItem:
      icon: dashboard          # System icon or custom appIcon
      text: My Plugin          # Sidebar menu text
```

### Mount Points

```yaml
mountPoints:
  - mountPoint: entity.page.overview/cards
    importName: MyCard
    config:
      layout:
        gridColumn: '1 / -1'   # Full width
      if:
        allOf:
          - isKind: component
          - hasAnnotation: my-plugin/enabled
```

### API Factories

```yaml
apiFactories:
  - importName: myApiFactory   # Or myApiRef if plugin exports it
```

### App Icons

```yaml
appIcons:
  - name: myIcon
    importName: MyIconComponent
```

## Common Patterns

### Page Plugin

Plugin that adds a standalone page:

```yaml
dynamicRoutes:
  - path: /my-plugin
    importName: MyPluginPage
    menuItem:
      icon: extension
      text: My Plugin
```

### Entity Card Plugin

Plugin that adds a card to entity pages:

```yaml
mountPoints:
  - mountPoint: entity.page.overview/cards
    importName: MyEntityCard
    config:
      if:
        allOf:
          - isKind: component
```

### Page + Card Plugin

Plugin with both page and entity integration:

```yaml
dynamicRoutes:
  - path: /my-plugin
    importName: MyPluginPage
    menuItem:
      icon: myIcon
      text: My Plugin

mountPoints:
  - mountPoint: entity.page.overview/cards
    importName: MyEntityCard

appIcons:
  - name: myIcon
    importName: MyIcon
```

## Notes

- The generated configuration is a starting point; adjust as needed
- Use `references/frontend-wiring.md` for complete configuration options
- Entity cards may need condition tuning based on target entity kinds
- Custom icons must be exported from the plugin's index.ts

### Reference Files

- **`references/frontend-wiring.md`** - Complete mount points, routes, bindings
- **`references/entity-page.md`** - Entity page customization
