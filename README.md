# claude-nfcore-docs

A [Claude Code](https://claude.ai/code) skill that loads [nf-core](https://nf-co.re/) specifications and documentation into context.

I'm a junior dev building Nextflow pipelines for my lab. I came from Snakemake, and when I started trying to follow nf-core conventions I didn't even realize `nf-core lint` or most of the nf-core tooling existed for a while. There's a lot to learn, and I've been leaning heavily on Claude Code to help me write pipelines that follow the conventions correctly.

I found that Claude writes much better nf-core-compliant code when it has the actual specs in context. Without them, you end up fixing lint warnings after the fact, and Claude doesn't always understand what the rule means or how to fix it properly. This skill gives it the specs upfront. Early stage, sharing in case others find it useful.

## Why not just use `nf-core lint`?

You should. Lint is excellent and catches hundreds of things. This skill is not a replacement for lint.

What lint does well:

- Structural checks (files exist, configs match template, schema validates)
- Module and subworkflow version tracking
- Parameter schema validation
- Template adherence

What this skill adds on top of lint:

- **Conventions before code**: When writing new modules, subworkflows, or pipeline features, Claude has the nf-core conventions in context so it follows them from the start rather than you fixing lint failures after
- **Spec context for lint warnings**: When lint flags something, Claude can read the actual spec text to understand why the rule exists and how to fix it correctly
- **Systematic audits**: Loads all specs at once and checks every MUST/SHOULD/MAY, searches your GitHub issues to skip things already tracked, and can create issues for new findings
- **Pipeline awareness**: Auto-detects your pipeline, counts modules/subworkflows, and loads relevant specs for your current task
- **Guardrails**: Prevents Claude from summarizing findings, truncating lint output, or reimplementing nf-core tools
- **Cross-audit tracking**: Compares findings across runs to show what's improving, and logs operational learnings to avoid repeating past mistakes

The short version: lint catches problems after you write code. This skill helps Claude write it right the first time, and gives you a way to do deeper compliance reviews when you need them.

## Install

### 1. Copy the skill

**Global install** (recommended, available in all projects):

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

**Global** (`~/.claude/settings.json`, recommended):

```json
{
  "permissions": {
    "allow": ["Read(//{home}/.cache/nfcore-docs/**)"]
  }
}
```

Alternatively, select "Always allow" when prompted on first use.

### 4. Use it

```
/nfcore-docs
```

Then tell Claude what you need:

- "Load the module specs for migration work"
- "Run a full compliance audit against all pipeline requirements"
- "What does the git branches spec say?"

## What's in the cache

| Directory                                        | Contents                            | Files  |
| ------------------------------------------------ | ----------------------------------- | ------ |
| `docs/specifications/pipelines/requirements/`    | Pipeline MUST requirements (19)     | 20     |
| `docs/specifications/pipelines/recommendations/` | Pipeline SHOULD recommendations (8) | 8      |
| `docs/specifications/components/modules/`        | Module conventions                  | 9      |
| `docs/specifications/components/subworkflows/`   | Subworkflow conventions             | 7      |
| `docs/specifications/reviews/`                   | PR review process                   | 5      |
| `docs/specifications/test-data/`                 | Test data guidelines                | 3      |
| `docs/contributing/`                             | Contribution guidelines             | ~20    |
| `docs/developing/`                               | Developer guides                    | ~15    |
| `docs/nf-core-tools/`                            | CLI tool reference                  | ~40    |
| `docs/running/`                                  | Pipeline execution                  | ~15    |
| `api_reference/`                                 | API docs by version (1.5-dev)       | ~2,400 |

## Accuracy disclaimer

AI-generated compliance reports can contain errors:

- Claude may misinterpret MUST/SHOULD/MAY requirements
- Compliance status for individual requirements may be incorrect
- The skill may miss violations that require deep code analysis

**Always verify** against `nf-core pipelines lint` output and the [original spec text](https://nf-co.re/docs/specifications/overview). The skill is a guide, not a gate.

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- `git` (for sparse checkout)
- `python3` (for index generation)
- `nf-core` tools (optional, for lint)
- `gh` CLI (optional, for issue creation)

## Tests

See [TESTS.md](TESTS.md) for 56 manual tests with copy-paste prompts.

## Acknowledgements

Built with [Claude Code](https://claude.ai/code). Design patterns adapted from:

- **Anthropic official plugins**: multi-agent parallel review, confidence filtering (`code-review`, `claude-code-setup`)
- **[impeccable](https://github.com/nichochar/impeccable)**: severity classification, behavioral guardrails
- **[gstack](https://github.com/garryslist/gstack)**: completion status protocol, operational self-improvement, confidence calibration

nf-core documentation sourced from [nf-core/website](https://github.com/nf-core/website) via sparse git checkout.

## License

MIT (same as nf-core)
