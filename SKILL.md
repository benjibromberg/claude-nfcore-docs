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

## Step 0: Check read permissions

This skill reads many files from `~/.cache/nfcore-docs/`. To avoid being prompted
for every file, add this permission to your global Claude Code settings
(`~/.claude/settings.json`) or project settings (`.claude/settings.local.json`):

```json
"permissions": {
  "allow": [
    "Read(//{home}/.cache/nfcore-docs/**)"
  ]
}
```

Or when prompted on first use, select "Always allow" for reads from this path.

## Step 1: Update docs and generate index

**If this skill has already been invoked earlier in this conversation**, skip the
preamble — the index and any loaded docs are already in context. Go directly to
Step 2 to ask what additional docs to load, or answer questions from what's
already loaded.

Otherwise, run this preamble to ensure docs are fresh and produce the index:

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

## Step 2: Determine what to load

The full index with page titles and section headers is now in context (~15K tokens).
You can already answer "what docs exist about X?" from the index alone.

If the user's intent is clear from their message (e.g., "load module specs",
"check CI compliance"), skip the prompt and load the relevant files directly.

If the user's intent is ambiguous (e.g., just `/nfcore-docs` with no context),
use AskUserQuestion to ask:

> The nf-core docs index is now loaded (172 pages with section headers).
> I can navigate any topic from the index. Want me to load the full text
> of specific sections into context?
>
> 1. Module migration — module structure, naming, ext.args, meta.yml (9 files)
> 2. Subworkflow restructure — conventions, I/O, naming (7 files)
> 3. nf-test coverage — testing specs for modules, subworkflows, pipelines (3 files)
> 4. Lint fixes — linting rules, parameter conventions (2 files)
> 5. CI setup — GitHub Actions, test profiles (1 file)
> 6. Full compliance audit — all pipeline requirements + recommendations (28 files)
> 7. Documentation — README, usage.md, output.md, module docs (3 files)
> 8. Git/branch model — branch naming, reviews, merge strategy (6 files)
> 9. First release prep — all requirements + recommendations + reviews (33 files)
> 10. nf-core CLI reference — tools docs (~40 files)
> 11. Load all specs — 56 spec files (~60K tokens, 6% of 1M context)
> 12. Load all docs — all 172 files (~275K tokens, 28% of 1M context)
> 13. Just use the index — don't load anything else yet, I'll ask for specific files
> 14. Something else — describe what you need

**Context budget (measured on Opus 1M):**

| Layer | Files | Tokens | % of 1M |
|-------|-------|--------|---------|
| Index only (already loaded) | — | ~15K | 1.5% |
| + Specifications | 56 | ~60K | 6% |
| + All remaining docs | 116 | ~200K | 20% |
| **Total (all docs)** | **172** | **~275K** | **28%** |

For most compliance work, **index + specs (~75K, 8%)** is sufficient. The remaining
200K of contributing/developing/running/community docs are reference material — load
selectively by section when needed.

## Step 3: Load doc files

Base paths:

- Docs: `~/.cache/nfcore-docs/sites/docs/src/content/docs/`
- API: `~/.cache/nfcore-docs/sites/docs/src/content/api_reference/`

**File mapping:**

| Selection | Files to Read |
|-----------|---------------|
| 1. Module migration | `specifications/components/modules/*.md` (9 files) |
| 2. Subworkflow work | `specifications/components/subworkflows/*.md` (7 files) |
| 3. nf-test coverage | `*/modules/testing.md` + `*/subworkflows/testing.md` + `*/recommendations/testing.md` |
| 4. Lint fixes | `*/requirements/linting.md` + `*/requirements/parameters.md` |
| 5. CI setup | `*/requirements/ci_testing.md` |
| 6. Full compliance audit | `specifications/pipelines/requirements/*.md` + `specifications/pipelines/recommendations/*.md` |
| 7. Documentation | `*/requirements/documentation.md` + `*/modules/documentation.md` + `*/subworkflows/documentation.md` |
| 8. Git/branch model | `*/requirements/git_branches.md` + `specifications/reviews/*.md` |
| 9. First release | All pipeline requirements + recommendations + reviews |
| 10. CLI reference | `nf-core-tools/*.md` |
| 11. All specs | All files under `specifications/` (56 files) |
| 12. All docs | All files under the docs root (172 files) |
| 13. Index only | No additional files — use index to answer questions or load specific files on demand |
| 14. Custom | Use Grep on the index output to find relevant files |

For API reference lookups, use Glob:
`~/.cache/nfcore-docs/sites/docs/src/content/api_reference/{version}/`

**Note:** Files contain Astro/Starlight frontmatter (YAML between `---`).
The specification content follows after the frontmatter.

## Step 4: Apply specs to the current work

After loading the relevant docs:
1. Identify which rules apply to the current task
2. Check the pipeline's current state against those rules
3. Flag any violations or missing requirements
4. Suggest specific fixes with file paths and code

**Never pipe output through head/tail/grep** — always show full output.

### Full compliance audit (selection 6)

When the user selects "Full compliance audit" or asks for a compliance check:

**Step A: Run all nf-core lint tools**

```bash
rm -rf ~/.config/nfcore/nf-core/modules/  # clear stale cache (tools ≤3.5.2 bug)
nf-core pipelines lint
nf-core modules lint
nf-core subworkflows lint
ls ro-crate-metadata.json 2>/dev/null && echo "RO-Crate: present" || echo "RO-Crate: missing"
```

**Step B: Read ALL spec files**

Read every `.md` file under `specifications/` recursively. Do NOT hardcode a
list of directories or files — the file tree IS the checklist. Each file
defines one or more compliance rules. This ensures the audit stays current
when nf-core adds, moves, or renames spec files.

```bash
find ~/.cache/nfcore-docs/sites/docs/src/content/docs/specifications -name "*.md" | sort
```

Read all of them into context.

**Step C: Evaluate compliance at all levels**

For each spec file, extract the MUST/SHOULD/MAY statements and evaluate
whether the current pipeline satisfies them based on:
- Lint output from Step A
- Pipeline file structure, config, and git state
- Per-module compliance against module spec files
- Per-subworkflow compliance against subworkflow spec files

**Step D: Produce the compliance report**

Build the report dynamically from the spec files read in Step B. Group by
directory (pipelines/requirements, pipelines/recommendations, components/modules,
components/subworkflows, reviews, test-data). Each row is one spec file:
- Title (from frontmatter)
- Status (✓/✗/N/A)
- Notes (specific findings, lint references, what's missing)
- Spec file path (so the user can read the full text)

Include per-module and per-subworkflow tables when relevant.

End with summary counts and this footer:

> *This compliance report is AI-generated and may contain inaccuracies.
> Verify against `nf-core pipelines lint` and the original specifications
> at https://nf-co.re/docs/specifications/overview*

### For other tasks

For non-audit work, run only the relevant nf-core tools and load only the
relevant spec files — not the full `specifications/` tree.

**Delegate to nf-core tools** — never reimplement their functionality:
- Module/subworkflow creation: `nf-core modules create`, `nf-core subworkflows create`
- Schema work: `nf-core pipelines schema build`
- RO-Crate: `nf-core pipelines rocrate`
- Module updates: `nf-core modules update`
- Finding existing modules: `nf-core modules list remote`
