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

## Test 9: Missing cache

Temporarily rename the cache and run the skill:

```bash
mv ~/.cache/nfcore-docs ~/.cache/nfcore-docs-backup
```

**Expected:** Shows setup instructions with copy-pasteable commands. Restore with:

```bash
mv ~/.cache/nfcore-docs-backup ~/.cache/nfcore-docs
```

## Test 10: Full compliance audit

Ask: "Load ALL pipeline requirements and recommendations for a full compliance audit."

**Expected:** Reads all ~28 pipeline spec files, counts MUST/SHOULD/MAY statements, and reports compliance status against the current pipeline.
