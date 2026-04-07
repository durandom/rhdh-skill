#!/usr/bin/env bash
# up.sh — Start RHDH Local containers
# Inspired by Ben Wilcock's rhdh-lab (https://github.com/benwilcock/rhdh-lab)
# See NOTICE for license information.

set -euo pipefail

WORKSPACE=""
BASELINE=false
LIGHTSPEED=false
ORCHESTRATOR=false
BOTH=false
FOLLOW_LOGS=false

# Bundled scripts dir (same directory as this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      WORKSPACE="$2"
      shift 2
      ;;
    --baseline)
      BASELINE=true
      shift
      ;;
    --customized)
      BASELINE=false
      shift
      ;;
    --lightspeed)
      LIGHTSPEED=true
      shift
      ;;
    --orchestrator)
      ORCHESTRATOR=true
      shift
      ;;
    --both)
      BOTH=true
      shift
      ;;
    --follow-logs | -f)
      FOLLOW_LOGS=true
      shift
      ;;
    --help | -h)
      echo "Usage: $0 --workspace <path> [options]"
      echo ""
      echo "  --workspace <path>  Path to rhdh-local-setup workspace root (required)"
      echo "  --baseline          Start without customizations (pristine RHDH)"
      echo "  --customized        Start with customizations applied (default)"
      echo "  --lightspeed        Include Lightspeed compose file"
      echo "  --orchestrator      Include Orchestrator compose file"
      echo "  --both              Include both Lightspeed and Orchestrator"
      echo "  --follow-logs, -f   Follow container logs after start"
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

# Apply or remove customizations based on mode
if [[ "$BASELINE" == "true" ]]; then
  echo "Removing customizations (starting in pristine/baseline mode)..."
  bash "$SCRIPT_DIR/remove-customizations.sh" --workspace "$WORKSPACE"
else
  echo "Applying customizations..."
  bash "$SCRIPT_DIR/apply-customizations.sh" --workspace "$WORKSPACE"
fi

# --both implies --lightspeed and --orchestrator
if [[ "$BOTH" == "true" ]]; then
  LIGHTSPEED=true
  ORCHESTRATOR=true
fi

# Build compose command
cd "$RHDH_LOCAL"
read -ra COMPOSE_CMD <<< "$COMPOSE -f compose.yaml"

[[ -f "compose.override.yaml" ]] && COMPOSE_CMD+=(-f compose.override.yaml)
[[ "$LIGHTSPEED" == "true" && -f "developer-lightspeed/compose.lightspeed.yaml" ]] && \
  COMPOSE_CMD+=(-f developer-lightspeed/compose.lightspeed.yaml)
[[ "$ORCHESTRATOR" == "true" && -f "developer-ai-orchestrator/compose.orchestrator.yaml" ]] && \
  COMPOSE_CMD+=(-f developer-ai-orchestrator/compose.orchestrator.yaml)

MODE="customized"
[[ "$BASELINE" == "true" ]] && MODE="baseline"

echo "Starting RHDH ($MODE mode)..."
"${COMPOSE_CMD[@]}" up -d

if [[ "$FOLLOW_LOGS" == "true" ]]; then
  "${COMPOSE_CMD[@]}" logs -f
fi

echo "RHDH started. Check http://localhost:7007"
