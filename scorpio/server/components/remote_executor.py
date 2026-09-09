from __future__ import annotations
from collections.abc import Iterator
from scorpio.cli.clients.ssh.ssh_client import SSHClient


class RemoteExecutor:
    """Owns the SSH connection used by every remote Scorpio operation."""

    def __init__(self) -> None:
        self._client: SSHClient | None = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def connect(self, hostname: str, username: str, password: str) -> None:
        client = SSHClient(hostname=hostname, username=username, password=password)
        client.connect()
        self._client = client

    def close(self) -> None:
        if self._client is not None:
            self._client.close_connection()
            self._client = None

    def stream(self, command: str) -> Iterator[str]:
        if self._client is None:
            raise ConnectionError("No active SSH connection.")

        yield from self._client.execute_streaming(command)
