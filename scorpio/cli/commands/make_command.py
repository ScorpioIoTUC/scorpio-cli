from scorpio.cli.commands.commands_types import CommandContract
from scorpio.cli.clients.github.github_contract import GithubContract
import subprocess
import sys
from collections.abc import Callable


class MakeCommand(CommandContract):
    def __init__(
        self,
        github_client: GithubContract,
        target: str | list[str],
        ensure_latest: bool = False,
        name: str | None = None,
    ) -> None:
        self.github_client = github_client
        self.target = target
        self.ensure_latest = ensure_latest
        self.name = name

    def execute(self, output_callback: Callable[[str], None] | None = None) -> None:
        if self.ensure_latest:
            directory, _ = self.github_client.ensure_latest_release()
        else:
            directory, _ = self.github_client.ensure_project_installed()

        try:
            # Validate if the target is a sequence of commands or a single command
            if isinstance(self.target, list):
                for t in self.target:
                    self._run_make(t, directory, output_callback)
            else:
                self._run_make(self.target, directory, output_callback)
        except subprocess.CalledProcessError as error:
            print(
                f"Scorpio command 'make {self.target}' failed with "
                f"exit code {error.returncode}. See the output above for the cause.",
                file=sys.stderr,
            )
            raise SystemExit(error.returncode) from None

    def _run_make(
        self,
        target: str,
        directory: str,
        output_callback: Callable[[str], None] | None,
    ) -> None:
        process = subprocess.Popen(
            ["make", target],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None

        for line in process.stdout:
            print(line, end="")
            if output_callback is not None:
                output_callback(line.rstrip("\n"))

        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, ["make", target])


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
