"""Shared constants and helpers for nfcore-docs tests."""

import json
import os
import re

# --- Paths ---
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
TESTS_MD = os.path.join(SKILL_DIR, "TESTS.md")
CLAUDE_MD = os.path.join(SKILL_DIR, "CLAUDE.md")
CHANGELOG_MD = os.path.join(SKILL_DIR, "CHANGELOG.md")
README_MD = os.path.join(SKILL_DIR, "README.md")
CONTRIBUTING_MD = os.path.join(SKILL_DIR, "CONTRIBUTING.md")

CACHE_DIR = os.path.expanduser("~/.cache/nfcore-docs")
DOCS_ROOT = os.path.join(CACHE_DIR, "sites/docs/src/content/docs")
SPEC_ROOT = os.path.join(DOCS_ROOT, "specifications")
API_ROOT = os.path.join(CACHE_DIR, "sites/docs/src/content/api_reference")

CACHE_EXISTS = os.path.isdir(CACHE_DIR)

# --- Pipeline fixtures ---
FIXTURES_DIR = os.path.join(SKILL_DIR, "tests", "fixtures")
FIXTURES_JSON = os.path.join(FIXTURES_DIR, "pipelines.json")


def load_fixture_config():
    """Load pipeline fixture definitions from pipelines.json."""
    with open(FIXTURES_JSON) as f:
        return json.load(f)


def get_fixture_path(name):
    """Get the path to a pipeline fixture. Returns None if not cloned."""
    path = os.path.join(FIXTURES_DIR, name)
    if os.path.isdir(path) and os.path.isfile(os.path.join(path, "nextflow.config")):
        return path
    return None


def fixture_available(name):
    """Check if a pipeline fixture is cloned and ready."""
    return get_fixture_path(name) is not None


# The smallest fixture — used as default for E2E tests
DEFAULT_FIXTURE = "fetchngs"


def available_fixtures():
    """Return names of all fixtures that are cloned and ready."""
    config = load_fixture_config()
    return [name for name in config if fixture_available(name)]


# --- Helpers ---


def read_file(filepath):
    with open(filepath) as f:
        return f.read()


def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file as a dict.

    Simple regex-based parser — no PyYAML dependency.
    Handles scalar values, multiline `|` strings, and `- item` lists.
    """
    content = read_file(filepath)
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    fm = {}
    current_key = None
    for line in match.group(1).split("\n"):
        list_match = re.match(r"^\s+-\s+(.+)", line)
        if list_match and current_key:
            if not isinstance(fm.get(current_key), list):
                fm[current_key] = []
            fm[current_key].append(list_match.group(1).strip())
            continue
        kv_match = re.match(r"^(\S+):\s*(.*)", line)
        if kv_match:
            current_key = kv_match.group(1)
            val = kv_match.group(2).strip()
            if val and val != "|":
                fm[current_key] = val
    return fm


def extract_first_bash_block(filepath):
    """Extract the first ```bash ... ``` code block from a markdown file."""
    content = read_file(filepath)
    match = re.search(r"```bash\n(.*?)```", content, re.DOTALL)
    return match.group(1) if match else None


def extract_python_from_bash(bash_script):
    """Extract the python3 -c inline script from a bash block."""
    if not bash_script:
        return None
    # Match python3 -c "..." with the script spanning to the closing quote + args
    match = re.search(
        r'python3 -c "\n(.*?)"\s+"\$DOCS_ROOT"\s+"\$API_ROOT"',
        bash_script,
        re.DOTALL,
    )
    return match.group(1) if match else None


def count_test_headings(filepath):
    """Count ## Test N headings in TESTS.md."""
    content = read_file(filepath)
    return len(re.findall(r"^## Test \d+", content, re.MULTILINE))


def find_spec_files():
    """Find all .md files under specifications/."""
    specs = []
    for dirpath, _, filenames in os.walk(SPEC_ROOT):
        for f in sorted(filenames):
            if f.endswith(".md"):
                specs.append(os.path.join(dirpath, f))
    return sorted(specs)


def find_all_doc_files():
    """Find all .md files under the docs root."""
    docs = []
    for dirpath, _, filenames in os.walk(DOCS_ROOT):
        for f in sorted(filenames):
            if f.endswith(".md"):
                docs.append(os.path.join(dirpath, f))
    return docs
