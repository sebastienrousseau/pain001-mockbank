# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The README's Build badge names a workflow this repository has.

Shields reads ``workflow/status/<owner>/<repo>/<file>``. The template
once filled it from ``REPO_DOMAIN_AND_PATH`` (``github.com/owner/repo``,
right for the Scorecard badge), and shields answered "repo or workflow
not found". This checks the rendered README offline.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _badge(alt: str) -> str:
    match = re.search(rf'<img src="([^"]+)" alt="{alt}"', README)
    assert match, f"no {alt} badge"
    return match.group(1)


def test_the_build_badge_points_at_this_repositorys_ci_workflow() -> None:
    match = re.fullmatch(
        r"https://img\.shields\.io/github/actions/workflow/status/"
        r"([\w.-]+)/([\w.-]+)/([\w.-]+\.ya?ml)\?.*",
        _badge("Build"),
    )
    assert match, _badge("Build")
    owner, repo, workflow = match.groups()
    assert (owner, repo) == ("sebastienrousseau", "pain001-mockbank")
    assert (ROOT / ".github" / "workflows" / workflow).is_file()


def test_the_registry_badge_has_a_label_a_message_and_a_colour() -> None:
    match = re.match(
        r"https://img\.shields\.io/badge/([^-?]+)-([^-?]+)-([^-?]+)\?",
        _badge("Registry"),
    )
    assert match, _badge("Registry")
