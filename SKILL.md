---
name: nfcore-docs
version: 1.0.1
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

# --- Check dependencies ---
echo ""
echo "=== Dependencies ==="
command -v git >/dev/null 2>&1 && echo "git: $(git --version | head -1)" || echo "git: NOT FOUND (required for cache)"
command -v python3 >/dev/null 2>&1 && echo "python3: $(python3 --version 2>&1)" || echo "python3: NOT FOUND (required for index)"
command -v nf-core >/dev/null 2>&1 && echo "nf-core: $(nf-core --version 2>&1 | grep -o '[0-9.]*' | head -1)" || echo "nf-core: not found (optional — needed for lint/compliance checks)"
command -v gh >/dev/null 2>&1 && echo "gh: $(gh --version 2>&1 | head -1)" || echo "gh: not found (optional — needed for issue creation)"

# --- Check CLAUDE.md for nfcore-docs reference ---
if [ -f "CLAUDE.md" ]; then
  if grep -q "nfcore-docs" CLAUDE.md 2>/dev/null; then
    echo "CLAUDE_MD_REF: yes"
  else
    echo "CLAUDE_MD_REF: missing"
  fi
else
  echo "CLAUDE_MD_REF: no_file"
fi

# --- Prior learnings ---
if [ -f .nfcore-docs/learnings.jsonl ]; then
  echo ""
  echo "=== Prior Learnings ==="
  echo "LEARNINGS: $(wc -l < .nfcore-docs/learnings.jsonl | tr -d ' ') entries"
  cat .nfcore-docs/learnings.jsonl
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

If `CLAUDE_MD_REF` is `no_file`, suggest the user run `/init` to create a
CLAUDE.md for their project first, then extend it with
`/claude-md-management:claude-md-improver`. After CLAUDE.md exists, re-run
`/nfcore-docs` to add the nf-core docs reference.

If `CLAUDE_MD_REF` is `missing` (CLAUDE.md exists but no nfcore-docs mention),
you **MUST** use the **AskUserQuestion tool** (not plain text output) to ask:

> Your CLAUDE.md doesn't reference `/nfcore-docs`. Adding a short section
> helps future sessions know the skill is available.
>
> A) Add nf-core docs reference to CLAUDE.md
> B) No thanks

⚠️ Do NOT skip this step, even if you think CLAUDE.md shouldn't be modified.
The user decides — not you. Do NOT output the question as plain text.

If A, append this to the end of CLAUDE.md:

```markdown

## nf-core Documentation

- Use `/nfcore-docs` to load nf-core specs and docs into context
- Docs cached at `~/.cache/nfcore-docs/` (sparse checkout of nf-core/website, auto-updates if >24h stale)
- The skill generates a dynamic index of all pages with section headers on each invocation
- Context budget: index ~15K tokens (1.5%), specs ~60K (6%), all docs ~275K (28%) of 1M
```

If `CLAUDE_MD_REF` is `yes`, skip — already referenced. This only runs once per project.

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

Use the Read tool to read each file sequentially into context. For large
file sets (56 files), read them in batches — the content stays in the
conversation history for the agents to reference.

**Step C: Evaluate compliance — parallel agent mode**

Launch 5 parallel agents, each responsible for one compliance domain.
Each agent receives the lint output from Step A and the relevant spec
files from Step B. Each returns findings with severity and confidence.

Before launching agents, you **MUST** use the **AskUserQuestion tool** to ask:

> Running parallel compliance audit with 5 agents. Which model?
>
> A) Inherit from current session (default)
> B) Haiku — fast, cheaper, good for quick checks
> C) Sonnet — balanced, recommended for thorough audits
> D) Opus — most thorough, highest cost

If the user already specified a model choice in their original message (e.g.,
"use the default model"), you MAY skip this question and use their stated
preference. Otherwise, you MUST ask via AskUserQuestion — not plain text.

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
2. Classify each finding by severity (from the spec language):
   - Critical: MUST / MUST NOT violation (blocks nf-core acceptance)
   - High: SHOULD / SHOULD NOT gap (strongly recommended)
   - Medium: MAY suggestion or quality improvement
   - Low: Minor polish (TODOs, version warnings, formatting)
3. Rate your confidence in each finding (1-10):
   - 9-10: Verified by lint output or reading specific code
   - 7-8: High confidence pattern match against spec
   - 5-6: Moderate — could be misinterpreting spec, add a caveat
   - 3-4: Low — flag for manual review
   - 1-2: Speculation — only include for Critical or High severity
4. List positive findings (requirements already met) with ✓
5. Return findings as a structured list, one per line:
   [SEVERITY] (confidence: N/10) — description | spec: {filename}
   Then positive findings as: ✓ description | spec: {filename}

CRITICAL: Return ALL findings — every single one. Do not summarize,
truncate, or omit any finding regardless of severity or confidence.
No preamble, no summary paragraph. Just the structured findings list
followed by positive findings.
```

Launch all 5 agents in a single message using multiple Agent tool calls
so they run in parallel.

⚠️ **IMMEDIATELY after all agents return — BEFORE any consolidation —
save every agent's raw output to disk.** This is a blocking prerequisite
for Step D. Do NOT proceed to consolidation until all 5 files are written.

```bash
mkdir -p .nfcore-docs/reports/agents
```
Write each agent's **complete, verbatim** output (copy-paste, no editing) to:
- `.nfcore-docs/reports/agents/{date}-agent1-pipeline-requirements.md`
- `.nfcore-docs/reports/agents/{date}-agent2-module-compliance.md`
- `.nfcore-docs/reports/agents/{date}-agent3-subworkflow-compliance.md`
- `.nfcore-docs/reports/agents/{date}-agent4-documentation-metadata.md`
- `.nfcore-docs/reports/agents/{date}-agent5-git-ci-reviews.md`

This preserves raw findings for:
- Debugging consolidation issues
- Comparing agent outputs across runs
- Verifying no findings were lost during deduplication
- Re-running consolidation without re-running agents

If any agent fails or returns an error, note which domain was not audited
and fall back to sequential evaluation for that domain only.

**Consolidation** (after all 5 raw agent files are saved):
- Collect all findings from all 5 agents — preserve the original text of
  each finding (do not paraphrase or rewrite). Reorganizing and grouping
  is allowed; changing the wording of individual findings is not.
- Deduplicate: two findings are duplicates if they reference the same spec
  filename AND the same severity level. Keep the one with higher confidence.
  If confidence is equal, keep both (independent assessments are valuable)
- Filter: confidence < 4 goes to a **Low-Confidence Appendix** section at
  the end of the report (unless Critical severity — those always stay inline)
- Sort: Critical first, then High, then by confidence descending
- Merge positive findings from all agents into one deduplicated list
- **Checkpoint:** Report pre- and post-deduplication counts in the report
  header, e.g. "Raw findings: 142 | After dedup: 76 | Appendix: 3"

**Step D: Produce the compliance report**

Build the report dynamically from the spec files read in Step B.

⚠️ The **primary organization** of the report is by spec directory — NOT by
severity. Severity is a column within each section, not the top-level grouping.

Group into these sections (one per spec directory):
1. `pipelines/requirements/` — Pipeline Requirements
2. `pipelines/recommendations/` — Pipeline Recommendations
3. `components/modules/` — Module Compliance
4. `components/subworkflows/` — Subworkflow Compliance
5. `reviews/` — Review Process
6. `test-data/` — Test Data

Within each section, present a table where each row is one spec file:

| Spec file | Title | Status | Severity | Confidence | Notes |
|-----------|-------|--------|----------|------------|-------|
| `documentation.md` | Bundled documentation | ✗ | Critical | 10/10 | README is template placeholder |

Start the report with:
- Deduplication counts: `Raw findings: N | After dedup: N | Low-confidence appendix: N`
- Severity summary: `Critical: N | High: N | Medium: N | Low: N`

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

After presenting the compliance report, you **MUST** use the **AskUserQuestion
tool** to offer issue creation. Do NOT output this as plain text — use the tool:

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

Group related findings into logical issues rather than one-per-finding
(e.g., all module structure findings → one module migration issue). Present
the proposed grouping to the user before creating. Use `gh issue create`
directly (not the pipeline's YAML issue templates, which are for bugs and
feature requests — compliance issues are a different category).

This prevents duplicate issues when running audits repeatedly.

**`.nfcore-docs/` directory:** Suggest adding to `.gitignore` — reports
and learnings are local session artifacts, not shared project data.

**Tool crashes vs compliance failures:** If a lint tool crashes (stack trace,
not a lint failure), do NOT treat the crash as a compliance failure. Instead:
1. Attempt a workaround (e.g., different flags, piping input)
2. If the workaround succeeds, use the workaround output but note the crash
   in the report under a "Tool Issues" section
3. If no workaround works, report BLOCKED for that domain
4. Always log the crash and workaround (if any) as an operational learning

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

- **DONE** — All steps completed cleanly with no tool issues or uncertain findings.
- **DONE_WITH_CONCERNS** — Completed, but flag issues: tool crashes (even if
  worked around), stale cache, uncertain findings, or any step that required
  a non-standard approach. Use this status if ANY lint tool crashed during
  the session, even if a workaround succeeded.
- **BLOCKED** — Cannot proceed. State what's blocking and what was tried.
- **NEEDS_CONTEXT** — Missing information. State exactly what's needed.

If blocked or uncertain after 3 attempts at a step, stop and escalate:
```
STATUS: BLOCKED | NEEDS_CONTEXT
REASON: [1-2 sentences]
ATTEMPTED: [what was tried]
RECOMMENDATION: [what the user should do next]
```
