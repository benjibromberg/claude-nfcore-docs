"""Test the embedded Python index generation script."""

import subprocess
import pytest
from tests.conftest import (
    SKILL_MD,
    CACHE_EXISTS,
    DOCS_ROOT,
    API_ROOT,
    extract_first_bash_block,
    extract_python_from_bash,
)

pytestmark = pytest.mark.skipif(
    not CACHE_EXISTS,
    reason="Docs cache not found at ~/.cache/nfcore-docs/ — run /nfcore-docs once to create it",
)

# Extract the Python script once
_BASH = extract_first_bash_block(SKILL_MD)
_PYTHON_SCRIPT = extract_python_from_bash(_BASH) if _BASH else None


def _run_index_script():
    """Run the extracted Python index script against the real cache."""
    assert _PYTHON_SCRIPT is not None, "Could not extract Python script from SKILL.md"
    result = subprocess.run(
        ["python3", "-c", _PYTHON_SCRIPT, DOCS_ROOT, API_ROOT],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Python script failed: {result.stderr}"
    return result.stdout


def test_index_generates_without_error():
    _run_index_script()


def test_index_has_documentation_header():
    output = _run_index_script()
    assert "## Documentation" in output


def test_index_has_api_reference_header():
    output = _run_index_script()
    assert "## API Reference" in output


def test_index_lists_all_categories():
    output = _run_index_script()
    for category in [
        "community/",
        "contributing/",
        "developing/",
        "get_started/",
        "nf-core-tools/",
        "running/",
        "specifications/",
    ]:
        assert category in output, f"Missing category: {category}"


def test_index_extracts_titles():
    output = _run_index_script()
    # Spec overview page should have its frontmatter title extracted
    assert "nf-core specifications" in output or "Specifications" in output


def test_index_has_section_headers():
    output = _run_index_script()
    # H2 headers indented with 2 spaces, H3 with 4
    lines = output.split("\n")
    h2_lines = [
        line
        for line in lines
        if line.startswith("  - ") and not line.startswith("    - ")
    ]
    h3_lines = [line for line in lines if line.startswith("    - ")]
    assert len(h2_lines) > 10, "Expected many H2 section headers"
    assert len(h3_lines) > 5, "Expected some H3 section headers"


def test_index_file_count():
    output = _run_index_script()
    # Lines listing files start with "- `" (backtick escaped in Python output)
    file_lines = [
        line for line in output.split("\n") if line.startswith("- ") and "`" in line
    ]
    assert len(file_lines) >= 150, (
        f"Expected ~172 doc files, got {len(file_lines)}. "
        f"First 3 lines: {output.split(chr(10))[:3]}"
    )


def test_api_reference_has_file_counts():
    output = _run_index_script()
    assert "files" in output.lower()
    assert "Total:" in output
