"""Test cross-file consistency — versions, test counts, names."""

import re
import os
from tests.conftest import (
    SKILL_MD, TESTS_MD, CLAUDE_MD, CHANGELOG_MD, README_MD, CONTRIBUTING_MD,
    parse_frontmatter, read_file, count_test_headings,
)


def test_version_consistency():
    """SKILL.md version matches CHANGELOG.md first entry."""
    fm = parse_frontmatter(SKILL_MD)
    skill_version = fm["version"]
    changelog = read_file(CHANGELOG_MD)
    # First [version] in changelog
    match = re.search(r"\[(\d+\.\d+\.\d+)\]", changelog)
    assert match, "No version found in CHANGELOG.md"
    assert match.group(1) == skill_version, (
        f"SKILL.md version ({skill_version}) != CHANGELOG.md first entry ({match.group(1)})"
    )


def test_test_count_in_tests_md():
    """Stated test count in TESTS.md header matches actual ## Test N count."""
    actual = count_test_headings(TESTS_MD)
    content = read_file(TESTS_MD)
    stated_match = re.search(r"(\d+)\s+tests?\s+total", content, re.IGNORECASE)
    assert stated_match, "No 'N tests total' found in TESTS.md header"
    stated = int(stated_match.group(1))
    assert stated == actual, (
        f"TESTS.md says {stated} tests but has {actual} ## Test N headings"
    )


def test_test_count_in_claude_md():
    """CLAUDE.md test count matches TESTS.md actual count."""
    actual = count_test_headings(TESTS_MD)
    content = read_file(CLAUDE_MD)
    match = re.search(r"(\d+).test", content)
    assert match, "No test count found in CLAUDE.md"
    stated = int(match.group(1))
    assert stated == actual, (
        f"CLAUDE.md says {stated} tests but TESTS.md has {actual}"
    )


def test_test_count_in_contributing_md():
    """CONTRIBUTING.md test count matches TESTS.md actual count."""
    actual = count_test_headings(TESTS_MD)
    content = read_file(CONTRIBUTING_MD)
    match = re.search(r"(\d+)\s+tests", content)
    assert match, "No test count found in CONTRIBUTING.md"
    stated = int(match.group(1))
    assert stated == actual, (
        f"CONTRIBUTING.md says {stated} tests but TESTS.md has {actual}"
    )


def test_test_count_in_readme_md():
    """README.md test count matches TESTS.md actual count."""
    actual = count_test_headings(TESTS_MD)
    content = read_file(README_MD)
    match = re.search(r"(\d+)\s+tests", content)
    assert match, "No test count found in README.md"
    stated = int(match.group(1))
    assert stated == actual, (
        f"README.md says {stated} tests but TESTS.md has {actual}"
    )


def test_skill_name_consistent():
    """Skill name consistent across SKILL.md, CLAUDE.md, README.md."""
    fm = parse_frontmatter(SKILL_MD)
    name = fm["name"]
    for filepath, label in [(CLAUDE_MD, "CLAUDE.md"), (README_MD, "README.md")]:
        content = read_file(filepath)
        assert name in content, f"Skill name '{name}' not found in {label}"


def test_changelog_has_current_version():
    """CHANGELOG.md first entry version matches SKILL.md version."""
    # Same as test_version_consistency but from the opposite direction
    fm = parse_frontmatter(SKILL_MD)
    changelog = read_file(CHANGELOG_MD)
    assert f"[{fm['version']}]" in changelog, (
        f"CHANGELOG.md missing entry for current version {fm['version']}"
    )


def test_coverage_map_complete():
    """Every ## Test N in TESTS.md appears in the Coverage Map table."""
    content = read_file(TESTS_MD)
    actual_count = count_test_headings(TESTS_MD)
    # Extract all test numbers from the coverage map (numbers in | cells)
    map_section = content[:content.index("---\n\n##")]  # everything before first test
    referenced = set()
    for match in re.finditer(r"\b(\d+)\b", map_section):
        num = int(match.group(1))
        if 1 <= num <= 200:  # reasonable test number range
            referenced.add(num)
    for i in range(1, actual_count + 1):
        assert i in referenced, (
            f"Test {i} exists in TESTS.md but is not in the Coverage Map"
        )


def test_no_stale_test_references():
    """Coverage Map does not reference test numbers beyond the actual count."""
    content = read_file(TESTS_MD)
    actual_count = count_test_headings(TESTS_MD)
    map_section = content[:content.index("---\n\n##")]
    for match in re.finditer(r"\b(\d+)\b", map_section):
        num = int(match.group(1))
        if 1 <= num <= 200:
            assert num <= actual_count, (
                f"Coverage Map references Test {num} but only {actual_count} tests exist"
            )


def test_required_files_exist():
    """All files listed in CLAUDE.md 'Files' section exist on disk."""
    content = read_file(CLAUDE_MD)
    # Extract filenames from "- `FILE` —" pattern in the Files section
    files_section = content[content.index("## Files"):content.index("## Development")]
    for match in re.finditer(r"`(\S+\.md)`", files_section):
        filename = match.group(1)
        # Skip paths (contain / before the filename) — only check bare filenames
        if "/" in filename:
            continue
        filepath = os.path.join(os.path.dirname(SKILL_MD), filename)
        assert os.path.exists(filepath), f"File listed in CLAUDE.md not found: {filename}"
