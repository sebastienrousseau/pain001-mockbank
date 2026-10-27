<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

## [0.0.1] - Unreleased

- Document the public development image and distinguish it from a release.

- Add authenticated SFTP with configurable inbox and outbox paths.
- Build matching ACCP, RJCT and PDNG pain.002 replies using core pain001.
- Apply bounded YAML rejection rules without evaluating Python.
- Offer optional REST history and a locally verified container image.
- Publish amd64 and arm64 development images to GHCR after CI gates pass,
  with explicit maintainer authorization for recurring publication.
- Floor the dev group's `certifi` at 2026.10.19 (PYSEC-2026-4320) and
  `filelock` at 4.2.1 (GHSA-9vhv-jxww-xfm5, GHSA-567q-5qvw-pf92,
  GHSA-v4x8-3wr5-3wq8); pip-audit installs only on Python 3.11+, and
  `make sec` says it skips pip-audit on 3.10.

This initial development iteration is not a tagged release.
