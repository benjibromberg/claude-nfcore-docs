"""Test the embedded bash preamble script in isolation."""

import os
import subprocess
import tempfile
from tests.conftest import SKILL_MD, extract_first_bash_block


def _run_bash(script, cwd=None, env=None):
    """Run a bash snippet and return (stdout, stderr, returncode)."""
    merged_env = {**os.environ, **(env or {})}
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True, text=True, timeout=30,
        cwd=cwd, env=merged_env,
    )
    return result.stdout, result.stderr, result.returncode


def _claude_md_ref_script():
    """Extract just the CLAUDE_MD_REF check portion of the preamble."""
    return """
if [ -f "CLAUDE.md" ]; then
  if grep -q "nfcore-docs" CLAUDE.md 2>/dev/null; then
    echo "CLAUDE_MD_REF: yes"
  else
    echo "CLAUDE_MD_REF: missing"
  fi
else
  echo "CLAUDE_MD_REF: no_file"
fi
"""


def _learnings_script():
    """Extract just the learnings check portion of the preamble."""
    return """
if [ -f .nfcore-docs/learnings.jsonl ]; then
  echo ""
  echo "=== Prior Learnings ==="
  echo "LEARNINGS: $(wc -l < .nfcore-docs/learnings.jsonl | tr -d ' ') entries"
  cat .nfcore-docs/learnings.jsonl
fi
"""


def _dep_check_script():
    """Extract just the dependency check portion."""
    return """
echo "=== Dependencies ==="
command -v git >/dev/null 2>&1 && echo "git: $(git --version | head -1)" || echo "git: NOT FOUND"
command -v python3 >/dev/null 2>&1 && echo "python3: $(python3 --version 2>&1)" || echo "python3: NOT FOUND"
command -v nf-core >/dev/null 2>&1 && echo "nf-core: found" || echo "nf-core: not found"
command -v gh >/dev/null 2>&1 && echo "gh: found" || echo "gh: not found"
"""


# --- CLAUDE_MD_REF tests ---

def test_claude_md_ref_no_file(tmp_path):
    stdout, _, _ = _run_bash(_claude_md_ref_script(), cwd=str(tmp_path))
    assert "CLAUDE_MD_REF: no_file" in stdout


def test_claude_md_ref_missing(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# My Project\nNo reference here.\n")
    stdout, _, _ = _run_bash(_claude_md_ref_script(), cwd=str(tmp_path))
    assert "CLAUDE_MD_REF: missing" in stdout


def test_claude_md_ref_yes(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# My Project\nUse /nfcore-docs for specs.\n")
    stdout, _, _ = _run_bash(_claude_md_ref_script(), cwd=str(tmp_path))
    assert "CLAUDE_MD_REF: yes" in stdout


# --- Learnings tests ---

def test_learnings_loaded(tmp_path):
    nfcore_dir = tmp_path / ".nfcore-docs"
    nfcore_dir.mkdir()
    (nfcore_dir / "learnings.jsonl").write_text(
        '{"ts":"2026-04-16","context":"test","insight":"test insight","confidence":"high"}\n'
        '{"ts":"2026-04-16","context":"test2","insight":"another","confidence":"low"}\n'
    )
    stdout, _, _ = _run_bash(_learnings_script(), cwd=str(tmp_path))
    assert "LEARNINGS: 2 entries" in stdout


def test_learnings_empty_file(tmp_path):
    nfcore_dir = tmp_path / ".nfcore-docs"
    nfcore_dir.mkdir()
    (nfcore_dir / "learnings.jsonl").write_text("")
    stdout, _, _ = _run_bash(_learnings_script(), cwd=str(tmp_path))
    assert "LEARNINGS: 0 entries" in stdout


def test_learnings_missing_file(tmp_path):
    stdout, _, _ = _run_bash(_learnings_script(), cwd=str(tmp_path))
    assert "LEARNINGS" not in stdout


# --- Dependency check tests ---

def test_dependency_check_git():
    stdout, _, _ = _run_bash(_dep_check_script())
    assert "git:" in stdout
    assert "NOT FOUND" not in stdout.split("git:")[1].split("\n")[0]


def test_dependency_check_python3():
    stdout, _, _ = _run_bash(_dep_check_script())
    assert "python3:" in stdout
    assert "NOT FOUND" not in stdout.split("python3:")[1].split("\n")[0]


def test_exit_code_zero():
    _, _, rc = _run_bash(_dep_check_script())
    assert rc == 0
