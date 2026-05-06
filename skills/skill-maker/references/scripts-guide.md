# Scripts Guide

Full guide: https://agentskills.io/skill-creation/using-scripts

## Default to Scripts

**Scripts are cheaper, faster, and more reliable than LLM instructions.** Every deterministic operation in a skill should be a script. For each step in a workflow, ask: "Could a script do this?" If yes, write the script. Only leave genuine judgment calls to instructions.

A skill that validates input, generates files from templates, and calls APIs should have scripts for all three — the SKILL.md just orchestrates when to call them and handles the decisions between steps.

Keep instructions for:
- Creative or exploratory reasoning
- Decisions that depend on ambiguous context
- Explaining tradeoffs to the user
- Tasks where the right approach varies significantly case-by-case

## Directory Convention

```
skill-name/
└── scripts/
    ├── validate.py
    ├── format-output.sh
    └── setup.py
```

## Making Scripts Executable

### Shebang lines

Every script needs a shebang so it can run directly:

```python
#!/usr/bin/env python3
```

```bash
#!/usr/bin/env bash
```

### Cross-platform compatibility

Skills run on macOS, Windows, and Linux. Write scripts that work on all three:

- Use `#!/usr/bin/env python3` (not a hardcoded path). On Windows, agents call `python script.py` instead of `./script.py`.
- **Temp directories**: Use `tempfile.mkdtemp()` or `tempfile.TemporaryDirectory()`, never hardcode `/tmp`. Windows uses `C:\Users\<user>\AppData\Local\Temp`.
- **Path separators**: Use `pathlib.Path` or `os.path.join()`, never hardcode `/` in paths.
- **Line endings**: Use `newline=""` when opening files for CSV/structured output. Don't assume `\n`.
- **Shell commands**: If a script calls external tools, document the platform differences or use Python stdlib equivalents.

```python
import tempfile
from pathlib import Path

# Good — works everywhere
work_dir = Path(tempfile.mkdtemp(prefix="skill-"))
output = work_dir / "result.json"

# Bad — breaks on Windows
work_dir = "/tmp/skill-output"
```

## Python Scripts

### Without dependencies (preferred)

Use stdlib only. Use `argparse` for argument parsing:

```python
#!/usr/bin/env python3
"""Validate workspace configuration."""

import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description="Validate workspace config")
    parser.add_argument("path", help="Path to workspace directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # ... validation logic ...

    if args.json:
        json.dump(result, sys.stdout)
    else:
        print(f"Validation: {'PASS' if result['valid'] else 'FAIL'}")

    sys.exit(0 if result["valid"] else 1)

if __name__ == "__main__":
    main()
```

### With dependencies (PEP 723)

When external packages are needed, use inline script metadata so `uv run` handles isolation:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "beautifulsoup4",
#   "requests",
# ]
# ///

"""Extract data from a web page."""

from bs4 import BeautifulSoup
import requests
# ...
```

Run with: `uv run scripts/extract.py`

`uv` creates an isolated environment, installs dependencies, and runs the script. `pipx run` also supports PEP 723.

## Designing for Agents

Scripts invoked by agents should follow these patterns:

### Structured output

Return JSON when piped, human-readable when in a terminal:

```python
import sys
import json

if sys.stdout.isatty():
    print(f"Found {count} issues")
else:
    json.dump({"count": count, "issues": issues}, sys.stdout)
```

### Clear exit codes

- `0` = success
- `1` = expected failure (validation failed, no results)
- `2` = usage error (bad arguments)

### Helpful --help

The agent reads `--help` to understand flags. Make it descriptive:

```python
parser.add_argument(
    "--strict",
    action="store_true",
    help="Treat warnings as errors. Use for CI checks."
)
```

### Idempotent operations

Scripts should be safe to re-run. Don't assume fresh state.
