# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Authenticated, bounded SFTP service for synthetic payment tests."""

from __future__ import annotations

import argparse
import asyncio
import hmac
import os
from collections import deque
from pathlib import Path
from typing import Any, BinaryIO, cast

import asyncssh

from pain001_mockbank.processor import MAX_UPLOAD_BYTES, make_reply
from pain001_mockbank.rules import Rule, load_rules


class Bank:
    """Own an isolated inbox, outbox, archive and bounded reply history.

    A client archives a reply it has collected by renaming it from the
    outbox into the archive, as a bank's SFTP service often allows.
    """

    def __init__(
        self,
        root: Path,
        rules: list[Rule],
        inbox: str = "inbox",
        outbox: str = "outbox",
        archive: str = "archive",
    ) -> None:
        """Create the three mailboxes under root.

        Raises:
            ValueError: A name is not a simple identifier, two names are
                the same, or a mailbox is a symlink.
        """
        names = (inbox, outbox, archive)
        if (
            any(not name.isidentifier() for name in names)
            or len(set(names)) != 3
        ):
            raise ValueError(
                "Inbox, outbox and archive must be distinct simple "
                "directory names"
            )
        self.root = root.resolve()
        self.inbox = self.root / inbox
        self.outbox = self.root / outbox
        self.archive = self.root / archive
        self.rules = rules
        self.replies: deque[dict[str, str]] = deque(maxlen=100)
        for directory in (self.inbox, self.outbox, self.archive):
            directory.mkdir(parents=True, exist_ok=True)
            if directory.is_symlink():
                raise ValueError("Mailbox directories must not be symlinks")

    def publish(self, path: Path) -> None:
        """Reply only to completed .xml files, never intermediate uploads."""
        if path.suffix.lower() != ".xml":
            return
        with path.open("rb") as stream:
            payload = stream.read(MAX_UPLOAD_BYTES + 1)
        xml = make_reply(payload, self.rules)
        target = self.outbox / (path.name + ".pain002.xml")
        if target.exists():
            return
        if len(list(self.outbox.iterdir())) >= 100:
            raise ValueError("Outbox quota reached; remove old test replies")
        # Exclusive creation prevents replacing an earlier acknowledgement.
        with target.open("x", encoding="utf-8") as stream:
            stream.write(xml)
        self.replies.append({"filename": target.name, "xml": xml})


class PasswordServer(asyncssh.SSHServer):
    """Authenticate one explicitly configured synthetic-test account."""

    def __init__(self, username: str, password: str) -> None:
        """Hold the one account this server accepts."""
        self.username = username
        self.password = password

    def begin_auth(self, username: str) -> bool:
        """Require authentication for every connection."""
        return True

    def password_auth_supported(self) -> bool:
        """Advertise password authentication without a shell or forwarding."""
        return True

    def validate_password(self, username: str, password: str) -> bool:
        """Compare credentials without logging or echoing them."""
        return hmac.compare_digest(
            username.encode(), self.username.encode()
        ) and hmac.compare_digest(password.encode(), self.password.encode())


class PaymentSFTP(asyncssh.SFTPServer):
    """Restrict mutations to new inbox files and publish on close or rename."""

    def __init__(self, channel: Any, bank: Bank) -> None:
        """Serve one SFTP session chrooted to the bank's root."""
        super().__init__(channel, chroot=os.fsencode(bank.root))
        self.bank = bank
        self.writing: dict[object, Path] = {}

    def _path(self, path: bytes, *, write: bool = False) -> Path:
        """Confine a flat filename to the configured mailbox directories."""
        result = Path(os.fsdecode(self.map_path(path))).resolve()
        bank = self.bank
        allowed = (
            {bank.inbox} if write else {bank.inbox, bank.outbox, bank.archive}
        )
        if result.parent not in allowed or result.is_symlink():
            raise asyncssh.SFTPPermissionDenied(
                "Only flat mailbox files are supported"
            )
        return result

    def open(
        self, path: bytes, pflags: int, attrs: asyncssh.SFTPAttrs
    ) -> object:
        """Open readers or create an exclusive, quota-bounded inbox upload."""
        writing = bool(
            pflags
            & (
                asyncssh.FXF_WRITE
                | asyncssh.FXF_CREAT
                | asyncssh.FXF_TRUNC
                | asyncssh.FXF_APPEND
            )
        )
        target = self._path(path, write=writing)
        if writing:
            if len(list(self.bank.inbox.iterdir())) >= 100:
                raise asyncssh.SFTPFailure("Inbox quota reached")
            handle = os.fdopen(
                os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                "wb",
            )
            self.writing[handle] = target
            return handle
        return target.open("rb")

    def write(self, file_obj: object, offset: int, data: bytes) -> int:
        """Reject oversized or sparse writes before allocating file space."""
        if (
            file_obj not in self.writing
            or offset < 0
            or offset + len(data) > MAX_UPLOAD_BYTES
        ):
            raise asyncssh.SFTPFailure(
                "Upload exceeds the 8 MiB limit or handle is read-only"
            )
        stream = cast(BinaryIO, file_obj)
        stream.seek(offset)
        return stream.write(data)

    def _publish(self, path: Path) -> None:
        """Return a safe protocol error for malformed synthetic payments."""
        try:
            self.bank.publish(path)
        except Exception as exc:
            raise asyncssh.SFTPFailure(
                "Payment rejected: invalid input or outbox quota"
            ) from exc

    def close(self, file_obj: object) -> None:
        """Finish a direct upload; temporary files wait for final rename."""
        path = self.writing.pop(file_obj, None)
        cast(BinaryIO, file_obj).close()
        if path is not None:
            self._publish(path)

    def rename(self, oldpath: bytes, newpath: bytes) -> None:
        """Publish within the inbox, or archive a reply; never overwrite.

        An inbox rename publishes the finished upload. An outbox reply
        may move into the archive, which publishes nothing. Any other
        pair is refused.
        """
        old, new = self._path(oldpath), self._path(newpath)
        if (old.parent, new.parent) == (self.bank.outbox, self.bank.archive):
            os.link(old, new)
            old.unlink()
            return
        old = self._path(oldpath, write=True)
        new = self._path(newpath, write=True)
        if old in self.writing.values():
            raise asyncssh.SFTPFailure("Close the upload before renaming it")
        os.link(old, new)
        old.unlink()
        self._publish(new)

    def posix_rename(self, oldpath: bytes, newpath: bytes) -> None:
        """Even the POSIX extension must not overwrite an existing payment."""
        self.rename(oldpath, newpath)

    def remove(self, path: bytes) -> None:
        """Permit explicit cleanup of inbox files and outbox replies."""
        self._path(path).unlink()

    def _deny(self, *args: Any, **kwargs: Any) -> None:
        """Disallow links, directories and metadata-based file truncation."""
        raise asyncssh.SFTPPermissionDenied(
            "Operation disabled in the test mailbox"
        )

    symlink = _deny
    link = _deny
    mkdir = _deny
    rmdir = _deny
    setstat = _deny
    fsetstat = _deny
    lsetstat = _deny


async def start_server(
    bank: Bank,
    username: str,
    password: str,
    host_key: asyncssh.SSHKey,
    host: str = "127.0.0.1",
    port: int = 2222,
) -> asyncssh.SSHAcceptor:
    """Start an authenticated SFTP-only listener with an explicit host key."""
    if not username or not password:
        raise ValueError("Explicit non-empty test credentials are required")
    return await asyncssh.create_server(
        lambda: PasswordServer(username, password),
        host,
        port,
        server_host_keys=[host_key],
        sftp_factory=lambda channel: PaymentSFTP(channel, bank),
        allow_scp=False,
    )


def rest_app(bank: Bank) -> Any:
    """Create an optional local-test REST view of the last 100 replies."""
    from fastapi import FastAPI, Query

    app = FastAPI(title="pain001 mockbank — synthetic tests only")

    @app.get("/replies")
    def replies(
        limit: int = Query(default=10, ge=1, le=100),
    ) -> list[dict[str, str]]:
        """Return newest replies first without reading arbitrary files."""
        return list(reversed(bank.replies))[:limit]

    return app


async def run(args: argparse.Namespace) -> None:
    """Run configured listeners until cancelled, closing sockets on exit."""
    rules = (
        load_rules(args.rules.read_text(encoding="utf-8"))
        if args.rules
        else []
    )
    bank = Bank(args.root, rules, args.inbox, args.outbox, args.archive)
    key = asyncssh.read_private_key(args.host_key)
    password = os.environ.get(args.password_env, "")
    async with await start_server(
        bank, args.username, password, key, args.host, args.port
    ):
        if args.rest_port is not None:
            import uvicorn

            await uvicorn.Server(
                uvicorn.Config(
                    rest_app(bank), host=args.host, port=args.rest_port
                )
            ).serve()
        else:
            await asyncio.Event().wait()


def _parser() -> argparse.ArgumentParser:
    """Describe every option, so ``--help`` is the option reference."""
    parser = argparse.ArgumentParser(description=__doc__)
    option = parser.add_argument
    option(
        "--root",
        type=Path,
        default=Path("mailbox"),
        help="directory holding the mailboxes (default: %(default)s)",
    )
    option(
        "--rules",
        type=Path,
        help="YAML rules file; without one, every payment is ACCP",
    )
    option(
        "--host-key",
        type=Path,
        required=True,
        help="SSH host private key; generate it outside the server",
    )
    option("--username", required=True, help="the one SFTP account name")
    option(
        "--password-env",
        default="MOCKBANK_PASSWORD",
        help="variable holding the password (default: %(default)s)",
    )
    option("--host", default="127.0.0.1", help="bind address (%(default)s)")
    option("--port", type=int, default=2222, help="SFTP port (%(default)s)")
    option(
        "--inbox",
        default="inbox",
        help="upload mailbox (default: %(default)s)",
    )
    option(
        "--outbox",
        default="outbox",
        help="reply mailbox (default: %(default)s)",
    )
    option(
        "--archive",
        default="archive",
        help="collected replies (default: %(default)s)",
    )
    option(
        "--rest-port",
        type=int,
        help="serve GET /replies on this port (needs the rest extra)",
    )
    return parser


def main() -> None:
    """Parse test settings with explicit credentials and host keys."""
    asyncio.run(run(_parser().parse_args()))
