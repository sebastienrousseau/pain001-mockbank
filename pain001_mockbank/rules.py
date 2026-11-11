# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Small declarative rejection language with no Python evaluation."""

from __future__ import annotations

import operator
import re
from dataclasses import dataclass
from decimal import Decimal

import yaml

_AMOUNT = re.compile(
    r"total_amount\s*(>=|<=|==|>|<)\s*([0-9](?:[0-9_]*[0-9])?(?:\.[0-9]{1,2})?)\Z"
)
_COUNTRY = re.compile(r"any_iban_country\s*==\s*[\"\']([A-Z]{2})[\"\']\Z")
_COMPARE = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
}


@dataclass(frozen=True)
class Rule:
    """A prevalidated condition and deterministic simulated bank reaction."""

    condition: str
    status: str
    reason_code: str
    reason: str

    def matches(self, total: Decimal, countries: set[str]) -> bool:
        """Evaluate only the two explicitly supported condition forms."""
        amount = _AMOUNT.fullmatch(self.condition)
        if amount:
            return bool(
                _COMPARE[amount[1]](total, Decimal(amount[2].replace("_", "")))
            )
        country = _COUNTRY.fullmatch(self.condition)
        if country is None:
            raise ValueError("Rule condition was not validated")
        return country[1] in countries


def _reject_references(text: str) -> None:
    """Refuse anchors, aliases and tags before the document is built."""
    for token in yaml.scan(text):
        if isinstance(
            token, (yaml.AliasToken, yaml.AnchorToken, yaml.TagToken)
        ):
            raise ValueError("YAML references and tags are not supported")


def _parse(text: str) -> object:
    """Parse at most 64 KiB of plain YAML with no references or tags."""
    if len(text.encode()) > 65536:
        raise ValueError("Rules exceed 64 KiB")
    try:
        _reject_references(text)
        return yaml.safe_load(text)
    except (yaml.YAMLError, RecursionError) as exc:
        raise ValueError("Invalid rules YAML") from exc


def _entries(parsed: object) -> list[object]:
    """Return the ``rules`` list of a document holding only that key."""
    if not isinstance(parsed, dict) or set(parsed) != {"rules"}:
        raise ValueError("Expected a rules list")
    entries = parsed["rules"]
    if not isinstance(entries, list) or len(entries) > 64:
        raise ValueError("Expected at most 64 rules")
    return entries


def _fields(entry: object) -> dict[str, object]:
    """Return ``entry`` when it has ``if`` and ``reaction`` and no extras."""
    if (
        not isinstance(entry, dict)
        or not {"if", "reaction"} <= set(entry)
        or set(entry) - {"if", "reaction", "reason_code", "reason"}
    ):
        raise ValueError("Invalid rule fields")
    return entry


def _condition(condition: object) -> str:
    """Accept only the two supported condition forms, up to 256 chars."""
    if (
        not isinstance(condition, str)
        or len(condition) > 256
        or not (_AMOUNT.fullmatch(condition) or _COUNTRY.fullmatch(condition))
    ):
        raise ValueError(
            "Use a total_amount comparison or any_iban_country equality"
        )
    return condition


def _status(reaction: object) -> str:
    """Map a reaction to its pain.002 status code."""
    if reaction not in ("reject", "pending"):
        raise ValueError("Reaction must be reject or pending")
    return "RJCT" if reaction == "reject" else "PDNG"


def _reason_code(reason_code: object) -> str:
    """Accept a four-character uppercase or digit reason code."""
    if not isinstance(reason_code, str) or not re.fullmatch(
        r"[A-Z0-9]{4}", reason_code
    ):
        raise ValueError(
            "Reason code must contain four uppercase letters or digits"
        )
    return reason_code


def _reason(reason: object) -> str:
    """Accept a reason of 1 to 105 characters."""
    if not isinstance(reason, str) or not 1 <= len(reason) <= 105:
        raise ValueError("Reason must contain 1–105 characters")
    return reason


def _rule(entry: object) -> Rule:
    """Validate one entry, check by check, and build its Rule."""
    fields = _fields(entry)
    return Rule(
        _condition(fields["if"]),
        _status(fields["reaction"]),
        _reason_code(fields.get("reason_code", "NARR")),
        _reason(fields.get("reason", "Matched mockbank policy")),
    )


def load_rules(text: str) -> list[Rule]:
    """Parse bounded YAML; first matching rule wins, default is ACCP."""
    return [_rule(entry) for entry in _entries(_parse(text))]
