# CLAUDE.md

## Project Overview

A Claude Code skill (`/nfcore-docs`) that loads nf-core documentation and specifications into context for compliance checking, spec-driven development, and auditing of nf-core pipelines.

## Files

- `SKILL.md` — The skill prompt file (installed to `~/.claude/skills/nfcore-docs/SKILL.md`)
- `README.md` — User-facing install and usage docs
- `TESTS.md` — 56 manual tests with copy-paste prompts
- `CONTRIBUTING.md` — How to contribute (linting, pre-commit, PR checklist)
- `CHANGELOG.md` — Version history
- `NOTICE.md` — Design pattern attribution
- `pyproject.toml` — Consolidated ruff + pytest configuration
- `.editorconfig` — Editor indent/charset/line-ending conventions
- `.pre-commit-config.yaml` — 8 pre-commit hooks (prettier, ruff, whitespace, YAML/JSON)
- `tests/` — Automated test suite (71 static + 18 E2E)
- `tests/fixtures/` — Pinned nf-core pipeline clones for E2E testing (gitignored)

## Development

```bash
# First-time setup
pre-commit install         # install git hooks
./tests/fixtures/setup.sh  # clone pipeline fixtures for E2E tests

# Edit the skill
vim SKILL.md

# Run tests + lint
./test.sh                  # 71 static tests (<1s)
pre-commit run --all-files # all 8 hooks

# Test in a new Claude Code session
cd tests/fixtures/funcscan && claude
# then: /nfcore-docs
```

## Key Constraints

- **No hardcoded spec content** — all compliance rules are derived from cached doc files at runtime
- **No static file lists** — the file tree IS the checklist (use `find`, not hardcoded paths)
- **NEVER summarize agent results** — preserve finding text (reorganizing OK, paraphrasing not)
- **NEVER truncate command output** — no head/tail/grep on lint or tool output
- **Delegate to nf-core tools** — never reimplement lint, create, schema build, etc.
- **Token budget awareness** — index ~15K, specs ~60K, all docs ~275K (measured on Opus 1M)
- **AskUserQuestion tool enforcement** — all interactive checkpoints (CLAUDE_MD_REF, model selection, issue creation) MUST use the AskUserQuestion tool, not plain text output
- **Agent reports before consolidation** — all 5 raw agent files must be written to disk BEFORE any consolidation begins (blocking prerequisite)
- **Report grouped by spec directory** — primary organization is by spec directory (pipelines/requirements, components/modules, etc.), not by severity level. Severity is a column.

## Docs Cache

Sparse git checkout of nf-core/website at `~/.cache/nfcore-docs/`.
Auto-setup on first use, auto-updates if >24h stale.

```bash
# Manual update
git -C ~/.cache/nfcore-docs pull origin main --depth 1

# Check what's cached
find ~/.cache/nfcore-docs/sites/docs/src/content/docs -name "*.md" | wc -l  # ~172 docs
find ~/.cache/nfcore-docs/sites/docs/src/content/api_reference -name "*.md" | wc -l  # ~2400 API ref
```

## Testing

### Automated tests (pytest)

```bash
./test.sh              # Tier 1: static tests only (no LLM, <1s)
./test.sh --e2e        # Tier 1 + Tier 2: E2E via claude -p (Max subscription)
./test.sh --verbose    # Show individual test names
```

- **Tier 1** (71 static tests): frontmatter, structure, cross-file consistency, bash preamble,
  python index generation, cache validation. Zero dependencies beyond python3.
- **Tier 2** (18 E2E tests): 6 test functions x 3 pipeline fixtures, spawn `claude -p`, parse NDJSON,
  verify tool calls. Uses Max subscription (no API cost). Opt-in via `--e2e`.
- **Pipeline fixtures**: fetchngs 1.12.0, funcscan 3.0.0, rnaseq 3.24.0 — see `tests/fixtures/README.md`.

### Manual tests (TESTS.md)

56 tests with copy-paste prompts for interactive session testing.
Coverage map at the top of TESTS.md.

Tests require being in an nf-core pipeline directory for most tests (exceptions: Test 21).
Some tests modify local state (.nfcore-docs/, cache timestamps) — clean up after.

Priority tests for quick validation: 1 (freshness), 10 (full audit), 11 (interactive menu),
18 (NEVER rules), 43 (dependencies), 51-56 (v1.0.1 guardrails).

## Issues

Tracked at https://github.com/benjibromberg/claude-nfcore-docs/issues.
