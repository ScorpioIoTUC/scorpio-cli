"""Dependencies supplied to use cases by the composition root.

Implementations are structural: adapters need not inherit these protocols.
Storage contains the existing JSON document; no new entity model is introduced.
"""

from collections.abc import Callable, Iterator
from datetime import tzinfo
from typing import Any, Protocol


class Storage(Protocol):
    """Read snapshots and replace the persisted server configuration."""

    def get(self) -> dict[str, Any]:
        """Return the complete document, including setup and SSH state."""
        ...

    def update(self, data: dict[str, Any]) -> None:
        """Replace the document; callers must preserve unrelated fields."""
        ...

    def update_scorpio_cli_version(self, version: str) -> None:
        """Change only the installed CLI version under setup.version."""
        ...


class RemoteCommands(Protocol):
    """Shared SSH session; stream raises on disconnect or command failure."""

    @property
    def is_connected(self) -> bool: ...
    def connect(self, hostname: str, username: str, password: str) -> None: ...
    def close(self) -> None: ...
    def stream(self, command: str) -> Iterator[str]:
        """Execute remotely and yield output without closing the session."""
        ...


class Release(Protocol):
    """Only the release tag is required by setup and version queries."""

    version: str


class Releases(Protocol):
    def get_latest_release(self) -> Release:
        """Resolve the latest project release or propagate the lookup error."""
        ...


class HostInfo(Protocol):
    def get_package_version(self, name: str) -> str | None:
        """Return the locally installed version, or None if absent."""
        ...

    def get_local_timezone(self) -> tzinfo: ...


class SetupJobs(Protocol):
    """Background installation state shared across requests."""

    def get_status(self) -> dict[str, Any]: ...
    def start(
        self,
        executor: RemoteCommands,
        command: str,
        on_success: Callable[[], None] | None = None,
    ) -> bool:
        """Start once; return False if running. Invoke callback on success."""
        ...


class StatusQueries(Protocol):
    def get_docker_compose_status(self) -> dict[str, Any]:
        """Return running and services; unavailable hosts report stopped."""
        ...

    def get_pypi_last_version(self) -> dict[str, Any]:
        """Return current/latest versions, or 'unknown' on lookup failure."""
        ...


class PackageUpgradeError(Exception):
    """Failed local upgrade, with the original command's output as details."""


class PackageInstaller(Protocol):
    def upgrade(self) -> None:
        """Upgrade local scorpio-cli; raise PackageUpgradeError on failure."""
        ...


class TokenEnvironment(Protocol):
    def update(self, api_url: str, token: str) -> None:
        """Update the local project .env while preserving unrelated keys."""
        ...


class DiscordDelivery(Protocol):
    def send(self, token: str, channel_id: str, message: str) -> str | None:
        """Return None on delivery, or the existing public error message."""
        ...
