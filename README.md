# claude-nfcore-docs

A [Claude Code](https://claude.ai/code) skill for loading [nf-core](https://nf-co.re/) documentation and specifications into context. Enables spec-driven development, compliance checking, and auditing for nf-core pipeline projects.

## What it does

- Downloads and caches all nf-core documentation from the [nf-core/website](https://github.com/nf-core/website) repo via sparse git checkout
- Auto-updates when docs are stale (>24 hours)
- Generates a full index of all doc pages with section headers
- Loads relevant spec files into Claude's context based on your current task
- Detects if you're in an nf-core pipeline repo and reports pipeline context
- Cross-references `nf-core pipelines lint` output against specifications

## Install

### 1. Copy the skill

**Global install** (recommended — available in all projects):
```bash
mkdir -p ~/.claude/skills/nfcore-docs
curl -sL https://raw.githubusercontent.com/benjibromberg/claude-nfcore-docs/main/SKILL.md \
  -o ~/.claude/skills/nfcore-docs/SKILL.md
```

**Or local install** (one project only):
```bash
mkdir -p .claude/skills/nfcore-docs
curl -sL https://raw.githubusercontent.com/benjibromberg/claude-nfcore-docs/main/SKILL.md \
  -o .claude/skills/nfcore-docs/SKILL.md
```

### 2. Set up the docs cache

```bash
mkdir -p ~/.cache/nfcore-docs && cd ~/.cache/nfcore-docs
git init
git remote add origin https://github.com/nf-core/website.git
git config core.sparseCheckout true
printf 'sites/docs/src/content/docs/\nsites/docs/src/content/api_reference/\n' > .git/info/sparse-checkout
git pull origin main --depth 1
```

This downloads ~172 doc pages + ~2,400 API reference files (~13MB on disk). Only the docs directory is checked out, not the full website repo.

The cache is shared across all projects. If you skip this step, the skill will auto-create the cache on first use.

### 3. Allow read permissions

To avoid being prompted for every file read, add this to your Claude Code settings:

**Global** (`~/.claude/settings.json` — recommended, works across all projects):
```json
{
  "permissions": {
    "allow": [
      "Read(//{home}/.cache/nfcore-docs/**)"
    ]
  }
}
```

**Or per-project** (`.claude/settings.local.json`):
```json
{
  "permissions": {
    "allow": [
      "Read(//{home}/.cache/nfcore-docs/**)"
    ]
  }
}
```

Alternatively, select "Always allow" when prompted on first use.

### 4. Add to your pipeline's CLAUDE.md (optional)

Add this to your nf-core pipeline's CLAUDE.md so Claude always knows the skill is available:

```markdown
## nf-core Documentation

- Use `/nfcore-docs` to load nf-core specs and docs into context
- Docs cached at `~/.cache/nfcore-docs/` (sparse checkout of nf-core/website, auto-updates if >24h stale)
- The skill generates a dynamic index of all pages with section headers on each invocation
- Context budget: index ~15K tokens (1.5%), specs ~60K (6%), all docs ~275K (28%) of 1M
```

### 5. Use it

```
/nfcore-docs
```

Then tell Claude what you need:
- "Load the module specs for migration work"
- "Run a full compliance audit against all pipeline requirements"
- "What does the git branches spec say?"
- "Find the API reference for nf-core tools 3.5.2"

## What's in the cache

| Directory | Contents | Files |
|-----------|----------|-------|
| `docs/specifications/pipelines/requirements/` | Pipeline MUST requirements (19) | 20 |
| `docs/specifications/pipelines/recommendations/` | Pipeline SHOULD recommendations (8) | 8 |
| `docs/specifications/components/modules/` | Module conventions | 9 |
| `docs/specifications/components/subworkflows/` | Subworkflow conventions | 7 |
| `docs/specifications/reviews/` | PR review process | 5 |
| `docs/specifications/test-data/` | Test data guidelines | 3 |
| `docs/contributing/` | Contribution guidelines | ~20 |
| `docs/developing/` | Developer guides | ~15 |
| `docs/nf-core-tools/` | CLI tool reference | ~40 |
| `docs/running/` | Pipeline execution | ~15 |
| `api_reference/` | API docs by version (1.5–dev) | ~2,400 |

## Task-based loading guide

The skill loads only the files relevant to your current task:

| Task | Spec files loaded |
|------|-------------------|
| Module migration | `specifications/components/modules/*.md` (9 files) |
| Subworkflow restructure | `specifications/components/subworkflows/*.md` (7 files) |
| nf-test coverage | `*/testing.md` across modules, subworkflows, recommendations |
| Lint fixes | `*/requirements/linting.md` + `*/requirements/parameters.md` |
| CI setup | `*/requirements/ci_testing.md` |
| Full compliance audit | All pipeline requirements + recommendations (~28 files) |
| Git/branch model | `*/requirements/git_branches.md` + `specifications/reviews/*.md` |
| First release prep | All requirements + recommendations + reviews |

## Accuracy disclaimer

This skill loads nf-core specifications into Claude's context to improve compliance awareness, but AI-generated compliance reports can contain errors:

- Claude may misinterpret MUST/SHOULD/MAY requirements
- Compliance status for individual requirements may be incorrect
- The skill may miss violations that require deep code analysis
- Lint output cross-referencing is heuristic, not deterministic

**Always verify** compliance reports against `nf-core pipelines lint` output and the [original spec text](https://nf-co.re/docs/specifications/overview). The skill is a guide, not a gate. For critical audits (pre-submission to nf-core), have a human review the compliance report.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- `git` (for sparse checkout)
- `gh` CLI (for repo operations, optional)
- `python3` (for index generation)
- `nf-core` tools (for lint, optional)

## Tests

See [TESTS.md](TESTS.md) for the full test suite (56 tests covering cache management, doc loading, interactive menu, compliance audits, multi-agent review, persistence, and edge cases).

## Acknowledgements

Built with [Claude Code](https://claude.ai/code). Design patterns adapted from:

- **[gstack](https://github.com/garryslist/gstack)** — completion status protocol, AskUserQuestion format, operational self-improvement, context recovery, escalation rules, confidence calibration, trend tracking (from `/review`, `/cso`, `/health`, `/investigate`, `/checkpoint` skills)
- **[impeccable](https://github.com/nichochar/impeccable)** — severity classification, positive findings, behavioral guardrails (NEVER rules), action mapping (from `/audit` skill)
- **Anthropic official plugins** — multi-agent parallel review with confidence filtering, references directory pattern (from `code-review`, `claude-code-setup`, `claude-md-management` plugins)

nf-core documentation sourced from [nf-core/website](https://github.com/nf-core/website) via sparse git checkout.

## License

MIT (same as nf-core)
