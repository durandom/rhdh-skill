# Explicit share and list

List recent local Claude Code transcripts:

```bash
"$FS" list
"$FS" list --limit 50
```

Explicitly export the most recent transcript:

```bash
"$FS" share --last
```

Or export a known transcript:

```bash
"$FS" share --transcript /path/to/session.jsonl --cwd /path/to/project
```

Explicit sharing is a deliberate user action and does not evaluate the automatic-hook policy. It commits only the exported transcript and leaves unrelated staged files untouched. Push separately after reviewing when required.
