---
name: create-plugin
description: >
  Full lifecycle for RHDH dynamic plugins — scaffold, implement, export, package,
  and configure. Use when asked to "create RHDH plugin", "bootstrap dynamic plugin",
  "create backend plugin", "create frontend plugin", "export dynamic plugin",
  "package plugin as OCI", "generate frontend wiring", "create plugin container image",
  "configure mount points", "create dynamic route", "add entity card", "scaffold
  RHDH plugin", "publish plugin to registry", "create tgz archive", or mentions
  creating, exporting, packaging, or wiring a Backstage plugin for Red Hat Developer
  Hub. Covers backend plugins (APIs, scaffolder actions, processors), frontend plugins
  (pages, cards, themes), export/packaging (OCI, tgz, npm), and frontend wiring
  configuration (mount points, routes, entity tabs, themes).
compatibility: "Node.js 22+, Yarn, podman or docker. Windows, macOS, Linux."
---

## Prerequisites

- Node.js 22+ and Yarn
- Container runtime (`podman` or `docker`) for OCI packaging
- Access to a container registry (e.g., quay.io) for publishing

## Commands

| Command | Category | Description | Reference |
|---------|----------|-------------|-----------|
| `backend` | Create | Scaffold and implement a backend dynamic plugin | [references/backend.md](references/backend.md) |
| `frontend` | Create | Scaffold and implement a frontend dynamic plugin | [references/frontend.md](references/frontend.md) |
| `export` | Package | Export, package, and push a plugin for RHDH deployment | [references/export.md](references/export.md) |
| `wiring` | Configure | Analyze a frontend plugin and generate wiring config | [references/wiring.md](references/wiring.md) |

### Routing rules

1. **No argument**: Show the command table. Ask what the user wants to do.
2. **First word matches a command**: Load its reference file and follow it.
3. **First word doesn't match**: Infer intent from context. "Create a new API plugin" → `backend`. "Package my plugin as OCI" → `export`. "Generate mount points" → `wiring`.

## Shared Knowledge

> **Script paths:** All `scripts/` and `references/` paths below are relative to this SKILL.md file's directory. Resolve them against the skill directory before invoking.

### RHDH Version Resolution

Before scaffolding, determine the target RHDH version. Consult `../rhdh/references/versions.md` for the compatibility matrix. Ask the user if not specified.

### Scaffold Script

Both backend and frontend plugins use a unified scaffold script:

```bash
python scripts/scaffold.py \
  --type backend \
  --rhdh-version 1.9 \
  --plugin-id my-plugin
```

Run `python scripts/scaffold.py --help` for all options (`--type`, `--path`, `--with-theme`, `--create-app-version`, `--json`).

### Export Script

Automates the full export → package → push pipeline:

```bash
python scripts/export-plugin.py \
  --plugin-dir plugins/my-plugin \
  --tag quay.io/ns/my-plugin:v0.1.0 \
  --push --clean
```

Run `python scripts/export-plugin.py --help` for all options (`--format`, `--shared-package`, `--embed-package`, `--json`).

### Plugin Lifecycle

The typical workflow chains these commands:

1. **`backend`** or **`frontend`** — Scaffold and implement
2. **`export`** — Build, export, package, push
3. **`wiring`** (frontend only) — Generate `dynamic-plugins.yaml` config

Each reference file is self-contained. Load only the one you need.

## Reference Index

### Command References

| File | Load when... |
|------|-------------|
| `references/backend.md` | Creating a backend plugin (API, scaffolder action, processor) |
| `references/frontend.md` | Creating a frontend plugin (page, card, theme) |
| `references/export.md` | Exporting, packaging, or publishing a plugin |
| `references/wiring.md` | Generating frontend wiring configuration |

### Deep-Dive References

| File | Load when... |
|------|-------------|
| `references/export-options.md` | Need details on `--shared-package`, `--embed-package`, dependency categories |
| `references/packaging-formats.md` | Comparing OCI vs tgz vs npm, multi-plugin bundles, private registries |
| `references/integrity-hashes.md` | Generating or verifying SHA-512/SHA-256 integrity hashes |
| `references/frontend-wiring.md` | Complete mount point, route, binding, entity tab reference |
| `references/entity-page.md` | Entity page customization — tabs, cards, conditions, grid layout |

### Examples

| File | Contents |
|------|----------|
| `examples/dynamic-plugins.yaml` | Backend, frontend, multi-plugin, tgz, npm, and local config patterns |
| `examples/frontend-wiring.yaml` | All frontend wiring patterns — tabs, cards, search, themes, scaffolder |

## Common Issues

### Plugin Not Loading

- Backend: Verify new backend system (`createBackendPlugin`) with default export
- Frontend: Verify `scalprum.name` matches key under `dynamicPlugins.frontend.<key>`
- Both: Check version compatibility with target RHDH

### Build/Export Failures

- Run `yarn tsc` to check TypeScript errors before export
- Clear stale artifacts: `rm -rf dist dist-dynamic && yarn build`
- Missing deps: `yarn add -D <missing-package>`

### MUI v5 Styles Missing (Frontend)

Add class name generator to `src/index.ts`:

```typescript
import { unstable_ClassNameGenerator as ClassNameGenerator } from '@mui/material/className';
ClassNameGenerator.configure(componentName =>
  componentName.startsWith('v5-') ? componentName : `v5-${componentName}`
);
```
