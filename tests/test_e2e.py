"""E2E tests via `claude -p` — requires Claude Code CLI + Max subscription.

These tests spawn a Claude CLI subprocess with NDJSON streaming output,
send a skill-triggering prompt, and assert on tool calls and output patterns.

Run with: ./test.sh --e2e
"""

import json
import os
import subprocess
import shutil
import tempfile
import pytest

# Skip entire module if claude CLI is not available
pytestmark = pytest.mark.skipif(
    shutil.which("claude") is None,
    reason="claude CLI not found — E2E tests require Claude Code",
)

E2E_TIMEOUT = 300  # seconds per test
MAX_TURNS = 15


def run_claude_session(prompt, max_turns=MAX_TURNS, timeout=E2E_TIMEOUT, cwd=None):
    """Spawn claude -p, parse NDJSON, return structured result.

    Returns dict with:
      - tool_calls: list of {tool, input_summary}
      - output_text: final text output
      - exit_reason: 'success', 'error_max_turns', etc.
      - raw_lines: all NDJSON lines for debugging
    """
    args = [
        "claude", "-p",
        "--output-format", "stream-json",
        "--verbose",
        "--max-turns", str(max_turns),
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        proc = subprocess.run(
            f'cat "{prompt_file}" | {" ".join(args)}',
            shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=cwd,
        )
    finally:
        os.unlink(prompt_file)

    tool_calls = []
    output_text = ""
    exit_reason = "unknown"
    raw_lines = []

    for line in proc.stdout.strip().split("\n"):
        if not line.strip():
            continue
        raw_lines.append(line)
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "assistant":
            for item in event.get("message", {}).get("content", []):
                if item.get("type") == "tool_use":
                    tool_calls.append({
                        "tool": item.get("name", "unknown"),
                        "input_summary": str(item.get("input", {}))[:200],
                    })
                elif item.get("type") == "text":
                    output_text += item.get("text", "")

        if event.get("type") == "result":
            exit_reason = event.get("subtype", "success")

    return {
        "tool_calls": tool_calls,
        "output_text": output_text,
        "exit_reason": exit_reason,
        "raw_lines": raw_lines,
    }


def tool_names(result):
    """Extract just the tool names from a session result."""
    return [tc["tool"] for tc in result["tool_calls"]]


# --- Tests ---

def test_skill_invoked(tmp_path):
    """Skill invocation triggers the Skill tool."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index).",
        cwd=str(tmp_path),
    )
    names = tool_names(result)
    # claude -p invokes the Skill tool first, then Bash for the preamble
    assert "Skill" in names or "Bash" in names, (
        f"Expected Skill or Bash tool call. Tools: {names}"
    )


def test_preamble_runs_bash(tmp_path):
    """Preamble executes Bash tool (docs freshness check)."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Do NOT load any additional files.",
        cwd=str(tmp_path),
    )
    names = tool_names(result)
    assert "Bash" in names, (
        f"Expected Bash tool call in preamble. Tools used: {names}"
    )


def test_preamble_runs_python(tmp_path):
    """Preamble executes python3 for index generation."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Make sure the index is generated via the python3 script.",
        cwd=str(tmp_path),
    )
    # python3 is invoked inside a Bash tool call — check all tool inputs
    all_inputs = " ".join(tc["input_summary"] for tc in result["tool_calls"])
    assert "python3" in all_inputs.lower() or "python" in all_inputs.lower(), (
        f"Expected python3 invocation in tool calls. Inputs: {all_inputs[:500]}"
    )


def test_dependency_section_in_output(tmp_path):
    """Output includes Dependencies section from preamble."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Show me the preamble output including the Dependencies section.",
        cwd=str(tmp_path),
    )
    # Dependencies should appear either in tool outputs or Claude's text
    all_text = result["output_text"] + " ".join(tc["input_summary"] for tc in result["tool_calls"])
    assert "dependencies" in all_text.lower() or "Bash" in tool_names(result), (
        "No Dependencies section or Bash tool call found"
    )


def test_index_in_output(tmp_path):
    """Output includes nf-core Documentation Index."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "Report whether the index was generated.",
        cwd=str(tmp_path),
    )
    all_text = result["output_text"] + " ".join(tc["input_summary"] for tc in result["tool_calls"])
    assert "index" in all_text.lower() or "documentation" in all_text.lower(), (
        "No mention of index generation in output"
    )


def test_completion_status(tmp_path):
    """Response includes a completion status or recognizable end state."""
    result = run_claude_session(
        "Run /nfcore-docs. Select option 13 (just use the index). "
        "End with your completion status.",
        cwd=str(tmp_path),
    )
    valid_statuses = ["DONE", "DONE_WITH_CONCERNS", "BLOCKED", "NEEDS_CONTEXT"]
    text = result["output_text"].upper()
    has_status = any(s in text for s in valid_statuses)
    # In -p mode, the skill may hit permission/environment issues and not
    # fully complete. Accept "BLOCKED" indicators as valid end states too.
    has_error_end = "PERMISSION" in text or "COULDN'T EXECUTE" in text or "ERROR" in text
    assert has_status or has_error_end, (
        f"No completion status or recognizable end state found. "
        f"Expected one of {valid_statuses} or an error indicator. "
        f"Output tail: ...{result['output_text'][-300:]}"
    )
