# CLAUDE.md

## Project Overview

A Claude Code skill (`/nfcore-docs`) that loads nf-core documentation and specifications into context for compliance checking, spec-driven development, and auditing of nf-core pipelines.

## Files

- `SKILL.md` — The skill prompt file. Installed to `~/.claude/skills/nfcore-docs/SKILL.md`.
  Keep the installed copy and repo copy in sync.
- `README.md` — User-facing install and usage docs.
- `TESTS.md` — 50-test suite with copy-paste prompts for manual testing in Claude Code sessions.
- `snippet.md` — 4-line CLAUDE.md snippet users paste into their pipeline's CLAUDE.md.

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
- **NEVER summarize agent results** — present ALL findings verbatim
- **NEVER truncate command output** — no head/tail/grep on lint or tool output
- **Delegate to nf-core tools** — never reimplement lint, create, schema build, etc.
- **Token budget awareness** — index ~15K, specs ~60K, all docs ~275K (measured on Opus 1M)

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

50 tests in TESTS.md. Each has a copy-paste prompt for standalone session testing.
Coverage map at the top of TESTS.md.

Tests require being in an nf-core pipeline directory for most tests (exceptions: Test 21).
Some tests modify local state (.nfcore-docs/, cache timestamps) — clean up after.

## Issues

Tracked at https://github.com/benjibromberg/claude-nfcore-docs/issues.
Open issues are testing (#10) and score calibration (#27).
