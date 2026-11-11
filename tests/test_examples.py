# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The examples and the README Quick Start run as a reader runs them.

The README is the first code a user copies and ``examples/`` the second.
A renamed flag, a broken entry point or a rule the parser no longer
accepts then fails CI instead of the reader's terminal.
"""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import asyncssh
import pytest

from pain001_mockbank.rules import load_rules

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
BIN = Path(sys.executable).parent
PAYMENT = (
    b'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">'
    b"<CstmrCdtTrfInitn><GrpHdr><MsgId>README-1</MsgId></GrpHdr>"
    b"<PmtInf><PmtInfId>BATCH-1</PmtInfId><CdtTrfTxInf>"
    b"<PmtId><EndToEndId>END-1</EndToEndId></PmtId><Amt>"
    b'<InstdAmt Ccy="EUR">100.00</InstdAmt></Amt></CdtTrfTxInf>'
    b"</PmtInf></CstmrCdtTrfInitn></Document>"
)


def test_the_example_rules_load():
    """examples/rules.yaml is valid: one reject rule, one pending rule."""
    rules = load_rules((EXAMPLES / "rules.yaml").read_text("utf-8"))
    assert [rule.status for rule in rules] == ["RJCT", "PDNG"]


def test_upload_and_collect_prints_both_statuses():
    """The SFTP example accepts the small payment, rejects the large."""
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / "upload_and_collect.py")],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "payment-1.xml EUR 100.00: ACCP",
        "payment-2.xml EUR 2000000.00: RJCT",
    ]


def quick_start_commands() -> list[list[str]]:
    """Return the README Quick Start commands, without ``poetry run``."""
    readme = (ROOT / "README.md").read_text("utf-8")
    section = readme.split("\n## Quick Start\n", 1)[1].split("\n## ", 1)[0]
    block = re.search(r"```sh\n(.*?)```", section, re.DOTALL)
    assert block, "no sh block under '## Quick Start'"
    commands = []
    for line in block[1].splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            argv = shlex.split(line)
            commands.append(
                argv[2:] if argv[:2] == ["poetry", "run"] else argv
            )
    return commands


def free_port() -> int:
    """Return a loopback port nothing is listening on right now."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


async def collect_reply(
    port: int, public_key: str, server: subprocess.Popen[bytes]
) -> bytes:
    """Upload over SFTP, trusting only the Quick Start's host key."""
    hosts = Path("known_hosts")
    hosts.write_text(f"[127.0.0.1]:{port} {public_key}", encoding="utf-8")
    deadline = time.monotonic() + 20
    while True:
        try:
            connection = await asyncssh.connect(
                "127.0.0.1",
                port=port,
                username="synthetic",
                password="test-only-password",
                known_hosts=str(hosts),
            )
            break
        except OSError:
            if time.monotonic() > deadline or server.poll() is not None:
                raise
            await asyncio.sleep(0.2)
    async with connection, connection.start_sftp_client() as client:
        async with client.open("/inbox/payment.xml", "wb") as stream:
            await stream.write(PAYMENT)
        async with client.open(
            "/outbox/payment.xml.pain002.xml", "rb"
        ) as stream:
            return bytes(await stream.read())


@pytest.mark.skipif(not shutil.which("ssh-keygen"), reason="no ssh-keygen")
def test_the_quick_start_serves_a_reply(tmp_path, monkeypatch):
    """Generate the key, start the server, upload, read the pain.002.

    The one change to the README's commands is ``--port``: the default,
    2222, may be taken on a CI runner, so the test picks a free port.
    """
    commands = quick_start_commands()
    assert [argv[0] for argv in commands] == ["ssh-keygen", "pain001-mockbank"]
    keygen, serve = commands
    monkeypatch.chdir(tmp_path)
    subprocess.run(keygen, check=True, capture_output=True, timeout=30)
    port = free_port()
    executable = shutil.which(serve[0], path=str(BIN)) or serve[0]
    server = subprocess.Popen(
        [executable, *serve[1:], "--port", str(port)],
        env={**os.environ, "MOCKBANK_PASSWORD": "test-only-password"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        public_key = Path("mock_host_key.pub").read_text("utf-8")
        reply = asyncio.run(collect_reply(port, public_key, server))
    finally:
        server.terminate()
        _, errors = server.communicate(timeout=10)
    assert server.returncode in (0, -15), errors.decode()
    assert ET.fromstring(reply).findtext(".//{*}GrpSts") == "ACCP"
    assert (tmp_path / "mailbox" / "outbox").is_dir()
