# Workflow: Switch Between Customized and Pristine Mode

<required_reading>

- `references/customization-system.md` — what customized vs pristine means
- `../overlay/references/rhdh-local.md` section `<container_lifecycle>` — use scripts, not direct compose commands
</required_reading>

<process>
> **Bare `rhdh-local` clone?** If `up.sh`/`down.sh` do not exist in your setup root, replace every `./down.sh` with `podman compose down` and every `./up.sh [flags]` with `podman compose up -d`, both run from the `rhdh-local/` directory.

## Mode Comparison

| Feature | Customized Mode | Pristine Mode |
|---------|----------------|---------------|
| Configuration | Your `rhdh-customizations/` files | RHDH defaults only |
| Authentication | Your GitHub OAuth (if configured) | Guest user only |
| Plugins | Your override plugins | Default plugins only |
| Environment | Your `.env` overrides | `default.env` only |
| Catalog entities | Your override entities | Example entities only |

**When to use Pristine Mode:**

- Isolating whether an issue is in your config or in RHDH itself
- Testing RHDH updates without your customizations interfering
- Creating minimal reproduction cases for bug reports

**When to use Customized Mode:**

- Normal daily development
- Production-like testing
- Demonstrating features to your team

---

## Switch to Pristine Mode

**With `up.sh`/`down.sh` (full `rhdh-local-setup` layout):**

```bash
./down.sh
./up.sh --baseline
```

> `down.sh` automatically removes the customization copies from `rhdh-local/`.

**With bare `rhdh-local` clone (no `up.sh`):**

```bash
cd rhdh-customizations && ./remove-customizations.sh
cd ../rhdh-local && podman compose down && podman compose up -d
```

---

## Switch Back to Customized Mode

**With `up.sh`/`down.sh`:**

```bash
cd rhdh-customizations && ./apply-customizations.sh
cd .. && ./down.sh && ./up.sh --customized [flags]
```

Add `--lightspeed`, `--orchestrator`, or `--both` as needed.

**With bare `rhdh-local` clone:**

```bash
cd rhdh-customizations && ./apply-customizations.sh
cd ../rhdh-local && podman compose down && podman compose up -d
```

---

## Check Current Mode

```bash
# Customization copies exist = Customized mode
ls -la rhdh-local/.env
ls -la rhdh-local/configs/app-config/app-config.local.yaml

# Or check git status (should be clean in either mode)
cd rhdh-local && git status
```

---

## Workflow: Troubleshoot Configuration Issues

If something isn't working in your customized setup:

```bash
# 1. Stop and switch to pristine
./down.sh
./up.sh --baseline

# 2. Test at http://localhost:7007
# If it works → issue is in your customizations
# If it doesn't → issue is in RHDH itself

# 3. Restore customized mode
cd rhdh-customizations && ./apply-customizations.sh
cd .. && ./down.sh && ./up.sh --customized [flags]

# 4. Re-enable customizations one at a time to isolate the problem
```

---

## Workflow: Test a RHDH Update

```bash
# 1. Stop and switch to pristine
./down.sh
cd rhdh-local && git pull && cd ..

# 2. Start pristine and verify new version works
./up.sh --baseline

# 3. Reapply customizations and test
cd rhdh-customizations && ./apply-customizations.sh
cd .. && ./down.sh && ./up.sh --customized [flags]

# 4. Check for deprecation warnings in logs
cd rhdh-local && podman compose logs rhdh 2>&1 | grep -i deprecat
```

</process>

<success_criteria>
**Pristine mode:**

- [ ] `rhdh-local/` git status is clean (`git status` shows no modified files)
- [ ] RHDH starts at `http://localhost:7007` with Guest login
- [ ] No custom plugins or config visible

**Customized mode:**

- [ ] `rhdh-customizations/apply-customizations.sh` ran without errors
- [ ] Override files exist in `rhdh-local/` (e.g. `rhdh-local/.env` exists)
- [ ] RHDH starts with your custom configuration
- [ ] Your plugins and entities are visible
</success_criteria>
