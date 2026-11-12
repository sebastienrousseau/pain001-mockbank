<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

## [Unreleased]

### Added

- The README's Security section names the project's
  [OpenSSF Best Practices passing badge](https://www.bestpractices.dev/projects/16559),
  meeting the OpenSSF Best Practices silver criterion
  `documentation_achievements`.

### Changed

- Suite Consistency no longer runs on another workflow's completion
  (`workflow_run`). It audits the family daily and on dispatch, as the
  core's does, since that trigger runs with the default branch's trust
  whatever started it. Regenerated from pain001's
  `scripts/render_ecosystem_workflows.py`.
- The SFTP listener no longer negotiates SHA-1: SHA-1 key exchange
  (diffie-hellman-group14-sha1 and its GSS form), SHA-1 MACs and ssh-rsa
  signatures, for the host key and for client keys, are removed from
  asyncssh's defaults. A client that offers only those is refused;
  OpenSSH, paramiko and asyncssh clients negotiate SHA-2 as before.

### Fixed

- Suite Consistency pins the core's ecosystem check at `febcd0a`, which
  accepts the five pain001 SDK repositories as known members not yet
  released. From the 0.0.86 release until this change every scheduled
  run failed on them as undeclared repositories.

## [0.0.86] - 2026-11-11

### Added

- Run the README Quick Start in the test suite (generate the host key,
  start the server, upload over SFTP, read the pain.002) and add
  `examples/upload_and_collect.py`, an in-process SFTP walkthrough
  that the suite runs and `make lint` checks.
- `make versions` also checks the `version` in `CITATION.cff`.
- Complete the repository layout: `GOVERNANCE.md`, `SUPPORT.md`,
  `KEYS.asc` (the SSH allowed-signers file that verifies commits and
  tags), `docs/ARCHITECTURE.md`, `.editorconfig`,
  `.pre-commit-config.yaml` and a dev container that runs `make check`.
  `DEVELOPMENT.md` now reproduces every CI gate locally and describes
  the test layout and release model.
- Spell-check the tree with codespell 2.4.1 (hash-pinned in
  `requirements/docs-lint.txt`) in the docs-lint workflow.
- Add issue forms, a pull request template, CITATION.cff and a
  markdownlint CI job (`docs-lint.yml`, configured in
  `.markdownlint-cli2.jsonc`).

### Changed

- Release 0.0.86 in lockstep with the pain001 suite and require core
  pain001 0.0.86; the locks resolve its published artifacts.
- `pain001-mockbank --help` describes every option and its default; a
  test fails on an option without help text. `make lint` holds the
  package and examples to ruff's pydocstyle rules (Google convention),
  which added the three missing `__init__` docstrings. The demo is
  re-rendered with the new help.
- The README follows the portfolio template exactly: a demo
  (`.github/demo.gif`, rendered from `.github/demo.tape` by `make demo`)
  under the badges, the template's Build badge, an Examples section
  naming the runnable example, and the Documentation links pointing at
  the architecture page. `render_readme.py --check` (in `make docs`)
  now also fails on a heading out of the template's order or an
  unresolved `{{...}}` token.
- `SECURITY.md` follows the suite's layout: reporting channels, the
  suite's response goals, threat model and hardening. The code of
  conduct is the suite's shared Contributor Covenant text.
- `load_rules` validates each rule through one small function per
  check, so it is within every complexity ceiling and
  `complexity-baseline.json` is empty. The checks, their order and
  their messages are unchanged; `tests/test_rules.py` pins them.
- The README logo and demo are absolute
  `raw.githubusercontent.com` URLs on `main`, as the portfolio template
  now requires, so they render where relative paths do not resolve
  (PyPI and other registries). `render_readme.py` builds the logo URL
  from the project name, and a test fails on any relative README image.
- `make sec` (run by the CI check job) also audits each hash-pinned
  `requirements/*.txt` with pip-audit, not only the `poetry.lock`
  environment: the Poetry, Atheris and codespell pins the image build
  and the fuzz and docs-lint jobs install were never audited.

### Fixed

- Answer each payment block with one `OrgnlPmtInfAndSts` holding all of
  its transactions. 0.0.85 wrote one block per transaction, each
  repeating the block's id. Needs core pain001 0.0.86, whose pain.002
  builder takes a `transactions` list, and the floor is now 0.0.86.

## [0.0.85] - 2026-11-10

### Added

- Answer pain.008 direct debits with a pain.002, as pain.001 credit
  transfers are answered.
- Add an `/archive` mailbox (`--archive`): a collected reply can be
  renamed from `/outbox` into it, for example by
  `pain001 download --after-fetch move:/archive`. No other rename across
  mailboxes is allowed, and nothing is overwritten.

### Changed

- Release 0.0.85 in lockstep with the pain001 suite and require core
  pain001 0.0.85; the locks resolve its published artifacts.
- `make_reply` is split into parsing, amount and row helpers, which takes
  it under the complexity ceilings and out of the baseline.

## [0.0.84] - 2026-11-09

### Added

- Audit all nine suite repositories and their publication channels daily and after publishing workflows, using the shared checker pinned to a core commit.

### Changed

- Release 0.0.84 with the suite and require core pain001 0.0.84. Regenerate dependency locks from the published core artifacts.


### Fixed

- Include the declared licence files and README in the container build context before package installation.

- Include the generated README as the wheel and source distribution description, with its Markdown content type.

- Emit the existing Apache-2.0 OR MIT licence as a PEP 639 expression. Remove the erroneous proprietary classifier produced by legacy Poetry metadata.

## [0.0.83] - 2026-11-09

- Require `pain001 >= 0.0.83, < 1`, the suite's lockstep floor;
  `poetry.lock` moves pain001 from 0.0.82 to 0.0.83. The pain.002
  builder the mock bank calls is unchanged in the core; its 0.0.83
  changes are to XML signing and signature verification.

## [0.0.82] - 2026-11-09

- Include the README, documentation sources, changelog and release notes in
  the source distribution.
- Require `pain001 >= 0.0.82, < 1`, the suite's lockstep floor;
  `poetry.lock` moves pain001 from 0.0.81 to 0.0.82. The pain.002
  builder the mock bank calls is unchanged in the core.
- Point the README's Build badge at this repository's CI workflow;
  shields.io answered "repo or workflow not found" because the badge
  named a domain-and-path instead of `owner/repo`.
- Show the README logo on GitHub's dark theme, and restyle the logo
  and badge row.

## [0.0.81] - 2026-11-08

- Install the image build's Poetry from a hash-pinned tree
  (`requirements/poetry.txt`), as OpenSSF Scorecard's
  Pinned-Dependencies check requires.
- Fuzz the upload and rules parsers with Atheris (`fuzz/`, a Fuzz
  workflow: two minutes on every change, thirty weekly), and replay the
  seed corpus through the harness in the test suite.
- Link the private advisory form and the suite security policy from
  `SECURITY.md`.
- Release in lockstep with the suite: a `v*.*.*` tag builds, attests and
  signs the sdist and wheel, pushes
  `ghcr.io/sebastienrousseau/pain001-mockbank:<version>` (amd64 and arm64,
  provenance and SBOM, signed by digest, never overwritten) and writes the
  release page in the suite's shape with the vendored
  `scripts/release_notes.py`.
- Document the public development image and distinguish it from a release.

- Add authenticated SFTP with configurable inbox and outbox paths.
- Build matching ACCP, RJCT and PDNG pain.002 replies using core pain001.
- Apply bounded YAML rejection rules without evaluating Python.
- Offer optional REST history and a locally verified container image.
- Publish amd64 and arm64 development images to GHCR after CI gates pass,
  with explicit maintainer authorization for recurring publication.
- Floor the dev group's `certifi` at 2026.10.19 (PYSEC-2026-4320) and
  `filelock` at 4.2.1 (GHSA-9vhv-jxww-xfm5, GHSA-567q-5qvw-pf92,
  GHSA-v4x8-3wr5-3wq8).
- Require `pain001 >= 0.0.81, < 1`, the suite's lockstep floor;
  `poetry.lock` moves pain001 from 0.0.74 to 0.0.81. Dependabot no
  longer proposes pain001 bumps: the floor moves with each release.
- Check that every restatement of the version (pyproject, `__version__`,
  CHANGELOG, README) and the pain001 floor agree: `make versions`, run
  by `make check` and by a `Version sources agree` workflow.
- Check daily that the published pain001 suite agrees on one version
  (`scripts/check_suite_consistency.py`, the family's script, and a
  `Suite Consistency` workflow).
- Score the supply chain with OpenSSF Scorecard weekly and on pushes to
  main, publishing results for the badge and uploading SARIF to code
  scanning, with every action pinned by commit SHA.
- Check that every pull-request commit carries a `Signed-off-by` trailer
  (DCO workflow, with the certificate text in `DCO.txt`).
- Hold every function to the suite's complexity ceilings (cyclomatic
  10, cognitive 15, Halstead difficulty 30, 60 lines; 500 per file)
  with `make complexity`, against a committed baseline that may only
  shrink. Two existing offenders are recorded: `make_reply` and
  `load_rules`.
- Require Python 3.11 or newer, as the rest of the pain001 suite does;
  CI runs 3.11, 3.12, 3.13 and 3.14, and `make sec` runs pip-audit on
  every one of them.

pain001-mockbank was never tagged at 0.0.1, so, as a member of the
pain001 suite, its first release ships at the family's version, 0.0.81.
