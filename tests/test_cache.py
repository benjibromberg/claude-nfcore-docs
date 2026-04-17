"""Test docs cache structure at ~/.cache/nfcore-docs/."""

import os
import pytest
from tests.conftest import (
    CACHE_DIR,
    CACHE_EXISTS,
    DOCS_ROOT,
    SPEC_ROOT,
    find_spec_files,
    find_all_doc_files,
    read_file,
)

pytestmark = pytest.mark.skipif(
    not CACHE_EXISTS,
    reason="Docs cache not found at ~/.cache/nfcore-docs/ — run /nfcore-docs once to create it",
)

EXPECTED_SPEC_SUBDIRS = [
    "components/modules",
    "components/subworkflows",
    "pipelines/requirements",
    "pipelines/recommendations",
    "reviews",
    "test-data",
]


def test_cache_dir_exists():
    assert os.path.isdir(CACHE_DIR)


def test_cache_is_git_repo():
    assert os.path.isdir(os.path.join(CACHE_DIR, ".git"))


def test_sparse_checkout_configured():
    sparse_file = os.path.join(CACHE_DIR, ".git", "info", "sparse-checkout")
    assert os.path.isfile(sparse_file), "sparse-checkout file missing"
    content = read_file(sparse_file)
    assert "sites/docs/src/content/docs/" in content
    assert "sites/docs/src/content/api_reference/" in content


def test_docs_root_exists():
    assert os.path.isdir(DOCS_ROOT)


def test_spec_files_exist():
    specs = find_spec_files()
    assert len(specs) >= 50, f"Expected 50+ spec files, got {len(specs)}"


def test_total_doc_files():
    docs = find_all_doc_files()
    assert len(docs) >= 150, f"Expected 150+ doc files, got {len(docs)}"


def test_spec_subdirectories():
    for subdir in EXPECTED_SPEC_SUBDIRS:
        path = os.path.join(SPEC_ROOT, subdir)
        assert os.path.isdir(path), f"Missing spec subdirectory: {subdir}"


def test_spec_files_have_frontmatter():
    for spec in find_spec_files():
        content = read_file(spec)
        assert content.startswith("---"), (
            f"Spec file missing frontmatter: {os.path.relpath(spec, SPEC_ROOT)}"
        )


def test_spec_files_have_titles():
    import re

    for spec in find_spec_files():
        content = read_file(spec)
        assert re.search(r"^title:", content, re.MULTILINE), (
            f"Spec file missing title: {os.path.relpath(spec, SPEC_ROOT)}"
        )
