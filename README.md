# RHDH Plugin Skill

A Claude Code skill for managing Red Hat Developer Hub plugins - onboarding, updating, and maintaining plugins in the Extensions Catalog.

## Structure

```
rhdh-plugin-skill/
├── skills/rhdh-plugin/
│   ├── SKILL.md              # Router + essential principles
│   ├── workflows/            # Step-by-step procedures
│   │   └── onboard-plugin.md
│   ├── references/           # Domain knowledge
│   │   ├── overlay-repo.md
│   │   └── ci-feedback.md
│   └── templates/            # Output structures
│       └── workspace-files.md
└── .claude/
    └── settings.json
```

## Usage

This skill is designed to be used with Claude Code. It provides guided workflows for:

- **Onboard a plugin** - Add a new Backstage plugin to RHDH Extensions Catalog
- **Update plugin version** - Bump to newer upstream version
- **Check plugin status** - Verify plugin health and compatibility
- **Deprecate plugin** - Remove from catalog with proper lifecycle

## Installation

Add as a submodule to your project:

```bash
git submodule add <repo-url> rhdh-plugin-skill
```

Then register in your Claude Code settings.

## Related

- [rhdh-plugin-export-overlays](https://github.com/redhat-developer/rhdh-plugin-export-overlays) - Overlay repository
- [rhdh-local](https://github.com/redhat-developer/rhdh-local) - Local testing environment
