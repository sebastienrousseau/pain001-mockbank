<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Architecture

pain001-mockbank is a synthetic bank for integration tests. A client
uploads a pain.001 credit transfer or a pain.008 direct debit over SFTP;
the bank writes a pain.002 status report back to the outbox. It holds
no money, keeps no accounts and settles nothing. This page is the map
for contributors; [usage.md](usage.md) is the operator's guide.

## Modules

The package is three modules, each with one job.

| Module | Job | Public names |
| :--- | :--- | :--- |
| `pain001_mockbank/rules.py` | Parse the YAML rules file into `Rule` objects and evaluate them | `Rule`, `load_rules` |
| `pain001_mockbank/processor.py` | Parse one upload, choose a status, build the pain.002 | `make_reply`, `MAX_UPLOAD_BYTES` |
| `pain001_mockbank/server.py` | Mailboxes, SFTP, authentication, the optional REST view and the CLI | `Bank`, `PasswordServer`, `PaymentSFTP`, `start_server`, `rest_app`, `run`, `main` |

## Request flow

1. `main` parses the command line and `run` builds a `Bank` (inbox,
   outbox and archive directories under `--root`), reads the host key
   and the password from the environment variable named by
   `--password-env`, and calls `start_server`.
2. `start_server` starts an asyncssh listener that offers SFTP only:
   `PasswordServer` checks the one configured account with
   constant-time comparison, and SCP, shells and forwarding are off.
3. `PaymentSFTP` confines every path to the three flat mailbox
   directories. Writes are allowed only into the inbox, with exclusive
   creation, the 8 MiB limit and a 100-file quota. Links, directory
   creation and metadata changes are refused.
4. When an upload ending in `.xml` is closed, or a staged file is
   renamed to `.xml`, `Bank.publish` reads it and calls `make_reply`.
5. `make_reply` parses the XML with `defusedxml` (DTDs refused), reads
   the group message id, each payment block's id and each transaction's
   end-to-end id and instructed amount, and totals the amounts in one
   currency. The first matching `Rule` decides the status (RJCT or
   PDNG); with no match the status is ACCP.
6. The rows go to core pain001's `build_pain002_report`, which owns
   all XML serialization. The mock bank never edits the XML core
   returns.
7. `Bank.publish` writes the reply to `/outbox/<upload>.pain002.xml`
   with exclusive creation, so an earlier reply is never replaced, and
   keeps the last 100 replies in memory for `rest_app`.
8. A client may rename a collected reply from the outbox into the
   archive. No other rename across mailboxes is allowed.

## Boundaries

- **Core owns the payment model.** Message parsing here is structural:
  identifiers and amounts, not XSD or rulebook validation. pain.002
  generation is delegated to the core
  [`pain001`](https://github.com/sebastienrousseau/pain001) library, so
  the mock bank's replies change when core's builder changes. The
  dependency floor moves with each suite release.
- **The rules language is closed.** Two condition forms
  (`total_amount <op> <decimal>` and `any_iban_country == "XX"`), checked
  by regular expressions at load time. YAML anchors, aliases and tags
  are refused, and nothing is evaluated as Python.
- **Every resource is bounded.** Upload size, inbox and outbox file
  counts, in-memory history, rules file size and rule count all have
  fixed limits, listed in [usage.md](usage.md).
- **Trust is explicit.** The host key and the credentials are
  required arguments; there are no defaults to fall back to.
- **No SHA-1.** The listener removes SHA-1 key exchange, SHA-1 MACs
  and ssh-rsa signatures from asyncssh's defaults
  (`tests/test_crypto_floor.py`).

## Tests and fuzzing

`tests/test_mockbank.py` drives real SFTP sessions against a listener
on an ephemeral port and checks each reply's XML. `tests/test_lifecycle.py`
covers the CLI and shutdown. `tests/test_examples.py` runs the README
Quick Start and `examples/`. `fuzz/fuzz_mockbank.py` fuzzes `make_reply`
and `load_rules` with Atheris; `tests/test_fuzz_harness.py` replays its
corpus on every test run. [DEVELOPMENT.md](../DEVELOPMENT.md) lists
every gate.
