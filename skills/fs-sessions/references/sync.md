# Push or pull shared sessions

Resolve the repository with `"$FS" config show`, then run Git inside that repository.

Push:

```bash
git -C /path/to/fullsend-sessions push
```

Pull without merge commits:

```bash
git -C /path/to/fullsend-sessions pull --rebase
```

Report commits transferred and newly available session files. Do not resolve transcript conflicts by editing content; preserve both source transcripts or ask the user when paths collide.
