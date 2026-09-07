from .commands_types import CommandContract
from scorpio.cli.clients.github.github_contract import GithubContract
from scorpio.cli.host.host import Host


class VersionCommand(CommandContract):
    def __init__(self, github_client: GithubContract):
        self.github_client = github_client

    def execute(self) -> None:
        scorpio_project_latest_release = self.github_client.get_latest_release()
        scorpio_project_version = scorpio_project_latest_release.version
        scorpio_cli_version = Host.get_package_version("scorpio-cli")
        print(f"Scorpio Project Version: {scorpio_project_version}")
        print(f"Scorpio CLI Version: {scorpio_cli_version}")
