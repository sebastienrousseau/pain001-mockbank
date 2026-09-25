# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Render the portfolio's canonical README layout from reviewed evidence."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render() -> str:
    """Fill every canonical placeholder without changing the layout."""
    values = json.loads((ROOT / "docs/readme-values.json").read_text())
    project = values["PROJECT_NAME"]
    repo = f"https://github.com/sebastienrousseau/{project}"
    defaults = {
        "PROJECT_NAME_LOWER": project,
        "REPO_URL": repo,
        "REPO_DOMAIN_AND_PATH": f"github.com/sebastienrousseau/{project}",
        "LICENSE_SPDX": "Apache-2.0 OR MIT",
        "LICENSE_URL_ENCODED": "Apache--2.0%20OR%20MIT",
        "LOGO_URL": "docs/logo.svg",
        "REGISTRY_URL": repo,
        "REGISTRY_BADGE_IMAGE": "https://img.shields.io/badge/distribution-source%20only",
        "API_DOCS_URL": "docs/usage.md",
        "API_DOCS_BADGE_IMAGE": "https://img.shields.io/badge/docs-source-blue.svg",
        "ECOSYSTEM_LOGO": "python",
        "DOCS_LOGO": "readthedocs",
        "MIN_TOOLCHAIN_BADGE_LABEL": "Python-3.10%2B",
        "MIN_TOOLCHAIN_TEXT": "Python 3.10 or newer",
        "ECOSYSTEM_NAME": "Python",
        "ECOSYSTEM_MANIFEST_LANG": "sh",
        "QUICK_START_LANG": "sh",
        "INSTALL_METHODS_SUMMARY": "source checkout and locked dependencies",
        "INSTALL_LIBRARY_SNIPPET": (
            f"git clone {repo}.git\ncd {project}\npoetry install --all-extras"
        ),
        "ADDITIONAL_INSTALL_METHODS": (
            "No PyPI release has been published for this initial iteration."
        ),
        "REQUIREMENTS_CONTENT": (
            "Python 3.10 or newer and Poetry. CI checks the floor and current "
            "Python on Linux. See [toolchain policy](docs/POLICIES.md)."
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
            "poetry install --all-extras\npoetry run make check"
        ),
        "DEVELOPMENT_CONTENT": (
            "Tests use synthetic records. README changes come from "
            "docs/readme-values.json and scripts/render_readme.py; "
            "CI rejects drift."
        ),
        "DOCUMENTATION_INDEX": (
            "[User manual](docs/usage.md) · "
            "[API and contract reference](docs/usage.md) · "
            "[Developer guide](DEVELOPMENT.md) · "
            "[Family map](https://github.com/sebastienrousseau/pain001)"
        ),
        "STABILITY_CONTENT": (
            "Initial version 0.0.1. Maintainers open each next iteration "
            "explicitly, one 0.0.1 step at a time. Output changes and "
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
    defaults.update(values)
    template = (ROOT / "docs/readme-template.md").read_text()
    return re.sub(
        r"\{\{([A-Z_]+)\}\}", lambda match: defaults[match[1]], template
    )


def main() -> None:
    """Write README.md or check that committed output is current."""
    rendered = render()
    target = ROOT / "README.md"
    if "--check" in sys.argv:
        if not target.exists() or target.read_text() != rendered:
            raise SystemExit(
                "README.md is stale: run scripts/render_readme.py"
            )
    else:
        target.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
