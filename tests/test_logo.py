# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The README logo is visible on GitHub's light and dark themes.

An SVG path with no fill is black, and vanishes on a dark page. The
logo sets its own fills and switches them under
``prefers-color-scheme: dark``.
"""

from __future__ import annotations

import re
from pathlib import Path

LOGO = (Path(__file__).resolve().parents[1] / "docs" / "logo.svg").read_text(encoding="utf-8")


def test_the_logo_sets_a_fill_for_light_and_for_dark() -> None:
    style = re.search(r"<style>(.*?)</style>", LOGO, re.S)
    assert style, "no <style>: paths default to black"
    light, _, dark = style.group(1).partition("@media (prefers-color-scheme: dark)")
    assert re.search(r"path\s*\{\s*fill:\s*#[0-9a-fA-F]{3,6}", light), "no light fill"
    assert re.search(r"path\s*\{\s*fill:\s*#[0-9a-fA-F]{3,6}", dark), "no dark-mode fill"


def test_no_path_overrides_the_themed_fill() -> None:
    assert not re.search(r"<path[^>]*\sfill=", LOGO), "a fill attribute beats the stylesheet"
