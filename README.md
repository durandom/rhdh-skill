# RHDH Plugin Skill

A Claude Code skill for managing Red Hat Developer Hub plugins - onboarding, updating, maintaining, and triaging plugins in the Extensions Catalog.

## Two Personas

This skill supports both **Plugin Owners** (contributors managing their plugins) and **Core Team** (COPE/Plugins team managing the overlay repository).

## What's Inside

| Category | Count | Description |
|----------|-------|-------------|
| **Commands** | 6 | Slash commands for quick invocation |
| **Skills** | 1 | Router-based skill with 5 workflows |
| **References** | 5 | Domain knowledge for overlay repo, CI, metadata, GitHub queries |
| **Templates** | 1 | Workspace file templates |

### Slash Commands

#### Plugin Owner Commands

| Command | Description |
|---------|-------------|
| `/onboard-plugin` | Add a new Backstage plugin to Extensions Catalog |
| `/update-plugin` | Bump plugin to newer upstream version |
| `/fix-plugin-build` | Debug and fix CI/publish failures |
| `/plugin-status` | Check plugin health and compatibility |

#### Core Team Commands

| Command | Description |
|---------|-------------|
| `/triage-overlay-prs` | Prioritize open PRs by criticality |
| `/analyze-overlay-pr` | Deep-dive on specific PR (assignment, compat, readiness) |

### Workflows

#### Plugin Owner Workflows

| Workflow | Description |
|----------|-------------|
| `onboard-plugin` | Full 6-phase process: Discovery → Workspace → PR → Metadata → Verify → Merge |
| `update-plugin` | Version bump with validation |
| `fix-build` | CI debugging with common error patterns |

#### Core Team Workflows

| Workflow | Description |
|----------|-------------|
| `triage-prs` | Prioritize PRs by labels (mandatory-workspace, workspace-update, etc.) |
| `analyze-pr` | Single PR analysis (assignment, checks, compatibility, merge readiness) |

## Installation

### Option 1: Plugin Marketplace (Recommended)

```bash
# Add the marketplace source
claude plugin marketplace add <org>/rhdh-plugin-skill

# Install the plugin
claude plugin install rhdh-plugin
```

### Option 2: Manual Installation

Copy to your Claude Code configuration:

```bash
# Commands (global, available everywhere)
cp -r commands/* ~/.claude/commands/

# Skills (global, available everywhere)
cp -r skills/* ~/.claude/skills/
```

### Option 3: Git Submodule

Add as a submodule to your project:

```bash
git submodule add <repo-url> rhdh-plugin-skill
```

Then register in your project's `.claude/settings.json`:

```json
{
  "skills": {
    "rhdh-plugin": {
      "path": "rhdh-plugin-skill/skills/rhdh-plugin/SKILL.md"
    }
  }
}
```

## Usage

### Plugin Owner Tasks

```
/onboard-plugin https://github.com/awslabs/backstage-plugins-for-aws
/update-plugin aws-ecs v0.8.0
/fix-plugin-build PR #1234
/plugin-status aws-codebuild
```

### Core Team Tasks

```
/triage-overlay-prs
/analyze-overlay-pr 1234
```

### Via Skill Invocation

The skill presents a role-based menu:

**Plugin Owner Tasks:**

1. Onboard a new plugin
2. Update plugin version
3. Check plugin status
4. Fix build failure

**Core Team Tasks:**
5. Triage overlay PRs
6. Analyze specific PR
7. Trigger publish

## Structure

```
rhdh-plugin-skill/
├── .claude-plugin/               # Marketplace registration
│   ├── plugin.json               # Plugin manifest
│   └── marketplace.json          # Marketplace metadata
├── .planning/                    # Task specifications (design docs)
│   ├── README.md                 # Task index and priorities
│   ├── 00-onboard-plugin.md      # Foundation task
│   ├── 01-pr-triage.md           # PR prioritization
│   └── ...                       # Other planned tasks
├── commands/                     # Slash command wrappers
│   ├── onboard-plugin.md
│   ├── update-plugin.md
│   ├── fix-plugin-build.md
│   ├── plugin-status.md
│   ├── triage-overlay-prs.md     # Core Team
│   └── analyze-overlay-pr.md     # Core Team
├── skills/rhdh-plugin/           # Main skill
│   ├── SKILL.md                  # Router + essential principles
│   ├── workflows/                # Step-by-step procedures
│   │   ├── onboard-plugin.md     # Full 6-phase process
│   │   ├── update-plugin.md      # Version bump
│   │   ├── fix-build.md          # CI debugging
│   │   ├── triage-prs.md         # Core Team: PR prioritization
│   │   └── analyze-pr.md         # Core Team: Single PR analysis
│   ├── references/               # Domain knowledge
│   │   ├── overlay-repo.md       # Workspace patterns
│   │   ├── ci-feedback.md        # Publish workflow interpretation
│   │   ├── metadata-format.md    # Package/Plugin entity specs
│   │   ├── github-queries.md     # gh CLI patterns
│   │   └── label-priority.md     # PR label classification
│   └── templates/                # Output structures
│       └── workspace-files.md    # source.json, plugins-list.yaml
├── DESIGN.md                     # Architecture and planned tasks
└── README.md
```

## Related Resources

- [rhdh-plugin-export-overlays](https://github.com/redhat-developer/rhdh-plugin-export-overlays) — Overlay repository for plugin exports
- [rhdh-plugin-export-utils](https://github.com/redhat-developer/rhdh-plugin-export-utils) — Reusable GitHub Actions
- [rhdh-local](https://github.com/redhat-developer/rhdh-local) — Local testing environment
- [rhdh-dynamic-plugin-factory](https://github.com/redhat-developer/rhdh-dynamic-plugin-factory) — Container for local builds

## License

Apache-2.0
