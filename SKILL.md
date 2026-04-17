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

## General principle: ask the user

Use AskUserQuestion throughout this skill — not just at the explicit
checkpoints listed below. When you face a judgment call, ambiguity, or
a decision with trade-offs, ask the user rather than guessing. Examples:

- Unsure which spec area is relevant? Ask.
- Multiple valid approaches to loading docs? Ask which the user prefers.
- A finding could be interpreted multiple ways? Ask for clarification.
- The user's request doesn't map cleanly to a menu option? Ask what they need.

The AskUserQuestion tool supports **2-4 options** (plus an automatic "Other"
write-in). For broader choices, use a **tiered approach**: ask a high-level
question first, then drill down with a follow-up question.

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

If `CLAUDE_MD_REF` is `no_file`, you **MUST** use the **AskUserQuestion tool**
to ask whether the user wants to create a CLAUDE.md first:

> This project has no CLAUDE.md. Creating one helps Claude understand your
> pipeline across sessions. You can set one up with `/init`, then enrich it
> with `/claude-md-management:claude-md-improver`.
>
> A) Create CLAUDE.md now (pause /nfcore-docs, run /init first)
> B) Skip — continue without CLAUDE.md

⚠️ Do NOT skip this step or make the decision yourself. Even for test
directories or fixtures, the user decides. Do NOT output as plain text.

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

**Always load first (before asking):** Read the git/review specs automatically —
they're relevant to any contribution and small enough to always include:

- `specifications/pipelines/requirements/git_branches.md`
- `specifications/reviews/*.md` (commit strategy, rapid merge, request reviewers, review scope)

Then, if the user's intent is ambiguous (e.g., just `/nfcore-docs` with no context),
use AskUserQuestion. Follow this structure for ALL AskUserQuestion calls:

1. **Re-ground** — State the pipeline (if detected) and current branch (1 sentence)
2. **Context** — What's already loaded (index + git/review specs)
3. **Recommend** — If one option is clearly best for the context, say so
4. **Options** — Use the AskUserQuestion tool (max 4 options + write-in)

⚠️ AskUserQuestion supports a maximum of 4 options. The user always gets an
additional "Other" write-in option automatically. Do NOT try to present more
than 4 options — the tool will reject it.

Before asking, briefly orient the user on what's available. Output something like:

> The nf-core docs cache has **172 files** across 7 categories:
>
> - **Specifications** (56 files) — pipeline requirements and recommendations, module/subworkflow
>   conventions, test data standards, review/merge guidelines, VIPs
> - **Developing** (37 files) — component creation (ext.args, meta maps, cross-org),
>   containers (ARM64, Seqera), nf-test assertions, template syncs, migration guides
>   (strict syntax, topic channels), institutional profiles, release procedure,
>   documentation style (Harshil alignment), external use
> - **nf-core tools** (34 files) — CLI reference: modules (create/install/lint/update/patch),
>   subworkflows, pipelines (lint/schema/download/launch/sync/rocrate), test-datasets, TUI
> - **Community** (13 files) — governance, branding (logos/colours/fonts), regulatory
>   validation, advisories, terminology
> - **Contributing** (12 files) — adding pipelines/components, contributor types,
>   reviewing PRs (checklists for components, pipelines, tools), nf-core-bot commands
> - **Get started** (10 files) — what is nf-core, environment setup, installing Nextflow,
>   software dependencies (Docker/Singularity/Conda), dev containers, VS Code, Prettier
> - **Running** (10 files) — running pipelines, configuration, reference genomes,
>   troubleshooting, offline use, Google Colab, managing work directory growth
>
> Git/review specs are already loaded. What would you like to do?

Then use AskUserQuestion:

**Tier 1: Top-level menu** (first AskUserQuestion call):

> A) Component work — module/subworkflow specs for migration, restructure, testing
> B) Full compliance audit — all specs + lint tools + parallel agents
> C) Pipeline requirements — CI, docs, parameters, linting, first release
> D) Load into context — load specs or all docs as a reference library, no audit

The write-in "Other" covers: CLI reference, just the index, custom requests.

**Tier 2: Follow-up** (if user picks A, C, or D, ask a second AskUserQuestion):

If **Component work** (A):

> Which component area?
>
> A) Module migration — structure, naming, ext.args, meta.yml (9 files)
> B) Subworkflow restructure — conventions, I/O, naming (7 files)
> C) nf-test coverage — testing specs for modules, subworkflows, pipelines (3 files)
> D) All component specs — modules + subworkflows + testing (16 files)

If **Pipeline requirements** (C):

> Which pipeline area?
>
> A) Lint fixes — linting rules, parameter conventions (2 files)
> B) CI setup — GitHub Actions, test profiles (1 file)
> C) Documentation — README, usage.md, output.md, module docs (3 files)
> D) First release prep — all requirements + recommendations (33 files)

If **Load into context** (D):

> How much to load?
>
> A) Just the specs — 56 specification/requirement files (~60K tokens, 6% of 1M)
> B) Everything — all 172 docs: specs + contributing + developing + running + tools (~275K tokens, 28% of 1M)

**Context budget (measured on Opus 1M):**

| Layer                                    | Files   | Tokens    | % of 1M |
| ---------------------------------------- | ------- | --------- | ------- |
| Index + git/review specs (always loaded) | ~6      | ~20K      | 2%      |
| + All remaining specifications           | ~50     | ~55K      | 5.5%    |
| + All remaining docs                     | 116     | ~200K     | 20%     |
| **Total (all docs)**                     | **172** | **~275K** | **28%** |

For most compliance work, **index + specs (~75K, 8%)** is sufficient. The remaining
200K of contributing/developing/running/community docs are reference material — load
selectively by section when needed.

## Step 3: Load doc files

Base paths:

- Docs: `~/.cache/nfcore-docs/sites/docs/src/content/docs/`
- API: `~/.cache/nfcore-docs/sites/docs/src/content/api_reference/`

**File mapping and nf-core tools to run:**

| Selection             | Spec files to Read                                                                                   | nf-core tool to run                                                           |
| --------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Module migration      | `specifications/components/modules/*.md`                                                             | `nf-core modules lint`                                                        |
| Subworkflow work      | `specifications/components/subworkflows/*.md`                                                        | `nf-core subworkflows lint`                                                   |
| nf-test coverage      | `*/modules/testing.md` + `*/subworkflows/testing.md` + `*/recommendations/testing.md`                | `nf-core modules test`, `nf-core subworkflows test`                           |
| All component specs   | `specifications/components/**/*.md`                                                                  | `nf-core modules lint` + `nf-core subworkflows lint`                          |
| Lint fixes            | `*/requirements/linting.md` + `*/requirements/parameters.md`                                         | `nf-core pipelines lint`                                                      |
| CI + git branches     | `*/requirements/ci_testing.md` + `*/requirements/git_branches.md` + `specifications/reviews/*.md`    | (check `.github/workflows/` + git branches)                                   |
| Documentation         | `*/requirements/documentation.md` + `*/modules/documentation.md` + `*/subworkflows/documentation.md` | `nf-core pipelines lint` (docs checks)                                        |
| First release         | All pipeline requirements + recommendations + reviews                                                | All: `pipelines lint` + `modules lint` + `subworkflows lint`                  |
| Full compliance audit | All `specifications/**/*.md` recursively                                                             | All: `pipelines lint` + `modules lint` + `subworkflows lint` + RO-Crate check |
| All specs             | All `specifications/**/*.md`                                                                         | (depends on task)                                                             |
| 10. CLI reference     | `nf-core-tools/*.md`                                                                                 | (reference only)                                                              |
| 11. All specs         | All `specifications/**/*.md`                                                                         | (depends on task)                                                             |
| 12. All docs          | All files under docs root                                                                            | (depends on task)                                                             |
| 13. Index only        | None — use index to navigate                                                                         | None                                                                          |
| 14. Custom            | Use Grep on index output                                                                             | (depends on task)                                                             |

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

If anything is unclear about the user's goal, the pipeline's state, or how a
spec should be interpreted — use AskUserQuestion to clarify before proceeding.
It's better to ask than to produce a report the user didn't want.

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

| Agent | Domain                   | Specs to include                                                                                          | Tool to reference                       |
| ----- | ------------------------ | --------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| 1     | Pipeline requirements    | `specifications/pipelines/requirements/*.md` + `specifications/pipelines/recommendations/*.md`            | `nf-core pipelines lint` output         |
| 2     | Module compliance        | `specifications/components/modules/*.md`                                                                  | `nf-core modules lint` output           |
| 3     | Subworkflow compliance   | `specifications/components/subworkflows/*.md`                                                             | `nf-core subworkflows lint` output      |
| 4     | Documentation & metadata | `specifications/pipelines/requirements/documentation.md`, `*/keywords.md`, `*/ro_crate.md`                | README, usage.md, output.md file checks |
| 5     | Git, CI & reviews        | `specifications/pipelines/requirements/git_branches.md`, `*/ci_testing.md`, `specifications/reviews/*.md` | git branch state, `.github/workflows/`  |

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

Before producing the report, consider whether the user needs to weigh in on
anything. If agent findings are surprising, contradictory, or depend on
context you don't have (e.g., "is this pipeline meant for nf-core submission
or internal use?"), use AskUserQuestion to clarify before finalizing.

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

| Spec file          | Title                 | Status | Severity | Confidence | Notes                          |
| ------------------ | --------------------- | ------ | -------- | ---------- | ------------------------------ |
| `documentation.md` | Bundled documentation | ✗      | Critical | 10/10      | README is template placeholder |

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

| Priority | Finding   | Fix with     | Command             |
| -------- | --------- | ------------ | ------------------- |
| Critical | {finding} | {what to do} | `nf-core {command}` |
| High     | {finding} | {what to do} | `nf-core {command}` |
| ...      |           |              |                     |

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

> _This compliance report is AI-generated and may contain inaccuracies.
> Verify against `nf-core pipelines lint` and the original specifications
> at https://nf-co.re/docs/specifications/overview_

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
