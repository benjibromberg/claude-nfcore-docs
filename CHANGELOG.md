# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-04-17

### Added

- Automated test infrastructure: `test.sh` runner with two tiers
  - Tier 1: 71 static pytest tests (frontmatter, structure, cross-file consistency,
    bash preamble, python index, cache validation) — no LLM, runs in <1s
  - Tier 2: 6 E2E tests via `claude -p` from pipeline fixture directories
- Pipeline test fixtures: fetchngs 1.12.0, funcscan 3.0.0, rnaseq 3.24.0 — pinned
  nf-core pipelines covering 3 template eras (pre-3.0, 3.3.x, 3.5.x). See
  `tests/fixtures/README.md` for selection rationale.
- GitHub Actions CI: static tests + ruff lint/format via `astral-sh/ruff-action@v3`
- Pre-commit hooks (8 hooks): prettier, trailing-whitespace, end-of-file, check-yaml,
  check-json, check-merge-conflict, ruff lint, ruff format
- `pyproject.toml`: consolidated ruff + pytest configuration
- `.editorconfig`: UTF-8, LF, consistent indent (4-space default, 2 for md/yml/json)
- `.prettierignore`: excludes fixture pipelines from formatting
- GitHub issue templates (bug report, feature request), PR template with checklist
- `CODEOWNERS`: @benjibromberg on all PRs
- 6 new manual tests in TESTS.md (Tests 51-56) for audit execution guardrails
- "General principle: ask the user" section at top of SKILL.md — use AskUserQuestion
  proactively throughout for judgment calls, ambiguity, and clarification
- Git/review specs auto-loaded before menu (always relevant, small cost)
- Comprehensive orient message showing all 7 doc categories with file counts before menu
- "Load into context" menu option with specs-only vs everything follow-up

### Changed

- Menu redesigned as tiered AskUserQuestion (max 4 options per tool call):
  Tier 1: Component work / Full audit / Pipeline requirements / Load into context
  Tier 2: drill-down for components, pipeline areas, or load scope
- CLAUDE_MD_REF `no_file` now MUST use AskUserQuestion (was silently skipped)
- Moved ruff config from standalone `ruff.toml` to `pyproject.toml`

### Fixed

- AskUserQuestion tool enforcement at all 3 interactive checkpoints
- Raw agent report saving as blocking prerequisite before consolidation
- Report format: primary organization by spec directory, not severity
- Consolidation: preserve finding text, reorganizing OK, paraphrasing not
- Dedup checkpoint with pre/post counts in report header
- Low-confidence appendix for confidence < 4 findings
- Tool crash: 4-step workaround flow replaces binary BLOCKED
- DONE_WITH_CONCERNS covers any tool crash, even if worked around
- Model selection: MAY skip if user pre-specified in message
- Stale test counts in CONTRIBUTING.md (50→56) and README.md (50→56)
- TESTS.md coverage map missing Test 13
- Unused imports and ambiguous variable names across test modules

## [1.0.0] - 2026-04-16

### Added

- Core skill: docs cache management with 24h staleness check and auto-setup
- Dynamic index generation with page titles and section headers
- Interactive 14-option menu with context budget estimates (index ~15K, specs ~60K, all docs ~275K tokens)
- Session re-invocation guard (skip preamble on second invocation)
- Pipeline context detection (modules, subworkflows, branch)
- Full compliance audit mode with Steps A-E
- Multi-agent parallel review (5 domain agents) with model selection
- Agent prompt template with severity/confidence rubric
- Raw agent findings persistence (`.nfcore-docs/reports/agents/`)
- Severity classification: Critical/High/Medium/Low (from MUST/SHOULD/MAY)
- Confidence scoring: 1-10 with display rules
- Positive findings section in audit reports
- Recommended next actions table with nf-core command mapping
- Compliance score (0-10) with per-category breakdown
- GitHub issue creation from audit findings with overlap detection and logical grouping
- Module/subworkflow creation workflow (`--empty-template` + spec guidance)
- Targeted compliance checks mapped to nf-core tools per category
- Dependency checking (git, python3, nf-core, gh) in preamble
- Prior learnings search at skill start
- Audit report persistence (`.nfcore-docs/reports/`)
- Operational learnings logging (`.nfcore-docs/learnings.jsonl`)
- Trend tracking across audits (resolved/persistent/new)
- Structured AskUserQuestion format (re-ground/context/recommend/options)
- Completion status protocol (DONE/DONE_WITH_CONCERNS/BLOCKED/NEEDS_CONTEXT)
- NEVER rules (10 behavioral guardrails)
- Accuracy disclaimer on all compliance reports
- Tool crash vs compliance failure differentiation
- `.gitignore` guidance for `.nfcore-docs/` directory
- Read permission documentation for `~/.cache/nfcore-docs/`
- Auto-suggest adding `/nfcore-docs` reference to pipeline CLAUDE.md (recommends `/init` if no CLAUDE.md exists)
- CLAUDE.md reference snippet for pipeline projects (inline in README install step 4)
- 50-test suite with copy-paste prompts (TESTS.md)
- README with install instructions (global and local)
- CONTRIBUTING.md
- NOTICE.md with design pattern attribution
