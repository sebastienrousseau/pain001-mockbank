<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Agent invariants

Read CONTRIBUTING.md and DEVELOPMENT.md before editing. Use synthetic data
only. Never commit credentials, private keys or generated mailbox content.
Do not change core-generated XML by post-processing it. Keep resource limits
and pre-authentication host trust explicit. Version 0.0.1 changes only with a
maintainer decision, one step at a time. Work on the next feat/v0.0.N branch.
Run make check and make sec before push; coverage remains 100% line and branch.
Sign conventional commits with SSH and include the DCO signoff.
README.md is generated from the canonical layout and reviewed evidence in
docs/. Edit those sources and regenerate; do not edit output directly.
