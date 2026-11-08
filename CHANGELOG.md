<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

## [0.0.81]

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
- Require `pain001 >= 0.0.80, < 1`, the suite's lockstep floor;
  `poetry.lock` moves pain001 from 0.0.74 to 0.0.80. Dependabot no
  longer proposes pain001 bumps: the floor moves with each release.
- Check that every restatement of the version (pyproject, `__version__`,
  CHANGELOG, README) and the pain001 floor agree: `make versions`, run
  by `make check` and by a `Version sources agree` workflow.
- Require Python 3.11 or newer, as the rest of the pain001 suite does;
  CI runs 3.11, 3.12, 3.13 and 3.14, and `make sec` runs pip-audit on
  every one of them.

pain001-mockbank was never tagged at 0.0.1, so, as a member of the
pain001 suite, its first release ships at the family's version, 0.0.81.
