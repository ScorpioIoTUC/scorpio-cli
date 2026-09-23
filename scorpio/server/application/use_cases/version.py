"""Application operations independent of HTTP and concrete adapters."""

from ..contracts.ports import HostInfo, Releases


class VersionUseCases:
    def __init__(self, github_client: Releases, host: HostInfo) -> None:
        self.github_client = github_client
        self.host = host

    def get_system_version(self) -> dict:
        scorpio_latest_release = self.github_client.get_latest_release()
        return {
            "scorpio_cli": self.host.get_package_version("scorpio-cli"),
            "scorpio_project": scorpio_latest_release.version,
        }
