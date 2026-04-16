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

## Test 20: Index covers all doc categories

After running the preamble, check that the index includes files from every category.

**Expected:** Index output contains entries from: community, contributing, developing, get_started, nf-core-tools, running, specifications. Also shows API reference summary with version directories.

## Test 21: Non-pipeline directory

Run `/nfcore-docs` from a directory that is NOT an nf-core pipeline (e.g., home directory).

**Expected:** Preamble completes without errors. Pipeline context section is skipped (no "Current Pipeline" output). Index still generates. Skill remains usable for browsing docs without a pipeline.

## Test 22: Lint cache bug workaround

Run a full compliance audit and verify the nf-core tools module cache is cleared.

**Expected:** The `rm -rf ~/.config/nfcore/nf-core/modules/` command runs before `nf-core pipelines lint`. Lint does not crash with "Branch 'master' not found."

## Test 23: Load all specs context cost

Select option 11 ("Load all specs") and check `/context` afterwards.

**Expected:** ~60K tokens consumed by spec files (~6% of 1M). Verify the number is in the ballpark — if wildly different, the context budget table in Step 2 needs updating.

## Test 24: Load all docs context cost

Select option 12 ("Load all docs") and check `/context` afterwards.

**Expected:** ~275K tokens consumed total (~28% of 1M). Same verification as test 23.

## Test 25: Escalation after repeated failure

Simulate a failing nf-core tool (e.g., by temporarily renaming `nf-core` binary).

**Expected:** After failing to run lint, the skill should not retry indefinitely. Should report BLOCKED status with what was attempted and what the user should do.

## Test 26: Duplicate issue detection

Create a GitHub issue titled "chore(compliance): Docker Support" manually, then run an audit that finds a Docker compliance gap.

**Expected:** Skill detects the existing issue via `gh issue list --search` and asks whether to skip or create a new one, rather than creating a duplicate.

## Test 27: Custom file request (option 14)

Select option 14 ("Something else") and ask for a specific doc page by name.

**Expected:** Skill uses the index to find the file path and reads it. Works for both spec files and non-spec files (e.g., "show me the release procedure docs").

## Test 28: Stale cache update preserves structure

Backdate FETCH_HEAD, run the skill, and verify the update doesn't break the index.

**Expected:** `git pull` runs, FETCH_HEAD timestamp updates, index regenerates with current file list. No orphaned files from previous versions.

## Test 29: Severity mapping accuracy

Load a spec file that contains MUST, SHOULD, and MAY statements. Run an audit.

**Expected:**
- MUST violations → Critical severity
- SHOULD gaps → High severity
- MAY suggestions → Medium severity
- Lint warnings without spec mapping → Low severity
- No severity level is skipped or misapplied

## Test 30: Positive findings completeness

Run a full audit on a pipeline that passes some requirements.

**Expected:** Positive findings section lists specific requirements that ARE met (not just "some requirements met"). Each positive finding references the spec file it corresponds to.

## Test 31: Action mapping specificity

Run a full audit with findings.

**Expected:** Each finding in the "Recommended Next Actions" table maps to a specific `nf-core` command, not generic advice. Commands should be copy-pasteable.

## Test 32: Mixed intent detection

Say: "I need help with module migration and also want to check CI."

**Expected:** Skill loads both `specifications/components/modules/*.md` AND `specifications/pipelines/requirements/ci_testing.md`. Runs both `nf-core modules lint` and checks `.github/workflows/`. Does not force user to pick just one option.

## Test 33: Index-only mode

Select option 13 ("Just use the index").

**Expected:** No additional files are read. Skill confirms the index is available and waits for specific questions. Can answer "what docs exist about testing?" from the index alone without loading any spec files.
