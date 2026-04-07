#!/usr/bin/env bash
# remove-customizations.sh — Remove override files from rhdh-local/ (restore pristine state)
# Inspired by Ben Wilcock's rhdh-lab (https://github.com/benwilcock/rhdh-lab)
# See NOTICE for license information.

set -euo pipefail

WORKSPACE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE="$2"
      shift 2
      ;;
    --help | -h)
      echo "Usage: $0 --workspace <path>"
      echo ""
      echo "  --workspace <path>  Path to rhdh-local-setup workspace root"
      echo ""
      echo "Environment:"
      echo "  RHDH_WORKSPACE_ROOT  Fallback if --workspace not provided"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# Fall back to env var
if [[ -z "$WORKSPACE" ]] && [[ -n "${RHDH_WORKSPACE_ROOT:-}" ]]; then
  WORKSPACE="$RHDH_WORKSPACE_ROOT"
fi

if [[ -z "$WORKSPACE" ]]; then
  echo "Error: --workspace <path> or RHDH_WORKSPACE_ROOT must be set" >&2
  exit 1
fi

SRC="$WORKSPACE/rhdh-customizations"
DST="$WORKSPACE/rhdh-local"

remove_customization() {
  local rel="$1"
  local dst="$DST/$rel"
  if [[ -f "$dst" ]]; then
    rm -f "$dst"
    echo "  Removed: $rel"
  fi
}

echo "Removing customizations from: $DST"

remove_customization "compose.override.yaml"
remove_customization ".env"
remove_customization "configs/app-config/app-config.local.yaml"
remove_customization "configs/dynamic-plugins/dynamic-plugins.override.yaml"
remove_customization "developer-lightspeed/configs/app-config/app-config.lightspeed.local.yaml"

# Remove wildcard-copied files (use source as reference)
shopt -s nullglob

for f in "$SRC"/configs/catalog-entities/*.override.yaml; do
  rel="${f#"$SRC/"}"
  remove_customization "$rel"
done

for f in "$SRC"/configs/extra-files/*; do
  [[ -f "$f" ]] || continue
  rel="${f#"$SRC/"}"
  remove_customization "$rel"
done

shopt -u nullglob

echo "Done."
