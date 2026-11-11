<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Getting support

pain001-mockbank is a test fixture maintained in a personal capacity,
with no SLA. Here is where to go, by need.

## Questions and how-to

- **Read first:** the [README](README.md), the
  [operator guide](docs/usage.md), the runnable
  [`examples/`](examples/) and, for message-type background, the core
  [`pain001`](https://github.com/sebastienrousseau/pain001) repository.
- **Still stuck?** Open a
  [GitHub issue](https://github.com/sebastienrousseau/pain001-mockbank/issues/new/choose)
  (the pain001 suite does not use GitHub Discussions). Include your
  Python version, the `pain001-mockbank` version
  (`python -c "import pain001_mockbank; print(pain001_mockbank.__version__)"`)
  or image tag, your rules file, and a synthetic upload that reproduces
  the problem.

## Bugs

Open a bug report at
<https://github.com/sebastienrousseau/pain001-mockbank/issues/new/choose>
with a minimal reproducer: the command line, the rules file, the
uploaded XML (synthetic only) and the reply or SFTP error you got.

## Feature requests

Open a feature request at the same link. New rule conditions and
message types are weighed against the scope in
[GOVERNANCE.md](GOVERNANCE.md#mission-and-scope).

## Security

**Do not** open public issues for vulnerabilities. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## Contributing and maintaining

See [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Supported versions

Fixes land on the latest release line. See [SECURITY.md](SECURITY.md)
for the supported-version policy. pain001-mockbank requires Python 3.11
or newer.
