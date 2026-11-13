# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Render the portfolio's canonical README layout from reviewed evidence.

``--check`` fails when the committed README differs from the rendering,
when its section headings leave the portfolio template's order
(``~/Code/README-TEMPLATE.md``, mirrored in ``docs/readme-template.md``),
or when a ``{{...}}`` token is left unresolved.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: The portfolio template's headings, in order. "{name}" is the project.
CANONICAL_HEADINGS = (
    "## Contents",
    "## Install",
    "### As a Python library",
    "## Requirements",
    "## Quick Start",
    "## The {name} ecosystem",
    "## Capabilities at a glance",
    "## Ecosystem comparison",
    "## Benchmarks",
    "## Features",
    "## Configuration",
    "## Examples",
    "## When not to use {name}",
    "## Development",
    "## Security",
    "## Documentation",
    "## Stability guarantees",
    "## License",
)

#: Placeholders that do not depend on the project name.
STATIC_DEFAULTS = {
    "LICENSE_SPDX": "Apache-2.0 OR MIT",
    "LICENSE_URL_ENCODED": "Apache--2.0%20OR%20MIT",
    "REGISTRY_BADGE_IMAGE": "https://img.shields.io/badge/distribution-source%20only",
    "API_DOCS_URL": "docs/usage.md",
    "API_DOCS_BADGE_IMAGE": "https://img.shields.io/badge/docs-source-blue.svg",
    "ECOSYSTEM_LOGO": "python",
    "DOCS_LOGO": "readthedocs",
    "MIN_TOOLCHAIN_BADGE_LABEL": "Python-3.11%2B",
    "MIN_TOOLCHAIN_TEXT": "Python 3.11 or newer",
    "ECOSYSTEM_NAME": "Python",
    "ECOSYSTEM_MANIFEST_LANG": "sh",
    "QUICK_START_LANG": "sh",
    "INSTALL_METHODS_SUMMARY": "source checkout and locked dependencies",
    "ADDITIONAL_INSTALL_METHODS": (
        "No PyPI release has been published for this initial iteration."
    ),
    "REQUIREMENTS_CONTENT": (
        "Python 3.11 or newer and Poetry. CI checks 3.11 to 3.15 "
        "on Linux. See [toolchain policy](docs/POLICIES.md)."
    ),
    "ECOSYSTEM_OVERVIEW": (
        "This companion builds on the core pain001 library without "
        "bundling a second payment engine."
    ),
    "ECOSYSTEM_CRATES_OR_MODULES_LIST": "core library and this companion",
    "COMPONENT_NAME": "[pain001](https://github.com/sebastienrousseau/pain001)",
    "COMPONENT_PURPOSE": "ISO 20022 generation and validation",
    "COMPONENT_USE_CASE": "Supply payment contracts and XML serialization",
    "CAPABILITY_STATUS": "Implemented; test-gated",
    "COMPARISON_DIMENSION_ONE": "Payment engine",
    "COMPARISON_DIMENSION_TWO": "Standalone bank",
    "COMPARISON_DIMENSION_THREE": "Synthetic tests",
    "PROJECT_COMPARISON_VALUE_ONE": "Delegates to core",
    "PROJECT_COMPARISON_VALUE_TWO": "No",
    "PROJECT_COMPARISON_VALUE_THREE": "Yes",
    "ECOSYSTEM_COMPARISON_SUMMARY": (
        "This is a focused companion, not an alternative payment engine."
    ),
    "BENCHMARK_SUMMARY": (
        "No throughput benchmark is claimed for this initial iteration."
    ),
    "BENCHMARK_SCENARIO": "Throughput",
    "BENCHMARK_RESULT": "Not measured",
    "BENCHMARK_ENVIRONMENT": "Not applicable",
    "DEVELOPMENT_COMMANDS": (
        "poetry install --all-extras\npoetry run make check\n"
        "poetry run make sec"
    ),
    "DEVELOPMENT_CONTENT": (
        "Coverage is gated at 100% line and branch, and the tests run "
        "the Quick Start and every example. Tests use synthetic records. "
        "README changes come from docs/readme-values.json and "
        "scripts/render_readme.py; CI rejects drift and any departure "
        "from the portfolio template. "
        "[DEVELOPMENT.md](DEVELOPMENT.md) reproduces every CI gate."
    ),
    "DOCUMENTATION_INDEX": (
        "[User manual](docs/usage.md) · "
        "[API and contract reference](docs/ARCHITECTURE.md) · "
        "[Developer guide](DEVELOPMENT.md) · "
        "[Family map](https://github.com/sebastienrousseau/pain001)"
    ),
    "STABILITY_CONTENT": (
        "Version {version}, in lockstep with the pain001 suite. "
        "Maintainers open each next iteration explicitly, one 0.0.1 "
        "step at a time. Output changes and "
        "contract changes require review; no stable public API or "
        "deprecation "
        "window is promised yet. Toolchain-floor changes require a "
        "documented maintainer decision."
    ),
    "LICENSE_CONTENT": (
        "Dual-licensed under [Apache-2.0](LICENSE-APACHE) OR "
        "[MIT](LICENSE-MIT), at your option. "
        "Dependencies retain their own licences."
    ),
}


def render() -> str:
    """Fill every canonical placeholder without changing the layout."""
    values = json.loads((ROOT / "docs/readme-values.json").read_text())
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"][
        "poetry"
    ]["version"]
    project = values["PROJECT_NAME"]
    repo = f"https://github.com/sebastienrousseau/{project}"
    defaults = {
        **STATIC_DEFAULTS,
        "STABILITY_CONTENT": STATIC_DEFAULTS["STABILITY_CONTENT"].format(
            version=version
        ),
        "PROJECT_NAME_LOWER": project,
        "REPO_URL": repo,
        "REPO_DOMAIN_AND_PATH": f"github.com/sebastienrousseau/{project}",
        # Shields wants owner/repo for a workflow badge, without the host.
        "REPO_SLUG": f"sebastienrousseau/{project}",
        # PyPI and other registries do not resolve relative image paths,
        # so the logo is served from the default branch.
        "LOGO_URL": (
            "https://raw.githubusercontent.com/"
            f"sebastienrousseau/{project}/main/docs/logo.svg"
        ),
        "REGISTRY_URL": repo,
        "INSTALL_LIBRARY_SNIPPET": (
            f"git clone {repo}.git\ncd {project}\npoetry install --all-extras"
        ),
    }
    defaults.update(values)
    template = (ROOT / "docs/readme-template.md").read_text()
    return re.sub(
        r"\{\{([A-Z_]+)\}\}", lambda match: defaults[match[1]], template
    )


def headings(text: str) -> list[str]:
    """Return the level-2 and level-3 headings outside code fences."""
    found, fenced = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{2,3} ", line):
            found.append(line.rstrip())
    return found


def structure_problems(text: str, name: str) -> list[str]:
    """Return every way text departs from the canonical README shape."""
    expected = [heading.format(name=name) for heading in CANONICAL_HEADINGS]
    problems = []
    actual = headings(text)
    if actual != expected:
        problems.append(
            "headings differ from the portfolio template:\n"
            f"  expected {expected}\n  found    {actual}"
        )
    tokens = sorted(set(re.findall(r"\{\{[^}]*\}\}", text)))
    if tokens:
        problems.append(f"unresolved template tokens: {tokens}")
    return problems


def main() -> None:
    """Write README.md or check that committed output is current."""
    rendered = render()
    target = ROOT / "README.md"
    if "--check" in sys.argv:
        if not target.exists() or target.read_text() != rendered:
            raise SystemExit(
                "README.md is stale: run scripts/render_readme.py"
            )
        name = json.loads((ROOT / "docs/readme-values.json").read_text())[
            "PROJECT_NAME"
        ]
        problems = structure_problems(rendered, name)
        if problems:
            raise SystemExit("README structure:\n" + "\n".join(problems))
    else:
        target.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
