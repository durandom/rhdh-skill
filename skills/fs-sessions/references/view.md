# View in AgentsView

Resolve the sessions repository with `"$FS" config show` and use its supported AgentsView command. For `fullsend-sessions`:

```bash
just -d /path/to/fullsend-sessions sessions
```

To force a complete re-index, stop the repository's compose stack with its volume-removal command before restarting. Do not delete or rewrite files under `sessions/`.

Sessions appear under `<user>_<project>`. The first synthetic user message supplies the session title and virtual `/sessions/<user>_<project>` working directory.
