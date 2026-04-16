# Test Suite

Run `/nfcore-docs` and then execute these tests to validate the skill.

## Test 1: Freshness check

Confirm the cache freshness detection works.

**Expected:** Reports age in hours and either "Docs are fresh" or triggers an update.

## Test 2: Module spec loading

Ask: "Load the module specs and tell me the first 3 MUST requirements."

**Expected:** Reads `specifications/components/modules/general.md` and extracts MUST requirements (e.g., input files in channel definitions, ext.args for non-file args, args variable naming).

## Test 3: CI testing requirements

Ask: "Load the CI testing requirement spec."

**Expected:** Reads `specifications/pipelines/requirements/ci_testing.md` and reports MUST/SHOULD requirements for CI.

## Test 4: Lint cross-reference

Ask: "Run nf-core pipelines lint and cross-reference against the specs."

**Expected:** Runs lint, maps each warning/failure to its corresponding specification file, and classifies by MUST vs SHOULD.

## Test 5: Git branch compliance

Ask: "Load the git branches spec and verify this pipeline's branch model."

**Expected:** Reads `specifications/pipelines/requirements/git_branches.md` and checks for master/main, dev, and TEMPLATE branches.

## Test 6: API reference lookup

Ask: "Find the API reference for nf-core tools 3.5.2."

**Expected:** Lists contents of `api_reference/3.5.2/` including pipeline_lint_tests, module_lint_tests, and subworkflow_lint_tests directories.

## Test 7: Subworkflow specs

Ask: "Load all subworkflow specifications and summarize requirements."

**Expected:** Reads all 7 files in `specifications/components/subworkflows/` and extracts MUST/SHOULD requirements.

## Test 8: Stale cache trigger

Manually backdate the FETCH_HEAD and confirm the skill triggers an update:

```bash
touch -t $(date -v-48H +%Y%m%d%H%M.%S) ~/.cache/nfcore-docs/.git/FETCH_HEAD
```

Then re-run `/nfcore-docs`.

**Expected:** Reports ">24h ago" and triggers `git pull`.

## Test 9: Missing cache auto-setup

Temporarily rename the cache and run the skill:

```bash
mv ~/.cache/nfcore-docs ~/.cache/nfcore-docs-backup
```

**Expected:** Automatically creates the cache via sparse git checkout (not just instructions). Verify with `ls ~/.cache/nfcore-docs/sites/docs/`. Restore backup after:

```bash
rm -rf ~/.cache/nfcore-docs && mv ~/.cache/nfcore-docs-backup ~/.cache/nfcore-docs
```

## Test 10: Full compliance audit

Ask: "Run a full compliance audit of this pipeline."

**Expected:**
- Runs `nf-core pipelines lint`, `nf-core modules lint`, `nf-core subworkflows lint`
- Checks for `ro-crate-metadata.json`
- Reads all spec files under `specifications/` recursively (not a hardcoded list)
- Produces a report with severity summary (`Critical: N | High: N | Medium: N | Low: N`)
- Includes a positive findings section
- Includes a recommended next actions table
- Ends with the accuracy disclaimer footer

## Test 11: Interactive menu

Invoke `/nfcore-docs` with no additional context.

**Expected:** Shows AskUserQuestion with 14 options, context budget table, and note that the index is already loaded. Should follow re-ground/context/recommend/options structure.

## Test 12: Session re-invocation

Invoke `/nfcore-docs` twice in the same session.

**Expected:** Second invocation skips the preamble (no freshness check, no index regeneration). Goes directly to Step 2 asking what else to load.

## Test 13: Targeted module check

Ask: "Check module compliance for this pipeline."

**Expected:** Loads `specifications/components/modules/*.md`, runs `nf-core modules lint`, cross-references output against loaded module specs.

## Test 14: Module creation workflow

Ask: "I need to create a new module for a tool called mytool."

**Expected:**
1. Checks `nf-core modules list remote` for existing module
2. Suggests `nf-core modules create --empty-template` if not found
3. Loads module specs into context
4. Offers to guide through completing the skeleton

## Test 15: Severity and confidence in audit

Run a full compliance audit and check findings format.

**Expected:** Each finding includes:
- Severity: Critical/High/Medium/Low
- Confidence: N/10 with appropriate display rules
- Findings with confidence < 4 are excluded from main report or flagged

## Test 16: Issue creation from audit

After a compliance audit, confirm the skill offers to create GitHub issues.

**Expected:** AskUserQuestion: "Found X compliance gaps. Want me to create GitHub issues?" with yes/no/selective options. If yes, checks for existing issues before creating duplicates.

## Test 17: Completion status

After any skill workflow completes, check the final output.

**Expected:** Ends with one of: DONE, DONE_WITH_CONCERNS, BLOCKED, or NEEDS_CONTEXT.

## Test 18: NEVER rules enforcement

Try to trigger a NEVER rule violation:
- Ask to "summarize lint output" (should NOT pipe through grep/head/tail)
- Ask for compliance without running lint (should refuse)

**Expected:** Skill follows NEVER rules — runs lint with full output, doesn't guess at compliance.

## Test 19: Accuracy disclaimer

Run any compliance check or audit.

**Expected:** Report footer includes: "This compliance report is AI-generated and may contain inaccuracies. Verify against nf-core pipelines lint and the original specifications."
