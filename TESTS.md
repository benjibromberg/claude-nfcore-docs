# Test Suite

Each test includes a **Prompt** you can paste into a new Claude Code session to run it.
Most tests require being in an nf-core pipeline directory (e.g., `plantmine/`) unless noted otherwise.

---

## Test 1: Freshness check

**Prompt:**
```
Run /nfcore-docs. When it asks what to load, select "13" (just use the index). Report the freshness status from the preamble output.
```

**Expected:** Reports age in hours and either "Docs are fresh" or triggers an update.

---

## Test 2: Module spec loading

**Prompt:**
```
Run /nfcore-docs. Select option 1 (module migration). After loading the module specs, tell me the first 3 MUST requirements from general.md.
```

**Expected:** Reads `specifications/components/modules/general.md` and extracts MUST requirements (e.g., input files in channel definitions, ext.args for non-file args, args variable naming).

---

## Test 3: CI testing requirements

**Prompt:**
```
Run /nfcore-docs. Select option 5 (CI setup). What does nf-core require for CI testing?
```

**Expected:** Reads `specifications/pipelines/requirements/ci_testing.md` and reports MUST/SHOULD requirements for CI.

---

## Test 4: Lint cross-reference

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). Run all lint tools and cross-reference each warning/failure against the spec files. Classify each by MUST vs SHOULD.
```

**Expected:** Runs lint, maps each warning/failure to its corresponding specification file, and classifies by severity (Critical for MUST, High for SHOULD).

---

## Test 5: Git branch compliance

**Prompt:**
```
Run /nfcore-docs. Select option 8 (git/branch model). Load the git branches spec and verify this pipeline's branch model is compliant.
```

**Expected:** Reads `specifications/pipelines/requirements/git_branches.md` and checks for master/main, dev, and TEMPLATE branches.

---

## Test 6: API reference lookup

**Prompt:**
```
Run /nfcore-docs. Select option 13 (index only). Then ask: find the API reference for nf-core tools 3.5.2 and list what lint tests are documented.
```

**Expected:** Uses Glob to find `api_reference/3.5.2/` and lists pipeline_lint_tests, module_lint_tests, and subworkflow_lint_tests contents.

---

## Test 7: Subworkflow specs

**Prompt:**
```
Run /nfcore-docs. Select option 2 (subworkflow restructure). Summarize all MUST and SHOULD requirements for subworkflows.
```

**Expected:** Reads all 7 files in `specifications/components/subworkflows/` and extracts MUST/SHOULD requirements.

---

## Test 8: Stale cache trigger

**Prompt:**
```
First run this bash command to backdate the cache:
touch -t $(date -v-48H +%Y%m%d%H%M.%S) ~/.cache/nfcore-docs/.git/FETCH_HEAD

Then run /nfcore-docs. Select option 13 (index only). Report whether it triggered an update.
```

**Expected:** Reports ">24h ago" and triggers `git pull`.

---

## Test 9: Missing cache auto-setup

**Prompt:**
```
First run: mv ~/.cache/nfcore-docs ~/.cache/nfcore-docs-backup

Then run /nfcore-docs. Select option 13 (index only). After testing, restore:
rm -rf ~/.cache/nfcore-docs && mv ~/.cache/nfcore-docs-backup ~/.cache/nfcore-docs
```

**Expected:** Automatically creates the cache via sparse git checkout (not just instructions). Index generates after setup.

---

## Test 10: Full compliance audit

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). Produce the full report. I want to see: severity summary, positive findings, recommended next actions table, and the accuracy disclaimer.
```

**Expected:**
- Runs `nf-core pipelines lint`, `nf-core modules lint`, `nf-core subworkflows lint`
- Checks for `ro-crate-metadata.json`
- Reads all spec files under `specifications/` recursively
- Report includes severity summary (`Critical: N | High: N | Medium: N | Low: N`)
- Includes a positive findings section
- Includes a recommended next actions table with specific nf-core commands
- Ends with the accuracy disclaimer footer
- Ends with completion status (DONE or DONE_WITH_CONCERNS)

---

## Test 11: Interactive menu

**Prompt:**
```
Run /nfcore-docs
```

**Expected:** Shows AskUserQuestion with 14 options, context budget table, and note that the index is already loaded. Should follow re-ground/context/recommend/options structure.

---

## Test 12: Session re-invocation

**Prompt:**
```
Run /nfcore-docs. Select option 13 (index only).
Then run /nfcore-docs again. Does it skip the preamble?
```

**Expected:** Second invocation skips the preamble (no freshness check, no index regeneration). Goes directly to Step 2 asking what else to load.

---

## Test 13: Targeted module check

**Prompt:**
```
Run /nfcore-docs. Select option 1 (module migration). After loading specs, run nf-core modules lint and cross-reference the output against the loaded module specs.
```

**Expected:** Loads `specifications/components/modules/*.md`, runs `nf-core modules lint`, maps output to module spec requirements.

---

## Test 14: Module creation workflow

**Prompt:**
```
Run /nfcore-docs. I need to create a new local module for a tool called "mytool". Walk me through the process.
```

**Expected:**
1. Checks `nf-core modules list remote` for existing module
2. Suggests `nf-core modules create --empty-template` if not found
3. Loads module specs into context
4. Offers to guide through completing the skeleton

---

## Test 15: Severity and confidence in audit

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). For each finding in the report, I want to see both severity (Critical/High/Medium/Low) AND confidence (N/10). Show me findings across all confidence levels.
```

**Expected:** Each finding includes:
- Severity: Critical/High/Medium/Low (mapped from MUST/SHOULD/MAY)
- Confidence: N/10 with appropriate display rules
- Findings with confidence < 4 are flagged or excluded from main report

---

## Test 16: Issue creation from audit

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). After the report, when asked about creating issues, select "let me pick which ones."
```

**Expected:** AskUserQuestion: "Found X compliance gaps. Want me to create GitHub issues?" with yes/no/selective options. If selective, presents each finding and asks create/skip. Checks for existing issues before creating.

---

## Test 17: Completion status

**Prompt:**
```
Run /nfcore-docs. Select option 4 (lint fixes). Load the specs, run pipelines lint, and cross-reference. What status do you end with?
```

**Expected:** Ends with one of: DONE, DONE_WITH_CONCERNS, BLOCKED, or NEEDS_CONTEXT.

---

## Test 18: NEVER rules enforcement

**Prompt:**
```
Run /nfcore-docs. Tell me if this pipeline is nf-core compliant WITHOUT running any lint tools. Just guess based on the file structure.
```

**Expected:** Skill refuses to guess. States it must run lint tools first per NEVER rules. Offers to run the tools instead.

---

## Test 19: Accuracy disclaimer

**Prompt:**
```
Run /nfcore-docs. Select option 4 (lint fixes). Run lint and produce a compliance check. Does the output include an accuracy disclaimer?
```

**Expected:** Report footer includes: "This compliance report is AI-generated and may contain inaccuracies..."

---

## Test 20: Index covers all doc categories

**Prompt:**
```
Run /nfcore-docs. Select option 13 (index only). Does the index include files from ALL these categories: community, contributing, developing, get_started, nf-core-tools, running, specifications? Also check that API reference is listed.
```

**Expected:** Index output contains entries from all 7 categories plus API reference summary with version directories.

---

## Test 21: Non-pipeline directory

**Prompt (run from home directory, NOT a pipeline):**
```
cd ~ && Run /nfcore-docs. Select option 13 (index only). Does it work without a pipeline?
```

**Expected:** Preamble completes without errors. Pipeline context section is skipped. Index still generates. Skill remains usable for browsing docs.

---

## Test 22: Lint cache bug workaround

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). Check: does it clear ~/.config/nfcore/nf-core/modules/ before running lint?
```

**Expected:** The `rm -rf ~/.config/nfcore/nf-core/modules/` command runs before `nf-core pipelines lint`. Lint does not crash with "Branch 'master' not found."

---

## Test 23: Load all specs context cost

**Prompt:**
```
Run /context first to get baseline.
Then run /nfcore-docs. Select option 11 (load all specs).
Then run /context again. How many tokens did the specs consume?
```

**Expected:** ~60K tokens consumed by spec files (~6% of 1M).

---

## Test 24: Load all docs context cost

**Prompt:**
```
Run /context first to get baseline.
Then run /nfcore-docs. Select option 12 (load all docs).
Then run /context again. How many tokens did all docs consume?
```

**Expected:** ~275K tokens consumed total (~28% of 1M).

---

## Test 25: Escalation after repeated failure

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). Before running lint, temporarily rename nf-core:
sudo mv $(which nf-core) $(which nf-core).bak

Then try the audit. After testing, restore:
sudo mv $(which nf-core).bak $(which nf-core)
```

**Expected:** After failing to run lint, reports BLOCKED status with what was attempted and what the user should do. Does not retry indefinitely.

---

## Test 26: Duplicate issue detection

**Prompt:**
```
First create a test issue: gh issue create --title "chore(compliance): Docker Support" --body "test"
Then run /nfcore-docs. Select option 6 (full compliance audit). When asked about creating issues, say yes. Does it detect the existing Docker issue?
Clean up: gh issue close <number> after testing.
```

**Expected:** Skill detects the existing issue via `gh issue list --search` and asks whether to skip or create a new one.

---

## Test 27: Custom file request (option 14)

**Prompt:**
```
Run /nfcore-docs. Select option 14 (something else). Say: "Show me the release procedure documentation."
```

**Expected:** Skill searches the index for "release procedure", finds `developing/pipelines/release-procedure.md`, and reads it.

---

## Test 28: Stale cache update preserves structure

**Prompt:**
```
First backdate: touch -t $(date -v-48H +%Y%m%d%H%M.%S) ~/.cache/nfcore-docs/.git/FETCH_HEAD
Then run /nfcore-docs. Select option 13 (index only).
Does the index regenerate correctly after the update? Any missing categories?
```

**Expected:** `git pull` runs, FETCH_HEAD updates, index regenerates with all categories intact.

---

## Test 29: Severity mapping accuracy

**Prompt:**
```
Run /nfcore-docs. Load specifications/pipelines/requirements/git_branches.md. This file contains MUST, SHOULD, and MAY statements. Now run an audit of just the git branch model. Are the severity levels correctly mapped?
```

**Expected:**
- MUST violations → Critical
- SHOULD gaps → High
- MAY suggestions → Medium
- No severity misapplied

---

## Test 30: Positive findings completeness

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). In the positive findings section, does each finding reference a specific spec file? Are they specific (e.g., "MIT license present") or vague (e.g., "some requirements met")?
```

**Expected:** Each positive finding references a specific spec file and is concrete, not vague.

---

## Test 31: Action mapping specificity

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). In the recommended next actions table, is every command copy-pasteable? Any generic advice like "fix this" without a specific command?
```

**Expected:** Every action maps to a specific `nf-core` command. No generic advice.

---

## Test 32: Mixed intent detection

**Prompt:**
```
Run /nfcore-docs. I need help with module migration and also want to check CI compliance. Load both sets of docs and run both checks.
```

**Expected:** Loads `specifications/components/modules/*.md` AND `specifications/pipelines/requirements/ci_testing.md`. Runs both `nf-core modules lint` and checks CI workflows. Does not force user to pick one.

---

## Test 33: Index-only mode

**Prompt:**
```
Run /nfcore-docs. Select option 13 (just use the index). Then ask: "What docs exist about testing?" Answer from the index without reading any spec files.
```

**Expected:** No additional files are read. Answers from the index by listing testing-related entries (module testing, subworkflow testing, pipeline testing recommendation, test data specs).

---

## Test 34: Compliance score

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). Does the report include a compliance score (0-10) with per-category breakdown?
```

**Expected:** Report includes `nf-core Compliance Score: X.X/10` with breakdown across pipeline lint, module compliance, subworkflow compliance, MUST requirements, and SHOULD recommendations.

---

## Test 35: Audit report persistence

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). After the report, check: was it saved to .nfcore-docs/reports/?
ls .nfcore-docs/reports/ 2>/dev/null
```

**Expected:** A file like `.nfcore-docs/reports/{date}-compliance.md` exists containing the full report.

---

## Test 36: Operational learning logged

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). After the audit, does the skill reflect on what happened and log any learnings? Check:
cat .nfcore-docs/learnings.jsonl 2>/dev/null
```

**Expected:** If a genuine discovery was made (e.g., unexpected lint behavior, spec interpretation), a JSONL entry with `ts`, `context`, `insight`, and `confidence` fields is appended.

---

## Test 37: Prior learnings loaded on start

**Prompt:**
```
First, manually create a test learning:
mkdir -p .nfcore-docs && echo '{"ts":"2026-04-16","context":"testing","insight":"nf-core tools 3.5.2 cache bug requires rm -rf before lint","confidence":"high"}' > .nfcore-docs/learnings.jsonl

Then run /nfcore-docs. Does the preamble show the prior learning?
Clean up: rm -rf .nfcore-docs/learnings.jsonl
```

**Expected:** Preamble output includes `LEARNINGS: 1 entries` and displays the learning content.

---

## Test 38: Trend tracking across audits

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit) and complete it.
Then run /nfcore-docs again. Select option 6 again for a second audit.
Does the second audit compare against the first and show a trend?
```

**Expected:** Second audit mentions the previous report, summarizes resolved/persistent/new findings, and reports trend (improving/degrading/stable).

---

## Test 39: Learnings have correct fields

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). After completion, check:
cat .nfcore-docs/learnings.jsonl 2>/dev/null | python3 -c "import json,sys; [print(sorted(json.loads(l).keys())) for l in sys.stdin]"
```

**Expected:** Each learning entry has exactly these fields: `confidence`, `context`, `insight`, `ts`. No missing fields.

---

## Test 40: Empty learnings file handled gracefully

**Prompt:**
```
mkdir -p .nfcore-docs && touch .nfcore-docs/learnings.jsonl
Run /nfcore-docs. Select option 13 (index only). Does the preamble handle an empty learnings file without errors?
Clean up: rm .nfcore-docs/learnings.jsonl
```

**Expected:** Shows `LEARNINGS: 0 entries` or similar. No errors from empty file.

---

## Test 41: No report directory yet

**Prompt:**
```
Make sure .nfcore-docs/reports/ does not exist:
rm -rf .nfcore-docs/reports/

Run /nfcore-docs. Select option 6 (full compliance audit). Does it create the directory and save the report?
```

**Expected:** Creates `.nfcore-docs/reports/` directory and saves the report file. No errors about missing directory.

---

## Test 42: Compliance score reflects actual state

**Prompt:**
```
Run /nfcore-docs. Select option 6 (full compliance audit). If lint shows 0 failures, does the compliance score reflect that (high score)? If there are many warnings, is the score lower than 10?
```

**Expected:** Score correlates with actual compliance state. A pipeline with 0 lint failures but many structural issues (missing meta.yml, no nf-test) should not get 10/10.
