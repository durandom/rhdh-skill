# DESIGN.md — AI-Assisted PR Triage for Overlay Repository

> **Source:** Meeting notes from 2025-12-17 "Overlay repo AI PR review flow"
> **Participants:** Marcel Hild, David Festal (overlay maintainer), Tomas Kral

---

## Context

The overlay repository (`rhdh-plugin-export-overlays`) has a large backlog of PRs with communication/prioritization challenges. The goal is to leverage AI assistance for triage rather than building more traditional automation—validating the approach locally before promoting to CI workflows.

---

## Task Dimensions

### Dimension 1: Plugin Lifecycle

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────┐
│  ONBOARD    │───▶│  ACTIVE MAINT   │───▶│  DEPRECATE   │
│             │    │                 │    │              │
│ First PR    │    │ Updates, fixes  │    │ Remove from  │
│ Add to repo │    │ Version bumps   │    │ catalog      │
└─────────────┘    └─────────────────┘    └──────────────┘
```

### Dimension 2: Personas

| Persona | Description | Primary Concern |
|---------|-------------|-----------------|
| **Plugin Owner** | External contributor or team managing their own plugin(s) | Getting their plugin built, updated, merged |
| **Core Team** | COPE/Plugins team managing repository infrastructure | Keeping backlog moving, enforcing standards, coordination |

---

## Task Matrix

### By Lifecycle Stage

```
                    │  Plugin Owner          │  Core Team
────────────────────┼────────────────────────┼──────────────────────────
 ONBOARD            │  • Code Owner Entry    │  • Gating Review
                    │  • Plugin Config Setup │  • Publish Trigger
                    │                        │  • Assignment
────────────────────┼────────────────────────┼──────────────────────────
 ACTIVE MAINTENANCE │  • Update Response     │  • PR Triage
                    │  • Compatibility Fix   │  • Stale PR Pings
                    │                        │  • Auto-Merge Readiness
                    │                        │  • Compatibility Detector
────────────────────┼────────────────────────┼──────────────────────────
 DEPRECATE          │  • (none yet)          │  • (none yet)
────────────────────┴────────────────────────┴──────────────────────────
```

---

## Tasks by Lifecycle Stage

### 🟢 ONBOARD — First Plugin Addition

#### For Plugin Owner

**1. Code Owner Entry Check**

Ensure new plugins add contributor to CODEOWNERS file.

| Aspect | Detail |
|--------|--------|
| Problem | New plugins merged without CODEOWNERS → no one responsible for updates |
| Trigger | PR with `workspace-addition` label or new directory |
| Action | Flag if CODEOWNERS not modified; comment with template |
| Effort | Low |

**2. Plugin Config Setup Guide**

Help contributor add smoke test configuration.

| Aspect | Detail |
|--------|--------|
| Problem | Smoke tests require catalog entity config; contributors don't know format |
| Trigger | After initial workspace creation |
| Action | Generate template for `metadata/` catalog entities |
| Effort | Medium |

#### For Core Team

**3. Gating Review Assist**

First-merge decision support for new workspaces.

| Aspect | Detail |
|--------|--------|
| Problem | Root code owners must approve first PR; need context |
| Trigger | New `workspace-addition` PR from non-owner |
| Action | Surface: upstream source, backstage compatibility, similar existing plugins |
| Effort | Medium |

**4. Publish Trigger** (`/publish-overlay-pr`)

Add `/publish` comment to kick off build.

| Aspect | Detail |
|--------|--------|
| Problem | GitHub workflow limitations prevent auto-triggering on bot-created PRs |
| Trigger | New PR without publish check |
| Action | Post `/publish` comment; return workflow link |
| Effort | Low |

**5. Assignment Checker**

Ensure PRs have individual reviewers, not just teams.

| Aspect | Detail |
|--------|--------|
| Problem | Team assignments dilute responsibility |
| Trigger | PR requested to team or unassigned >2 days |
| Action | Suggest specific individual from CODEOWNERS |
| Effort | Low |

---

### 🔵 ACTIVE MAINTENANCE — Ongoing Updates

#### For Plugin Owner

**6. Update Response Assist**

Help owners respond to auto-generated update PRs.

| Aspect | Detail |
|--------|--------|
| Problem | Plugin owners get notified but may not understand what to check |
| Trigger | Owner receives update PR for their plugin |
| Action | Summarize: what changed upstream, smoke test status, merge readiness |
| Effort | Low |

**7. Compatibility Fix Guide**

Help when plugin breaks due to Backstage version bump.

| Aspect | Detail |
|--------|--------|
| Problem | Plugin owner may not know how to patch overlay for new Backstage |
| Trigger | Compatibility report shows plugin incompatible |
| Action | Link to patching guide; suggest common fixes |
| Effort | Medium |

#### For Core Team

**8. PR Triage Command** (`/triage-overlay-prs`)

Prioritize open PRs by criticality.

| Aspect | Detail |
|--------|--------|
| Problem | Too many PRs, reviewers overwhelmed |
| Priority Logic | Critical: `mandatory-workspace` + `update`; Medium: `mandatory` + `addition`; Low: other; Skip: `do-not-merge` |
| Output | Actionable table with staleness, assignment status, next actions |
| Effort | Medium |

```
## Overlay PR Triage Report

### 🔴 Critical (mandatory updates)
| PR | Plugin | Days Stale | Assigned? | Action |
|----|--------|------------|-----------|--------|

### 🟡 Medium Priority
...
```

**9. Slack Notification Drafter**

Draft pings for stale priority PRs.

| Aspect | Detail |
|--------|--------|
| Problem | GitHub notifications have poor signal/noise |
| Trigger | Stale PR (>X days based on priority) |
| Action | Look up Slack handle; draft contextual ping message |
| Effort | Medium |

```
Hey @handle - PR #1234 (aws-ecs update) needs attention.
Status: Smoke tests passing, needs review.
Priority: Mandatory workspace for RHDH catalog.
```

**10. Auto-Merge Readiness Check**

Show which PRs could auto-merge.

| Aspect | Detail |
|--------|--------|
| Problem | PRs could auto-merge when all checks pass, but prereqs unclear |
| Prereqs | Publish ✓, Smoke test ✓, CODEOWNERS entry ✓, Approval ✓ |
| Output | Badge/status in triage report |
| Effort | Low |

**11. Compatibility Bypass Detector**

Warn when manual commits skip version checks.

| Aspect | Detail |
|--------|--------|
| Problem | Manual `source.json` edits bypass automated compatibility checks |
| Trigger | PR with direct source.json modification |
| Check | Compare target Backstage version in commit vs overlay's current target |
| Action | Warning comment if version is higher than overlay supports |
| Effort | Medium |

---

### 🔴 DEPRECATE — Plugin Removal (Future)

*No tasks extracted from meeting. Potential future additions:*

- Deprecation announcement workflow
- Removal PR generation
- Downstream impact check (who uses this plugin?)
- Archive/sunset communication

---

## Relationship to Existing Skill Workflows

| Existing Workflow | New Tasks | Integration Point |
|-------------------|-----------|-------------------|
| `onboard-plugin` | Code Owner Entry, Plugin Config Setup | Phase 5 verification |
| `update-plugin` | Update Response Assist, Compatibility Fix | Pre/post guidance |
| `fix-build` | Compatibility Bypass Detector | Diagnostic check |
| `plugin-status` | Auto-Merge Readiness | Extend status output |
| (new) | PR Triage, Slack Drafter | Top-level for Core Team |

---

## Implementation Priority

### Quick Wins (Low effort, High value)

| Task | Persona | Lifecycle |
|------|---------|-----------|
| Publish Trigger | Core | Onboard |
| Assignment Checker | Core | Onboard |
| Code Owner Entry | Owner | Onboard |

### High Value (Worth the investment)

| Task | Persona | Lifecycle |
|------|---------|-----------|
| PR Triage Command | Core | Active |
| Slack Notification Drafter | Core | Active |

### Complete the Picture

| Task | Persona | Lifecycle |
|------|---------|-----------|
| Plugin Config Setup | Owner | Onboard |
| Compatibility Bypass Detector | Core | Active |
| Update Response Assist | Owner | Active |

---

## Next Steps

1. **Prototype PR Triage** — Core team's most pressing need
2. **Add Publish Trigger** — Quick win, unblocks CI
3. **Integrate Code Owner Check** into existing onboard workflow
4. **Build Slack mapping** — Enables notification drafter

---

## Repository References

### Core Repositories

| Repository | Purpose | Key Paths |
|------------|---------|-----------|
| [rhdh-plugin-export-overlays](https://github.com/redhat-developer/rhdh-plugin-export-overlays) | Main overlay repo — workspace definitions | `workspaces/`, `versions.json`, `CODEOWNERS` |
| [rhdh-plugin-export-utils](https://github.com/redhat-developer/rhdh-plugin-export-utils) | Reusable GitHub Actions & workflows | `.github/workflows/` |
| [rhdh-dynamic-plugin-factory](https://github.com/redhat-developer/rhdh-dynamic-plugin-factory) | Container for local plugin building | Used via `podman`/`docker` |
| [rhdh-local](https://github.com/redhat-developer/rhdh-local) | Local RHDH testing environment | Smoke test your plugin locally |

### Overlay Repository Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| Wiki: Compatibility Report | [/wiki/Backstage-Compatibility-Report](https://github.com/redhat-developer/rhdh-plugin-export-overlays/wiki/Backstage-Compatibility-Report) | Auto-updated per merge |
| Wiki: Workspace Status | [/wiki/Workspace-Status](https://github.com/redhat-developer/rhdh-plugin-export-overlays/wiki/Workspace-Status) | Current merged versions |
| Catalog Entity Docs | [catalog-entities/marketplace/README.md](https://github.com/redhat-developer/rhdh-plugin-export-overlays/blob/main/catalog-entities/marketplace/README.md) | Metadata format reference |
| Version Target | [versions.json](https://github.com/redhat-developer/rhdh-plugin-export-overlays/blob/main/versions.json) | Current Backstage target |

### Productization Files (in overlay repo)

| File | Support Level | Drives |
|------|---------------|--------|
| `rhdh-supported-packages.txt` | GA (fully supported) | Mandatory workspace label |
| `rhdh-techpreview-packages.txt` | Tech Preview | Mandatory workspace label |
| `community-packages.txt` | Dev Preview / Community | Non-mandatory |

### Upstream Plugin Sources

| Source Repo | Example Plugins | Notes |
|-------------|-----------------|-------|
| [backstage/community-plugins](https://github.com/backstage/community-plugins) | todo, tech-radar, etc. | Most community plugins |
| [awslabs/backstage-plugins-for-aws](https://github.com/awslabs/backstage-plugins-for-aws) | aws-ecs, aws-codebuild | Needs patches for workspace glob |
| [redhat-developer/rhdh-plugins](https://github.com/redhat-developer/rhdh-plugins) | lightspeed, etc. | Red Hat maintained |
