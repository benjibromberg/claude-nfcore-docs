---
name: nfcore-docs
version: 1.0.0
description: |
  Load nf-core documentation and specifications into context. Pulls latest docs from
  nf-core/website if stale (>24h). Covers specifications (pipeline requirements,
  module/subworkflow conventions), contributing guidelines, development docs, and
  nf-core tools reference. Works with any nf-core pipeline.
  Use when asked to "check nf-core compliance", "load nf-core docs", "nf-core spec",
  or when doing compliance work (module migration, testing, lint fixes, audits).
  Proactively suggest when working on nf-core pipeline development.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
---

# nf-core Documentation Loader

## Step 1: Update docs and generate index

Run this preamble to ensure docs are fresh and produce a full page + header index:

```bash
DOCS_CACHE="$HOME/.cache/nfcore-docs"
DOCS_ROOT="$DOCS_CACHE/sites/docs/src/content/docs"
STALE_HOURS=24

# --- Update if stale ---
if [ -d "$DOCS_CACHE/.git" ]; then
  FETCH_HEAD="$DOCS_CACHE/.git/FETCH_HEAD"
  if [ -f "$FETCH_HEAD" ]; then
    if [ "$(uname)" = "Darwin" ]; then
      AGE_HOURS=$(( ($(date +%s) - $(stat -f %m "$FETCH_HEAD")) / 3600 ))
    else
      AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$FETCH_HEAD")) / 3600 ))
    fi
    echo "Docs last fetched: ${AGE_HOURS}h ago"
    if [ "$AGE_HOURS" -ge "$STALE_HOURS" ]; then
      echo "Updating..."
      git -C "$DOCS_CACHE" pull origin main --depth 1 2>&1
    else
      echo "✓ Docs are fresh (< ${STALE_HOURS}h)"
    fi
  else
    git -C "$DOCS_CACHE" pull origin main --depth 1 2>&1
  fi
else
  echo "⚠ nf-core docs cache not found. Setting up..."
  mkdir -p "$DOCS_CACHE" && cd "$DOCS_CACHE"
  git init
  git remote add origin https://github.com/nf-core/website.git
  git config core.sparseCheckout true
  printf 'sites/docs/src/content/docs/\nsites/docs/src/content/api_reference/\n' > .git/info/sparse-checkout
  git pull origin main --depth 1 2>&1
  cd - > /dev/null
  echo "✓ Docs cache created at $DOCS_CACHE"
fi

# --- Generate index ---
CONTENT_ROOT="$DOCS_CACHE/sites/docs/src/content"
API_ROOT="$CONTENT_ROOT/api_reference"

echo ""
echo "=== nf-core Documentation Index ==="
echo "Docs root: $DOCS_ROOT"
echo "API root:  $API_ROOT"
echo ""
python3 -c "
import os, re, sys

docs_root = sys.argv[1]
api_root = sys.argv[2]

# --- Full index of docs (172 files, with headers) ---
print('## Documentation')
print()
for dirpath, dirnames, filenames in sorted(os.walk(docs_root)):
    dirnames.sort()
    for fname in sorted(filenames):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(dirpath, fname)
        rel = os.path.relpath(fpath, docs_root)
        with open(fpath) as f:
            content = f.read()
        title_match = re.search(r'^title:\s*[\"\']*(.+?)[\"\']*\s*$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else fname.replace('.md', '')
        body = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        headers = re.findall(r'^(#{2,3})\s+(.+)$', body, re.MULTILINE)
        print(f'- \`{rel}\` — {title}')
        for level, header in headers:
            indent = '  ' if level == '##' else '    '
            print(f'{indent}- {header}')

# --- API reference summary (top-level dirs + file counts) ---
print()
print('## API Reference')
print()
if os.path.isdir(api_root):
    total = 0
    for entry in sorted(os.listdir(api_root)):
        entry_path = os.path.join(api_root, entry)
        if os.path.isdir(entry_path):
            count = sum(1 for f in os.listdir(entry_path) if f.endswith('.md'))
            total += count
            print(f'- \`api_reference/{entry}/\` — {count} files')
        elif entry.endswith('.md'):
            total += 1
            print(f'- \`api_reference/{entry}\`')
    print(f'  Total: {total} API reference files')
else:
    print('  (not found)')
" "$DOCS_ROOT" "$API_ROOT"

# --- Pipeline context (if in a pipeline repo) ---
echo ""
if [ -f "nextflow.config" ] && grep -q "nf-core\|nf_core" nextflow.config 2>/dev/null; then
  echo "=== Current Pipeline ==="
  grep "name\s*=" nextflow.config | head -1
  echo "Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
  echo "Local modules: $(find modules/local -name '*.nf' 2>/dev/null | wc -l | tr -d ' ')"
  echo "nf-core modules: $(find modules/nf-core -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"
  echo "Local subworkflows: $(find subworkflows/local -name '*.nf' 2>/dev/null | wc -l | tr -d ' ')"
fi
```

## Step 2: Load relevant doc files

Based on the index output and the user's task, use the Read tool to load the
relevant documentation files into context.

**File locations:**
- Docs: `~/.cache/nfcore-docs/sites/docs/src/content/docs/`
- API reference: `~/.cache/nfcore-docs/sites/docs/src/content/api_reference/`

**Quick reference — which files for which task:**

| Task | Directory/files |
|------|----------------|
| Module migration | `docs/specifications/components/modules/*.md` |
| Subworkflow work | `docs/specifications/components/subworkflows/*.md` |
| nf-test coverage | `*/modules/testing.md` + `*/subworkflows/testing.md` + `*/recommendations/testing.md` |
| Lint fixes | `*/requirements/linting.md` + `*/requirements/parameters.md` |
| CI setup | `*/requirements/ci_testing.md` |
| Full compliance audit | `docs/specifications/pipelines/requirements/*.md` + `docs/specifications/pipelines/recommendations/*.md` |
| Git/branch model | `*/requirements/git_branches.md` + `docs/specifications/reviews/*.md` |
| Documentation updates | `*/requirements/documentation.md` + `*/modules/documentation.md` |
| First release prep | All pipeline requirements + recommendations + reviews |
| nf-core CLI usage | `docs/nf-core-tools/` |
| Pipeline execution | `docs/running/` |
| Pipeline/module API | `api_reference/` (use Glob to find specific pipeline/module) |

Read the files the user needs. For targeted work, load only the relevant section.
For audits, load all pipeline specs. For API reference, search by pipeline or module name.

**Note:** Files contain Astro/Starlight frontmatter (YAML between `---`).
The specification content follows after the frontmatter.

## Step 3: Apply specs to the current work

After loading the relevant docs:
1. Identify which rules apply to the current task
2. Check the pipeline's current state against those rules
3. Flag any violations or missing requirements
4. Suggest specific fixes with file paths and code

If the user asks for a compliance check, also run:

```bash
# Clear stale nf-core tools module cache (known bug in tools ≤3.5.2)
rm -rf ~/.config/nfcore/nf-core/modules/
# Run lint — never pipe through head/tail/grep
nf-core pipelines lint
```
