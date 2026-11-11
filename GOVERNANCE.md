<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# pain001-mockbank Governance

This document describes how pain001-mockbank is run, how decisions are
made, and how to take on responsibility for it. It exists to make the
project legible and sustainable, and to reduce its dependence on any
single person.

## Mission and scope

pain001-mockbank is a synthetic bank for integration tests in the
[`pain001`](https://github.com/sebastienrousseau/pain001) suite. It
accepts pain.001 and pain.008 uploads over SFTP and answers them with
pain.002 status reports built by the core library. Changes are weighed
against that scope: a faithful, bounded test fixture, never a real bank,
a settlement simulator or a production endpoint.

## Roles

| Role | Who | Can |
| :--- | :--- | :--- |
| **Maintainer** | Sebastien Rousseau ([@sebastienrousseau](https://github.com/sebastienrousseau)), lead | Merge PRs, cut releases, triage, set direction |
| **Contributor** | Anyone with a merged PR | Propose changes, review, discuss |
| **User** | Everyone | File issues, ask questions, request features |

## Decision making

- **Day-to-day changes** (fixes, docs, tests, additive features within
  scope) proceed by **lazy consensus**: open a PR; if no maintainer
  objects and CI is green, a maintainer merges it.
- **Significant changes** (a new rule condition, a new message type, a
  change to the mailbox layout or the command line, a new dependency)
  need explicit approval from a maintainer in the PR, and should start
  as an issue.
- **Disagreement** is resolved by discussion aiming for consensus; if
  none is reached, the lead maintainer decides and records the
  rationale.

Every change must pass the full gate (`make check` and `make sec`: 100%
line and branch coverage, mypy strict, ruff, the complexity ceilings,
bandit and pip-audit) before merge, enforced in CI, not by trust.

## Releases

pain001-mockbank tracks
[`pain001`](https://github.com/sebastienrousseau/pain001) version for
version: when the suite releases `0.0.X`, this repository ships a
matching `0.0.X`. [DEVELOPMENT.md](DEVELOPMENT.md#release-model)
describes the tag-triggered pipeline. Only maintainers tag releases;
release authority rests with the lead maintainer.

## Becoming a maintainer

More maintainers is the single biggest thing that would de-risk the
project.

1. Contribute a few reviewed PRs in an area
   ([docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) is the map).
2. Help triage issues and review others' PRs.
3. Open an issue expressing interest.

A maintainer proposes you; with no objection from existing maintainers
within a week, you are added to the roles table for your area.

## Sustainability (bus factor)

pain001-mockbank today has **one** maintainer. The mitigations in
place:

- **The work is legible:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  maps the code and [DEVELOPMENT.md](DEVELOPMENT.md) reproduces every CI
  gate and describes the release pipeline.
- **Quality is enforced by CI,** not by one person's memory.
- **The goal is at least two maintainers** with independent release
  authority.

### Continuity plan

What happens to each piece of the project if the lead maintainer becomes
unavailable. Items marked **Not yet arranged** have no continuity
arrangement today; the plan is incomplete until they do.

| Asset | Today | Continuity |
| :--- | :--- | :--- |
| Signing keys | SSH keys listed in [`KEYS.asc`](KEYS.asc); commits and tags are signed with them | A new maintainer signs with their own key, added to `KEYS.asc` in a reviewed change; old releases stay verifiable because the file's history is kept. **Not yet arranged:** a documented key backup. |
| Container image `ghcr.io/sebastienrousseau/pain001-mockbank` | Published by `ci.yml` and `release.yml` under the lead maintainer's account | **Not yet arranged:** no second account can publish it. |
| GitHub repository | Owned by the lead maintainer's account | Transfer to an organisation or foundation with at least two owners, keeping redirects. **Not yet arranged:** no target account has been chosen. |
| Domain `pain001.com` (the security contact address) | Registered by the lead maintainer | **Not yet arranged:** no one else is named to renew or transfer it. |
| Releases and CI | Documented in `DEVELOPMENT.md` and run by GitHub Actions | Anyone with release rights can cut a release from the documented process. |
| The code | Apache-2.0 OR MIT, public history | Anyone can fork and continue it, with or without the project. |

### Review policy

A merge has no independent reviewer while there is one maintainer.
Agents need explicit authorization naming a particular pull request
before merging; green checks alone do not authorize a merge.

## Code of conduct and security

Participation is governed by
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Security issues follow the
private disclosure process in [`SECURITY.md`](SECURITY.md); do not open
public issues for vulnerabilities.
