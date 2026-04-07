#!/usr/bin/env bash
# apply-customizations.sh — Copy override files from rhdh-customizations/ into rhdh-local/
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

if [[ ! -d "$SRC" ]]; then
  echo "Error: rhdh-customizations not found at: $SRC" >&2
  exit 1
fi

if [[ ! -d "$DST" ]]; then
  echo "Error: rhdh-local not found at: $DST" >&2
  exit 1
fi

copy_customization() {
  local src_rel="$1"
  local src="$SRC/$src_rel"
  local dst="$DST/$src_rel"
  if [[ -f "$src" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  Copied: $src_rel"
  fi
}

echo "Applying customizations: $SRC → $DST"

copy_customization "compose.override.yaml"
copy_customization ".env"
copy_customization "configs/app-config/app-config.local.yaml"
copy_customization "configs/dynamic-plugins/dynamic-plugins.override.yaml"
copy_customization "developer-lightspeed/configs/app-config/app-config.lightspeed.local.yaml"

# Wildcard copies (skip silently if no matches)
shopt -s nullglob

for f in "$SRC"/configs/catalog-entities/*.override.yaml; do
  rel="${f#"$SRC/"}"
  copy_customization "$rel"
done

for f in "$SRC"/configs/extra-files/*; do
  [[ -f "$f" ]] || continue
  rel="${f#"$SRC/"}"
  copy_customization "$rel"
done

shopt -u nullglob

echo "Done."
