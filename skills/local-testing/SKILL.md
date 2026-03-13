---
name: local-testing
description: Skill for testing RHDH plugins locally using the rhdh-local-setup customization system. Covers enabling/disabling plugins, switching modes, and running end-to-end plugin tests.
---

<essential_principles>

<principle name="copy_sync_first">
All configuration edits go in `rhdh-customizations/`, never in `rhdh-local/` directly.
After every edit, run `apply-customizations.sh` to sync copies. This is the fundamental invariant.
</principle>

<principle name="use_scripts">
Use `./up.sh` and `./down.sh` — never `podman compose restart/up/down` directly when Lightspeed or Orchestrator are enabled. Network namespace sharing causes 504 errors if containers are restarted independently.
See `references/customization-system.md` for details.
</principle>

<principle name="data_sources">
Plugin package definitions come from `rhdh-plugin-export-overlays` on GitHub.
Always fetch the OCI reference from `spec.dynamicArtifact` in the package metadata — do NOT construct OCI URLs manually.
</principle>

</essential_principles>

<intake>
## Step 1: Identify What You Want to Do

What would you like to do with your local RHDH instance?

1. **Enable a plugin** — Add a plugin from the export-overlays catalog to your local RHDH
2. **Disable a plugin** — Disable or remove a plugin from your local RHDH
3. **Switch mode** — Switch between Customized (your config) and Pristine (RHDH defaults)
4. **Test a plugin** — Run end-to-end verification after enabling a plugin
5. **Check status** — See which plugins are currently enabled

**Wait for response before proceeding.**
</intake>

<routing>
| Response | Workflow |
|----------|----------|
| 1, "enable", "add plugin", "install plugin" | `workflows/enable-plugin.md` |
| 2, "disable", "remove plugin", "turn off plugin" | `workflows/disable-plugin.md` |
| 3, "switch", "pristine", "customized", "mode" | `workflows/switch-mode.md` |
| 4, "test", "verify", "check plugin" | `workflows/test-plugin.md` |
| 5, "status", "list plugins", "show plugins" | Read `rhdh-customizations/configs/dynamic-plugins/dynamic-plugins.override.yaml` and list entries |
</routing>

<reference_index>
**Customization system (copy-sync, file mapping, edit rules):** `references/customization-system.md`
**Container lifecycle, startup scripts, network namespace:** `../overlay/references/rhdh-local.md` sections `<container_lifecycle>` and `<common_operations>`
**Dynamic plugin YAML format, OCI references:** `../overlay/references/rhdh-local.md` section `<dynamic_plugins_config>`
</reference_index>

<skills_index>

| Skill | Purpose | Path |
|-------|---------|------|
| overlay | Onboard/update plugins in rhdh-plugin-export-overlays | `../overlay/SKILL.md` |
| rhdh | Orchestrator — routes to all skills, runs CLI checks | `../rhdh/SKILL.md` |

</skills_index>
