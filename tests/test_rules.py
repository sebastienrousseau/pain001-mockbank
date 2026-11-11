# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Characterise load_rules: every rejection message and every field kept.

These pin the observable contract of the rules loader (which check runs
first, the exact message each raises, and the Rule each entry becomes)
so its internal structure can change without changing what callers see.
"""

import re

import pytest
import yaml

from pain001_mockbank.rules import Rule, load_rules

_FIELDS = "Invalid rule fields"
_CONDITION = "Use a total_amount comparison or any_iban_country equality"
_REACTION = "Reaction must be reject or pending"
_CODE = "Reason code must contain four uppercase letters or digits"
_REASON = "Reason must contain 1–105 characters"
_RULE = "rules:\n- if: total_amount > 1\n  reaction: reject\n"


@pytest.mark.parametrize(
    "text,message",
    [
        ("x" * 65537, "Rules exceed 64 KiB"),
        ("é" * 32769, "Rules exceed 64 KiB"),
        ("[", "Invalid rules YAML"),
        ("a: [", "Invalid rules YAML"),
        ("rules: [!!str x]", "YAML references and tags are not supported"),
        ("rules: [&a {}, *a]", "YAML references and tags are not supported"),
        ("rules: [&a x]", "YAML references and tags are not supported"),
        ("{}", "Expected a rules list"),
        ("- 1", "Expected a rules list"),
        ("rules: []\nother: 1", "Expected a rules list"),
        ("rules: nope", "Expected at most 64 rules"),
        ("rules:\n" + "- 1\n" * 65, "Expected at most 64 rules"),
        ("rules:\n- 1", _FIELDS),
        ("rules:\n- if: x", _FIELDS),
        ("rules:\n- reaction: reject", _FIELDS),
        (_RULE + "  extra: 1", _FIELDS),
        ("rules:\n- if: true\n  reaction: reject", _CONDITION),
        ("rules:\n- if: 'open(1)'\n  reaction: reject", _CONDITION),
        (
            "rules:\n- if: total_amount > " + "1" * 300 + "\n  reaction: x",
            _CONDITION,
        ),
        ("rules:\n- if: 'open(1)'\n  reaction: execute", _CONDITION),
        ("rules:\n- if: total_amount > 1\n  reaction: execute", _REACTION),
        ("rules:\n- if: total_amount > 1\n  reaction: [reject]", _REACTION),
        (
            "rules:\n- if: total_amount > 1\n  reaction: execute\n"
            "  reason_code: bad",
            _REACTION,
        ),
        (_RULE + "  reason_code: bad", _CODE),
        (_RULE + "  reason_code: 1234", _CODE),
        (_RULE + "  reason_code: NARRX", _CODE),
        (_RULE + "  reason_code: bad\n  reason: ''", _CODE),
        (_RULE + "  reason: ''", _REASON),
        (_RULE + "  reason: 7", _REASON),
        (_RULE + "  reason: " + "r" * 106, _REASON),
        (_RULE + "- 1", _FIELDS),
    ],
)
def test_rejection_message(text, message):
    """Each invalid input fails on the first check it breaks, by message."""
    with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
        load_rules(text)


def test_yaml_errors_are_chained():
    """The YAML parser's error stays attached as the cause."""
    with pytest.raises(ValueError) as caught:
        load_rules("[")
    assert isinstance(caught.value.__cause__, yaml.YAMLError)


def test_loaded_rules_keep_order_and_fields():
    """Entries become Rules in file order, with defaults filled in."""
    text = (
        "rules:\n"
        "- if: total_amount >= 1_000.50\n"
        "  reaction: reject\n"
        "  reason_code: AM02\n"
        "  reason: " + "r" * 105 + "\n"
        "- if: any_iban_country == 'DE'\n"
        "  reaction: pending\n"
        "- if: total_amount < 5\n"
        "  reaction: reject\n"
        "  reason: x\n"
    )
    assert load_rules(text) == [
        Rule("total_amount >= 1_000.50", "RJCT", "AM02", "r" * 105),
        Rule(
            "any_iban_country == 'DE'",
            "PDNG",
            "NARR",
            "Matched mockbank policy",
        ),
        Rule("total_amount < 5", "RJCT", "NARR", "x"),
    ]


def test_limits_are_inclusive():
    """64 KiB of text and 64 rules are accepted, not rejected."""
    assert (
        len(
            load_rules(
                "rules:\n"
                + "- if: total_amount > 1\n  reaction: reject\n" * 64
            )
        )
        == 64
    )
    padded = "rules: []\n" + "#" * (65536 - len("rules: []\n"))
    assert load_rules(padded) == []
