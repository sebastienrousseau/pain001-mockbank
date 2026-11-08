# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The Atheris harness runs, and the fuzz corpus holds to its contract.

Atheris runs only on Linux x86_64 (.github/workflows/fuzz.yml); this
replays every seed and a few hostile inputs through ``test_one_input``
without it, so a change that breaks the harness or the contract fails
here first.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

FUZZ = Path(__file__).resolve().parents[1] / "fuzz"


def _harness() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "fuzz_mockbank", FUZZ / "fuzz_mockbank.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CORPUS = sorted((FUZZ / "corpus").iterdir())


def test_the_corpus_has_both_kinds_of_seed() -> None:
    starts = {path.read_bytes()[:1] for path in CORPUS}
    assert {b"<", b"r"} <= starts


@pytest.mark.parametrize("path", CORPUS, ids=[p.name for p in CORPUS])
def test_every_seed_meets_the_contract(path: Path) -> None:
    _harness().test_one_input(path.read_bytes())


@pytest.mark.parametrize(
    "data",
    [
        b"<",
        b"<Document",
        b'<!DOCTYPE x [<!ENTITY a "b">]><x>&a;</x>',
        b"rules: [&a {}, *a]",
        b"rules:\n- if: total_amount > 1\n  reaction: reject",
        b"\x00" + (FUZZ / "corpus" / "payment-accp.xml").read_bytes(),
        b"rules:\n- if: total_amount > 1\n  reaction: reject\x00<x/>",
        b"",
    ],
)
def test_hostile_inputs_are_refused_not_crashed(data: bytes) -> None:
    _harness().test_one_input(data)


def test_a_reply_that_is_not_pain002_is_a_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _harness()
    monkeypatch.setattr(harness, "make_reply", lambda *_: "<Document/>")
    with pytest.raises(AssertionError, match="not a pain.002"):
        harness.test_one_input(b"<x/>")


def test_an_unexpected_exception_is_a_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = _harness()

    def explode(*_: object) -> str:
        raise KeyError("boom")

    monkeypatch.setattr(harness, "make_reply", explode)
    with pytest.raises(KeyError):
        harness.test_one_input(b"<x/>")


def test_main_needs_atheris() -> None:
    harness = _harness()
    if harness.atheris is not None:
        pytest.skip("atheris is installed here")
    with pytest.raises(SystemExit, match="atheris is not installed"):
        harness.main()
