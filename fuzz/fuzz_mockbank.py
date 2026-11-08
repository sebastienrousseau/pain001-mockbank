# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Coverage-guided fuzzing of the mock bank's two parsers with Atheris.

The contract: ``load_rules`` returns rules or raises ``ValueError``, and
``make_reply`` returns a pain.002 document or raises ``ValueError`` (or
``ParseError`` for malformed XML). The SFTP server turns each refusal
into a protocol error, so any other exception, or a reply that
is not a pain.002 Document, is a crash that libFuzzer reports.

An input that starts with ``<`` is an uploaded payment, answered under
the example rules; one that starts with ``rules`` is a rules file. Both
kinds sit in ``fuzz/corpus/`` as seeds. Any other input is split into a
rules file and a payment.

Run (Linux x86_64)::

    pip install --require-hashes -r requirements/poetry.txt
    poetry install --only main --all-extras
    poetry run pip install --require-hashes -r requirements/fuzz.txt
    poetry run python fuzz/fuzz_mockbank.py fuzz/corpus -max_total_time=60

``tests/test_fuzz_harness.py`` replays the corpus through
``test_one_input`` without Atheris, so the harness stays runnable.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from xml.etree.ElementTree import ParseError  # nosec B405 - exception only

try:
    import atheris
except ImportError:  # the corpus replay in the test suite needs no Atheris
    atheris = None

_instrument = (
    atheris.instrument_imports() if atheris else contextlib.nullcontext()
)
with _instrument:
    from defusedxml.ElementTree import fromstring

    from pain001_mockbank.processor import make_reply
    from pain001_mockbank.rules import Rule, load_rules

EXAMPLE_RULES = load_rules(
    (Path(__file__).parent / "corpus" / "rules-example.yaml").read_text(
        encoding="utf-8"
    )
)
PAIN002 = "{urn:iso:std:iso:20022:tech:xsd:pain.002.001."


def _rules(text: str) -> list[Rule] | None:
    try:
        rules = load_rules(text)
    except ValueError:
        return None
    if not all(isinstance(rule, Rule) for rule in rules):
        raise AssertionError("load_rules returned a non-rule")
    return rules


def _reply(payload: bytes, rules: list[Rule]) -> None:
    try:
        reply = make_reply(payload, rules)
    except (ValueError, ParseError):
        return
    root = fromstring(reply.encode("utf-8"))
    if not (root.tag.startswith(PAIN002) and root.tag.endswith("}Document")):
        raise AssertionError(f"reply is not a pain.002 Document: {root.tag}")


def _split(data: bytes) -> tuple[str, bytes]:
    if atheris is None:
        cut = data.find(b"\0")
        cut = len(data) if cut < 0 else cut
        return data[:cut].decode("utf-8", "replace"), data[cut + 1 :]
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 512))
    return text, fdp.ConsumeBytes(fdp.remaining_bytes())


def test_one_input(data: bytes) -> None:
    """Run one input and hold the result to the contract."""
    if data[:1] == b"<":
        _reply(data, EXAMPLE_RULES)
        return
    if data[:5] == b"rules":
        _rules(data.decode("utf-8", "replace"))
        return
    text, payload = _split(data)
    rules = _rules(text)
    _reply(payload, EXAMPLE_RULES if rules is None else rules)


def main() -> None:
    """Hand the harness to libFuzzer."""
    if atheris is None:
        raise SystemExit("atheris is not installed: see the module docstring")
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
