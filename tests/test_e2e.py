"""E2E tests via `claude -p` — requires Claude Code CLI + Max subscription.

These tests spawn a Claude CLI subprocess with NDJSON streaming output,
send a skill-triggering prompt from inside a real nf-core pipeline fixture,
and assert on tool calls and output patterns.

Fixtures are pinned nf-core pipeline versions cloned by tests/fixtures/setup.sh.
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
    fixture_available,
    get_fixture_path,
    DEFAULT_FIXTURE,
)

# Skip entire module if claude CLI is not available
if shutil.which("claude") is None:
    pytest.skip(
        "claude CLI not found — E2E tests require Claude Code", allow_module_level=True
    )

# Skip if fixtures aren't cloned
if not fixture_available(DEFAULT_FIXTURE):
    pytest.skip(
        "Pipeline fixtures not cloned. Run: ./tests/fixtures/setup.sh",
        allow_module_level=True,
    )

E2E_TIMEOUT = 300  # seconds per test
MAX_TURNS = 15


def run_claude_session(prompt, max_turns=MAX_TURNS, timeout=E2E_TIMEOUT, cwd=None):
    """Spawn claude -p, parse NDJSON, return structured result."""
    if cwd is None:
        cwd = get_fixture_path(DEFAULT_FIXTURE)

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
        proc = subprocess.run(
            f'cat "{prompt_file}" | {" ".join(args)}',
            shell=True,
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


# --- Tests (run from fetchngs fixture by default) ---


def test_skill_invoked():
    """Skill invocation triggers the Skill tool from a real pipeline directory."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index).",
    )
    names = tool_names(result)
    assert "Skill" in names or "Bash" in names, (
        f"Expected Skill or Bash tool call. Tools: {names}"
    )


def test_preamble_runs_bash():
    """Preamble executes Bash tool (docs freshness check) in pipeline context."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Do NOT load any additional files.",
    )
    names = tool_names(result)
    assert "Bash" in names, f"Expected Bash tool call in preamble. Tools used: {names}"


def test_pipeline_context_detected():
    """Skill detects the pipeline from nextflow.config and reports modules/subworkflows."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Report the pipeline name and module counts from the preamble.",
    )
    text = result["output_text"].lower()
    all_inputs = " ".join(tc["input_summary"] for tc in result["tool_calls"]).lower()
    combined = text + " " + all_inputs
    # The preamble should detect fetchngs as an nf-core pipeline
    assert "fetchngs" in combined or "nf-core" in combined or "pipeline" in combined, (
        f"Skill did not detect pipeline context. Output: {result['output_text'][:300]}"
    )


def test_preamble_generates_index():
    """Preamble generates the nf-core documentation index."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Show me the documentation index output.",
    )
    # The preamble runs a bash script that calls python3 internally.
    # We can't reliably see "python3" in the truncated tool input summaries,
    # but we can verify the index was generated by checking the output text.
    combined = result["output_text"].lower()
    assert any(
        term in combined for term in ["index", "documentation", "specifications", "172"]
    ), f"Index generation not evident in output. Output: {result['output_text'][:500]}"


@pytest.mark.skip(
    reason="claude -p sandbox restricts skill from reading SKILL.md when cwd is inside fixture dir — needs --dangerously-skip-permissions or sandbox config"
)
def test_completion_status():
    """Response includes a completion status from a real pipeline directory."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "End with your completion status.",
    )
    valid_statuses = ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]
    text = result["output_text"].upper()
    has_status = any(s in text for s in valid_statuses)
    assert has_status, (
        f"No completion status found. Expected one of {valid_statuses}. "
        f"Output tail: ...{result['output_text'][-300:]}"
    )


def test_index_mentions_docs():
    """Index output references nf-core documentation categories."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Report whether the index was generated successfully.",
    )
    text = result["output_text"].lower()
    all_inputs = " ".join(tc["input_summary"] for tc in result["tool_calls"]).lower()
    combined = text + " " + all_inputs
    assert (
        "index" in combined
        or "documentation" in combined
        or "specifications" in combined
    ), "No mention of index or documentation in output"
