<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="docs/logo.svg" alt="pain001-mockbank logo" width="128" />
</p>

<h1 align="center">pain001-mockbank</h1>

<p align="center">
  Accept synthetic pain.001 uploads over SFTP and return configurable pain.002 acknowledgements.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/pain001-mockbank/actions"><img src="https://github.com/sebastienrousseau/pain001-mockbank/workflows/ci/badge.svg?style=for-the-badge&logo=github" alt="Build" /></a>
  <a href="https://github.com/sebastienrousseau/pain001-mockbank/pkgs/container/pain001-mockbank"><img src="https://img.shields.io/badge/distribution-GHCR?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" /></a>
  <a href="docs/usage.md"><img src="https://img.shields.io/badge/docs-source-blue.svg?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/pain001-mockbank"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/pain001-mockbank?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" /></a>
  <a href="https://github.com/sebastienrousseau/pain001-mockbank/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.10%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.10 or newer" /></a>
</p>

---

## Contents

**Getting started**

- [Install](#install) — source checkout and locked dependencies
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — start a local synthetic bank

**The pain001-mockbank ecosystem**

- [The pain001-mockbank ecosystem](#the-pain001-mockbank-ecosystem) — core library and this companion

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use pain001-mockbank](#when-not-to-use-pain001-mockbank) — limitations
- [Development](#development) — make targets, fuzzing, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
git clone https://github.com/sebastienrousseau/pain001-mockbank.git
cd pain001-mockbank
poetry install --all-extras
```

Public development images are published for linux/amd64 and linux/arm64:

```sh
docker pull ghcr.io/sebastienrousseau/pain001-mockbank:edge
```

Use `sha-<full-commit-id>` for a commit-addressed development tag. `edge` moves
on main/feature pushes after checks. These are development images, not versioned
releases. See [container configuration](docs/usage.md); explicit host keys,
test credentials and mailbox storage are still required.

---

## Requirements

Python 3.10 or newer and Poetry. CI checks the floor and current Python on Linux. See [toolchain policy](docs/POLICIES.md).

---

## Quick Start

```sh
ssh-keygen -t ed25519 -N '' -f ./mock_host_key
# Set MOCKBANK_PASSWORD in your shell to a test-only secret first.
poetry run pain001-mockbank --host-key ./mock_host_key --username synthetic
```

The server listens on 127.0.0.1:2222. Upload synthetic XML into /inbox; read acknowledgements from /outbox. Compare the host key with the locally generated public key before connecting.

---

## The pain001-mockbank ecosystem

This companion builds on the core pain001 library without bundling a second payment engine.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [pain001](https://github.com/sebastienrousseau/pain001) | ISO 20022 generation and validation | Supply payment contracts and XML serialization |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Integration testing | SFTP upload, conditional ACCP/RJCT/PDNG replies and optional REST history | Implemented; test-gated |

---

## Ecosystem comparison

This is a focused companion, not an alternative payment engine.

| Project | Payment engine | Standalone bank | Synthetic tests |
| :--- | :---: | :---: | :---: |
| **pain001-mockbank** | Delegates to core | No | Yes |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

No throughput benchmark is claimed for this initial iteration.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| Throughput | Not measured | Not applicable |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

Authenticated SFTP, explicit host keys, exclusive uploads, bounded mailbox storage, deterministic rule selection and pain.002 serialization delegated to core.

---

## Configuration

Use --rules for a YAML policy, --root for mailbox storage, --inbox/--outbox for simple directory names, and --rest-port to enable optional local reply history. Run --help for the generated option reference.

---

## Examples

See [rules.yaml](examples/rules.yaml) and the [container guide](docs/usage.md).

---

## When not to use pain001-mockbank

Do not use for real payments, settlement simulation, production bank authentication, or mixed-currency total calculations. It is a test fixture, not a bank.

---

## Development

```bash
poetry install --all-extras
poetry run make check
```

Tests use synthetic records. README changes come from docs/readme-values.json and scripts/render_readme.py; CI rejects drift.

---

## Security

Use only synthetic data. Credentials and host keys are explicit; bind to loopback and do not expose the optional unauthenticated REST view publicly. YAML has no executable expressions, XML DTDs are refused, and uploads are limited to 8 MiB.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[User manual](docs/usage.md) · [API and contract reference](docs/usage.md) · [Developer guide](DEVELOPMENT.md) · [Family map](https://github.com/sebastienrousseau/pain001)

---

## Stability guarantees

Initial version 0.0.1. Maintainers open each next iteration explicitly, one 0.0.1 step at a time. Output changes and contract changes require review; no stable public API or deprecation window is promised yet. Toolchain-floor changes require a documented maintainer decision.

---

## License

Dual-licensed under [Apache-2.0](LICENSE-APACHE) OR [MIT](LICENSE-MIT), at your option. Dependencies retain their own licences.
