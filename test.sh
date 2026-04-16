#!/usr/bin/env bash
# test.sh — nfcore-docs skill test runner
#
# Usage:
#   ./test.sh              Static tests only (no LLM, free, <5s)
#   ./test.sh --e2e        Static + E2E tests (needs claude CLI + Max subscription)
#   ./test.sh --e2e-only   E2E tests only
#   ./test.sh --verbose    Show individual test names
#   ./test.sh --help       Show this help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E=false
E2E_ONLY=false
VERBOSE=""
EXTRA_ARGS=""

for arg in "$@"; do
  case "$arg" in
    --e2e)      E2E=true ;;
    --e2e-only) E2E=true; E2E_ONLY=true ;;
    --verbose)  VERBOSE="-v" ;;
    --help|-h)
      echo "Usage: ./test.sh [--e2e] [--e2e-only] [--verbose]"
      echo ""
      echo "  (no flags)   Static tests only — no LLM, free, <5s"
      echo "  --e2e        Static + E2E tests (needs claude CLI + Max subscription)"
      echo "  --e2e-only   E2E tests only"
      echo "  --verbose    Show individual test names"
      exit 0 ;;
    *)
      EXTRA_ARGS="$EXTRA_ARGS $arg" ;;
  esac
done

cd "$SCRIPT_DIR"

echo "=== nfcore-docs test runner ==="
echo ""

# Check for pytest
if ! python3 -m pytest --version >/dev/null 2>&1; then
  echo "WARNING: pytest not found, falling back to unittest" >&2
  RUNNER="python3 -m unittest discover -s tests -p test_*.py"
  RUNNER_E2E="python3 -m unittest tests.test_e2e"
else
  RUNNER="python3 -m pytest tests/ -x $VERBOSE --ignore=tests/test_e2e.py $EXTRA_ARGS"
  RUNNER_E2E="python3 -m pytest tests/test_e2e.py -x $VERBOSE $EXTRA_ARGS"
fi

STATIC_EXIT=0
E2E_EXIT=0

if [ "$E2E_ONLY" = false ]; then
  echo "--- Tier 1: Static tests (no LLM) ---"
  echo ""
  if $RUNNER; then
    STATIC_EXIT=0
  else
    STATIC_EXIT=$?
  fi
  echo ""
fi

if [ "$E2E" = true ]; then
  if ! command -v claude >/dev/null 2>&1; then
    echo "ERROR: claude CLI not found. E2E tests require Claude Code." >&2
    exit 1
  fi
  echo "--- Tier 2: E2E tests (claude -p) ---"
  echo "(Uses your Max subscription — no API cost)"
  echo ""
  if $RUNNER_E2E; then
    E2E_EXIT=0
  else
    E2E_EXIT=$?
  fi
  echo ""
fi

# Summary
echo "=== Results ==="
[ "$E2E_ONLY" = false ] && echo "Static: $([ $STATIC_EXIT -eq 0 ] && echo 'PASS' || echo 'FAIL')"
[ "$E2E" = true ] && echo "E2E:    $([ $E2E_EXIT -eq 0 ] && echo 'PASS' || echo 'FAIL')"

exit $(( STATIC_EXIT + E2E_EXIT ))
