# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Upload two synthetic payments and print the bank's pain.002 statuses.

Starts the mock bank in-process on a free loopback port with the rules
in ``examples/rules.yaml`` and an ephemeral host key, connects as an
SFTP client that trusts exactly that key, uploads a payment under the
rules' 1,000,000 limit and one over it, then reads each reply from the
outbox. Nothing leaves the machine and every value is synthetic.

Run it with ``poetry run python examples/upload_and_collect.py``.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET  # nosec B405 - parses our own reply

import asyncssh

from pain001_mockbank.rules import load_rules
from pain001_mockbank.server import Bank, start_server

HERE = Path(__file__).resolve().parent
USERNAME, PASSWORD = "synthetic", "test-only-password"

# A minimal synthetic pain.001: one block, one transaction. The IBAN is
# the well-known documentation example and passes mod-97.
PAYMENT = """\
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
<CstmrCdtTrfInitn><GrpHdr><MsgId>EXAMPLE-{n}</MsgId></GrpHdr>
<PmtInf><PmtInfId>BATCH-{n}</PmtInfId><DbtrAcct><Id>
<IBAN>DE89370400440532013000</IBAN></Id></DbtrAcct><CdtTrfTxInf>
<PmtId><EndToEndId>END-{n}</EndToEndId></PmtId><Amt>
<InstdAmt Ccy="EUR">{amount}</InstdAmt></Amt></CdtTrfTxInf>
</PmtInf></CstmrCdtTrfInitn></Document>
"""


async def upload(client: asyncssh.SFTPClient, name: str, xml: str) -> str:
    """Upload one payment and return the group status of its reply."""
    async with client.open(f"/inbox/{name}", "wb") as stream:
        await stream.write(xml.encode())
    async with client.open(f"/outbox/{name}.pain002.xml", "rb") as stream:
        reply = await stream.read()
    return ET.fromstring(reply).findtext(".//{*}GrpSts") or "?"  # nosec B314


async def main() -> None:
    """Run the bank, upload both payments and print their statuses."""
    rules = load_rules((HERE / "rules.yaml").read_text(encoding="utf-8"))
    key = asyncssh.generate_private_key("ssh-ed25519")
    with tempfile.TemporaryDirectory() as work:
        bank = Bank(Path(work) / "mailbox", rules)
        listener = await start_server(bank, USERNAME, PASSWORD, key, port=0)
        async with listener:
            port = listener.get_port()
            known_hosts = Path(work) / "known_hosts"
            known_hosts.write_text(
                f"[127.0.0.1]:{port} {key.export_public_key().decode()}",
                encoding="utf-8",
            )
            async with asyncssh.connect(
                "127.0.0.1",
                port=port,
                username=USERNAME,
                password=PASSWORD,
                known_hosts=str(known_hosts),
            ) as connection:
                async with connection.start_sftp_client() as client:
                    for n, amount in ((1, "100.00"), (2, "2000000.00")):
                        xml = PAYMENT.format(n=n, amount=amount)
                        status = await upload(client, f"payment-{n}.xml", xml)
                        print(f"payment-{n}.xml EUR {amount}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
