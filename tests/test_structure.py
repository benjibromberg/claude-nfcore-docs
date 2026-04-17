"""Test SKILL.md structural validation — required sections, patterns, guardrails."""

import re
from tests.conftest import SKILL_MD, read_file

CONTENT = None


def _content():
    global CONTENT
    if CONTENT is None:
        CONTENT = read_file(SKILL_MD)
    return CONTENT


# --- Required sections ---


def test_has_step0():
    assert "## Step 0" in _content()


def test_has_step1():
    assert "## Step 1" in _content()


def test_has_step2():
    assert "## Step 2" in _content()


def test_has_step3():
    assert "## Step 3" in _content()


def test_has_step4():
    assert "## Step 4" in _content()


def test_has_rules_section():
    assert "## Rules" in _content()


def test_has_persistence_section():
    assert "## Persistence" in _content()


def test_has_completion_section():
    assert "## Completion" in _content()


# --- Menu options ---


def test_has_tiered_menu():
    c = _content()
    # Tier 1 top-level options
    assert "Component work" in c
    assert "Full compliance audit" in c
    assert "Pipeline requirements" in c
    assert "Load into context" in c
    # Tier 2 follow-ups
    assert "Module migration" in c
    assert "Subworkflow restructure" in c


def test_git_review_specs_always_loaded():
    c = _content()
    assert "Always load first" in c or "always load" in c.lower()
    assert "git_branches.md" in c
    assert "reviews" in c.lower()


def test_has_context_budget_table():
    assert "% of 1M" in _content()


# --- Compliance audit structure ---


def test_has_5_agent_domains():
    c = _content()
    assert "Pipeline requirements" in c
    assert "Module compliance" in c
    assert "Subworkflow compliance" in c
    assert "Documentation & metadata" in c
    assert "Git, CI & reviews" in c or "Git, CI" in c


def test_has_severity_levels():
    c = _content()
    for level in ["Critical", "High", "Medium", "Low"]:
        assert level in c


def test_has_completion_statuses():
    c = _content()
    for status in ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]:
        assert status in c


def test_has_never_rules():
    c = _content()
    assert "NEVER" in c
    never_count = len(
        re.findall(
            r"^- .+$",
            c[c.index("**NEVER:**") : c.index("## Persistence")],
            re.MULTILINE,
        )
    )
    assert never_count >= 8, f"Expected at least 8 NEVER rules, found {never_count}"


def test_has_accuracy_disclaimer():
    assert "AI-generated and may contain inaccuracies" in _content()


# --- v1.0.1 guardrails ---


def test_has_general_ask_principle():
    c = _content()
    assert "General principle" in c or "ask the user" in c.lower()
    assert "judgment call" in c.lower() or "ambiguity" in c.lower()


def test_has_askuserquestion_enforcement():
    c = _content()
    # Must appear in 3 contexts: CLAUDE_MD_REF, model selection, issue creation
    auq_mentions = [i for i in range(len(c)) if c[i:].startswith("AskUserQuestion")]
    assert len(auq_mentions) >= 3, (
        f"AskUserQuestion mentioned {len(auq_mentions)} times, expected at least 3 "
        "(CLAUDE_MD_REF, model selection, issue creation)"
    )


def test_has_agent_report_save_before_consolidation():
    c = _content()
    save_pos = c.find("IMMEDIATELY after all agents return")
    if save_pos == -1:
        save_pos = c.find("BEFORE any consolidation")
    assert save_pos != -1, "Missing blocking prerequisite for agent report saving"
    consolidation_pos = c.find("**Consolidation**")
    assert consolidation_pos != -1, "Missing Consolidation section"
    assert save_pos < consolidation_pos, (
        "Agent report save instruction must appear BEFORE consolidation"
    )


def test_report_organized_by_spec_directory():
    assert (
        "primary organization" in _content().lower()
        or "spec directory" in _content().lower()
    )


def test_has_dedup_checkpoint():
    assert "Raw findings:" in _content() or "pre- and post-dedup" in _content().lower()


def test_has_low_confidence_appendix():
    c = _content().lower()
    assert "appendix" in c or "confidence < 4" in c


def test_has_tool_crash_flow():
    c = _content()
    assert "workaround" in c.lower()
    assert "log" in c.lower() and "learning" in c.lower()


# --- Embedded scripts ---


def test_bash_block_present():
    assert "```bash" in _content()


def test_python_block_present():
    assert "python3 -c" in _content()


def test_has_sparse_checkout_setup():
    assert "sparseCheckout" in _content() or "sparse-checkout" in _content()


def test_has_stale_check():
    assert "STALE_HOURS" in _content()
    assert "AGE_HOURS" in _content() or "AGE_HOURS" in _content()


def test_has_dependency_check():
    c = _content()
    for dep in ["git", "python3", "nf-core", "gh"]:
        assert f"command -v {dep}" in c, f"Missing dependency check for {dep}"
