"""Test SKILL.md YAML frontmatter validation."""

import re
from tests.conftest import SKILL_MD, parse_frontmatter

REQUIRED_TOOLS = ["Bash", "Read", "Grep", "Glob", "Agent", "AskUserQuestion"]
ALLOWED_KEYS = {"name", "version", "description", "allowed-tools"}


def test_frontmatter_exists():
    fm = parse_frontmatter(SKILL_MD)
    assert fm is not None, "SKILL.md has no YAML frontmatter (missing --- delimiters)"


def test_name_field():
    fm = parse_frontmatter(SKILL_MD)
    assert fm["name"] == "nfcore-docs"


def test_version_field():
    fm = parse_frontmatter(SKILL_MD)
    assert re.match(r"^\d+\.\d+\.\d+", fm["version"]), (
        f"Version '{fm['version']}' is not valid semver"
    )


def test_description_field():
    # description uses multiline `|` syntax which our simple parser skips the value for.
    # Just verify the key exists in the raw frontmatter text.
    from tests.conftest import read_file
    content = read_file(SKILL_MD)
    assert "description:" in content, "Missing description field in frontmatter"


def test_allowed_tools_present():
    fm = parse_frontmatter(SKILL_MD)
    assert "allowed-tools" in fm, "Missing allowed-tools field"
    assert isinstance(fm["allowed-tools"], list), "allowed-tools should be a list"


def test_allowed_tools_contains_required():
    fm = parse_frontmatter(SKILL_MD)
    tools = fm["allowed-tools"]
    for tool in REQUIRED_TOOLS:
        assert tool in tools, f"Missing required tool: {tool}"


def test_no_extra_frontmatter_keys():
    fm = parse_frontmatter(SKILL_MD)
    extra = set(fm.keys()) - ALLOWED_KEYS
    assert not extra, f"Unexpected frontmatter keys: {extra}"
