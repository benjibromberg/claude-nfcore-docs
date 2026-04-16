# CLAUDE.md

## Project Overview

A Claude Code skill (`/nfcore-docs`) that loads nf-core documentation and specifications into context for compliance checking, spec-driven development, and auditing of nf-core pipelines.

## Files

- `SKILL.md` — The skill prompt file. Installed to `~/.claude/skills/nfcore-docs/SKILL.md`.
  Keep the installed copy and repo copy in sync.
- `README.md` — User-facing install and usage docs.
- `TESTS.md` — 56-test suite with copy-paste prompts for manual testing in Claude Code sessions.
- `CONTRIBUTING.md` — How to contribute.
- `CHANGELOG.md` — Version history.
- `NOTICE.md` — Design pattern attribution.

## Development

```bash
# Edit the skill
vim SKILL.md

# Sync to installed location (must stay in sync)
cp SKILL.md ~/.claude/skills/nfcore-docs/SKILL.md

# Test in a new Claude Code session
# cd to an nf-core pipeline dir, then:
# /nfcore-docs

# Run a specific test
# "Read /path/to/TESTS.md and run Test N"
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

- **Tier 1** (69 static tests): frontmatter, structure, cross-file consistency, bash preamble,
  python index generation, cache validation. Zero dependencies beyond python3.
- **Tier 2** (6 E2E tests): spawn `claude -p --output-format stream-json`, parse NDJSON,
  verify tool calls. Uses Max subscription (no API cost). Opt-in via `--e2e`.

### Manual tests (TESTS.md)

56 tests with copy-paste prompts for interactive session testing.
Coverage map at the top of TESTS.md.

Tests require being in an nf-core pipeline directory for most tests (exceptions: Test 21).
Some tests modify local state (.nfcore-docs/, cache timestamps) — clean up after.

Priority tests for quick validation: 1 (freshness), 10 (full audit), 11 (interactive menu),
18 (NEVER rules), 43 (dependencies), 51-56 (v1.0.1 guardrails).

## Issues

Tracked at https://github.com/benjibromberg/claude-nfcore-docs/issues.
Open issues are testing (#10) and score calibration (#27).
