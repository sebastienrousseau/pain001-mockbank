<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Security Policy

## Supported versions

Security fixes land on the latest published release. Older 0.0.x
releases do not receive them; upgrade to the latest release, which
ships in lockstep with the core
[`pain001`](https://github.com/sebastienrousseau/pain001) library.

## Reporting a vulnerability

**Do not open a public issue for security reports.**

Use one of the following private channels, in this order of
preference:

1. **GitHub Private Vulnerability Reporting**
   <https://github.com/sebastienrousseau/pain001-mockbank/security/advisories/new>
   (the maintainers are notified automatically; do this first)
2. **Email**: `security@pain001.com`, or the maintainer's address in
   `pyproject.toml`

Please include:

1. Description of the vulnerability and its potential impact
2. Steps to reproduce (preferably a failing test case), with synthetic
   data only: no real payment data or credentials
3. The version affected
   (`python -c "import pain001_mockbank; print(pain001_mockbank.__version__)"`,
   or the image tag or digest)
4. Suggested fix (if available)

These are goals, not guarantees: the pain001 suite is maintained in a
personal capacity, with no SLA and no out-of-hours cover.

**Acknowledgement**: the goal is within 5 working days.
**Triage**: a severity assessment and remediation plan after
acknowledgement.
**Fix windows** (best effort): critical 7 days, high 30 days, medium 60
days, low best-effort. The clock starts at triage, not at report.

Published advisories are listed at
<https://github.com/sebastienrousseau/pain001-mockbank/security/advisories>.
This package also follows the
[`pain001` security policy](https://github.com/sebastienrousseau/pain001/blob/main/SECURITY.md).

## Threat model

pain001-mockbank is a synthetic test fixture, not a production security
boundary. It listens for SFTP on `127.0.0.1:2222` by default and, with
the `rest` extra and `--rest-port`, serves an unauthenticated read-only
REST view of recent replies. Do not expose either listener publicly.
The security surface is:

- **Uploaded XML** from any authenticated SFTP client, parsed to build a
  reply.
- **The rules file**, YAML read at start-up.
- **SFTP path handling**: every client path must stay inside the three
  mailbox directories.

## Hardening

- **XML**: parsed with `defusedxml`; DTDs and entities are refused.
  Uploads are limited to 8 MiB.
- **Rules**: YAML anchors, aliases and tags are refused, the file is
  limited to 64 KiB and 64 rules, and the two condition forms are
  matched by regular expressions; nothing is evaluated as Python.
- **Authentication**: one explicitly configured account, compared in
  constant time; the password comes from an environment variable and is
  never logged. The host key is a required argument.
- **SFTP only**: no shell, SCP or port forwarding. Paths are confined to
  flat files in the inbox, outbox and archive; links, directory creation
  and metadata changes are refused; files are created exclusively and
  never overwritten.
- **Bounded resources**: 100 inbox files, 100 outbox files and 100
  in-memory replies.
- **Container**: the image runs as an unprivileged user from
  digest-pinned base images.

## Continuous integration

- `ci.yml` runs ruff, mypy, the complexity ceilings, pytest with the
  100% line and branch floor, bandit and pip-audit on Python 3.11 to
  3.14.
- `fuzz.yml` fuzzes the upload and rules parsers with Atheris on every
  change and weekly; the corpus is replayed by the test suite.
- `scorecard.yml` runs OpenSSF Scorecard and uploads its results to code
  scanning.
- Dependabot proposes weekly updates for pip dependencies, GitHub
  Actions and the Docker base image.

No independent security audit is claimed.
