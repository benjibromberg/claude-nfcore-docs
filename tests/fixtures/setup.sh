#!/usr/bin/env bash
# setup.sh — Download pinned nf-core pipeline fixtures for E2E testing.
#
# Shallow-clones each pipeline at a specific tag. Skips if already present.
# Run once before E2E tests: ./tests/fixtures/setup.sh
#
# Pipelines are defined in pipelines.json alongside this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINES_JSON="$SCRIPT_DIR/pipelines.json"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 required for JSON parsing" >&2
  exit 1
fi

# Parse pipelines.json and clone each
python3 -c "
import json, sys
with open('$PIPELINES_JSON') as f:
    pipelines = json.load(f)
for name, info in pipelines.items():
    print(f\"{name}|{info['repo']}|{info['tag']}\")
" | while IFS='|' read -r name repo tag; do
  dest="$SCRIPT_DIR/$name"

  if [ -d "$dest" ]; then
    # Verify it's the right tag
    existing_tag=$(git -C "$dest" describe --tags --exact-match 2>/dev/null || echo "unknown")
    if [ "$existing_tag" = "$tag" ]; then
      echo "✓ $name @ $tag (already present)"
      continue
    else
      echo "! $name exists but at $existing_tag, re-cloning at $tag..."
      rm -rf "$dest"
    fi
  fi

  echo "⬇ Cloning $repo @ $tag → $dest"
  git clone --depth 1 --branch "$tag" "https://github.com/$repo.git" "$dest" 2>&1
  echo "✓ $name @ $tag"
done

echo ""
echo "Fixtures ready. Total size:"
du -sh "$SCRIPT_DIR"/*/  2>/dev/null | grep -v __pycache__
