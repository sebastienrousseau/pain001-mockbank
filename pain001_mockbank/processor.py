# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Parse synthetic pain.001 uploads and build matching pain.002 replies."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation
from typing import Any
from xml.etree.ElementTree import (
    Element,  # nosec B405 - type only; defusedxml parses below
)

from defusedxml.ElementTree import fromstring
from pain001.pain002 import build_pain002_report

from pain001_mockbank.rules import Rule

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
# The initiation element, the transaction element and the amount's path
# under it for each message the mock bank answers: credit transfers
# (pain.001, Amt/InstdAmt) and direct debits (pain.008, InstdAmt).
_SHAPES = {
    "pain.001": ("CstmrCdtTrfInitn", "CdtTrfTxInf", ("Amt", "InstdAmt")),
    "pain.008": ("CstmrDrctDbtInitn", "DrctDbtTxInf", ("InstdAmt",)),
}


def _text(parent: Element, path: str) -> str:
    """Require an explicit original identifier without inventing one."""
    value = parent.findtext(path)
    if not value or not 1 <= len(value) <= 35:
        raise ValueError("Missing or oversized payment identifier")
    return value


def _path(namespace: str, *parts: str) -> str:
    """Build an exact namespace-qualified path."""
    return "/".join(namespace + part for part in parts)


def _initiation(
    payload: bytes,
) -> tuple[str, str, Element, tuple[str, tuple[str, ...]]]:
    """Parse the payment and find its initiation element.

    Returns:
        The message type, its namespace, the initiation element, and its
        transaction element's name with the amount's path under it.

    Raises:
        ValueError: Empty, oversized, or not a pain.001 or pain.008.
    """
    if not payload or len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError("Payment must be non-empty and at most 8 MiB")
    root = fromstring(payload, forbid_dtd=True)
    match = re.fullmatch(
        r"\{urn:iso:std:iso:20022:tech:xsd:((pain\.00[18])\.001\.[0-9]{2})\}Document",
        root.tag,
    )
    if not match:
        raise ValueError("Expected a pain.001 or pain.008 Document")
    initiation_tag, transaction_tag, amount_path = _SHAPES[match[2]]
    namespace = root.tag.split("}")[0] + "}"
    initiation = root.find(namespace + initiation_tag)
    if initiation is None:
        raise ValueError(f"Missing {initiation_tag}")
    return match[1], namespace, initiation, (transaction_tag, amount_path)


def _amount(
    transaction: Element, namespace: str, amount_path: tuple[str, ...]
) -> tuple[Decimal, str]:
    """Return a transaction's instructed amount and currency.

    Raises:
        ValueError: Missing, oversized, non-finite or non-positive, or
            without a currency.
    """
    amount = transaction.find(_path(namespace, *amount_path))
    if amount is None or not amount.text or len(amount.text) > 32:
        raise ValueError("Missing or oversized instructed amount")
    try:
        number = Decimal(amount.text)
    except InvalidOperation as exc:
        raise ValueError("Invalid instructed amount") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError("Instructed amount must be positive and finite")
    currency = amount.get("Ccy", "")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("Missing currency")
    return number, currency


def _rows(
    initiation: Element,
    namespace: str,
    shape: tuple[str, tuple[str, ...]],
) -> tuple[list[dict[str, Any]], Decimal]:
    """Collect each block's transaction identifiers and the total.

    Returns one row per payment block, its transactions listed under
    ``transactions``, as the pain.002 builder groups them, and the
    single-currency total of every instructed amount.

    Raises:
        ValueError: No blocks, an empty block, or mixed currencies.
    """
    transaction_tag, amount_path = shape
    blocks = initiation.findall(_path(namespace, "PmtInf"))
    if not blocks:
        raise ValueError("Payment has no payment information blocks")
    total, currencies, rows = Decimal(0), set(), []
    for block in blocks:
        transactions = block.findall(_path(namespace, transaction_tag))
        if not transactions:
            raise ValueError("Payment block has no transactions")
        listed = []
        for transaction in transactions:
            end_to_end = _text(
                transaction, _path(namespace, "PmtId", "EndToEndId")
            )
            number, currency = _amount(transaction, namespace, amount_path)
            currencies.add(currency)
            total += number
            listed.append({"original_end_to_end_id": end_to_end})
        rows.append(
            {
                "original_payment_information_id": _text(
                    block, _path(namespace, "PmtInfId")
                ),
                "transactions": listed,
            }
        )
    if len(currencies) != 1:
        raise ValueError(
            "Mixed-currency totals require an explicit exchange-rate policy"
        )
    return rows, total


def make_reply(payload: bytes, rules: list[Rule]) -> str:
    """Return a group acknowledgement with original payment identifiers.

    This parses structural fields, not a bank rulebook or settlement model.
    Mixed currencies are refused because no exchange rates are available.
    Credit transfers (pain.001) and direct debits (pain.008) are answered.
    """
    message_type, namespace, initiation, shape = _initiation(payload)
    original_id = _text(initiation, _path(namespace, "GrpHdr", "MsgId"))
    rows, total = _rows(initiation, namespace, shape)
    countries = {
        (node.text or "")[:2].upper()
        for node in initiation.iter(namespace + "IBAN")
    }
    matched = next(
        (rule for rule in rules if rule.matches(total, countries)), None
    )
    status = matched.status if matched else "ACCP"
    for row in rows:
        row["payment_information_status"] = status
        for tx in row["transactions"]:
            tx["transaction_status"] = status
            if matched:
                tx["status_reason"] = matched.reason_code
    # The core builder owns XML serialization. Its current contract supports
    # reason codes, not free-text reason descriptions; do not rewrite its XML.
    return build_pain002_report(
        "MOCK-" + hashlib.sha256(payload).hexdigest()[:24],
        original_id,
        status,
        rows,
        original_message_name_id=message_type,
    )
