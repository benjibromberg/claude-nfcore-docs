# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-04-16

### Added

- Automated test infrastructure: `test.sh` runner with two tiers
  - Tier 1: 69 static pytest tests (frontmatter, structure, cross-file consistency,
    bash preamble, python index, cache validation) — no LLM, runs in <1s
  - Tier 2: 6 E2E tests via `claude -p` with NDJSON parsing — uses Max subscription
- 6 new manual tests in TESTS.md (Tests 51-56) for v1.0.1 guardrails

### Fixed

- AskUserQuestion tool enforcement: added explicit MUST callouts at all 3 interactive
  checkpoints (CLAUDE_MD_REF, model selection, issue creation) — plain text output no
  longer satisfies these requirements
- Raw agent report saving: moved save instructions BEFORE consolidation as a blocking
  prerequisite with all 5 filenames listed explicitly
- Report format: clarified primary organization is by spec directory (not severity),
  added example table showing the expected per-spec-file row format
- Consolidation wording: "verbatim" means preserve finding text — reorganizing is
  allowed, paraphrasing individual findings is not
- Dedup checkpoint: consolidation must report pre- and post-dedup counts in report header
- Low-confidence appendix: confidence < 4 findings go to a named appendix section
- Tool crash handling: replaced binary BLOCKED with 4-step flow (workaround → use
  output → note crash → log learning)
- Completion status: DONE_WITH_CONCERNS now explicitly covers any tool crash, even if
  worked around
- Model selection: added MAY skip clause when user pre-specifies model in their message

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
