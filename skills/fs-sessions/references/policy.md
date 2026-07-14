# Repository policy

The global policy lives under `sessions.policy` in `~/.config/rhdh-skill/config.json`.

## Semantics

- Git `cwd` is resolved to its canonical Git root before matching.
- `origin` values normalize SSH and HTTPS URLs to `host/owner/repo`, such as `github.com/example-org/service`.
- `path` values match the canonical absolute Git root and may contain shell-style globs.
- Rules are evaluated top to bottom; the last matching rule wins.
- Non-Git directories are denied regardless of the default.
- `.rhdh/config.json` may only opt out with `{"sessions":{"enabled":false}}`.

## Common policies

Whitelist:

```bash
"$FS" policy default deny
"$FS" policy allow --origin 'github.com/example-org/*'
```

Blacklist (use only when the user explicitly accepts automatic export from otherwise-unmatched repositories):

```bash
"$FS" policy default allow
"$FS" policy deny --path '/work/customer-*'
```

Mixed exceptions:

```bash
"$FS" policy allow --path '/work/*'
"$FS" policy deny --path '/work/customer-*'
"$FS" policy allow --path '/work/customer-sanitized-demo'
```

## Manage and explain

```bash
"$FS" policy rules
"$FS" policy check /path/to/repository
"$FS" policy remove 3
```

After every mutation, run `policy rules` and `policy check` for affected repositories. Report the default, matching rule, normalized origin, Git root, and final decision.
