# Workflow: Doctor

Diagnose and fix environment issues for the RHDH Plugin skill.

<prerequisites>
- Git installed
- GitHub SSH access configured (for cloning repos)
</prerequisites>

<quick_start>

## Fastest Path

```bash
rhdh-plugin setup submodule add --all
```

Creates `repo/` directory with required repositories as git submodules.

Run `rhdh-plugin` to verify setup, then continue with your original task.
</quick_start>

<process>

## Option 1: Submodules (Recommended)

```bash
rhdh-plugin setup submodule list      # Check status
rhdh-plugin setup submodule add --all # Add required repos
rhdh-plugin                           # Verify
```

## Option 2: Existing Checkouts

Point to repositories you've already cloned:

```bash
rhdh-plugin config set repos.overlay /path/to/rhdh-plugin-export-overlays
rhdh-plugin config set repos.local /path/to/rhdh-local
rhdh-plugin                           # Verify
```

## Option 3: Environment Variables

For CI/CD:

```bash
export RHDH_OVERLAY_REPO=/path/to/rhdh-plugin-export-overlays
export RHDH_LOCAL_REPO=/path/to/rhdh-local
```

</process>

<tracking>

## Activity Logging

Log setup events for troubleshooting:

```bash
# Initial setup
rhdh-plugin log add "Environment setup complete" --tag setup

# Configuration changes
rhdh-plugin log add "Configured overlay repo: <path>" --tag setup --tag config
rhdh-plugin log add "Configured rhdh-local: <path>" --tag setup --tag config
```

## Follow-up Todos

```bash
# If setup blocked
rhdh-plugin todo add "Request access to overlay repo" --context "setup"
rhdh-plugin todo add "Set up GitHub SSH keys" --context "setup"
```

</tracking>

<success_criteria>
Setup complete when `rhdh-plugin` shows `needs_setup: false`.
</success_criteria>
