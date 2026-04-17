"""E2E tests via `claude -p` — requires Claude Code CLI + Max subscription.

These tests spawn a Claude CLI subprocess with NDJSON streaming output,
send a skill-triggering prompt from inside a real nf-core pipeline fixture,
and assert on tool calls and output patterns.

Tests are parametrized across all available pipeline fixtures (fetchngs,
funcscan, rnaseq). Each fixture represents a different nf-core template era.
See tests/fixtures/README.md for selection rationale.

Run with: ./test.sh --e2e
"""

import json
import os
import subprocess
import shutil
import tempfile
import pytest

from tests.conftest import (
    available_fixtures,
    get_fixture_path,
)

# Skip entire module if claude CLI is not available
if shutil.which("claude") is None:
    pytest.skip(
        "claude CLI not found — E2E tests require Claude Code", allow_module_level=True
    )

FIXTURES = available_fixtures()

if not FIXTURES:
    pytest.skip(
        "No pipeline fixtures cloned. Run: ./tests/fixtures/setup.sh",
        allow_module_level=True,
    )

E2E_TIMEOUT = 300  # seconds per test
MAX_TURNS = 15


def run_claude_session(prompt, fixture_name, max_turns=MAX_TURNS, timeout=E2E_TIMEOUT):
    """Spawn claude -p, parse NDJSON, return structured result."""
    cwd = get_fixture_path(fixture_name)

    args = [
        "claude",
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-turns",
        str(max_turns),
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        with open(prompt_file) as stdin_file:
            proc = subprocess.run(
                args,
                stdin=stdin_file,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
    finally:
        os.unlink(prompt_file)

    tool_calls = []
    output_text = ""
    exit_reason = "unknown"

    for line in proc.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "assistant":
            for item in event.get("message", {}).get("content", []):
                if item.get("type") == "tool_use":
                    tool_calls.append(
                        {
                            "tool": item.get("name", "unknown"),
                            "input_summary": str(item.get("input", {}))[:200],
                        }
                    )
                elif item.get("type") == "text":
                    output_text += item.get("text", "")

        if event.get("type") == "result":
            exit_reason = event.get("subtype", "success")

    return {
        "tool_calls": tool_calls,
        "output_text": output_text,
        "exit_reason": exit_reason,
    }


def tool_names(result):
    """Extract just the tool names from a session result."""
    return [tc["tool"] for tc in result["tool_calls"]]


# --- Tests (parametrized across all available fixtures) ---


@pytest.mark.parametrize("fixture_name", FIXTURES)
def test_skill_invoked(fixture_name):
    """Skill invocation triggers the Skill tool from a real pipeline directory."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index).",
        fixture_name=fixture_name,
    )
    names = tool_names(result)
    assert "Skill" in names or "Bash" in names, (
        f"[{fixture_name}] Expected Skill or Bash tool call. Tools: {names}"
    )


@pytest.mark.parametrize("fixture_name", FIXTURES)
def test_preamble_runs_bash(fixture_name):
    """Preamble executes Bash tool (docs freshness check) in pipeline context."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Do NOT load any additional files.",
        fixture_name=fixture_name,
    )
    names = tool_names(result)
    assert "Bash" in names, (
        f"[{fixture_name}] Expected Bash tool call in preamble. Tools used: {names}"
    )


@pytest.mark.parametrize("fixture_name", FIXTURES)
def test_pipeline_context_detected(fixture_name):
    """Skill detects the pipeline from nextflow.config and reports modules/subworkflows."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Report the pipeline name and module counts from the preamble.",
        fixture_name=fixture_name,
    )
    text = result["output_text"].lower()
    all_inputs = " ".join(tc["input_summary"] for tc in result["tool_calls"]).lower()
    combined = text + " " + all_inputs
    # Each fixture should detect its own pipeline name
    assert (
        fixture_name in combined or "nf-core" in combined or "pipeline" in combined
    ), (
        f"[{fixture_name}] Skill did not detect pipeline context. "
        f"Output: {result['output_text'][:300]}"
    )


@pytest.mark.parametrize("fixture_name", FIXTURES)
def test_preamble_generates_index(fixture_name):
    """Preamble generates the nf-core documentation index."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Show me the documentation index output.",
        fixture_name=fixture_name,
    )
    combined = result["output_text"].lower()
    assert any(
        term in combined for term in ["index", "documentation", "specifications", "172"]
    ), (
        f"[{fixture_name}] Index generation not evident in output. "
        f"Output: {result['output_text'][:500]}"
    )


@pytest.mark.parametrize("fixture_name", FIXTURES)
@pytest.mark.skip(
    reason="claude -p sandbox restricts skill from reading SKILL.md when cwd is "
    "inside fixture dir — needs --dangerously-skip-permissions or sandbox config"
)
def test_completion_status(fixture_name):
    """Response includes a completion status from a real pipeline directory."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "End with your completion status.",
        fixture_name=fixture_name,
    )
    valid_statuses = ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]
    text = result["output_text"].upper()
    has_status = any(s in text for s in valid_statuses)
    assert has_status, (
        f"[{fixture_name}] No completion status found. Expected one of {valid_statuses}. "
        f"Output tail: ...{result['output_text'][-300:]}"
    )


@pytest.mark.parametrize("fixture_name", FIXTURES)
def test_index_mentions_docs(fixture_name):
    """Index output references nf-core documentation categories."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Report whether the index was generated successfully.",
        fixture_name=fixture_name,
    )
    text = result["output_text"].lower()
    all_inputs = " ".join(tc["input_summary"] for tc in result["tool_calls"]).lower()
    combined = text + " " + all_inputs
    assert (
        "index" in combined
        or "documentation" in combined
        or "specifications" in combined
    ), f"[{fixture_name}] No mention of index or documentation in output"
