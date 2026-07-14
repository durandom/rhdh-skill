# Global SessionEnd hook

Manage the hook only through the CLI so JSON settings and unrelated hooks are preserved.

```bash
"$FS" hook install
"$FS" hook status
"$FS" hook uninstall
```

The global settings file defaults to `~/.claude/settings.json`. Use `--settings PATH` only to inspect/migrate a project-local settings file or for testing.

`hook install` is idempotent: it replaces any managed Python hook or legacy command containing `export-session`, then writes one command pointing to this installed skill's script.

The internal `hook run` command reads Claude's SessionEnd JSON from stdin. Do not invoke it without a test event. It intentionally exits successfully and silently for policy denials, malformed events, unavailable Git remotes, or export/push failures so Claude shutdown cannot be blocked.

For migration, verify the global hook and policy before uninstalling the local hook. Otherwise a gap between removal and installation can drop session exports.
