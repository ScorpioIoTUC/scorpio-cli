from scorpio.cli.commands.commands_types import CommandContract
from scorpio.cli.clients.github.github_contract import GithubContract
import subprocess
import sys


class MakeCommand(CommandContract):
    def __init__(
        self,
        github_client: GithubContract,
        target: str,
        ensure_latest: bool = False,
    ) -> None:
        self.github_client = github_client
        self.target = target
        self.ensure_latest = ensure_latest

    def execute(self) -> None:
        if self.ensure_latest:
            directory, _ = self.github_client.ensure_latest_release()
        else:
            directory, _ = self.github_client.ensure_project_installed()

        try:
            subprocess.run(
                ["make", self.target],
                cwd=directory,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            print(
                f"Scorpio command 'make {self.target}' failed with "
                f"exit code {error.returncode}. See the output above for the cause.",
                file=sys.stderr,
            )
            raise SystemExit(error.returncode) from None


class ResetCommand(CommandContract):
    def __init__(self, make_command: MakeCommand):
        self.make_command = make_command

    def execute(self) -> None:
        print("WARNING: this will permanently delete Scorpio Docker data.")
        print("MQTT data, logs and the SQLite database will be removed.")

        try:
            confirmation = input("Type 'reset' to continue: ")
        except (EOFError, KeyboardInterrupt):
            print("\nReset cancelled.")
            return

        if confirmation.strip().lower() != "reset":
            print("Reset cancelled.")
            return

        self.make_command.execute()
