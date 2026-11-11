# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The SFTP listener negotiates no SHA-1 key exchange, MAC or signature.

asyncssh's defaults still accept diffie-hellman-group14-sha1,
hmac-sha1 and ssh-rsa (RSA with SHA-1); a client that offers only one
of those is refused, and an ordinary client still connects.
"""

import asyncio

import asyncssh
import pytest
from test_mockbank import RULES

from pain001_mockbank.rules import load_rules
from pain001_mockbank.server import Bank, start_server


async def _connect(tmp_path, **algorithms):
    bank = Bank(tmp_path / "mailbox", load_rules(RULES))
    key = asyncssh.generate_private_key("ssh-rsa", key_size=2048)
    listener = await start_server(
        bank, "synthetic", "test-only-password", key, port=0
    )
    async with listener:
        async with asyncssh.connect(
            "127.0.0.1",
            port=listener.get_port(),
            username="synthetic",
            password="test-only-password",
            known_hosts=None,
            **algorithms,
        ) as connection:
            return connection.get_extra_info("send_mac")


@pytest.mark.parametrize(
    "algorithms",
    [
        {"kex_algs": ["diffie-hellman-group14-sha1"]},
        {"mac_algs": ["hmac-sha1"], "encryption_algs": ["aes128-ctr"]},
        {"server_host_key_algs": ["ssh-rsa"]},
    ],
    ids=["kex", "mac", "host-key-signature"],
)
def test_sha1_only_client_is_refused(tmp_path, algorithms):
    with pytest.raises(asyncssh.Error):
        asyncio.run(_connect(tmp_path, **algorithms))


def test_ordinary_client_still_connects(tmp_path):
    assert asyncio.run(_connect(tmp_path)) is not None
