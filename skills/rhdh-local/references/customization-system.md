# Reference: RHDH Local Customization System

The copy-sync system for managing RHDH Local configuration without modifying the upstream `rhdh-local/` git repository.

<architecture>
**Workspace layout:**

```
rhdh-local-setup/
├── rhdh-local/                    # Upstream git repo — NEVER edit directly
│   ├── compose.yaml
│   ├── default.env
│   └── configs/
│       ├── app-config/app-config.yaml
│       └── dynamic-plugins/dynamic-plugins.default.yaml
├── rhdh-customizations/           # Your overrides — ALWAYS edit here
│   ├── apply-customizations.sh    # Copies files into rhdh-local/
│   ├── remove-customizations.sh   # Deletes copies from rhdh-local/
│   ├── .env
│   ├── compose.override.yaml
│   └── configs/
│       ├── app-config/app-config.local.yaml
│       ├── dynamic-plugins/dynamic-plugins.override.yaml
│       ├── catalog-entities/users.override.yaml
│       └── extra-files/github-app-credentials.yaml
├── up.sh                          # Start containers (use instead of podman compose up)
├── down.sh                        # Stop containers (use instead of podman compose down)
└── backup.sh                      # Archive this workspace
```

**The copy-sync invariant:**

- `rhdh-customizations/` is the single source of truth for all configuration
- `apply-customizations.sh` physically copies files into `rhdh-local/`
- Containers read files from `rhdh-local/` (they cannot access paths outside their mount)
- `remove-customizations.sh` deletes the copies, restoring pristine state
- `rhdh-local/` git status should always be "working tree clean" — the copied files are gitignored
</architecture>

<file_mapping>
**Source → Destination** (what `apply-customizations.sh` copies):

| Edit here (`rhdh-customizations/`) | Copied to (`rhdh-local/`) |
|------------------------------------|---------------------------|
| `compose.override.yaml` | `compose.override.yaml` |
| `.env` | `.env` |
| `configs/app-config/app-config.local.yaml` | `configs/app-config/app-config.local.yaml` |
| `configs/dynamic-plugins/dynamic-plugins.override.yaml` | `configs/dynamic-plugins/dynamic-plugins.override.yaml` |
| `configs/catalog-entities/*.override.yaml` | `configs/catalog-entities/*.override.yaml` |
| `configs/extra-files/*` | `configs/extra-files/*` |
| `developer-lightspeed/configs/app-config/app-config.lightspeed.local.yaml` | same relative path |
</file_mapping>

<configuration_layers>
**Precedence (lowest → highest):**

1. **Layer 1 — Defaults:** `rhdh-local/` version-controlled files
   - `default.env`, `app-config.yaml`, `dynamic-plugins.default.yaml`
2. **Layer 2 — Overrides:** Files copied from `rhdh-customizations/`
   - `.env`, `app-config.local.yaml`, `dynamic-plugins.override.yaml`
3. **Layer 3 — app-config.local.yaml:** Loads last, highest precedence among config files
4. **Environment variables** from `.env` override `default.env`
</configuration_layers>

<edit_rules>
**ALWAYS:**

- Edit customization files in `rhdh-customizations/` directory
- Run `apply-customizations.sh` after every edit
- Verify pristine state: `cd rhdh-local && git status` → "working tree clean"
- Use `./up.sh` and `./down.sh` scripts for container lifecycle

**NEVER:**

- Modify files in `rhdh-local/` for customization purposes
- Manually copy files (use `apply-customizations.sh`)
- Commit `*.local.yaml`, `*.override.yaml`, or `.env` to the rhdh-local repository
- Edit the copied files in `rhdh-local/` — they get overwritten on the next `apply-customizations.sh`
</edit_rules>

<quick_reference>
**What to edit and where:**

| Change | File |
|--------|------|
| App configuration | `rhdh-customizations/configs/app-config/app-config.local.yaml` |
| Plugin enable/disable | `rhdh-customizations/configs/dynamic-plugins/dynamic-plugins.override.yaml` |
| Environment variables | `rhdh-customizations/.env` |
| Extra services (Jenkins etc.) | `rhdh-customizations/compose.override.yaml` |
| Catalog entities | `rhdh-customizations/configs/catalog-entities/components.override.yaml` |
| Credentials | `rhdh-customizations/configs/extra-files/github-app-credentials.yaml` |
| Lightspeed config | `rhdh-customizations/developer-lightspeed/configs/app-config/app-config.lightspeed.local.yaml` |

**Standard change workflow:**

```bash
# 1. Edit the file in rhdh-customizations/
# 2. Sync into rhdh-local/
cd rhdh-customizations && ./apply-customizations.sh
# 3. Restart
cd .. && ./down.sh && ./up.sh --customized [flags]
```

**Update rhdh-local from upstream:**

```bash
./down.sh
cd rhdh-local && git pull && cd ..
cd rhdh-customizations && ./apply-customizations.sh
cd .. && ./up.sh --customized [flags]
```

</quick_reference>
