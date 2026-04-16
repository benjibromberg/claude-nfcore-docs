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
use AskUserQuestion. Follow this structure for ALL AskUserQuestion calls:

1. **Re-ground** — State the pipeline (if detected) and current branch (1 sentence)
2. **Context** — What's already loaded (index, specs, etc.)
3. **Recommend** — If one option is clearly best for the context, say so
4. **Options** — Lettered/numbered list

Ask:

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

**File mapping and nf-core tools to run:**

| Selection | Spec files to Read | nf-core tool to run |
|-----------|-------------------|---------------------|
| 1. Module migration | `specifications/components/modules/*.md` | `nf-core modules lint` |
| 2. Subworkflow work | `specifications/components/subworkflows/*.md` | `nf-core subworkflows lint` |
| 3. nf-test coverage | `*/modules/testing.md` + `*/subworkflows/testing.md` + `*/recommendations/testing.md` | `nf-core modules test`, `nf-core subworkflows test` |
| 4. Lint fixes | `*/requirements/linting.md` + `*/requirements/parameters.md` | `nf-core pipelines lint` |
| 5. CI setup | `*/requirements/ci_testing.md` | (check `.github/workflows/`) |
| 6. Full compliance audit | All `specifications/**/*.md` recursively | All: `pipelines lint` + `modules lint` + `subworkflows lint` + RO-Crate check |
| 7. Documentation | `*/requirements/documentation.md` + `*/modules/documentation.md` + `*/subworkflows/documentation.md` | `nf-core pipelines lint` (docs checks) |
| 8. Git/branch model | `*/requirements/git_branches.md` + `specifications/reviews/*.md` | (check git branches) |
| 9. First release | All pipeline requirements + recommendations + reviews | All: `pipelines lint` + `modules lint` + `subworkflows lint` |
| 10. CLI reference | `nf-core-tools/*.md` | (reference only) |
| 11. All specs | All `specifications/**/*.md` | (depends on task) |
| 12. All docs | All files under docs root | (depends on task) |
| 13. Index only | None — use index to navigate | None |
| 14. Custom | Use Grep on index output | (depends on task) |

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

**Step A: Run lint tools and gather pipeline state**

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

**Step C: Evaluate compliance — parallel agent mode**

Launch 5 parallel agents, each responsible for one compliance domain.
Each agent receives the lint output from Step A and the relevant spec
files from Step B. Each returns findings with severity and confidence.

Before launching agents, ask the user via AskUserQuestion:

> Running parallel compliance audit with 5 agents. Which model?
>
> A) Inherit from current session (default)
> B) Haiku — fast, cheaper, good for quick checks
> C) Sonnet — balanced, recommended for thorough audits
> D) Opus — most thorough, highest cost

Use the Agent tool with `subagent_type: "general-purpose"` and set the
`model` parameter based on the user's choice (omit for option A).

| Agent | Domain | Specs to include | Tool to reference |
|-------|--------|-----------------|-------------------|
| 1 | Pipeline requirements | `specifications/pipelines/requirements/*.md` + `specifications/pipelines/recommendations/*.md` | `nf-core pipelines lint` output |
| 2 | Module compliance | `specifications/components/modules/*.md` | `nf-core modules lint` output |
| 3 | Subworkflow compliance | `specifications/components/subworkflows/*.md` | `nf-core subworkflows lint` output |
| 4 | Documentation & metadata | `specifications/pipelines/requirements/documentation.md`, `*/keywords.md`, `*/ro_crate.md` | README, usage.md, output.md file checks |
| 5 | Git, CI & reviews | `specifications/pipelines/requirements/git_branches.md`, `*/ci_testing.md`, `specifications/reviews/*.md` | git branch state, `.github/workflows/` |

**Agent prompt template** (adapt per agent domain):

```
You are auditing an nf-core pipeline for compliance. Your domain: {DOMAIN}.

## Specs (read these — they define the rules)
{SPEC FILE CONTENTS}

## Lint output to cross-reference
{RELEVANT LINT OUTPUT SECTION}

## Pipeline state
{RELEVANT FILE LISTINGS, CONFIG EXCERPTS, GIT STATE}

## Instructions
1. For each spec rule (MUST/SHOULD/MAY), evaluate whether the pipeline complies
2. Classify each finding:
   - Severity: Critical (MUST violation), High (SHOULD gap), Medium (MAY), Low (polish)
   - Confidence: 1-10 (10=verified by lint/code, 5=moderate, 1=speculation)
3. List positive findings (requirements already met)
4. Return findings as a structured list, one per line:
   [SEVERITY] (confidence: N/10) — description | spec: {filename}

Return ALL findings — every single one. Do not summarize, truncate, or
omit any finding regardless of severity or confidence. No preamble, no
summary paragraph. Just the structured findings list.
```

Launch all 5 agents in a single message using multiple Agent tool calls
so they run in parallel.

**Consolidation** (after all agents return):
- Collect all findings from all 5 agents
- Deduplicate: if two agents flag the same spec file with the same status,
  keep the one with higher confidence
- Filter: confidence < 4 goes to appendix only (unless Critical severity)
- Sort: Critical first, then High, then by confidence descending
- Merge positive findings from all agents into one list

**Save raw agent findings** before consolidation:
```bash
mkdir -p .nfcore-docs/reports/agents
```
Write each agent's verbatim output to:
`.nfcore-docs/reports/agents/{date}-agent{N}-{domain}.md`

This preserves the raw findings for:
- Debugging consolidation issues
- Comparing agent outputs across runs
- Verifying no findings were lost during deduplication
- Re-running consolidation without re-running agents

If any agent fails or returns an error, note which domain was not audited
and fall back to sequential evaluation for that domain only.

Classify each finding by severity and confidence:

**Severity** (from spec language):
- **Critical** — MUST / MUST NOT violation (blocks nf-core acceptance)
- **High** — SHOULD / SHOULD NOT gap (strongly recommended)
- **Medium** — MAY suggestion or quality improvement
- **Low** — Minor polish (TODOs, version warnings, formatting)

**Confidence** (1-10):
- 9-10: Verified by lint output or reading specific code. Show normally.
- 7-8: High confidence pattern match against spec. Show normally.
- 5-6: Moderate — could be misinterpreting spec. Show with caveat.
- 3-4: Low — flag for manual review, don't include in main report.
- 1-2: Speculation — only report for Critical or High severity items.

**Step D: Produce the compliance report**

Build the report dynamically from the spec files read in Step B. Group by
directory (pipelines/requirements, pipelines/recommendations, components/modules,
components/subworkflows, reviews, test-data). Each row is one spec file:
- Title (from frontmatter)
- Severity (Critical/High/Medium/Low)
- Status (✓/✗/N/A)
- Notes (specific findings, lint references, what's missing)
- Spec file path (so the user can read the full text)

Start with a severity summary: `Critical: N | High: N | Medium: N | Low: N`

Include a **Positive Findings** section with:
- Requirements already met (list each with ✓)
- Good patterns found in the codebase (e.g., proper ext.args usage, clean
  container directives, well-structured channels)
- Exemplary modules or subworkflows that could serve as templates for others
- Progress since last audit (if a previous report exists)

This helps users know what NOT to change and what patterns to replicate.

Include per-module and per-subworkflow tables when relevant.

End with a **Recommended Next Actions** table:

| Priority | Finding | Fix with | Command |
|----------|---------|----------|---------|
| Critical | {finding} | {what to do} | `nf-core {command}` |
| High | {finding} | {what to do} | `nf-core {command}` |
| ... | | | |

Common mappings:
- Module structure → `nf-core modules create --empty-template`
- Missing meta.yml → `nf-core modules create --empty-template`
- Schema mismatch → `nf-core pipelines schema build`
- Missing RO-Crate → `nf-core pipelines rocrate`
- Module version updates → `nf-core modules update`
- Local module exists upstream → `nf-core modules install {name}`

Compute a **compliance score** (0-10) based on the ratio of passing to total
requirements across all categories (pipeline lint, module compliance, subworkflow
compliance, MUST requirements, SHOULD recommendations). Present as:
`nf-core Compliance Score: X.X/10` with per-category breakdown.

End with summary counts and this footer:

> *This compliance report is AI-generated and may contain inaccuracies.
> Verify against `nf-core pipelines lint` and the original specifications
> at https://nf-co.re/docs/specifications/overview*

**Step E: Offer to create GitHub issues for findings (optional)**

After presenting the compliance report, use AskUserQuestion:

> Found X compliance gaps. Want me to create GitHub issues for them?
> (yes / no / let me pick which ones)

If yes or selective:
1. For each non-compliant item, check for existing issues first:
   ```bash
   gh issue list --search "{requirement keyword}" --state open
   ```
2. If a matching open issue exists, show it and ask whether to skip or create a new one
3. For new issues, create with:
   ```bash
   gh issue create --title "chore(compliance): {spec title}" --body "..."
   ```
   The body should include: spec reference, current status, what needs to change,
   and the spec file path for reference. Add `--label "nf-core compliance"` if
   the label exists on the repo (check with `gh label list` first, or skip the
   label flag to avoid errors).

This prevents duplicate issues when running audits repeatedly.

### For other tasks

For non-audit work, run only the relevant nf-core tools and load only the
relevant spec files — not the full `specifications/` tree.

**Delegate to nf-core tools** — never reimplement their functionality:
- Schema work: `nf-core pipelines schema build`
- RO-Crate: `nf-core pipelines rocrate`
- Module updates: `nf-core modules update`
- Finding existing modules: `nf-core modules list remote`

### Creating new modules or subworkflows

When the user needs to create a new module or subworkflow:

1. Check if an nf-core module already exists: `nf-core modules list remote`
2. If it exists, install it: `nf-core modules install <name>`
3. If not, generate a compliant skeleton:
   - `nf-core modules create --empty-template`
   - `nf-core subworkflows create --empty-template`
4. Load the relevant specs into context (selection 1 for modules, 2 for subworkflows)
5. Review the generated skeleton against the loaded specs
6. Guide the user through completing it with spec-compliant code
7. Run `nf-core modules lint` or `nf-core subworkflows lint` to verify

## Rules

**NEVER:**
- Report compliance without running the actual nf-core lint tools first
- Hardcode a list of requirements — always derive from cached spec files
- Truncate or filter lint/tool output (no head/tail/grep on diagnostics)
- Guess at compliance status — if uncertain, say so explicitly
- Skip the accuracy disclaimer on compliance reports
- Create GitHub issues without checking for existing duplicates
- Reimplement nf-core tools functionality (lint, create, schema build, rocrate, etc.)
- Assume spec files are current without checking cache freshness
- Load the full index/preamble if already loaded earlier in the conversation
- Summarize, truncate, or omit agent results — present ALL findings from every agent verbatim

## Persistence

**Audit reports:** After producing a compliance report (Step D), save it:
```bash
mkdir -p .nfcore-docs/reports
```
Write the report to `.nfcore-docs/reports/{date}-compliance.md`. This enables
trend tracking across audits and cross-session reference.

**Operational learnings:** Before completing, reflect:
- Did any nf-core tools fail unexpectedly?
- Did a spec interpretation turn out to be wrong?
- Did the user correct a compliance assessment?
- Was a spec file missing or outdated?

If yes, log a learning:
```bash
mkdir -p .nfcore-docs
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","context":"WHAT_WAS_BEING_DONE","insight":"WHAT_WAS_LEARNED","confidence":"high|medium|low"}' >> .nfcore-docs/learnings.jsonl
```
Only log genuine discoveries. A good test: would knowing this save time in a
future session? If yes, log it. Don't log transient errors or obvious things.

**Prior learnings:** At skill start (end of Step 1), check for learnings:
```bash
if [ -f .nfcore-docs/learnings.jsonl ]; then
  echo "LEARNINGS: $(wc -l < .nfcore-docs/learnings.jsonl | tr -d ' ') entries"
  cat .nfcore-docs/learnings.jsonl
fi
```
Use prior learnings to avoid repeating mistakes from previous sessions.

**Trend tracking:** If a previous report exists, compare against it:
```bash
ls -t .nfcore-docs/reports/*.md 2>/dev/null | head -2
```
If two or more reports exist, summarize: resolved findings, persistent findings,
new findings, and overall trend (improving/degrading/stable).

## Completion

End every skill invocation with a status:

- **DONE** — All steps completed. Summarize what was loaded/checked.
- **DONE_WITH_CONCERNS** — Completed, but with issues to flag (e.g., stale cache, lint failures, uncertain findings).
- **BLOCKED** — Cannot proceed. State what's blocking and what was tried.
- **NEEDS_CONTEXT** — Missing information. State exactly what's needed.

If blocked or uncertain after 3 attempts at a step, stop and escalate:
```
STATUS: BLOCKED | NEEDS_CONTEXT
REASON: [1-2 sentences]
ATTEMPTED: [what was tried]
RECOMMENDATION: [what the user should do next]
```
