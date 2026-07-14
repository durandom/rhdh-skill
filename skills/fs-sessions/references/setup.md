# Setup or migrate

Use this workflow for first-time global setup or migration from the legacy project-local Bash hook.

## 1. Resolve the shared sessions repository

Prefer, in order:

1. Existing `repos.sessions` in `~/.config/rhdh-skill/config.json`.
2. Legacy `FULLSEND_SESSIONS_REPO` from `~/.config/fullsend/sessions.env`.
3. A path supplied by the user.

Require an existing Git repository containing or intended to contain `sessions/`.

## 2. Initialize safe global configuration

```bash
"$FS" config init --repo /absolute/path/to/fullsend-sessions --default deny
```

This updates only `repos.sessions` and `sessions`; it preserves all other `rhdh-skill` configuration.

## 3. Add the initial allow rule

For migration, preserve the behavior of each repository that already had a local hook. Prefer an origin rule for team repositories and a path rule for local-only repositories:

```bash
"$FS" policy allow --origin 'github.com/example-org/*'
# or
"$FS" policy allow --path '/absolute/path/to/repository'
```

Do not change `default` to `allow` merely to make setup convenient; that would export every Git repository not explicitly denied.

## 4. Preview the decision

```bash
"$FS" policy check /absolute/path/to/repository
```

Continue only when it reports `allow` and the expected rule number.

## 5. Install the global hook

```bash
"$FS" hook install
"$FS" hook status
```

The installer replaces prior managed hooks in the selected settings file and preserves unrelated settings/hooks.

## 6. Remove legacy project hooks

After the global status and policy check pass, inspect each formerly configured project. Remove only the managed session hook:

```bash
"$FS" hook uninstall --settings /path/to/project/.claude/settings.json
```

Keep unrelated project hooks. Commit the project settings change when that settings file is tracked.

## 7. Verify

```bash
"$FS" status
```

Setup is complete when config is valid, the intended repository is allowed, exactly one global managed hook exists, and no legacy project-local session hook remains.
