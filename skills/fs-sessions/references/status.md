# Status and diagnosis

Run:

```bash
"$FS" status
```

It reports the global config path, sessions repository, enabled state, policy, global hook, and stored transcript count.

For a repository-specific diagnosis, also run:

```bash
"$FS" policy check /path/to/repository
```

Interpret common denial reasons:

| Reason | Meaning | Action |
|--------|---------|--------|
| `not_git_repository` | `cwd` has no Git root | No automatic export; use an explicit share if desired |
| `globally_disabled` | `sessions.enabled` is false | Enable globally only after user confirmation |
| `project_opt_out` | `.rhdh/config.json` disables sharing | Preserve the opt-out unless the user owns and changes it |
| `default_deny` | No allow rule matched | Add the narrowest suitable origin/path allow rule |
| `matched_rule` | An ordered rule decided | Report its one-based index and selector |

If hook status is installed but no export occurs, check policy first, then validate `repos.sessions`, Git identity, and the sessions repository remote.
