#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fail when the release version is restated differently anywhere.

Single source of truth: ``version`` in ``pyproject.toml``. The same string
must appear as:

* ``__version__`` in ``pain001_mockbank/__init__.py``;
* a ``## [X.Y.Z]`` heading in ``CHANGELOG.md``;
* the "Version X.Y.Z, in lockstep" stability line in ``README.md``,
  rendered from ``scripts/render_readme.py``;
* the ``pain001 >=`` floor in ``pyproject.toml``.

The pain001 suite releases together at one version, core first, so the
floor on the core is this version: a lower one lets an older core, and
the older advisory floors it declares, resolve under this release.
mockbank sat at ``pain001 >= 0.0.70`` while the suite moved to 0.0.80.

Standard library only, so the workflow needs no install.

Usage: python3 scripts/verify_versions.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_INIT = "pain001_mockbank/__init__.py"

#: The pain001 floor as Poetry writes it: ``pain001 = ">=X.Y.Z,<1"``.
_FLOOR = re.compile(r'^pain001\s*=\s*"\s*>=\s*(\d+\.\d+\.\d+)', re.MULTILINE)


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def _read(root: Path, name: str) -> str:
    path = root / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def pyproject_version(root: Path) -> str:
    """The version ``pyproject.toml`` declares: the source of truth."""
    version = _search(
        r'^version\s*=\s*"([^"]+)"', _read(root, "pyproject.toml")
    )
    if version is None:
        raise SystemExit("pyproject.toml has no version field")
    return version


def _dunder(root: Path, expected: str) -> list[str]:
    pattern = r'^__version__\s*=\s*"([^"]+)"'
    found = _search(pattern, _read(root, PACKAGE_INIT))
    if found == expected:
        return []
    return [f"{PACKAGE_INIT}: __version__ is {found}"]


def _changelog(root: Path, expected: str) -> list[str]:
    text = _read(root, "CHANGELOG.md")
    if f"\n## [{expected}]" in f"\n{text}":
        return []
    return [f"CHANGELOG.md: no ## [{expected}] heading"]


def _readme(root: Path, expected: str) -> list[str]:
    pattern = r"Version (\d+\.\d+\.\d+), in lockstep"
    found = _search(pattern, _read(root, "README.md"))
    if found == expected:
        return []
    return [f"README.md: stability section names version {found}"]


def _pain001_floor(root: Path, expected: str) -> list[str]:
    floors = _FLOOR.findall(_read(root, "pyproject.toml"))
    if not floors:
        return ["pyproject.toml: no pain001>= floor"]
    return [
        f"pyproject.toml: pain001>={floor}, the suite is at {expected}"
        for floor in floors
        if floor != expected
    ]


def problems(root: Path = ROOT) -> list[str]:
    """Every restatement of the version that disagrees with pyproject."""
    expected = pyproject_version(root)
    checks = (_dunder, _changelog, _readme, _pain001_floor)
    return [problem for check in checks for problem in check(root, expected)]


def main() -> int:
    """Compare every restatement of the version and report."""
    expected = pyproject_version(ROOT)
    found = problems(ROOT)
    for problem in found:
        print(f"ERROR: {problem}")
    if found:
        return 1
    print(f"OK: every version source agrees on {expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
