# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every restatement of the release version is checked; each drift fails.

The checks run on a small synthetic tree rather than this checkout, so
they test the script and not the state of the release: the checkout
itself is checked by ``make versions`` and the versions workflow. One
source at a time is moved off the version, so each check is seen to
catch its own drift.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.0.42"

TREE = {
    "pyproject.toml": (
        "[tool.poetry]\n"
        'name = "pain001-mockbank"\n'
        f'version = "{VERSION}"\n\n'
        "[tool.poetry.dependencies]\n"
        f'pain001 = ">={VERSION},<1"\n'
    ),
    "pain001_mockbank/__init__.py": f'__version__ = "{VERSION}"\n',
    "CHANGELOG.md": f"# Changelog\n\n## [{VERSION}]\n\n- Something.\n",
    "README.md": f"Version {VERSION}, in lockstep with the pain001 suite.\n",
}


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "verify_versions", ROOT / "scripts" / "verify_versions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A synthetic checkout whose every version source agrees."""
    for name, text in TREE.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return tmp_path


def _rewrite(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {path.name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_an_agreeing_tree_has_no_problems(tree: Path) -> None:
    assert _script().problems(tree) == []


def test_a_stale_dunder_version_fails(tree: Path) -> None:
    _rewrite(tree / "pain001_mockbank/__init__.py", VERSION, "0.0.1")
    assert _script().problems(tree) == [
        "pain001_mockbank/__init__.py: __version__ is 0.0.1"
    ]


def test_a_missing_changelog_heading_fails(tree: Path) -> None:
    _rewrite(tree / "CHANGELOG.md", f"## [{VERSION}]", "## [0.0.1]")
    assert _script().problems(tree) == [
        f"CHANGELOG.md: no ## [{VERSION}] heading"
    ]


def test_a_stale_readme_fails(tree: Path) -> None:
    _rewrite(tree / "README.md", VERSION, "0.0.1")
    assert _script().problems(tree) == [
        "README.md: stability section names version 0.0.1"
    ]


def test_a_pain001_floor_below_the_release_fails(tree: Path) -> None:
    """A floor below the suite lets an older core resolve."""
    _rewrite(tree / "pyproject.toml", f'">={VERSION},<1"', '">=0.0.70,<1"')
    assert _script().problems(tree) == [
        f"pyproject.toml: pain001>=0.0.70, the suite is at {VERSION}"
    ]


def test_a_missing_pain001_floor_fails(tree: Path) -> None:
    _rewrite(tree / "pyproject.toml", f'">={VERSION},<1"', '"*"')
    assert _script().problems(tree) == ["pyproject.toml: no pain001>= floor"]


def test_a_missing_pyproject_version_stops(tree: Path) -> None:
    _rewrite(tree / "pyproject.toml", f'version = "{VERSION}"\n', "")
    with pytest.raises(SystemExit, match="no version field"):
        _script().problems(tree)


def test_a_missing_file_reads_as_drift(tree: Path) -> None:
    (tree / "README.md").unlink()
    assert _script().problems(tree) == [
        "README.md: stability section names version None"
    ]


def test_main_reports_ok(
    tree: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script = _script()
    monkeypatch.setattr(script, "ROOT", tree)
    assert script.main() == 0
    assert (
        capsys.readouterr().out
        == f"OK: every version source agrees on {VERSION}\n"
    )


def test_main_reports_each_problem(
    tree: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    script = _script()
    monkeypatch.setattr(script, "ROOT", tree)
    _rewrite(tree / "README.md", VERSION, "0.0.1")
    assert script.main() == 1
    assert capsys.readouterr().out == (
        "ERROR: README.md: stability section names version 0.0.1\n"
    )
