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


def load_rules(text: str) -> list[Rule]:
    """Parse bounded YAML; first matching rule wins, default is ACCP."""
    if len(text.encode()) > 65536:
        raise ValueError("Rules exceed 64 KiB")
    try:
        for token in yaml.scan(text):
            if isinstance(
                token, (yaml.AliasToken, yaml.AnchorToken, yaml.TagToken)
            ):
                raise ValueError("YAML references and tags are not supported")
        parsed = yaml.safe_load(text)
    except (yaml.YAMLError, RecursionError) as exc:
        raise ValueError("Invalid rules YAML") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"rules"}:
        raise ValueError("Expected a rules list")
    entries = parsed["rules"]
    if not isinstance(entries, list) or len(entries) > 64:
        raise ValueError("Expected at most 64 rules")
    rules = []
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not {"if", "reaction"} <= set(entry)
            or set(entry) - {"if", "reaction", "reason_code", "reason"}
        ):
            raise ValueError("Invalid rule fields")
        condition = entry["if"]
        if (
            not isinstance(condition, str)
            or len(condition) > 256
            or not (
                _AMOUNT.fullmatch(condition) or _COUNTRY.fullmatch(condition)
            )
        ):
            raise ValueError(
                "Use a total_amount comparison or any_iban_country equality"
            )
        reaction = entry["reaction"]
        if reaction not in ("reject", "pending"):
            raise ValueError("Reaction must be reject or pending")
        reason_code = entry.get("reason_code", "NARR")
        reason = entry.get("reason", "Matched mockbank policy")
        if not isinstance(reason_code, str) or not re.fullmatch(
            r"[A-Z0-9]{4}", reason_code
        ):
            raise ValueError(
                "Reason code must contain four uppercase letters or digits"
            )
        if not isinstance(reason, str) or not 1 <= len(reason) <= 105:
            raise ValueError("Reason must contain 1–105 characters")
        rules.append(
            Rule(
                condition,
                "RJCT" if reaction == "reject" else "PDNG",
                reason_code,
                reason,
            )
        )
    return rules
