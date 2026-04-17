# Contributing

Thanks for your interest in improving claude-nfcore-docs.

## Quick start

```bash
# Clone and install
git clone https://github.com/benjibromberg/claude-nfcore-docs.git
cd claude-nfcore-docs

# Install the skill locally (links to your working copy)
mkdir -p ~/.claude/skills/nfcore-docs
ln -sf "$(pwd)/SKILL.md" ~/.claude/skills/nfcore-docs/SKILL.md

# Set up the docs cache (if not already done)
# The skill auto-creates this on first use, but you can do it manually:
mkdir -p ~/.cache/nfcore-docs && cd ~/.cache/nfcore-docs
git init && git remote add origin https://github.com/nf-core/website.git
git config core.sparseCheckout true
printf 'sites/docs/src/content/docs/\nsites/docs/src/content/api_reference/\n' > .git/info/sparse-checkout
git pull origin main --depth 1
```

Now edit `SKILL.md`, invoke `/nfcore-docs` in any Claude Code session, and your
changes are live immediately.

## Testing

56 tests in [TESTS.md](TESTS.md). Each has a copy-paste prompt for manual testing.

```
# In a Claude Code session from an nf-core pipeline directory:
Read /path/to/claude-nfcore-docs/TESTS.md and run Test N
```

Run the full test suite by working through all 56 tests. Priority tests for
quick validation: 1 (freshness), 10 (full audit), 11 (interactive menu),
18 (NEVER rules), 43 (dependencies).

## What to contribute

- **Bug fixes** — skill produces wrong output, crashes, or violates its own NEVER rules
- **Guardrail improvements** — better prompting that reduces hallucination or error
- **Test cases** — new tests for untested scenarios or edge cases
- **nf-core spec coverage** — the skill should stay current with nf-core spec changes
- **Documentation** — README, TESTS.md, or CLAUDE.md improvements

## Key constraints

Read the CLAUDE.md for full constraints. The critical ones:

- **No hardcoded spec content** — derive everything from cached doc files at runtime
- **NEVER summarize agent results** — present all findings verbatim
- **NEVER truncate command output** — no head/tail/grep on diagnostics
- **Delegate to nf-core tools** — never reimplement lint, create, schema build, etc.
- **Keep the installed copy in sync** — if you edit SKILL.md, the installed copy at
  `~/.claude/skills/nfcore-docs/SKILL.md` must match

## Linting

All Python code must pass [ruff](https://docs.astral.sh/ruff/) lint and format checks.
Configuration is in `ruff.toml` (excludes fixture pipelines).

```bash
# Check for lint issues
ruff check tests/

# Check formatting
ruff format --check tests/

# Auto-fix both
ruff check tests/ --fix && ruff format tests/
```

CI enforces both — PRs will fail if ruff reports any issues.

## Pull requests

- One feature or fix per PR
- Run `ruff check` and `ruff format` before pushing
- Update TESTS.md if adding testable behavior
- Update CLAUDE.md if changing constraints or architecture
- Test your changes by actually using `/nfcore-docs` in a real session
