<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Development

The single entry point for working on `pain001-mockbank`: how to set up
the toolchain, how to run every CI gate on your machine, where the
tests live, and how a release is made. [CONTRIBUTING.md](CONTRIBUTING.md)
covers the pull request workflow, [AGENTS.md](AGENTS.md) the invariants
that must not drift, and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
how the code fits together.

## Toolchain

- Python 3.11 or newer (CI tests 3.11, 3.12, 3.13, 3.14 and 3.15).
- [Poetry](https://python-poetry.org/docs/#installation) 2.4.1, the
  version CI installs. `poetry check --lock` runs in CI, so the lock
  must match `pyproject.toml`.
- `ssh-keygen` (OpenSSH), used by the Quick Start and its test.
- Node.js 22 for `npx markdownlint-cli2`.
- Docker, only to build the container image locally.
- Git with SSH commit signing and `git commit -s` (DCO, checked by
  `dco.yml`).

```bash
git clone git@github.com:sebastienrousseau/pain001-mockbank.git
cd pain001-mockbank
poetry install --all-extras
poetry run make check
poetry run make sec
```

Tests bind loopback sockets, so they need permission to listen on
`127.0.0.1`. They use synthetic data and ephemeral host keys, never a
bank endpoint.

The dev container (`.devcontainer/devcontainer.json`) does the same on
Python 3.12 with Node, and finishes by running `make check`.
`pre-commit install` (pre-commit from pipx or pip) enables the hooks in `.pre-commit-config.yaml`
(whitespace, YAML and TOML checks, codespell, ruff and mypy); CI stays
the authority.

## Running every CI gate locally

`make check` is the gate to run before every push. It runs, in order:
`lint` (ruff check and ruff format over the package, tests, scripts,
fuzz harness and examples, plus the pydocstyle rules on the package and
examples), `type` (mypy strict), `complexity`, `test`
(pytest with the 100% line and branch coverage floor), `docs` (the
README is current and follows the portfolio template) and `versions`
(every version restatement agrees). `make sec` runs bandit and
pip-audit, over the installed `poetry.lock` environment and each
hash-pinned `requirements/*.txt`.

| Workflow | Job | Local command |
| :--- | :--- | :--- |
| `ci.yml` | check (Python 3.11 to 3.15) | `poetry check --lock && poetry run make check && poetry run make sec` |
| `ci.yml` | container | `docker build -t pain001-mockbank:local-test .` |
| `docs-lint.yml` | codespell | `pip install --require-hashes -r requirements/docs-lint.txt && codespell` |
| `docs-lint.yml` | markdownlint | `npx markdownlint-cli2@0.23.3 "**/*.md"` |
| `versions.yml` | Version sources agree | `python3 scripts/verify_versions.py` |
| `fuzz.yml` | Atheris (Linux x86_64) | see the header of `fuzz/fuzz_mockbank.py` |
| `dco.yml` | Sign-off on every commit | `git log --format=%B origin/main..` shows a `Signed-off-by:` per commit |
| `suite-consistency.yml` | Ecosystem publication | GitHub only; reads the published registries |
| `scorecard.yml` | OpenSSF Scorecard | GitHub only |
| `release.yml` | Build, sign, image, release page | tag-triggered; maintainers only |

### Coverage

The floor is 100% of `pain001_mockbank/` lines and branches, set in
`pyproject.toml` (`--cov-branch --cov-fail-under=100`), so `make test`
fails below it on every Python version CI runs. Scripts, examples and
the fuzz harness are exercised by tests but are not part of the
measured package.

### Complexity

`scripts/check_complexity.py` holds every function in the package and
`scripts/` to cyclomatic 10, cognitive 15, Halstead difficulty 30 and
60 lines, and every file to 500 lines. Existing offenders are recorded
in `complexity-baseline.json`, which may only shrink:
`python3 scripts/check_complexity.py --update` rewrites it after an
improvement, never to absorb a regression.

## Test layout

- `tests/` holds every test; pytest finds them through `testpaths` in
  `pyproject.toml`.
- `test_mockbank.py`: reply building, rules, resource limits and real
  SFTP sessions against a listener on an ephemeral port.
- `test_lifecycle.py`: the command line, the REST mode and shutdown.
- `test_examples.py`: runs the README Quick Start commands (with a free
  port instead of 2222) and every example in `examples/`.
- `test_fuzz_harness.py`: replays `fuzz/corpus/` through the Atheris
  harness without Atheris, so the harness stays runnable.
- `test_check_complexity.py`, `test_verify_versions.py`,
  `test_release_notes.py`, `test_check_suite_consistency.py`,
  `test_readme_badges.py`, `test_render_readme.py` and `test_logo.py`
  cover the scripts and the generated README.

A bug fix comes with a test that failed before the fix.

## Documentation

- `docs/` is the only documentation root: `usage.md` (operator guide),
  `ARCHITECTURE.md`, `POLICIES.md` (toolchain and versioning policy),
  `COMPARISON.md` and `BENCHMARKS.md`. There is no rendered manual.
- `README.md` is rendered from `docs/readme-template.md` (the
  portfolio's canonical layout) and `docs/readme-values.json`: edit the
  values, then run `poetry run python scripts/render_readme.py`.
  `--check`, run by `make docs`, fails on drift, on a heading out of the
  template's order and on an unresolved `{{...}}` token.
- `.github/demo.gif`, the README demo, is rendered by `make demo` (needs
  [vhs](https://github.com/charmbracelet/vhs)) from `.github/demo.tape`.
  Re-render it in the same change when its output changes.
- Every public module, class, method and function in the package and
  the examples has a docstring: `make lint` runs ruff's pydocstyle rules
  (`D`, Google convention) over them. `pain001-mockbank --help` is the
  option reference; a test fails when an option has no help text.

## Release model

Versions stay on `0.0.x` and move one step at a time, in lockstep with
the core [`pain001`](https://github.com/sebastienrousseau/pain001)
library. The maintainer opens each release on a `feat/v<next-version>`
branch; all work for that version, including Dependabot updates, lands
there and reaches `main` through one pull request. The version lives in
`pyproject.toml`, `pain001_mockbank/__init__.py`, `CITATION.cff`, the
`CHANGELOG.md` heading and the README's stability section;
`make versions` checks that they agree with each other and with the
pain001 floor.

A signed `v<version>` tag runs `release.yml`: it builds, attests and
signs the sdist and wheel, pushes
`ghcr.io/sebastienrousseau/pain001-mockbank:<version>` (amd64 and arm64,
signed by digest, never overwritten) and writes the release page with
`scripts/release_notes.py`. The package is not published to PyPI.
Pushes to `main` and feature branches publish the `edge` and
`sha-<commit>` development images after the checks pass. Never rewrite
published history.
