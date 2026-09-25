# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Synthetic-only acknowledgements, resource limits and real SFTP transfers."""

import asyncio
import io
import time
from decimal import Decimal
from unittest.mock import Mock
from xml.etree import ElementTree as ET

import asyncssh
import pytest
from fastapi.testclient import TestClient

from pain001_mockbank.processor import MAX_UPLOAD_BYTES, make_reply
from pain001_mockbank.rules import load_rules
from pain001_mockbank.server import (
    Bank,
    PasswordServer,
    PaymentSFTP,
    rest_app,
    start_server,
)

PAYMENT = (
    b'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">'
    b"<CstmrCdtTrfInitn><GrpHdr><MsgId>SYNTHETIC-1</MsgId></GrpHdr>"
    b"<PmtInf><PmtInfId>BATCH-1</PmtInfId><DbtrAcct><Id>"
    b"<IBAN>DE89370400440532013000</IBAN></Id></DbtrAcct><CdtTrfTxInf>"
    b"<PmtId><EndToEndId>END-1</EndToEndId></PmtId><Amt>"
    b'<InstdAmt Ccy="EUR">100.00</InstdAmt></Amt></CdtTrfTxInf>'
    b"</PmtInf></CstmrCdtTrfInitn></Document>"
)
RULES = """rules:
  - if: total_amount > 1_000_000
    reaction: reject
    reason_code: NARR
    reason: Total exceeds 1M limit
  - if: any_iban_country == "XX"
    reaction: pending
"""


@pytest.mark.parametrize(
    "payload,status",
    [
        (PAYMENT, "ACCP"),
        (PAYMENT.replace(b"100.00", b"2000000.00"), "RJCT"),
        (PAYMENT.replace(b"DE89370400440532013000", b"XX-SYNTHETIC"), "PDNG"),
    ],
)
def test_reply_matches_original(payload, status):
    """Replies carry the original group, batch and transaction identifiers."""
    root = ET.fromstring(make_reply(payload, load_rules(RULES)))
    assert root.findtext(".//{*}OrgnlMsgId") == "SYNTHETIC-1"
    assert root.findtext(".//{*}OrgnlPmtInfId") == "BATCH-1"
    assert root.findtext(".//{*}OrgnlEndToEndId") == "END-1"
    assert root.findtext(".//{*}GrpSts") == status
    assert root.findtext(".//{*}TxSts") == status
    if status != "ACCP":
        assert root.findtext(".//{*}Rsn/{*}Cd") == "NARR"


@pytest.mark.parametrize(
    "operator,match",
    [("<", False), ("<=", True), ("==", True), (">", False), (">=", True)],
)
def test_amount_operators(operator, match):
    """Every supported comparison evaluates exact decimal values."""
    rule = load_rules(
        f"rules:\n- if: total_amount {operator} 12.34\n  reaction: reject"
    )[0]
    assert rule.matches(Decimal("12.34"), set()) is match


@pytest.mark.parametrize(
    "text",
    [
        "x" * 65537,
        "[",
        "{}",
        "rules: nope",
        "rules:\n- 1",
        "rules:\n- if: true",
        "rules: [!!str x]",
        "rules: [&a {}, *a]",
        "rules:\n- if: 'open(1)'\n  reaction: reject",
        "rules:\n- if: total_amount > 1\n  reaction: execute",
        "rules:\n- if: total_amount > 1\n  reaction: reject\n"
        "  reason_code: bad",
        "rules:\n- if: total_amount > 1\n  reaction: reject\n  reason: ''",
        "rules:\n- if: total_amount > 1\n  reaction: reject\n  extra: 1",
        "rules:\n- if: true\n  reaction: reject",
        "rules:\n- if: total_amount > 1\n  reaction: reject\n"
        "  reason_code: 1234",
        "rules:\n- if: total_amount > 1\n  reaction: reject\n  reason: 123",
    ],
)
def test_invalid_rules(text):
    """Rule files cannot execute code or bypass their bounded schema."""
    with pytest.raises(ValueError):
        load_rules(text)


def test_rule_count_limit():
    """Oversized lists are rejected before condition compilation."""
    with pytest.raises(ValueError):
        load_rules(
            "rules:\n" + "- if: total_amount > 1\n  reaction: reject\n" * 65
        )
    assert load_rules("rules: []") == []


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"x" * (MAX_UPLOAD_BYTES + 1),
        b"<root/>",
        PAYMENT.replace(b"CstmrCdtTrfInitn", b"Other"),
        PAYMENT.replace(b"SYNTHETIC-1", b""),
        PAYMENT.replace(b"PmtInf>", b"Other>"),
        PAYMENT.replace(b"CdtTrfTxInf", b"Other"),
        PAYMENT.replace(b"100.00", b""),
        PAYMENT.replace(b"100.00", b"nonsense"),
        PAYMENT.replace(b"100.00", b"NaN"),
        PAYMENT.replace(b"100.00", b"-1"),
        PAYMENT.replace(b' Ccy="EUR"', b""),
        PAYMENT.replace(b"100.00", b"1" * 33),
    ],
)
def test_invalid_payment(payload):
    """Missing identifiers and unsafe monetary values are not invented."""
    with pytest.raises(ValueError):
        make_reply(payload, [])


def test_mixed_currency_refused():
    """No implicit foreign-exchange assumptions enter rejection rules."""
    transaction = PAYMENT.split(b"<CdtTrfTxInf>")[1].split(b"</CdtTrfTxInf>")[
        0
    ]
    second = (
        b"<CdtTrfTxInf>"
        + transaction.replace(b"EUR", b"USD")
        + b"</CdtTrfTxInf>"
    )
    with pytest.raises(ValueError, match="Mixed-currency"):
        make_reply(PAYMENT.replace(b"</PmtInf>", second + b"</PmtInf>"), [])


def test_xml_entities_rejected():
    """A DTD cannot read local files or expand an entity bomb."""
    with pytest.raises(Exception, match="DTDForbidden"):
        make_reply(b'<!DOCTYPE x [<!ENTITY x "unsafe">]>' + PAYMENT, [])


@pytest.mark.parametrize("staged,status", [(False, "ACCP"), (True, "RJCT")])
def test_sftp_roundtrip_under_one_second(tmp_path, staged, status):
    """Real authenticated SFTP yields a matching reply before one second."""

    async def scenario():
        bank = Bank(tmp_path / "mailbox", load_rules(RULES))
        key = asyncssh.generate_private_key("ssh-ed25519")
        listener = await start_server(
            bank, "synthetic", "test-only-password", key, port=0
        )
        async with listener:
            port = listener.get_port()
            hosts = tmp_path / "known_hosts"
            hosts.write_text(
                f"[127.0.0.1]:{port} " + key.export_public_key().decode(),
                encoding="utf-8",
            )
            async with asyncssh.connect(
                "127.0.0.1",
                port=port,
                username="synthetic",
                password="test-only-password",
                known_hosts=str(hosts),
            ) as connection:
                async with connection.start_sftp_client() as client:
                    payload = (
                        PAYMENT.replace(b"100.00", b"2000000.00")
                        if staged
                        else PAYMENT
                    )
                    start = time.monotonic()
                    path = (
                        "/inbox/payment.tmp"
                        if staged
                        else "/inbox/payment.xml"
                    )
                    async with client.open(path, "wb") as stream:
                        await stream.write(payload)
                    if staged:
                        assert await client.listdir("/outbox") == [".", ".."]
                        await client.rename(path, "/inbox/payment.xml")
                    async with client.open(
                        "/outbox/payment.xml.pain002.xml", "rb"
                    ) as stream:
                        reply = await stream.read()
                    assert time.monotonic() - start < 1
                    assert (
                        ET.fromstring(reply).findtext(".//{*}GrpSts") == status
                    )
                    with pytest.raises(asyncssh.SFTPError):
                        await client.open("/outbox/forbidden.xml", "wb")
                    with pytest.raises(asyncssh.SFTPError):
                        await client.symlink(
                            "/inbox/payment.xml", "/inbox/link"
                        )
                    await client.remove("/inbox/payment.xml")
                    await client.remove("/outbox/payment.xml.pain002.xml")

    asyncio.run(scenario())


def test_bank_quotas_and_duplicate(tmp_path):
    """Replies are never overwritten and mailboxes are bounded."""
    bank = Bank(tmp_path, [])
    target = bank.inbox / "payment.xml"
    target.write_bytes(PAYMENT)
    bank.publish(target)
    bank.publish(target)
    assert len(bank.replies) == 1
    for index in range(99):
        (bank.outbox / str(index)).touch()
    second = bank.inbox / "second.xml"
    second.write_bytes(PAYMENT)
    with pytest.raises(ValueError, match="quota"):
        bank.publish(second)


def test_rest_history(tmp_path):
    """REST limits history, orders newest first and rejects bad bounds."""
    bank = Bank(tmp_path, [])
    bank.replies.extend(
        [
            {"filename": "first", "xml": "one"},
            {"filename": "second", "xml": "two"},
        ]
    )
    client = TestClient(rest_app(bank))
    assert client.get("/replies?limit=1").json() == [
        {"filename": "second", "xml": "two"}
    ]
    assert client.get("/replies?limit=101").status_code == 422


def test_password_and_empty_credentials(tmp_path):
    """No implicit test password or unauthenticated SFTP mode exists."""
    server = PasswordServer("user", "pass")
    assert server.begin_auth("user") and server.password_auth_supported()
    assert server.validate_password("user", "pass")
    assert not server.validate_password("bad", "pass")
    assert not server.validate_password("user", "bad")
    with pytest.raises(ValueError, match="credentials"):
        asyncio.run(
            start_server(
                Bank(tmp_path, []),
                "user",
                "",
                asyncssh.generate_private_key("ssh-ed25519"),
            )
        )


def test_invalid_mailboxes(tmp_path):
    """Configuration cannot escape the root or collapse inbox and outbox."""
    for inbox, outbox in [("../escape", "outbox"), ("same", "same")]:
        with pytest.raises(ValueError):
            Bank(tmp_path, [], inbox, outbox)
    (tmp_path / "outside").mkdir()
    (tmp_path / "inbox").symlink_to(
        tmp_path / "outside", target_is_directory=True
    )
    with pytest.raises(ValueError, match="symlinks"):
        Bank(tmp_path, [])


def test_sftp_failure_paths(tmp_path):
    """SFTP refuses out-of-root writes, oversize data and open-file rename."""
    bank = Bank(tmp_path, [])
    server = PaymentSFTP(Mock(), bank)
    stream = server.open(
        b"/inbox/broken.xml", asyncssh.FXF_WRITE, asyncssh.SFTPAttrs()
    )
    with pytest.raises(asyncssh.SFTPFailure):
        server.write(stream, MAX_UPLOAD_BYTES, b"x")
    with pytest.raises(asyncssh.SFTPFailure):
        server.rename(b"/inbox/broken.xml", b"/inbox/other.xml")
    server.write(stream, 0, b"broken")
    with pytest.raises(asyncssh.SFTPFailure, match="invalid input"):
        server.close(stream)
    for index in range(99):
        (bank.inbox / str(index)).touch()
    with pytest.raises(asyncssh.SFTPFailure, match="quota"):
        server.open(
            b"/inbox/full.xml", asyncssh.FXF_WRITE, asyncssh.SFTPAttrs()
        )
    with pytest.raises(asyncssh.SFTPPermissionDenied):
        server.open(b"/escape", asyncssh.FXF_READ, asyncssh.SFTPAttrs())
    with pytest.raises(asyncssh.SFTPFailure):
        server.write(io.BytesIO(), 0, b"x")
    staged = bank.inbox / "0"
    staged.write_bytes(PAYMENT)
    server.posix_rename(b"/inbox/0", b"/inbox/final.xml")
    assert (bank.outbox / "final.xml.pain002.xml").is_file()
