# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The README logo is visible on GitHub's light and dark themes.

An SVG path with no fill is black, and vanishes on a dark page. The
logo sets its own fills and switches them under
``prefers-color-scheme: dark``.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGO = (ROOT / "docs" / "logo.svg").read_text(encoding="utf-8")
FILL = r"path\s*\{\s*fill:\s*#[0-9a-fA-F]{3,6}"


def test_the_logo_sets_a_fill_for_light_and_for_dark() -> None:
    style = re.search(r"<style>(.*?)</style>", LOGO, re.S)
    assert style, "no <style>: paths default to black"
    css = style.group(1)
    light, _, dark = css.partition("@media (prefers-color-scheme: dark)")
    assert re.search(FILL, light), "no light fill"
    assert re.search(FILL, dark), "no dark-mode fill"


def test_no_path_overrides_the_themed_fill() -> None:
    attribute = re.search(r"<path[^>]*\sfill=", LOGO)
    assert not attribute, "a fill attribute beats the stylesheet"
