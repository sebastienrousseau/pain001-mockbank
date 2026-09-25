# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Parse synthetic pain.001 uploads and build matching pain.002 replies."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation
from xml.etree.ElementTree import (
    Element,  # nosec B405 - type only; defusedxml parses below
)

from defusedxml.ElementTree import fromstring
from pain001.pain002 import build_pain002_report

from pain001_mockbank.rules import Rule

MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def _text(parent: Element, path: str) -> str:
    """Require an explicit original identifier without inventing one."""
    value = parent.findtext(path)
    if not value or not 1 <= len(value) <= 35:
        raise ValueError("Missing or oversized payment identifier")
    return value


def make_reply(payload: bytes, rules: list[Rule]) -> str:
    """Return a group acknowledgement with original payment identifiers.

    This parses structural fields, not a bank rulebook or settlement model.
    Mixed currencies are refused because no exchange rates are available.
    """
    if not payload or len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError("Payment must be non-empty and at most 8 MiB")
    root = fromstring(payload, forbid_dtd=True)
    match = re.fullmatch(
        r"\{urn:iso:std:iso:20022:tech:xsd:(pain\.001\.001\.[0-9]{2})\}Document",
        root.tag,
    )
    if not match:
        raise ValueError("Expected a pain.001 Document")
    message_type = match[1]
    namespace = root.tag.split("}")[0] + "}"
    initiation = root.find(namespace + "CstmrCdtTrfInitn")
    if initiation is None:
        raise ValueError("Missing customer credit transfer initiation")

    def path(*parts: str) -> str:
        """Build an exact namespace-qualified path."""
        return "/".join(namespace + part for part in parts)

    original_id = _text(initiation, path("GrpHdr", "MsgId"))
    blocks = initiation.findall(path("PmtInf"))
    if not blocks:
        raise ValueError("Payment has no payment information blocks")
    total = Decimal(0)
    currencies = set()
    rows = []
    for block in blocks:
        payment_id = _text(block, path("PmtInfId"))
        transactions = block.findall(path("CdtTrfTxInf"))
        if not transactions:
            raise ValueError("Payment block has no transactions")
        for transaction in transactions:
            end_to_end = _text(transaction, path("PmtId", "EndToEndId"))
            amount = transaction.find(path("Amt", "InstdAmt"))
            if amount is None or not amount.text or len(amount.text) > 32:
                raise ValueError("Missing or oversized instructed amount")
            try:
                number = Decimal(amount.text)
            except InvalidOperation as exc:
                raise ValueError("Invalid instructed amount") from exc
            if not number.is_finite() or number <= 0:
                raise ValueError(
                    "Instructed amount must be positive and finite"
                )
            currency = amount.get("Ccy", "")
            if not re.fullmatch(r"[A-Z]{3}", currency):
                raise ValueError("Missing currency")
            currencies.add(currency)
            total += number
            rows.append(
                {
                    "original_payment_information_id": payment_id,
                    "original_end_to_end_id": end_to_end,
                }
            )
    if len(currencies) != 1:
        raise ValueError(
            "Mixed-currency totals require an explicit exchange-rate policy"
        )
    countries = {
        (node.text or "")[:2].upper()
        for node in initiation.iter(namespace + "IBAN")
    }
    matched = next(
        (rule for rule in rules if rule.matches(total, countries)), None
    )
    status = matched.status if matched else "ACCP"
    for row in rows:
        row.update(
            payment_information_status=status, transaction_status=status
        )
        if matched:
            row["status_reason"] = matched.reason_code
    # The core builder owns XML serialization. Its current contract supports
    # reason codes, not free-text reason descriptions; do not rewrite its XML.
    return build_pain002_report(
        "MOCK-" + hashlib.sha256(payload).hexdigest()[:24],
        original_id,
        status,
        rows,
        original_message_name_id=message_type,
    )
