# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The suite-consistency check reads the published suite from PyPI.

mockbank ships on GHCR, not PyPI, so the check never compares this tree
with a release of its own; it still reports a published member that is
behind the core, or one PyPI cannot answer for.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "check_suite_consistency.py"
)


@pytest.fixture
def checker() -> types.ModuleType:
    """The script, loaded as a module."""
    spec = importlib.util.spec_from_file_location("consistency", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(
    checker: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tree: str,
    published: dict[str, str],
) -> list[str]:
    monkeypatch.setattr(checker, "tree_version", lambda: tree)
    monkeypatch.setattr(checker, "published_version", published.get)
    problems, _ = checker.check()
    return problems


def _suite(core: str, lsp: str) -> dict[str, str]:
    versions = dict.fromkeys(
        (
            "pain001",
            "pain001-mcp",
            "pain001-loader-mt101",
            "pain001-loader-xlsx",
        ),
        core,
    )
    versions["pain001-lsp"] = lsp
    return versions


def test_this_package_is_named_from_pyproject(
    checker: types.ModuleType,
) -> None:
    assert checker.tree_name() == "pain001-mockbank"


def test_mockbank_is_not_looked_up_on_pypi(
    checker: types.ModuleType,
) -> None:
    assert "pain001-mockbank" not in checker.MEMBERS


def test_a_tree_ahead_of_the_suite_is_not_a_problem(
    checker: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Between releases this tree carries the next version first."""
    suite = _suite("0.0.80", "0.0.80")
    assert not _run(checker, monkeypatch, "0.0.81", suite)


def test_a_member_behind_the_core_is_reported(
    checker: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    problems = _run(checker, monkeypatch, "0.0.81", _suite("0.0.81", "0.0.80"))
    assert problems == [
        "pain001-lsp: published 0.0.80, but the suite is at 0.0.81"
    ]


def test_an_unreadable_member_is_reported(
    checker: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    published = _suite("0.0.80", "0.0.80")
    del published["pain001-mcp"]
    problems = _run(checker, monkeypatch, "0.0.80", published)
    assert problems == ["pain001-mcp: could not read PyPI"]
