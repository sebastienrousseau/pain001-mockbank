# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Configured CLI lifecycle and cancellation close listeners cleanly."""

import argparse
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from pain001_mockbank import server
from pain001_mockbank.rules import Rule


@pytest.mark.parametrize("rest", [True, False])
def test_run_lifecycle(monkeypatch, tmp_path, rest):
    """REST and SFTP-only modes both close their listener."""
    key = tmp_path / "key"
    key.write_text("synthetic", encoding="utf-8")
    rules = tmp_path / "rules.yaml"
    rules.write_text("rules: []", encoding="utf-8")
    listener = MagicMock()
    listener.__aenter__ = AsyncMock()
    listener.__aexit__ = AsyncMock(return_value=False)
    start = AsyncMock(return_value=listener)
    monkeypatch.setattr(server, "start_server", start)
    monkeypatch.setattr(
        server.asyncssh, "read_private_key", lambda path: "synthetic-key"
    )
    monkeypatch.setenv("MOCKBANK_PASSWORD", "test-only")
    args = argparse.Namespace(
        root=tmp_path / "mail",
        rules=rules if rest else None,
        inbox="inbox",
        outbox="outbox",
        host_key=key,
        password_env="MOCKBANK_PASSWORD",
        username="user",
        host="127.0.0.1",
        port=0,
        rest_port=8080 if rest else None,
    )
    if rest:
        import uvicorn

        http = MagicMock()
        http.serve = AsyncMock()
        monkeypatch.setattr(uvicorn, "Server", lambda config: http)
        asyncio.run(server.run(args))
        http.serve.assert_awaited_once()
    else:

        async def cancel():
            task = asyncio.create_task(server.run(args))
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        asyncio.run(cancel())
    listener.__aexit__.assert_awaited_once()
    assert start.call_args.args[1:4] == ("user", "test-only", "synthetic-key")


def test_main_parses_settings(monkeypatch, tmp_path):
    """Options map to the coroutine with explicit host-key ownership."""
    run = AsyncMock()
    monkeypatch.setattr(server, "run", run)
    monkeypatch.setattr(
        "sys.argv",
        [
            "pain001-mockbank",
            "--username",
            "synthetic",
            "--host-key",
            str(tmp_path / "key"),
        ],
    )
    server.main()
    args = run.call_args.args[0]
    assert args.username == "synthetic"
    assert args.port == 2222 and args.host == "127.0.0.1"
    assert args.rest_port is None


def test_manually_constructed_bad_rule():
    """Bypassing the YAML parser cannot execute an invalid condition."""
    with pytest.raises(ValueError, match="not validated"):
        Rule("unsafe()", "RJCT", "NARR", "test").matches(Decimal(1), set())
