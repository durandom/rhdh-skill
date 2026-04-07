#!/usr/bin/env bash
# down.sh — Stop RHDH Local containers
# Inspired by Ben Wilcock's rhdh-lab (https://github.com/benwilcock/rhdh-lab)
# See NOTICE for license information.

set -euo pipefail

WORKSPACE=""
REMOVE_VOLUMES=false

# Bundled scripts dir (same directory as this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE="$2"
      shift 2
      ;;
    --volumes | -v)
      REMOVE_VOLUMES=true
      shift
      ;;
    --keep-volumes)
      REMOVE_VOLUMES=false
      shift
      ;;
    --help | -h)
      echo "Usage: $0 --workspace <path> [options]"
      echo ""
      echo "  --workspace <path>  Path to rhdh-local-setup workspace root (required)"
      echo "  --volumes, -v       Remove named volumes on stop"
      echo "  --keep-volumes      Keep volumes on stop (default)"
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

RHDH_LOCAL="$WORKSPACE/rhdh-local"

if [[ ! -d "$RHDH_LOCAL" ]]; then
  echo "Error: rhdh-local not found at: $RHDH_LOCAL" >&2
  exit 1
fi

# Auto-detect container runtime
if command -v podman &>/dev/null; then
  COMPOSE="podman compose"
elif command -v docker &>/dev/null; then
  COMPOSE="docker compose"
else
  echo "Error: Neither podman nor docker found in PATH" >&2
  exit 1
fi

cd "$RHDH_LOCAL"

# Include all possible compose files for thorough shutdown
read -ra COMPOSE_CMD <<< "$COMPOSE -f compose.yaml"
[[ -f "compose.override.yaml" ]] && COMPOSE_CMD+=(-f compose.override.yaml)
[[ -f "developer-lightspeed/compose.lightspeed.yaml" ]] && \
  COMPOSE_CMD+=(-f developer-lightspeed/compose.lightspeed.yaml)
[[ -f "developer-ai-orchestrator/compose.orchestrator.yaml" ]] && \
  COMPOSE_CMD+=(-f developer-ai-orchestrator/compose.orchestrator.yaml)

echo "Stopping RHDH..."
if [[ "$REMOVE_VOLUMES" == "true" ]]; then
  "${COMPOSE_CMD[@]}" down -v
else
  "${COMPOSE_CMD[@]}" down
fi

# Always remove customizations after shutdown
echo "Removing customizations..."
bash "$SCRIPT_DIR/remove-customizations.sh" --workspace "$WORKSPACE"

echo "RHDH stopped."
