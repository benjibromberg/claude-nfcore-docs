# Changelog

All notable changes to this project will be documented in this file.

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
- CLAUDE.md snippet for pipeline projects (4 lines)
- 50-test suite with copy-paste prompts (TESTS.md)
- README with install instructions (global and local)
- CONTRIBUTING.md
- NOTICE.md with design pattern attribution
