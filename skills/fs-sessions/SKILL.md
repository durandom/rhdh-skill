---
name: fs-sessions
description: |
  Manage and share Claude Code session transcripts through a policy-controlled global SessionEnd hook and AgentsView. Use when asked to configure session sharing, install or migrate the session hook globally, whitelist or blacklist repositories, diagnose why a repository is or is not exporting, share/list/push/pull sessions, or start AgentsView for team transcripts. Also use for requests mentioning fs-sessions, FULLSEND_SESSIONS_REPO, session export, transcript sharing, or repository-specific session privacy.
---

# fs-sessions

Share Claude Code transcripts through a global, fail-closed repository policy.

<cli_setup>

Resolve the CLI relative to this file and use it for every deterministic operation:

```bash
FS="<skill-directory>/scripts/fs-sessions"
"$FS" --help
```

Consume complete command output. Do not reimplement JSON or Claude settings edits manually.

</cli_setup>

<essential_principles>

- **Global policy grants access** — only `~/.config/rhdh-skill/config.json` may allow export. A repository's `.rhdh/config.json` may set `sessions.enabled: false`, but cannot opt itself in; this prevents checked-out code from authorizing transcript upload.
- **Fail closed** — malformed/missing config, non-Git directories, unmatched repositories under `default: deny`, and export errors all skip silently in the SessionEnd hook.
- **Rules are ordered** — the last matching `allow` or `deny` rule wins. This supports whitelist, blacklist, and narrow exceptions with one explainable model.
- **One global hook** — install into `~/.claude/settings.json`. After verifying it, remove legacy project-local `export-session.sh` hooks so a session cannot be exported twice.
- **Transcripts remain append-only in Git** — the exporter may refresh its copied file when the source grows, but do not manually alter shared transcript content.

</essential_principles>

<intake>

## What would you like to do?

1. **Setup or migrate** — configure the shared repo, safe policy, and global hook
2. **Policy** — allow, deny, list rules, or explain a repository decision
3. **Hook** — install, inspect, or uninstall the global SessionEnd hook
4. **Status** — inspect configuration, hook, policy, and stored sessions
5. **Share/list** — explicitly export or list local sessions
6. **Push/pull** — synchronize the shared sessions repository
7. **View** — start or stop AgentsView

If the user already stated an operation, route directly without repeating this menu. Otherwise wait for their selection.

</intake>

<routing>

| Response | Reference |
|----------|-----------|
| 1, "setup", "migrate", "global install" | `references/setup.md` |
| 2, "policy", "allow", "deny", "whitelist", "blacklist" | `references/policy.md` |
| 3, "hook", "SessionEnd", "install hook" | `references/hook.md` |
| 4, "status", "configured?", "why not exporting?" | `references/status.md` |
| 5, "share", "export", "list sessions" | `references/share.md` |
| 6, "push", "pull", "sync" | `references/sync.md` |
| 7, "view", "AgentsView", "browse sessions" | `references/view.md` |

</routing>

<reference_index>

| Reference | Load when | Path |
|-----------|-----------|------|
| setup | First installation or legacy-hook migration | `references/setup.md` |
| policy | Editing or explaining repository rules | `references/policy.md` |
| hook | Hook-only lifecycle work | `references/hook.md` |
| status | Diagnosing the current state | `references/status.md` |
| share | Explicit manual export/list | `references/share.md` |
| sync | Git synchronization | `references/sync.md` |
| view | AgentsView lifecycle | `references/view.md` |

</reference_index>

<success_criteria>

- Configuration preserves unrelated `rhdh-skill` keys and validates successfully.
- `policy check <repo>` reports the intended action and matching rule.
- Exactly one managed hook exists globally; legacy local hooks are absent after migration.
- A denied repository produces no exported file; an allowed repository exports only its transcript path.

</success_criteria>
